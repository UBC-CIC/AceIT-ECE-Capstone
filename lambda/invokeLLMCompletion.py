import json
import boto3
import psycopg2
from psycopg2.extras import Json
from utils.get_rds_secret import get_secret

session = boto3.Session()
bedrock = session.client('bedrock-runtime', 'us-west-2') 

def lambda_handler(event, context):
    try:
        # Parse the request body
        body = json.loads(event.get("body", "{}"))
        course_id = "76cd9469-45cb-45a6-9737-aa1df4b4335d"

        # Validate required fields
        message = body.get("message")
        print("Message got: ", message)
        if not message:
            return {
                "statusCode": 400,
                'headers': {
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                "body": json.dumps({"error": "'message' is required"})
            }

        # Optional fields
        context = body.get("context", "")
        print("context:", context)
        # sources = body.get("sources", [])

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

         # Fetch embeddings for the query from AWS PostgreSQL
        query_embedding = generate_embeddings(message)

        # Retrieve relevant context from the database based on embeddings
        relevant_docs = get_course_vector(DB_CONFIG, query_embedding, course_id, 6)
        print("relevant_docs:", relevant_docs)
        print("document names:", relevant_docs[0]["documentName"])

        # Combine context with the input message for the LLM
        final_input = compose_input(message, context, relevant_docs)
        print("final input:", final_input)

        # Call the LLM API to generate a response
        llm_response = call_llm(final_input)

        return {
            "statusCode": 200,
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            "body": json.dumps({
                "response": llm_response,
                "sources": relevant_docs
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            "body": json.dumps({"error": f"An unexpected error occurred: {str(e)}"})
        }

def generate_embeddings(text):
    """Generates embeddings for the input text using Bedrock."""
    try:
        model_id = "amazon.titan-embed-text-v2:0"
        payload = {"inputText": text}
        response = bedrock.invoke_model(
            modelId=model_id,
            body=json.dumps(payload),
            contentType="application/json",
            accept="application/json"
        )
        result = json.loads(response["body"].read().decode("utf-8"))
        return result.get("embedding")
    except Exception as e:
        print(f"Error generating embeddings: {e}")
        return None

def get_course_vector(DB_CONFIG, query, course_id, num_max_results):
    # Connect to the PostgreSQL database
    try:
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor()

        sanitized_course_id = course_id.replace("-", "_")
        # Query the vector database with explicit casting
        query_vectors_sql = f"""
        SELECT document_name, sourceURL, document_content, embeddings <-> %s::vector AS similarity
        FROM course_vectors_{sanitized_course_id}
        ORDER BY similarity
        LIMIT %s;
        """
        # Ensure the query is passed as a string formatted like '[0.1, 0.2, 0.3]'
        formatted_query = f"[{', '.join(map(str, query))}]"  # Format the query embedding
        cursor.execute(query_vectors_sql, (formatted_query, num_max_results))
        rows = cursor.fetchall()

        results = [
            {
                "documentName": row[0],
                "sourceUrl": row[1],  # Add source_url to the result
                "documentContent": row[2],
                # "similarity": row[3]
            }
            for row in rows
        ]

        cursor.close()
        connection.close()

        return results
    except Exception as e:
        print(f"Error querying vectors: {e}")
        return "cannot connect to db"

def compose_input(message, context_data, relevant_docs):
    """Combines the message, context, and sources for the LLM."""
    complete_msg = []
    if context_data:
        for past_conv in context_data:
            complete_msg.append(past_conv)
    context = "\n".join([f"Document: {doc['documentName']}\n{doc['documentContent']}" for doc in relevant_docs])
    prompt = f"Given the following documents, Answer the query. Documents:\n{context}\nQuery: {message}\n"
    complete_msg.append({
        'role': 'user', 
                'content': prompt,
    })
    body=json.dumps({
            'messages': complete_msg
         })

    return body

def call_llm(input_text):
    """Invokes the LLM for completion."""
    model_id = "mistral.mistral-large-2407-v1:0"  # Make sure this is the correct model ID for generation

    try:
        response = bedrock.invoke_model(
            modelId=model_id,
            body=input_text,
            # contentType="application/json",
            # accept="application/json"
        )
        print("LLM response: ", response)

        # Read the StreamingBody and decode it to a string
        response_body = response['body'].read().decode('utf-8')

        # Parse the JSON response
        response_json = json.loads(response_body)
        print("Parsed response: ", response_json)

        # Extract the assistant's message content
        assistant_message = response_json['choices'][0]['message']['content']
    
        return assistant_message
    
    except Exception as e:
        print(f"Error generating answer: {e}")
        return "Sorry, there was an error generating an answer."