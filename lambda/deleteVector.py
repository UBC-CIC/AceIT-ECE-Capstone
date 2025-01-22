import json
import os
import boto3
import psycopg2
from datetime import datetime
import uuid
import psycopg2.extras


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
        "host": "privaceitececapstonemainstack-t4grdsdb098395df-d2z9wnhmh5ka.czgq6uq2qr6h.us-west-2.rds.amazonaws.com",
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

def get_secret():
    secret_name = "MyRdsSecretF2FB5411-KUVYnbkG81km"
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

def delete_vectors_by_course(DB_CONFIG, course_id):
    # Connect to the PostgreSQL database
    try:
        # Connect to the PostgreSQL database
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor()

        # Delete query
        delete_query = """
        DELETE FROM course_vectors
        WHERE course_id = %s
        """
        cursor.execute(delete_query, (course_id,))
        rows_deleted = cursor.rowcount

        # Commit the transaction
        connection.commit()
        cursor.close()
        connection.close()
        print("All vectors from this course deleted!")
        print("deleted rows: ", rows_deleted)

        # Return whether any rows were deleted
        return rows_deleted > 0

    except Exception as e:
        print(f"Error during deletion: {e}")
        raise