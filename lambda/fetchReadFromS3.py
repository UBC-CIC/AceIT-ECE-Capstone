import json
import os
import boto3
from langchain.document_loaders import PyMuPDFLoader
import fitz  # so we can also get metadata or do direct PyMuPDF calls if needed
from langchain.text_splitter import RecursiveCharacterTextSplitter
import docx
# For HTML
from bs4 import BeautifulSoup

s3_client = boto3.client("s3")
bedrock = boto3.client("bedrock-runtime",
                       region_name = 'us-west-2')

def lambda_handler(event, context):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=20000,
        chunk_overlap=100
    )

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

        embeddings = []
        for chunk in results[key]:
            chunk_embeddings = generate_embeddings(chunk)  # Assuming `generate_embeddings` calls your embedding model
            embeddings.append(chunk_embeddings)

    # 4. Return the results
    return {
        "statusCode": 200,
        'headers': {
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        "body": json.dumps({"pdf_results": results, "embeddings": embeddings})
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
