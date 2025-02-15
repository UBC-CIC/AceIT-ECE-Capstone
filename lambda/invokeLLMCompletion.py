import json
import boto3
import psycopg2
from psycopg2.extras import Json
import re
from utils.get_rds_secret import get_secret
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

SUPPORTED_LANGUAGES = {
    "en": "English",
    "fr-CA": "French",
    "zh": "Chinese (Simplified)",
    "ja": "Japanese",
    "pa": "Punjabi",
    "es": "Spanish",
    "ar": "Arabic",
    "tl": "Tagalog",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese"
}

session = boto3.Session()
bedrock = session.client('bedrock-runtime', 'us-west-2') 
translate_client = boto3.client("translate", region_name="us-west-2")

def lambda_handler(event, context):
    try:
        # Parse the request body
        body = json.loads(event.get("body", "{}"))
        # course_id = "1"
        course_id = body.get("course")  # Ensure course_id is extracted
        course_id = str(course_id)

        # Validate required fields
        message = body.get("message")
        student_language_pref = body.get("language", "")
        print("Message got: ", message)
        if not message:
            return {
                "statusCode": 400,
                'headers': {
                    'Access-Control-Allow-Headers': '*',
                    'Access-Control-Allow-Origin': 'https://d2rs0jk5lfd7j4.cloudfront.net',
                    'Access-Control-Allow-Methods': '*',
                    'Access-Control-Allow-Credentials': 'true'
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
            "host": "myrdsproxy.proxy-czgq6uq2qr6h.us-west-2.rds.amazonaws.com",
            "port": 5432,
            "dbname": "postgres",
            "user": username,
            "password": password,
        }

         # Fetch embeddings for the query from AWS PostgreSQL
        query_embedding = generate_embeddings(message)

        # Retrieve relevant context from the database based on embeddings
        relevant_docs = get_course_vector(DB_CONFIG, query_embedding, course_id, 8)
        print("relevant_docs:", relevant_docs)
        print("document names:", relevant_docs[0]["documentName"])

        # Combine context with the input message for the LLM
        final_input = compose_input(message, context, relevant_docs)
        print("final input:", final_input)

        # Call the LLM API to generate a response
        llm_response = call_llm(final_input)
        # Translate the response if needed
        if student_language_pref and student_language_pref != "":
            translated_response = translate_text(llm_response, student_language_pref)
            llm_response = translated_response

        return {
            "statusCode": 200,
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': 'https://d2rs0jk5lfd7j4.cloudfront.net',
                'Access-Control-Allow-Methods': '*',
                'Access-Control-Allow-Credentials': 'true'
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
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': 'https://d2rs0jk5lfd7j4.cloudfront.net',
                'Access-Control-Allow-Methods': '*',
                'Access-Control-Allow-Credentials': 'true'
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

        # Query the vector database with explicit casting
        query_vectors_sql = f"""
        SELECT document_name, sourceURL, document_content, embeddings <-> %s::vector AS similarity
        FROM course_vectors_{course_id}
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
    documents_text = "\n".join(
        [
            f"""Document: {doc.get('documentName', 'Unknown')}
URL: {doc.get('sourceUrl', 'No URL')}
Content: {doc.get('documentContent', 'No Content')}"""
            for doc in relevant_docs if doc
        ]
    )

    # Start with previous conversation history
    composed_prompt = context_data.strip()
    # Find the last occurrence of <|eot_id|> in the message
    last_eot_index = context_data.rfind("<|eot_id|>")

    if last_eot_index != -1:
        # Insert relevant documents before the last <|eot_id|>
        modified_context = (
            context_data[:last_eot_index] +
            f"\nRelevant Documents:\n {documents_text}\n" +
            context_data[last_eot_index:]
        )
    else:
        # If <|eot_id|> is not found, just append the documents at the end
        modified_context = context_data + f"\nRelevant Documents:\n{documents_text}\n"

    # Append the new user query
    final_prompt = (
        modified_context.strip() +
        f"\n<|start_header_id|>user<|end_header_id|>\n{message}<|eot_id|>\n<|start_header_id|>assistant<|end_header_id|>"
    )

    print("final prompt:", final_prompt)   
    return final_prompt

def call_llm(input_text):
    """Invokes the LLM for completion."""
    model_id = "arn:aws:bedrock:us-west-2:842676002045:inference-profile/us.meta.llama3-3-70b-instruct-v1:0"  # Make sure this is the correct model ID for generation

    try:
        response = bedrock.invoke_model(
            modelId=model_id,
            body=json.dumps({"prompt": input_text, "max_gen_len": 1024, "temperature": 0.5, "top_p": 0.9})
            # contentType="application/json",
            # accept="application/json"
        )
        print("LLM response: ", response)

        response_body = response['body'].read().decode('utf-8')
        if not response_body.strip():
            print("LLM response is empty!")
            return "Summary not available."
        response_json = json.loads(response_body)
        generated_response = response_json.get("generation", "Summary not available.")
        generated_response = re.sub(r"^(ai:|AI:)\s*", "", generated_response).strip()
        print("generated response: ", generated_response)

        return generated_response
    
    except Exception as e:
        print(f"Error generating answer: {e}")
        return "Sorry, there was an error generating an answer."
    

def translate_text(text, target_language):
    """Translates text to the student's preferred language using Amazon Translate."""
    if target_language not in SUPPORTED_LANGUAGES:
        print(f"Language '{target_language}' not supported. Defaulting to English.")
        return text  # Return original if the language is unsupported

    try:
        response = translate_client.translate_text(
            Text=text,
            SourceLanguageCode="auto",  # Auto-detect source language
            TargetLanguageCode=target_language
        )
        return response["TranslatedText"]
    except Exception as e:
        print(f"Error translating text: {e}")
        return text  # Return original text if translation fails