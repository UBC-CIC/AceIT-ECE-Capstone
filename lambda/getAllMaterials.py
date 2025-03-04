import psycopg2
import psycopg2.extras
from utils.get_rds_secret import get_cached_secret, load_db_config
from utils.get_user_info import get_user_info
from utils.construct_response import construct_response

def lambda_handler(event, context):
    try:
        headers = event.get("headers", {})
        auth_token = headers.get("Authorization", "")
        if not auth_token:
            return construct_response(400, {"error": "Missing required header fields: 'Authorization' is required"})

        # Call Canvas API to get user info
        user_info = get_user_info(auth_token)
        if not user_info:
            return construct_response(500, {"error": "Failed to fetch user info from Canvas"})
        # Extract Canvas user ID
        student_id = user_info.get("userId", "")
        if not student_id:
            return construct_response(500, {"error": "User ID not found"})

        course_id = event.get("queryStringParameters", {}).get("course")
        if not course_id:
            return construct_response(400, {"error": "Missing required parameter: 'course' is required"})
        # Get database credentials
        credentials = get_cached_secret()
        username = credentials['username']
        password = credentials['password']
        static_db_config = load_db_config()
        # Combine static DB config and dynamic credentials
        DB_CONFIG = {
            **static_db_config,
            "user": username,
            "password": password
        }

        DB_CONNECTION = psycopg2.connect(**DB_CONFIG)

        documents = []

        # Connect to the PostgreSQL database
        DB_CONNECTION = psycopg2.connect(**DB_CONFIG)
        cursor = DB_CONNECTION.cursor()

        # Construct query to get document names and URLs
        query = f"""
        SELECT document_name, sourceURL
        FROM course_vectors_{course_id};
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()

        # Use a set to get unique pairs of document_name and source_url
        unique_documents = {
            (str(row[0]), str(row[1])) for row in rows
        }

        # Convert set back to a list of dictionaries
        documents = [
            {"document_name": name, "source_url": url} for name, url in unique_documents
        ]

        return construct_response(200, documents)
    except Exception as e:
        print(f"Error invoking Lambda function: {e}")
        return construct_response(400, {"error": "Unexpected error when invoking get all materials function"})
