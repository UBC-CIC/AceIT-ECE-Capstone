import os
import json
import boto3
import psycopg2
import psycopg2.extras
from utils.create_course_vectors_tables import create_table_if_not_exists
from utils.get_rds_secret import get_secret, load_db_config
from utils.construct_response import construct_response
from utils.get_course_vector import get_course_vector

bedrock = boto3.client("bedrock-runtime", region_name = os.getenv('AWS_REGION'))

def lambda_handler(event, context):
    params = event.get("queryStringParameters", {})
    course_id = params.get("course")
    query = params.get("query")
    num_max_results = int(params.get("numMaxResults", 8))  # Default to 8 if not provided

    # Validate required fields
    if not course_id or not query:
        return construct_response(400, {"error": "Missing required fields: 'course' and 'query' are required"})
    
    secret = get_secret()
    credentials = json.loads(secret)
    username = credentials['username']
    password = credentials['password']
    static_db_config = load_db_config()
    # Combine static DB config and dynamic credentials
    DB_CONFIG = {
        **static_db_config,
        "user": username,
        "password": password
    }
    
    create_table_if_not_exists(DB_CONFIG, course_id)
    query_embedding = generate_embeddings(str(query))
    response_body = get_course_vector(DB_CONFIG, query_embedding, course_id, num_max_results)

    return construct_response(200, response_body)

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