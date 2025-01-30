import json
import boto3
import psycopg2
import psycopg2.extras
from psycopg2.extras import DictCursor
import requests  # to make HTTP requests
import base64
import utils
import utils.get_canvas_secret
import utils.get_rds_secret

s3_client = boto3.client('s3')
lambda_client = boto3.client("lambda")

def lambda_handler(event, context):
    courses = get_all_courses()
    refreshed_courses = []

    # Invoke refreshCourse for each course
    for course in courses:
        invoke_refresh_course(course["id"])
        print(course["id"])
        refreshed_courses.append(course["id"])

    response_message = f"Courses: {', '.join(map(str, refreshed_courses))} have been refreshed."

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': json.dumps({"message": response_message})
    }


def get_all_courses():
    """
    Fetch all courses from canvas lms.
    """
    secret = utils.get_canvas_secret.get_secret()
    credentials = json.loads(secret)
    BASE_URL = credentials['baseURL']
    TOKEN = credentials['adminAccessToken']
    HEADERS = {"Authorization": f"Bearer {TOKEN}"}

    url = f"{BASE_URL}/api/v1/accounts/1/courses"
    response = requests.get(url, headers=HEADERS)
    return response.json()
    

def invoke_refresh_course(course_id):
    # Here we are calling the function as an event, passing the course_id in the Payload as query params or as part of the body depending on your Lambda setup
    url = "https://i6t0c7ypi6.execute-api.us-west-2.amazonaws.com/prod/api/llm/content/refresh"

    # Prepare the payload
    payload = {"course": course_id}
    
    try:
        # Send a POST request
        response = requests.post(url, json=payload)  # Use `json` to serialize the body as JSON
        print(f"Refreshed course {course_id}: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Error refreshing course {course_id}: {e}")