import json
import os
import boto3
import psycopg2
from datetime import datetime
import uuid
import psycopg2.extras
from utils.create_course_config_table import create_table_if_not_exists
from utils.get_rds_secret import get_secret
from utils.get_user_info import get_user_info
from utils.get_rds_secret import load_db_config

lambda_client = boto3.client("lambda")

def lambda_handler(event, context):
    
    # Extract and validate headers
    headers = event.get("headers", {})
    auth_token = headers.get("Authorization", "")
    if not auth_token:
        return {
            "statusCode": 400,
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': 'https://d2rs0jk5lfd7j4.cloudfront.net',
                'Access-Control-Allow-Methods': '*',
                'Access-Control-Allow-Credentials': 'true'
            },
            "body": json.dumps({"error": "Missing required Authorization token"})
        }

    # Call Canvas API to get user info
    user_info = get_user_info(auth_token)
    if not user_info:
        return {
            "statusCode": 500,
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': 'https://d2rs0jk5lfd7j4.cloudfront.net',
                'Access-Control-Allow-Methods': '*',
                'Access-Control-Allow-Credentials': 'true'
            },
            "body": json.dumps({"error": "Failed to fetch user info from Canvas"})
        }
    # Extract Canvas user ID
    student_id = user_info.get("userId")
    if not student_id:
        return {
            "statusCode": 500,
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': 'https://d2rs0jk5lfd7j4.cloudfront.net',
                'Access-Control-Allow-Methods': '*',
                'Access-Control-Allow-Credentials': 'true'
            },
            "body": json.dumps({"error": "User ID not found"})
        }
    student_id = str(student_id)

    # TODO: need to check if this user is an instructor for this course
    
    # Parse and validate the request body
    body = ""
    try:
        body = json.loads(event.get("body", "{}"))
    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': 'https://d2rs0jk5lfd7j4.cloudfront.net',
                'Access-Control-Allow-Methods': '*',
                'Access-Control-Allow-Credentials': 'true'
            },
            "body": json.dumps({"error": "Invalid JSON in request body"})
        }
    
    required_fields = [
        "course", "studentAccessEnabled", "selectedSupportedQuestions", 
        "selectedIncludedCourseContent", "customResponseFormat"
    ]
    
    missing_fields = [field for field in required_fields if field not in body]
    if missing_fields:
        return {
            "statusCode": 400,
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': 'https://d2rs0jk5lfd7j4.cloudfront.net',
                'Access-Control-Allow-Methods': '*',
                'Access-Control-Allow-Credentials': 'true'
            },
            "body": json.dumps({"error": f"Missing required fields: {', '.join(missing_fields)}"})
        }

    course_id = body["course"]
    student_access_enabled = body["studentAccessEnabled"]
    selected_supported_questions = body["selectedSupportedQuestions"]
    selected_included_course_content = body["selectedIncludedCourseContent"]
    auto_update_on = body.get("autoUpdateOn")
    custom_response_format = body.get("customResponseFormat", "Provide clear and helpful responses.")  # Nullable field

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

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Origin': 'https://d2rs0jk5lfd7j4.cloudfront.net',
            'Access-Control-Allow-Methods': '*',
            'Access-Control-Allow-Credentials': 'true'
        },
        # 'body': json.dumps("Returns the current (updated) course configuration.")
        'body': json.dumps({"db create": ret1, "db retrieve": ret2,})
    }

def update_course_config(DB_CONFIG, course_id, student_access_enabled, selected_supported_questions, 
                         selected_included_course_content, custom_response_format, auto_update_on=None):
    system_prompt = create_system_prompt(selected_supported_questions, custom_response_format)
    
    try:
        # Connect to the PostgreSQL database
        connection = psycopg2.connect(**DB_CONFIG)
        print("Connected to DB successfully")
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
        print("Invoked update prompt!")
        return "Course configuration updated successfully"

    except Exception as e:
        print(f"Error: {e}")
        return "Cannot connect to db"
    

def create_system_prompt(supported_questions, custom_response_format):
    """
    Generate a system prompt for the course assistant based on professor's settings,
    emphasizing both enabled and disabled features.
    :param settings: A dictionary containing course assistant configuration.
    :return: A formatted system prompt string.
    """
    # Define mappings for question types
    question_types = {
        "RECOMMENDATIONS": "provide study recommendations",
        "PRACTICE_PROBLEMS": "provide practice problems",
        "SOLUTION_REVIEW": "review solutions",
        "EXPLANATION": "offer detailed explanations"
    }

    # Separate enabled and disabled features
    enabled_features = [
        phrase for key, phrase in question_types.items() if supported_questions.get(key, False)
    ]
    disabled_features = [
        phrase for key, phrase in question_types.items() if not supported_questions.get(key, False)
    ]

    # Format the enabled features into a readable list
    enabled_features_list = ", ".join(enabled_features[:-1])
    if len(enabled_features) > 1:
        enabled_features_list += f", and {enabled_features[-1]}"  # Add "and" before the last item
    elif enabled_features:
        enabled_features_list = enabled_features[0]

    # Format the disabled features into a readable list (if any)
    disabled_features_list = ", ".join(disabled_features[:-1])
    if len(disabled_features) > 1:
        disabled_features_list += f", and {disabled_features[-1]}"
    elif disabled_features:
        disabled_features_list = disabled_features[0]

    # Construct the system prompt
    system_prompt = f"""
You are a course assistant on designed to help students in their learning journey. Your role is to:
{enabled_features_list}.
"""
    # Add the "Do not" section only if there are disabled features
    if disabled_features:
        system_prompt += f"""
Do not:
{disabled_features_list}.
"""

    # Add the custom response format
    system_prompt += f"""
Respond to all student inquiries in the following style: {custom_response_format}.
Ensure your responses are always accurate, engaging, and inform students when you have questions unsure or encountering a controversial topic.
"""
    print(system_prompt.strip())
    return system_prompt.strip()


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
        print(f"Successfully invoked UpdateConversationPrompt for course {course_id}")
        return
    except Exception as e:
        print(f"Error invoking Lambda function: {e}")
        return