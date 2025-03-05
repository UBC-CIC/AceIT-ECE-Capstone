import json
import boto3
from langchain.document_loaders import PyMuPDFLoader
import fitz  # so we can also get metadata or do direct PyMuPDF calls if needed
from langchain.text_splitter import RecursiveCharacterTextSplitter
import docx
from bs4 import BeautifulSoup # For HTML
import psycopg2
from datetime import datetime
import psycopg2.extras
import utils.get_canvas_secret
import utils.get_course_related_stuff
from utils.get_rds_secret import get_secret, load_db_config
from utils.create_course_vectors_tables import create_table_if_not_exists
from utils.retrieve_course_config import retrieve_course_config
from utils.construct_response import construct_response
from io import BytesIO

s3_client = boto3.client("s3")
bedrock = boto3.client("bedrock-runtime",
                       region_name = 'us-west-2')

def lambda_handler(event, context):
    bucket_name = "bucket-for-course-documents"

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100
    )

    params = event.get("queryStringParameters", {})
    course_id = params.get("course")

    if not course_id:
        return construct_response(400, {"error": "Missing required fields: 'course' is required"})
    
    secret = get_secret()
    credentials = json.loads(secret)
    username = credentials['username']
    password = credentials['password']
    # Database connection parameters
    static_db_config = load_db_config()
    # Combine static DB config and dynamic credentials
    DB_CONFIG = {
        **static_db_config,
        "user": username,
        "password": password
    }

    create_table_if_not_exists(DB_CONFIG, course_id)

    ## first check course config settings
    course_config = retrieve_course_config(course_id)

    if isinstance(course_config, str):  # If there's an error message
        print("Error:", course_config)
        return construct_response(500, {"error": "Error retrieving course configuration"})
    
    # Access fields in the dictionary
    files_enabled = course_config["selectedIncludedCourseContent"].get("FILES", False)
    syllabus_enabled = course_config["selectedIncludedCourseContent"].get("SYLLABUS", False)
    announcements_enabled = course_config["selectedIncludedCourseContent"].get("ANNOUNCEMENTS", False)
    assignments_enabled = course_config["selectedIncludedCourseContent"].get("ASSIGNMENTS", False)
    quizzes_enabled = course_config["selectedIncludedCourseContent"].get("QUIZZES", False)
    discussions_enabled = course_config["selectedIncludedCourseContent"].get("DISCUSSIONS", False)
    pages_enabled = course_config["selectedIncludedCourseContent"].get("PAGES", False)
    
    prefix = f"{course_id}/"  # Assuming course_id is used as a folder structure
    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    
    files_metadata = []
    results = {}
    embeddings = []

    if "Contents" in response and files_enabled:
        for obj in response["Contents"]:
            file_key = obj["Key"]

            # Fetch file metadata
            metadata_response = s3_client.head_object(Bucket=bucket_name, Key=file_key)
            metadata = metadata_response.get("Metadata", {})

            files_metadata.append({
                "file_key": file_key,
                "s3_url": f"s3://{bucket_name}/{file_key}",
                "original_url": metadata.get("original_url", "N/A"),
                "display_name": metadata.get("display_name", "N/A"),
                "updated_at": metadata.get("updated_at", "N/A"),
            })

            # Process file based on type (without downloading)
            if file_key.lower().endswith(".pdf"):
                results[file_key] = read_pdf_streaming(bucket_name, file_key, text_splitter)
            elif file_key.lower().endswith(".docx"):
                results[file_key] = read_docx_streaming(bucket_name, file_key, text_splitter)
            elif file_key.lower().endswith(".html"):
                results[file_key] = read_html_streaming(bucket_name, file_key, text_splitter)
            elif file_key.lower().endswith((".txt", ".md", ".c", ".cpp", ".css", ".go", ".py", ".js", ".rtf")):
                results[file_key] = read_text_streaming(bucket_name, file_key, text_splitter)
            else:
                print(f"Unsupported file type: {file_key}")

            document_embeddings = []
            for chunk in results[file_key]:
                chunk_embeddings = generate_embeddings(chunk)  # Assuming `generate_embeddings` calls your embedding model
                if chunk_embeddings:
                    document_embeddings.append(chunk_embeddings)
                    source_url = metadata.get("original_url", "N/A"),
                    file_name_db = metadata.get("display_name", file_key)
                    store_embeddings(file_name_db, chunk_embeddings, course_id, DB_CONFIG, source_url, chunk)
            embeddings.append({file_key: document_embeddings})

    # add canvas contents based on instructor configuration
    canvas_secret = utils.get_canvas_secret.get_secret()
    canvas_credentials = json.loads(canvas_secret)
    BASE_URL = canvas_credentials['baseURL']
    TOKEN = canvas_credentials['adminAccessToken']
    if syllabus_enabled:
        syllabus_url = f"{BASE_URL}/courses/{course_id}/assignments/syllabus"
        syllabus_text = utils.get_course_related_stuff.fetch_syllabus_from_canvas(TOKEN, BASE_URL, course_id)
        if syllabus_text:
            syllabus_chunks = text_splitter.split_text(syllabus_text)
            embeddings = []
            for chunk in syllabus_chunks:
                embedding = generate_embeddings(chunk)
                if embedding:
                    embeddings.append(embedding)
                    store_embeddings("Syllabus", embedding, course_id, DB_CONFIG, syllabus_url, chunk)

    if announcements_enabled:
        announcements_url = f"{BASE_URL}/courses/{course_id}/announcements"
        announcements_text = utils.get_course_related_stuff.fetch_announcments_from_canvas(TOKEN, BASE_URL, course_id)
        if announcements_text:
            announcements_chunks = text_splitter.split_text(announcements_text)
            embeddings = []
            for chunk in announcements_chunks:
                embedding = generate_embeddings(chunk)
                if embedding:
                    embeddings.append(embedding)
                    store_embeddings("Announcements", embedding, course_id, DB_CONFIG, announcements_url, chunk)

    if assignments_enabled:
        assignments_url = f"{BASE_URL}/courses/{course_id}/assignments"
        assignments_text = utils.get_course_related_stuff.fetch_assignments_from_canvas(TOKEN, BASE_URL, course_id)
        if assignments_text:
            assignments_chunks = text_splitter.split_text(assignments_text)
            embeddings = []
            for chunk in assignments_chunks:
                embedding = generate_embeddings(chunk)
                if embedding:
                    embeddings.append(embedding)
                    store_embeddings("Assignments", embedding, course_id, DB_CONFIG, assignments_url, chunk)

    if quizzes_enabled:
        quizzes_url = f"{BASE_URL}/courses/{course_id}/quizzes"
        quizzes_text = utils.get_course_related_stuff.fetch_quizzes_from_canvas(TOKEN, BASE_URL, course_id)
        if quizzes_text:
            quizzes_chunks = text_splitter.split_text(quizzes_text)
            embeddings = []
            for chunk in quizzes_chunks:
                embedding = generate_embeddings(chunk)
                if embedding:
                    embeddings.append(embedding)
                    store_embeddings("Quizzes", embedding, course_id, DB_CONFIG, quizzes_url, chunk)

    if discussions_enabled:
        discussions_url = f"{BASE_URL}/courses/{course_id}/discussion_topics"
        discussions_text = utils.get_course_related_stuff.fetch_discussions_from_canvas(TOKEN, BASE_URL, course_id)
        if discussions_text:
            discussions_chunks = text_splitter.split_text(discussions_text)
            embeddings = []
            for chunk in discussions_chunks:
                embedding = generate_embeddings(chunk)
                if embedding:
                    embeddings.append(embedding)
                    store_embeddings("Discussions", embedding, course_id, DB_CONFIG, discussions_url, chunk)

    if pages_enabled:
        pages_url = f"{BASE_URL}/courses/{course_id}/pages"
        pages_text = utils.get_course_related_stuff.fetch_pages_from_canvas(TOKEN, BASE_URL, course_id)
        if pages_text:
            pages_chunks = text_splitter.split_text(pages_text)
            embeddings = []
            for chunk in pages_chunks:
                embedding = generate_embeddings(chunk)
                if embedding:
                    embeddings.append(embedding)
                    store_embeddings("Pages", embedding, course_id, DB_CONFIG, pages_url, chunk)

    # 4. Return the results
    return construct_response(200, {"message": "success"})
    
