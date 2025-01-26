import json
import os
import boto3
import psycopg2
from datetime import datetime
import uuid
import psycopg2.extras
from utils.get_rds_secret import get_secret

def lambda_handler(event, context):
    params = event.get("queryStringParameters", {})
    course_id = params.get("course")
    # Validate required fields
    if not course_id:
        return {
            "statusCode": 400,
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,GET'
            },
            "body": json.dumps({"error": "Missing required fields: 'course' is required"})
        }
    
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
    ret1 = delete_vectors_by_course(DB_CONFIG, course_id)

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': json.dumps({"delete result": ret1})
    }

def delete_vectors_by_course(DB_CONFIG, course_id):
    # Connect to the PostgreSQL database
    try:
        # Connect to the PostgreSQL database
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor()
        sanitized_course_id = course_id.replace("-", "_")

        # Delete query
        drop_table_query = f"""
        DROP TABLE IF EXISTS course_vectors_{sanitized_course_id};
        """
        cursor.execute(drop_table_query)

        connection.commit()
        cursor.close()
        return "Vectors deleted successfully"

    except Exception as e:
        print(f"Error during deletion: {e}")
        return "Error deleting vectors"