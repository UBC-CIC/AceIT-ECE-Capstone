import json
import os
import boto3
import utils.get_canvas_secret
import utils.get_rds_secret
from utils.retrieve_course_config import call_get_course_config
from utils.construct_response import construct_response
from utils.canvas_api_calls import get_all_courses
from utils.create_course_vectors_tables import create_table_if_not_exists as create_vectors_table
from utils.create_course_config_table import create_table_if_not_exists as create_config_table

lambda_client = boto3.client("lambda")
env_prefix = os.environ.get("ENV_PREFIX")
def lambda_handler(event, context):
    courses = get_all_courses()
    if courses is None:
        return construct_response(500, {"error": "Failed to fetch courses from Canvas"})

    refreshed_courses = []
    secret = utils.get_canvas_secret.get_secret()
    credentials = json.loads(secret)
    TOKEN = credentials['adminAccessToken']
    secret = utils.get_rds_secret.get_secret()
    credentials = json.loads(secret)
    username = credentials['username']
    password = credentials['password']
    # Database connection parameters
    static_db_config = utils.get_rds_secret.load_db_config()
    # Combine static DB config and dynamic credentials
    DB_CONFIG = {
        **static_db_config,
        "user": username,
        "password": password
    }

    create_config_table(DB_CONFIG)
    # Invoke refreshCourse for each course
    for course in courses:
        # fetch course config and check if auto update is on
        if course["workflow_state"] == "available":
            course_config = call_get_course_config(TOKEN, course["id"], lambda_client)
            auto_update_on = course_config.get("autoUpdateOn", False)
            create_vectors_table(DB_CONFIG, course["id"])
            if (auto_update_on):
                invoke_refresh_course(course["id"])
                refreshed_courses.append(course["id"])

    response_message = f"Courses: {', '.join(map(str, refreshed_courses))} have been refreshed."

    return construct_response(200, {"message": response_message})

def invoke_refresh_course(course_id):
    payload = {
        "body": json.dumps({"course": course_id}) 
    }
    try:
        response = lambda_client.invoke(
            FunctionName=f"{env_prefix}RefreshContentLambda",  # Replace with actual function name
            # InvocationType="RequestResponse",  # Use 'Event' for async calls
            InvocationType="Event",
            Payload=json.dumps(payload)
        )
        print(f"Successfully invoked RefreshContentLambda for course {course_id}")
        return
    except Exception as e:
        print(f"Error invoking Lambda function: {e}")
        return