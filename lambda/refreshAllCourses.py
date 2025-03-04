import json
import boto3
import psycopg2
import psycopg2.extras
from psycopg2.extras import DictCursor
import requests  # to make HTTP requests
import utils
import utils.get_canvas_secret
import utils.get_rds_secret
from utils.retrieve_course_config import call_get_course_config
from utils.construct_response import construct_response

s3_client = boto3.client('s3')
lambda_client = boto3.client("lambda")

def lambda_handler(event, context):
    courses = get_all_courses()
    if courses is None:
        return construct_response(500, {"error": "Failed to fetch courses from Canvas"})

    refreshed_courses = []
    secret = utils.get_canvas_secret.get_secret()
    credentials = json.loads(secret)
    TOKEN = credentials['adminAccessToken']

    # Invoke refreshCourse for each course
    for course in courses:
        # fetch course config and check if auto update is on
        if course["workflow_state"] == "available":
            course_config = call_get_course_config(TOKEN, course["id"], lambda_client)
            auto_update_on = course_config.get("autoUpdateOn", False)
            if (auto_update_on):
                invoke_refresh_course(course["id"])
                refreshed_courses.append(course["id"])

    response_message = f"Courses: {', '.join(map(str, refreshed_courses))} have been refreshed."

    return construct_response(200, {"message": response_message})

def get_all_courses():
    """
    Fetch all courses from canvas lms.
    """
    secret = utils.get_canvas_secret.get_secret()
    credentials = json.loads(secret)
    BASE_URL = credentials['baseURL']
    TOKEN = credentials['adminAccessToken']
    ACCOUNT_ID = credentials['adminAccountID']
    
    HEADERS = {"Authorization": f"Bearer {TOKEN}"}

    url = f"{BASE_URL}/api/v1/accounts/{ACCOUNT_ID}/courses"
    try:
        response = requests.get(url, headers=HEADERS, verify=False)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        return None
    except requests.exceptions.RequestException as req_err:
        print(f"Request error occurred: {req_err}")
        return None

def invoke_refresh_course(course_id):
    payload = {
        "body": json.dumps({"course": course_id}) 
    }
    try:
        response = lambda_client.invoke(
            FunctionName="RefreshContentLambda",  # Replace with actual function name
            # InvocationType="RequestResponse",  # Use 'Event' for async calls
            InvocationType="Event",
            Payload=json.dumps(payload)
        )
        print(f"Successfully invoked RefreshContentLambda for course {course_id}")
        return
    except Exception as e:
        print(f"Error invoking Lambda function: {e}")
        return