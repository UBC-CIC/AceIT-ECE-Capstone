from utils.get_user_info import get_user_info
from utils.retrieve_course_config import retrieve_course_config
from utils.construct_response import construct_response

def lambda_handler(event, context):
    try:
        headers = event.get("headers", {})
        auth_token = headers.get("Authorization", "")
        if not auth_token:
            return construct_response(400, {"error": "Missing required header field: 'Authorization' is required"})

        # Call Canvas API to get user info
        user_info = get_user_info(auth_token)
        if not user_info:
            return construct_response(500, {"error": "Failed to fetch user info from Canvas"})
        # Extract Canvas user ID
        student_id = user_info.get("userId", "")
        if not student_id:
            return construct_response(500, {"error": "User ID not found"})

        course_id = event.get("queryStringParameters", {}).get("course")
        if not course_id:
            return construct_response(400, {"error": "Missing required parameter: 'course' is required"})
        
        course_config = retrieve_course_config(str(course_id))

        return construct_response(200, course_config)
    except Exception as e:
        print(f"Error invoking Lambda function: {e}")
        return construct_response(400, {"error": "Unexpected error when invoking get course config function"})
