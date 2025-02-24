import json
import os
import boto3
import psycopg2
from datetime import datetime
import uuid
import psycopg2.extras
from utils.create_course_config_table import create_table_if_not_exists
from utils.get_rds_secret import get_cached_secret, load_db_config
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
        # Get database credentials
        credentials = get_cached_secret()
        username = credentials['username']
        password = credentials['password']
        static_db_config = load_db_config()
        # Combine static DB config and dynamic credentials
        DB_CONFIG = {
            **static_db_config,
            "user": username,
            "password": password
        }
        print("Connecting to database")
        DB_CONNECTION = psycopg2.connect(**DB_CONFIG)

        documents = []

        # Connect to the PostgreSQL database
        DB_CONNECTION = psycopg2.connect(**DB_CONFIG)
        cursor = DB_CONNECTION.cursor()
        print("Connected to the database successfully.")

        # Construct query to get document names and URLs
        query = f"""
        SELECT document_name, sourceURL
        FROM course_vectors_{course_id};
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        print("Query executed successfully.")
        print("Rows: ", rows)

        # Use a set to get unique pairs of document_name and source_url
        unique_documents = {
            (str(row[0]), str(row[1])) for row in rows
        }

        # Convert set back to a list of dictionaries
        documents = [
            {"document_name": name, "source_url": url} for name, url in unique_documents
        ]

        # Debugging: Check the unique documents
        print("Unique Documents List: ", json.dumps(documents, indent=2))

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': 'https://d2rs0jk5lfd7j4.cloudfront.net',
                'Access-Control-Allow-Methods': '*',
                'Access-Control-Allow-Credentials': 'true'
            },
            'body': json.dumps(documents)
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
            "body": json.dumps({"error": "Unexpected error when invoking get all materials function."})
        }
