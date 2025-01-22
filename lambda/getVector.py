import json
import os
import boto3
import psycopg2
from datetime import datetime
import uuid
import psycopg2.extras

bedrock = boto3.client("bedrock-runtime",
                       region_name = 'us-west-2')

def lambda_handler(event, context):
    params = event.get("queryStringParameters", {})
    course_id = params.get("course")
    query = params.get("query")
    num_max_results = int(params.get("numMaxResults", 8))  # Default to 8 if not provided

    # Validate required fields
    if not course_id or not query:
        return {
            "statusCode": 400,
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,GET'
            },
            "body": json.dumps({"error": "Missing required fields: 'course' and 'query' are required"})
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
    ret1 = create_table_if_not_exists(DB_CONFIG)
    query_embedding = generate_embeddings(str(query))
    ret2 = get_course_vector(DB_CONFIG, query_embedding, course_id, num_max_results)

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': json.dumps({"db": ret1, "get_vectors": ret2})
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

def create_table_if_not_exists(DB_CONFIG):
    """
    Ensure the embeddings table exists in the database.
    """
    connection = None
    try:
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        create_embeddings_query = """
        CREATE EXTENSION IF NOT EXISTS vector;
        CREATE TABLE IF NOT EXISTS course_vectors (
            id SERIAL PRIMARY KEY,
            course_id UUID REFERENCES course_configuration(course_id) ON DELETE CASCADE,
            document_name TEXT NOT NULL,
            embeddings VECTOR(1024),
            created_at TIMESTAMP DEFAULT NOW()
        );
        """

        cursor.execute(create_embeddings_query)
        connection.commit()
        cursor.close()
        return "DBSuccess"
    except Exception as e:
        print(f"Error creating table: {e}")
    finally:
        if connection:
            connection.close()

def get_course_vector(DB_CONFIG, query, course_id, num_max_results):
    # Connect to the PostgreSQL database
    try:
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor()

        # Debugging: Print all embeddings for the given course_id
        debug_sql = "SELECT document_name, embeddings FROM course_vectors WHERE course_id = %s;"
        cursor.execute(debug_sql, (str(course_id),))
        all_rows = cursor.fetchall()
        print(f"All embeddings for course_id {course_id}: {all_rows}")

        # Query the vector database with explicit casting
        query_vectors_sql = """
        SELECT document_name, embeddings <-> %s::vector AS similarity
        FROM course_vectors
        WHERE course_id = %s
        ORDER BY similarity
        LIMIT %s;
        """
        # Ensure the query is passed as a string formatted like '[0.1, 0.2, 0.3]'
        formatted_query = f"[{', '.join(map(str, query))}]"  # Square brackets for VECTOR type
        cursor.execute(query_vectors_sql, (formatted_query, str(course_id), num_max_results))
        rows = cursor.fetchall()

        # Construct the response
        results = [{"documentName": row[0], "similarity": row[1]} for row in rows]

        cursor.close()
        connection.close()

        return results
    except Exception as e:
        print(f"Error querying vectors: {e}")
        return "cannot connect to db"
    

def generate_embeddings(chunk):
    model_id = "amazon.titan-embed-text-v2:0"  # Or whatever the correct model ID
    accept = "application/json"
    content_type = "application/json"

    # The Bedrock model likely expects 'inputText' or similarly named key
    payload = {
        "inputText": chunk
    }

    json_payload = json.dumps(payload)

    try:
        response = bedrock.invoke_model(
            modelId=model_id,
            body=json_payload,
            contentType=content_type,
            accept=accept
        )

        # Bedrock returns a streaming response; parse the body
        response_body = json.loads(response["body"].read().decode("utf-8"))

        # Titan embedding typically returns an 'embedding' field
        embedding = response_body.get("embedding")
        return embedding

    except Exception as e:
        print(f"Error invoking model: {str(e)}")
        return None    