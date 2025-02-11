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
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': '*'
            },
            "body": json.dumps({"error": "Missing required fields: 'course' is required"})
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
    ret1 = delete_all_from_this_course(DB_CONFIG, course_id)

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': '*'
        },
        'body': json.dumps({"delete result": ret1})
    }

def delete_all_from_this_course(DB_CONFIG, course_id):
    # Connect to the PostgreSQL database
    try:
        # Connect to the PostgreSQL database
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor()

        # Delete query
        delete_query1 = f"""
        DROP TABLE IF EXISTS course_vectors_{course_id};
        """
        delete_query2 = """
        DELETE FROM course_configuration
        WHERE course_id = %s
        """
        cursor.execute(delete_query1)
        vectors_deleted = cursor.rowcount
        cursor.execute(delete_query2, (course_id,))
        configs_deleted = cursor.rowcount

        # Commit the transaction
        connection.commit()
        cursor.close()
        connection.close()
        print("All vectors from this course deleted!")
        print("deleted vectors: ", vectors_deleted)
        print("deleted configs: ", configs_deleted)

        # Return whether any rows were deleted
        return vectors_deleted > 0

    except Exception as e:
        print(f"Error during deletion: {e}")
        raise