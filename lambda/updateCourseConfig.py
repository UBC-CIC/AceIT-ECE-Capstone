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
    custom_response_format = body.get("customResponseFormat", "Provide clear and helpful responses.")  # Nullable field

    secret = get_secret()
    credentials = json.loads(secret)
    username = credentials['username']
    password = credentials['password']
    # Database connection parameters
    DB_CONFIG = {
        "host": "myrdsproxy.proxy-czgq6uq2qr6h.us-west-2.rds.amazonaws.com",
        "port": 5432,
        "dbname": "postgres",
        "user": username,
        "password": password,
    }
    ret1 = create_table_if_not_exists(DB_CONFIG)
    ret2 = update_course_config(DB_CONFIG, course_id, student_access_enabled, selected_supported_questions, 
                                selected_included_course_content, custom_response_format)

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
                                selected_included_course_content, custom_response_format):
    system_prompt = create_system_prompt(selected_supported_questions, custom_response_format)
    try:
        # Connect to the PostgreSQL database
        connection = psycopg2.connect(**DB_CONFIG)
        print("connect success")
        cursor = connection.cursor()

        # Query the course configuration
        query = """
        INSERT INTO course_configuration (course_id, student_access_enabled, selected_supported_questions, 
                                          selected_included_course_content, custom_response_format, system_prompt)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (course_id)
        DO UPDATE SET
            student_access_enabled = EXCLUDED.student_access_enabled,
            selected_supported_questions = EXCLUDED.selected_supported_questions,
            selected_included_course_content = EXCLUDED.selected_included_course_content,
            custom_response_format = EXCLUDED.custom_response_format,
            system_prompt = EXCLUDED.system_prompt
        """
        cursor.execute(query, (str(course_id), 
            student_access_enabled, 
            json.dumps(selected_supported_questions), 
            json.dumps(selected_included_course_content), 
            custom_response_format, system_prompt))
        # query = """DROP TABLE IF EXISTS course_configuration CASCADE;"""
        # cursor.execute(query)
        # create_course_config_query = """
        # CREATE TABLE IF NOT EXISTS course_configuration (
        #     course_id TEXT PRIMARY KEY,                         -- Unique ID for the course
        #     student_access_enabled BOOLEAN NOT NULL,             -- Whether student access is enabled
        #     selected_supported_questions JSONB NOT NULL,         -- Supported questions as JSON -- controlled from system msg
        #     selected_included_course_content JSONB NOT NULL,     -- Included content as JSON -- controlled from s3 buckets download
        #     custom_response_format TEXT,                          -- Instruction for LLM -- controlled from system msg
        #     system_prompt TEXT,                                  -- Auto-generated system prompt for the assistant
        #     material_last_updated_time TIMESTAMP DEFAULT '1970-01-01 00:00:00'
        # );
        # """
        # cursor.execute(create_course_config_query)
        connection.commit()
        cursor.close()
        connection.close()
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