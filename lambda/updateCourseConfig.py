import json
import os
import boto3
import psycopg2
from datetime import datetime
import uuid
import psycopg2.extras
from utils.create_course_config_table import create_table_if_not_exists
from utils.get_rds_secret import get_secret

def lambda_handler(event, context):
    
    # Extract and validate headers
    auth_token = event.get("headers", {}).get("Authorization")
    if not auth_token:
        return {
            "statusCode": 401,
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': '*'
            },
            "body": json.dumps({"error": "Missing Authorization header"})
        }
    
    # Parse and validate the request body
    body = ""
    try:
        body = json.loads(event.get("body", "{}"))
    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': '*'
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
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': '*'
            },
            "body": json.dumps({"error": f"Missing required fields: {', '.join(missing_fields)}"})
        }

    course_id = body["course"]
    student_access_enabled = body["studentAccessEnabled"]
    selected_supported_questions = body["selectedSupportedQuestions"]
    selected_included_course_content = body["selectedIncludedCourseContent"]
    custom_response_format = body.get("customResponseFormat")  # Nullable field

    secret = get_secret()
    credentials = json.loads(secret)
    username = credentials['username']
    password = credentials['password']
    # Database connection parameters
    DB_CONFIG = {
        "host": "privaceitececapstonemainstack-t4grdsdb098395df-qli4kax6xfly.czgq6uq2qr6h.us-west-2.rds.amazonaws.com",
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
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': '*'
            },
        # 'body': json.dumps("Returns the current (updated) course configuration.")
        'body': json.dumps({"db create": ret1, "db retrieve": ret2,})
    }

def update_course_config(DB_CONFIG, course_id, student_access_enabled, selected_supported_questions, 
                                selected_included_course_content, custom_response_format):
    try:
        # Connect to the PostgreSQL database
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor()

        # Query the course configuration
        query = """
        INSERT INTO course_configuration (course_id, student_access_enabled, selected_supported_questions, 
                                          selected_included_course_content, custom_response_format)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (course_id)
        DO UPDATE SET
            student_access_enabled = EXCLUDED.student_access_enabled,
            selected_supported_questions = EXCLUDED.selected_supported_questions,
            selected_included_course_content = EXCLUDED.selected_included_course_content,
            custom_response_format = EXCLUDED.custom_response_format;
        """
        cursor.execute(query, (str(course_id), 
            student_access_enabled, 
            json.dumps(selected_supported_questions), 
            json.dumps(selected_included_course_content), 
            custom_response_format))
        connection.commit()
        cursor.close()
        connection.close()
        return "Course configuration updated successfully"
    except Exception as e:
        print(f"Error: {e}")
        return "Cannot connect to db"