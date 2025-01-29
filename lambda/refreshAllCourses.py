import json
import boto3
import psycopg2
import psycopg2.extras
from psycopg2.extras import DictCursor
import requests  # to make HTTP requests
import base64
from utils.get_rds_secret import get_secret

s3_client = boto3.client('s3')
lambda_client = boto3.client("lambda")

def lambda_handler(event, context):
    secret = get_secret()
    credentials = json.loads(secret)
    username = credentials['username']
    password = credentials['password']
    # Database connection parameters
    DB_CONFIG = {
        "host": "privaceitececapstonemainstack-t4grdsdb098395df-peocbczfvpie.czgq6uq2qr6h.us-west-2.rds.amazonaws.com",
        "port": 5432,
        "dbname": "postgres",
        "user": username,
        "password": password,
    }

    courses = get_all_courses(DB_CONFIG)
    refreshed_courses = []

    # Invoke refreshCourse for each course
    for course in courses:
        invoke_refresh_course(course["course_id"])
        print(course["course_id"])
        refreshed_courses.append(course["course_id"])

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


def get_all_courses(DB_CONFIG):
    """
    Fetch all courses from the course_configuration table.
    """
    connection = None
    try:
        # Connect to the PostgreSQL database
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor(cursor_factory=DictCursor)  # Use DictCursor for dictionary-like access

        query = "SELECT course_id FROM course_configuration;"
        cursor.execute(query)
        rows = cursor.fetchall()

        # Convert rows to list of dictionaries
        return [{"course_id": row["course_id"]} for row in rows]
    except Exception as e:
        print(f"Error fetching courses: {e}")
        return []
    finally:
        if connection:
            connection.close()

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