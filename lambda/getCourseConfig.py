import json
import os
import boto3
import psycopg2
from datetime import datetime
import uuid
import psycopg2.extras

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
    auth_token = event.get("headers", {}).get("Authorization")
    if not auth_token:
        return {
            "statusCode": 401,
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            "body": json.dumps({"error": "Missing Authorization header"})
        }

    secret = get_secret()
    credentials = json.loads(secret)
    username = credentials['username']
    password = credentials['password']
    # Database connection parameters
    DB_CONFIG = {
        "host": "privaceitececapstonemainstack-t4grdsdb098395df-k9zj5cjjmn4b.czgq6uq2qr6h.us-west-2.rds.amazonaws.com",
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
        'body': json.dumps({"db create": ret1, "db retrieve": ret2,})
    }

def get_secret():
    secret_name = "MyRdsSecretF2FB5411-AMahlTQtUobh"
    region_name = "us-west-2"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except Exception as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    secret = get_secret_value_response['SecretString']
    return secret

def create_table_if_not_exists(DB_CONFIG):
    """
    Ensure the embeddings table exists in the database.
    """
    connection = None
    try:
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor()

        create_course_config_query = """
        CREATE TABLE IF NOT EXISTS course_configuration (
            course_id UUID PRIMARY KEY,                          -- Unique ID for the course
            student_access_enabled BOOLEAN NOT NULL,             -- Whether student access is enabled
            selected_supported_questions JSONB NOT NULL,         -- Supported questions as JSON
            selected_included_course_content JSONB NOT NULL,     -- Included content as JSON
            custom_response_format TEXT,                          -- Instruction for LLM
            last_updated_time TIMESTAMP DEFAULT '1970-01-01 00:00:00'
        );
        """
        cursor.execute(create_course_config_query)
        connection.commit()
        cursor.close()
        return "DBSuccess"
    except Exception as e:
        print(f"Error creating table: {e}")
    finally:
        if connection:
            connection.close()

def retrieve_course_config(DB_CONFIG, course_id):
    try:
        # Connect to the PostgreSQL database
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor()

        # Query the course configuration
        query = """
        SELECT student_access_enabled, selected_supported_questions, 
               selected_included_course_content, custom_response_format, last_updated_time
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
            "lastUpdatedTime": row[4].isoformat()
        }

        # Close database connection
        cursor.close()
        connection.close()

        return response_body
    except Exception as e:
        print(f"Error: {e}")
        return "Cannot connect to db"