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

s3_client = boto3.client("s3")
bedrock = boto3.client("bedrock-runtime",
                       region_name = 'us-west-2')

def lambda_handler(event, context):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=20000,
        chunk_overlap=100
    )

    course_id = "76cd9469-45cb-45a6-9737-aa1df4b4335d"

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
    ret = create_table_if_not_exists(DB_CONFIG)

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
            retdb = store_embeddings(key, chunk_embeddings, course_id, DB_CONFIG)
        embeddings.append({key: document_embeddings})

    # 4. Return the results
    return {
        "statusCode": 200,
        'headers': {
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        "body": json.dumps({"pdf_results": results, "embeddings": embeddings, "db":retdb})
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
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    secret = get_secret_value_response['SecretString']
    return secret


def store_embeddings(document_name, embeddings, course_id, DB_CONFIG):
    """
    Store embeddings into the PostgreSQL database.
    """
    connection = None
    try:
        # Connect to the PostgreSQL database
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # Updated query to include course_id
        insert_query = """
        INSERT INTO course_vectors (course_id, document_name, embeddings, created_at)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(insert_query, (str(course_id), document_name, embeddings, datetime.now()))
        
        # Commit the transaction
        connection.commit()
        cursor.close()
        print("SQL SUCCESS")
        return "storeSuccess"
    except Exception as e:
        print(f"Error inserting embeddings: {e}")
    finally:
        if connection:
            connection.close()



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