def read_pdf_streaming(bucket_name, file_key, text_splitter):
    """Extract text from a large PDF file using S3 streaming."""
    response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
    file_stream = BytesIO(response["Body"].read())  # Read as BytesIO for PyMuPDF
    
    try:
        doc = fitz.open(stream=file_stream, filetype="pdf")  # Open PDF in memory
        extracted_text = []
        
        for page in doc:
            text = page.get_text("text")
            extracted_text.append(text)
        
        chunks = text_splitter.split_text("\n\n".join(extracted_text))
        return chunks
    except Exception as e:
        return f"Error processing PDF: {str(e)}"

def read_docx_streaming(bucket_name, file_key, text_splitter):
    """Extract text from a large DOCX file using S3 streaming."""
    response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
    file_stream = BytesIO(response["Body"].read())  # Read DOCX into memory

    try:
        doc = docx.Document(file_stream)  # Open DOCX in memory
        paragraphs = [p.text for p in doc.paragraphs]
        text = "\n".join(paragraphs)
        
        chunks = text_splitter.split_text(text)
        return chunks
    except Exception as e:
        return f"Error processing DOCX: {str(e)}"

def read_html_streaming(bucket_name, file_key, text_splitter):
    """Extract text from an HTML file streamed from S3."""
    response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
    
    try:
        html_content = response["Body"].read().decode("utf-8")  # Read and decode HTML
        soup = BeautifulSoup(html_content, "html.parser")
        text = soup.get_text(separator="\n")
        
        chunks = text_splitter.split_text(text)
        return chunks
    except Exception as e:
        return f"Error processing HTML: {str(e)}"

def read_text_streaming(bucket_name, file_key, text_splitter):
    """Extract text from a large text file using chunk streaming."""
    response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
    
    extracted_text = []
    chunk_size = 8192  # 8KB chunks to process large files efficiently
    
    try:
        # Read file in chunks
        for chunk in response["Body"].iter_chunks(chunk_size=chunk_size):
            extracted_text.append(chunk.decode("utf-8"))  # Decode bytes to string
        
        chunks = text_splitter.split_text("\n".join(extracted_text))
        return chunks
    except Exception as e:
        return f"Error processing text file: {str(e)}"

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

def store_embeddings(document_name, embeddings, course_id, DB_CONFIG, source_url, document_content):
    """
    Store embeddings into the PostgreSQL database.
    """
    connection = None
    # sanitized_course_id = course_id.replace("-", "_")  # Replace hyphens with underscores
    try:
        # Connect to the PostgreSQL database
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor()

        # Dynamically construct insertion query
        insert_query = f"""
        INSERT INTO course_vectors_{course_id} (document_name, embeddings, created_at, sourceURL, document_content)
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