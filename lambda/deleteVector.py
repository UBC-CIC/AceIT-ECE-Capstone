import json
import psycopg2
import psycopg2.extras
from utils.get_rds_secret import get_secret, load_db_config
from utils.construct_response import construct_response

def lambda_handler(event, context):
    params = event.get("queryStringParameters", {})
    course_id = params.get("course")
    # Validate required fields
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
    delete_result = delete_vectors_by_course(DB_CONFIG, course_id)

    return construct_response(200, {"delete result": delete_result})

def delete_vectors_by_course(DB_CONFIG, course_id):
    # Connect to the PostgreSQL database
    try:
        # Connect to the PostgreSQL database
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor()

        # Delete query
        drop_table_query = f"""
        DROP TABLE IF EXISTS course_vectors_{course_id};
        """
        cursor.execute(drop_table_query)

        connection.commit()
        cursor.close()
        return "Vectors deleted successfully"

    except Exception as e:
        print(f"Error during deletion: {e}")
        return "Error deleting vectors"