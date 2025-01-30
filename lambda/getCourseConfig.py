import json
import os
import boto3
import psycopg2
from datetime import datetime
import uuid
import psycopg2.extras
from utils.create_course_config_table import create_table_if_not_exists
from utils.get_rds_secret import get_secret

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    
    course_id = event.get("queryStringParameters", {}).get("course")
    if not course_id:
        return {
            "statusCode": 400,
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            "body": json.dumps({"error": "Missing required parameter: course"})
        }
    
    # Extract and validate headers
    # auth_token = event.get("headers", {}).get("Authorization")
    # if not auth_token:
    #     return {
    #         "statusCode": 401,
    #         'headers': {
    #             'Access-Control-Allow-Headers': 'Content-Type',
    #             'Access-Control-Allow-Origin': '*',
    #             'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
    #         },
    #         "body": json.dumps({"error": "Missing Authorization header"})
    #     }

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
    ret1 = create_table_if_not_exists(DB_CONFIG)
    ret2 = retrieve_course_config(DB_CONFIG, course_id)

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        # 'body': json.dumps("Returns the current course configuration.")
        # 'body': json.dumps({"db create": ret1, "db retrieve": ret2,})
        'body': json.dumps(ret2)
    }

def retrieve_course_config(DB_CONFIG, course_id):
    try:
        # Connect to the PostgreSQL database
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor()

        # Query the course configuration
        query = """
        SELECT student_access_enabled, selected_supported_questions, 
               selected_included_course_content, custom_response_format, system_prompt, material_last_updated_time
        FROM course_configuration
        WHERE course_id = %s
        """
        cursor.execute(query, (str(course_id),))  # Convert UUID to string
        row = cursor.fetchone()

        if not row:
            return "Course configuration not found"

        # Construct the response
        response_body = {
            "studentAccessEnabled": row[0],
            "selectedSupportedQuestions": row[1],
            "selectedIncludedCourseContent": row[2],
            "customResponseFormat": row[3],
            "systemPrompt": row[4],
            "materialLastUpdatedTime": row[5].isoformat()
        }

        # Close database connection
        cursor.close()
        connection.close()

        return response_body
    except Exception as e:
        print(f"Error: {e}")
        return "Cannot connect to db"