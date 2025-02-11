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
from utils.retrieve_course_config import retrieve_course_config
import re

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    try:
        headers = event.get("headers", {})
        auth_token = headers.get("Authorization", "")
        if not auth_token:
            return {
                "statusCode": 400,
                'headers': {
                    'Access-Control-Allow-Headers': '*',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': '*'
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
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': '*'
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
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': '*'
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
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': '*'
                },
                "body": json.dumps({"error": "Missing required parameter: course"})
            }
        
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
        ret2 = retrieve_course_config(DB_CONFIG, course_id)

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': '*'
            },
            # 'body': json.dumps("Returns the current course configuration.")
            # 'body': json.dumps({"db create": ret1, "db retrieve": ret2,})
            'body': json.dumps(ret2)
        }
    except Exception as e:
        print(f"Error invoking Lambda function: {e}")
        return {
            "statusCode": 400,
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': '*'
            },
            "body": json.dumps({"error": "Unexpected error when invoking get course config function."})
        }