import json
import os
import boto3
import psycopg2
from datetime import datetime
import uuid
import psycopg2.extras
from utils.create_course_config_table import create_table_if_not_exists
from utils.get_rds_secret import get_cached_secret
from utils.get_user_info import get_user_info
from utils.retrieve_course_config import retrieve_course_config
import re

def lambda_handler(event, context):
    try:
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
        student_id = user_info.get("userId", "")
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

        course_id = event.get("queryStringParameters", {}).get("course")
        if not course_id:
            return {
                "statusCode": 400,
                'headers': {
                    'Access-Control-Allow-Headers': '*',
                    'Access-Control-Allow-Origin': 'https://d2rs0jk5lfd7j4.cloudfront.net',
                    'Access-Control-Allow-Methods': '*',
                    'Access-Control-Allow-Credentials': 'true'
                },
                "body": json.dumps({"error": "Missing required parameter: course"})
            }
        course_config = retrieve_course_config(str(course_id))
        print(course_config)

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': 'https://d2rs0jk5lfd7j4.cloudfront.net',
                'Access-Control-Allow-Methods': '*',
                'Access-Control-Allow-Credentials': 'true'
            },
            'body': json.dumps(course_config)
        }
    except Exception as e:
        print(f"Error invoking Lambda function: {e}")
        return {
            "statusCode": 400,
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': 'https://d2rs0jk5lfd7j4.cloudfront.net',
                'Access-Control-Allow-Methods': '*',
                'Access-Control-Allow-Credentials': 'true'
            },
            "body": json.dumps({"error": "Unexpected error when invoking get course config function."})
        }