import json
import os
import boto3
from langchain.document_loaders import PyMuPDFLoader
import fitz  # so we can also get metadata or do direct PyMuPDF calls if needed
from langchain.text_splitter import RecursiveCharacterTextSplitter
import docx
# For HTML
from bs4 import BeautifulSoup
import psycopg2
from datetime import datetime
import psycopg2.extras
from utils.get_rds_secret import get_secret

s3_client = boto3.client("s3")
bedrock = boto3.client("bedrock-runtime",
                       region_name = 'us-west-2')

def lambda_handler(event, context):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100
    )

    params = event.get("queryStringParameters", {})
    course_id = params.get("course")

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
        "host": "myrdsproxy.proxy-czgq6uq2qr6h.us-west-2.rds.amazonaws.com",
        "port": 5432,
        "dbname": "postgres",
        "user": username,
        "password": password,
    }
    ret = create_table_if_not_exists(DB_CONFIG, course_id)

    # 1. Determine the S3 bucket. Could be from env or event.
    bucket_name = event.get("bucket_name", "bucketfortextextract")

    # 2. List all objects in the bucket
    #    (This uses list_objects_v2, which returns up to 1000 objects per call.
    #     For more objects, we'd need pagination.)
    response = s3_client.list_objects_v2(Bucket=bucket_name)
    if "Contents" not in response:
        return {
            "statusCode": 200,
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            "body": json.dumps({"message": "Bucket is empty or does not exist."})
        }

    results = {}
    embeddings = []
    for obj in response["Contents"]:
        key = obj["Key"]

        local_path = f"/tmp/{os.path.basename(key)}"
        s3_client.download_file(bucket_name, key, local_path)

        text_extensions = [".txt", ".md", ".c", ".cpp", ".css", ".go", ".py", ".js", ".rtf"]

        # 3. Check if it's a PDF (or any other extension you want to handle)
        if key.lower().endswith(".pdf"):
            results[key] = read_pdf(text_splitter, local_path)
        elif key.lower().endswith(".docx"):
            results[key] = read_docx(text_splitter, local_path)
        elif key.lower().endswith(".html"):
            results[key] = read_html(text_splitter, local_path)
        elif any(key.lower().endswith(ext) for ext in text_extensions):
            results[key] = read_as_plain_text(text_splitter, local_path)
        
        document_embeddings = []
        for chunk in results[key]:
            chunk_embeddings = generate_embeddings(chunk)  # Assuming `generate_embeddings` calls your embedding model
            document_embeddings.append(chunk_embeddings)
            # response = s3_client.head_object(Bucket=bucket_name, Key=s3_key)
            # source_url = response["Metadata"].get("source-url", "Unknown source")
            source_url = "Unknown source"
            retdb = store_embeddings(key, chunk_embeddings, course_id, DB_CONFIG, source_url, chunk)
        embeddings.append({key: document_embeddings})

    # 4. Return the results
    return {
        "statusCode": 200,
        'headers': {
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        # "body": json.dumps({"pdf_results": results, "embeddings": embeddings, "db":retdb})
        "body": json.dumps(results)
    }

def read_pdf(text_splitter, local_path):
    try:
        # Use LangChain’s PyMuPDFLoader to extract text
        loader = PyMuPDFLoader(local_path)
        documents = loader.load()
        extracted_text = "\n\n".join(page.page_content for page in documents)

        chunks = text_splitter.split_text(extracted_text)
        return chunks

    except Exception as e:
                # If we fail on one file, log it but continue
        return f"Error processing PDF: {str(e)}"

def generate_embeddings(chunk):
    model_id = "amazon.titan-embed-text-v2:0"  # Or whatever the correct model ID
    # model_id = "mistral.mistral-large-2407-v1:0"
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

def read_docx(text_splitter, path):
    """Use python-docx to extract text from .docx."""
    doc = docx.Document(path)
    paragraphs = [p.text for p in doc.paragraphs]
    res = "\n".join(paragraphs)
    chunks = text_splitter.split_text(res)
    return chunks

def read_html(text_splitter, path):
    """Use BeautifulSoup to extract text from .html."""
    with open(path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
    res = soup.get_text(separator="\n")
    chunks = text_splitter.split_text(res)
    return chunks

def read_as_plain_text(text_splitter, path):
    """Naive approach: read file as UTF-8 text."""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        res = f.read()
        chunks = text_splitter.split_text(res)
        return chunks


def store_embeddings(document_name, embeddings, course_id, DB_CONFIG, source_url, document_content):
    """
    Store embeddings into the PostgreSQL database.
    """
    connection = None
    sanitized_course_id = course_id.replace("-", "_")  # Replace hyphens with underscores
    try:
        # Connect to the PostgreSQL database
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor()

        # Dynamically construct insertion query
        insert_query = f"""
        INSERT INTO course_vectors_{sanitized_course_id} (document_name, embeddings, created_at, sourceURL, document_content)
        VALUES (%s, %s, %s, %s, %s);
        """
        cursor.execute(insert_query, (document_name, embeddings, datetime.now(), source_url, document_content))

        # Commit the transaction
        connection.commit()
        cursor.close()
        print("SQL SUCCESS")
        return "Embedding stored successfully"
    except Exception as e:
        print(f"Error inserting embeddings: {e}")
        return "Error storing embeddings"
    finally:
        if connection:
            connection.close()



def create_table_if_not_exists(DB_CONFIG, course_id):
    """
    Dynamically create a table for the given course ID if it doesn't exist.
    """
    connection = None
    sanitized_course_id = course_id.replace("-", "_")  # Replace hyphens with underscores
    try:
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor()

        # Dynamically construct table creation query
        create_embeddings_query = f"""
        CREATE EXTENSION IF NOT EXISTS vector;
        CREATE TABLE IF NOT EXISTS course_vectors_{sanitized_course_id} (
            id SERIAL PRIMARY KEY,
            document_name TEXT NOT NULL,
            embeddings VECTOR(1024),
            created_at TIMESTAMP DEFAULT NOW(),
            sourceURL TEXT DEFAULT 'https://www.example.com',
            document_content TEXT
        );
        """
        cursor.execute(create_embeddings_query)
        connection.commit()
        cursor.close()
        return "Table created or already exists"
    except Exception as e:
        print(f"Error creating table: {e}")
        return "Error creating table"
    finally:
        if connection:
            connection.close()