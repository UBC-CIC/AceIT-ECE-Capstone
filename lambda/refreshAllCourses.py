import json
import boto3
import utils.get_canvas_secret
import utils.get_rds_secret
from utils.retrieve_course_config import call_get_course_config
from utils.construct_response import construct_response
from utils.canvas_api_calls import get_all_courses

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