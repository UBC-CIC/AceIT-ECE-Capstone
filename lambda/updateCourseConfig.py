import json
import boto3
import psycopg2
import psycopg2.extras
from utils.create_course_config_table import create_table_if_not_exists
from utils.retrieve_course_config import create_system_prompt
from utils.get_rds_secret import get_secret
from utils.get_user_info import get_user_info
from utils.get_rds_secret import load_db_config
from utils.construct_response import construct_response
from utils.canvas_api_calls import get_instructor_courses

lambda_client = boto3.client("lambda")

def lambda_handler(event, context):
    
    # Extract and validate headers
    headers = event.get("headers", {})
    auth_token = headers.get("Authorization", "")
    if not auth_token:
        return construct_response(400, {"error": "Missing required header field: 'Authorization' is required"})

    # Call Canvas API to get user info
    user_info = get_user_info(auth_token)
    if not user_info:
        return construct_response(500, {"error": "Failed to fetch user info from Canvas"})
    # Extract Canvas user ID
    student_id = user_info.get("userId")
    if not student_id:
        return construct_response(500, {"error": "User ID not found"})

    courses_as_instructor = get_instructor_courses(auth_token)
    if courses_as_instructor is None:
        return construct_response(500, {"error": "Failed to fetch instructor courses from Canvas"})
    
    list_of_courses_as_instructor = [course["id"] for course in courses_as_instructor]
    print("List of courses as instructor: ", list_of_courses_as_instructor)
    
    # Parse and validate the request body
    body = ""
    try:
        body = json.loads(event.get("body", "{}"))
    except json.JSONDecodeError:
        return construct_response(400, {"error": "Invalid JSON in request body"})
    required_fields = [
        "course", "studentAccessEnabled", "selectedSupportedQuestions", 
        "selectedIncludedCourseContent", "customResponseFormat"
    ]
    
    missing_fields = [field for field in required_fields if field not in body]
    if missing_fields:
        return construct_response(400, {"error": f"Missing required fields: {', '.join(missing_fields)}"})

    course_id = body["course"]
    student_access_enabled = body["studentAccessEnabled"]
    selected_supported_questions = body["selectedSupportedQuestions"]
    selected_included_course_content = body["selectedIncludedCourseContent"]
    auto_update_on = body.get("autoUpdateOn")
    custom_response_format = body.get("customResponseFormat", "Provide clear and helpful responses.")  # Nullable field

    if int(course_id) not in list_of_courses_as_instructor:
        return construct_response(400, {"error": "You are not the instructor for this course."})

    secret = get_secret()
    credentials = json.loads(secret)
    username = credentials['username']
    password = credentials['password']
    static_db_config = load_db_config()
    # Combine static DB config and dynamic credentials
    DB_CONFIG = {
        **static_db_config,
        "user": username,
        "password": password
    }
    ret1 = create_table_if_not_exists(DB_CONFIG)
    ret2 = update_course_config(DB_CONFIG, course_id, student_access_enabled, selected_supported_questions, 
                                selected_included_course_content, custom_response_format, auto_update_on)
    response_body = {
        "db create": ret1, 
        "db retrieve": ret2
    }

    return construct_response(200, response_body)

def update_course_config(DB_CONFIG, course_id, student_access_enabled, selected_supported_questions, 
                         selected_included_course_content, custom_response_format, auto_update_on=None):
    system_prompt = create_system_prompt(selected_supported_questions, custom_response_format)
    
    try:
        # Connect to the PostgreSQL database
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor()

        # Base query for inserting a new course config or updating existing ones
        query = """
        INSERT INTO course_configuration (course_id, student_access_enabled, selected_supported_questions, 
                                          selected_included_course_content, custom_response_format,
                                          system_prompt {auto_update_column})
        VALUES (%s, %s, %s, %s, %s, %s {auto_update_value})
        ON CONFLICT (course_id)
        DO UPDATE SET
            student_access_enabled = EXCLUDED.student_access_enabled,
            selected_supported_questions = EXCLUDED.selected_supported_questions,
            selected_included_course_content = EXCLUDED.selected_included_course_content,
            custom_response_format = EXCLUDED.custom_response_format,
            system_prompt = EXCLUDED.system_prompt
            {auto_update_update}
        """

        # Dynamically adjust query and parameters based on whether auto_update_on is provided
        query_params = [str(course_id), student_access_enabled, json.dumps(selected_supported_questions),
                        json.dumps(selected_included_course_content), custom_response_format, system_prompt]

        if auto_update_on is not None:  # Only update auto_update_on if it's provided
            query = query.format(
                auto_update_column=", auto_update_on",
                auto_update_value=", %s",
                auto_update_update=", auto_update_on = EXCLUDED.auto_update_on"
            )
            query_params.append(auto_update_on)
        else:  # Exclude auto_update_on from the update if it's missing
            query = query.format(
                auto_update_column="",
                auto_update_value="",
                auto_update_update=""
            )

        cursor.execute(query, query_params)
        connection.commit()
        cursor.close()
        connection.close()

        # Invoke prompt update
        invoke_update_system_prompt(system_prompt, course_id)
        return "Course configuration updated successfully"

    except Exception as e:
        print(f"Error: {e}")
        return "Cannot connect to db"
    

def invoke_update_system_prompt(system_prompt, course_id):
    payload = {
        "body": json.dumps({"course": course_id, "system_prompt":system_prompt}) 
    }
    try:
        lambda_client.invoke(
            FunctionName="UpdateConversationPromptLambda",  # Replace with actual function name
            # InvocationType="RequestResponse",  # Use 'Event' for async calls
            InvocationType="Event",
            Payload=json.dumps(payload)
        )
        # print(f"Successfully invoked UpdateConversationPrompt for course {course_id}")
        return
    except Exception as e:
        print(f"Error invoking Lambda function: {e}")
        return