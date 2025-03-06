import json
import os
import boto3
import psycopg2
import psycopg2.extras
from .get_rds_secret import get_cached_secret
from .get_rds_secret import load_db_config
from updateCourseConfig import create_system_prompt

# Cache for database connection
DB_CONNECTION = None

def get_db_connection():
    """Establishes or retrieves a cached database connection."""
    global DB_CONNECTION
    if DB_CONNECTION is None or DB_CONNECTION.closed:
        credentials = get_cached_secret()
        static_db_config = load_db_config()
        # Combine static DB config and dynamic credentials
        DB_CONFIG = {
            **static_db_config,
            "user": credentials['username'],
            "password": credentials['password'],
        }
        print("Connecting to database")
        DB_CONNECTION = psycopg2.connect(**DB_CONFIG)
    return DB_CONNECTION

def call_get_course_config(auth_token, course_id, lambda_client):
    """
    Calls getcourseconfig.
    """
    payload = {
        "headers": {
            "Content-Type": "application/json",
            "Authorization": auth_token,
        },
        "queryStringParameters": {
            "course": course_id
        },
    }
    try:
        response = lambda_client.invoke(
            FunctionName="GetCourseConfigLambda",  # Replace with actual function name
            InvocationType="RequestResponse",  # Use 'Event' for async calls
            Payload=json.dumps(payload)
        )
        response_payload = json.loads(response["Payload"].read().decode("utf-8"))
        print("response_payload: ", response_payload)
        body_dict = json.loads(response_payload["body"])
        print("Body: ", body_dict, "Type: ", type(body_dict))
        return body_dict
    except Exception as e:
        print(f"Error invoking Lambda function: {e}")
        return None

def retrieve_course_config(course_id):
    try:
        # Connect to the PostgreSQL database
        print("DB_CONNECTION: ", DB_CONNECTION)
        connection = get_db_connection()  # Get cached DB connection
        print("Connected to database")
        cursor = connection.cursor()

        # Query the course configuration
        query = """
        SELECT student_access_enabled, selected_supported_questions, 
               selected_included_course_content, custom_response_format, system_prompt,
               material_last_updated_time, auto_update_on
        FROM course_configuration
        WHERE course_id = %s
        """
        cursor.execute(query, (str(course_id),))  # Convert UUID to string
        row = cursor.fetchone()

        if not row:
        # Course configuration does not exist, insert default values
            default_config = {
                "course_id": course_id,
                "student_access_enabled": False,
                "selected_supported_questions": json.dumps({
                    "RECOMMENDATIONS": True,
                    "PRACTICE_PROBLEMS": True,
                    "SOLUTION_REVIEW": True,
                    "EXPLANATION": True
                }),
                "selected_included_course_content": json.dumps({
                    "ANNOUNCEMENTS": False,
                    "SYLLABUS": False,
                    "ASSIGNMENTS": False,
                    "FILES": False,
                    "QUIZZES": False,
                    "DISCUSSIONS": False,
                    "PAGES": False
                }),
                "custom_response_format": "",
                "material_last_updated_time": "1970-01-01 00:00:00",
                "auto_update_on": False
                }
            
            default_config["system_prompt"] = create_system_prompt(default_config["selected_supported_questions"], default_config["custom_response_format"])

            insert_query = """
            INSERT INTO course_configuration (course_id, student_access_enabled, selected_supported_questions, 
                selected_included_course_content, custom_response_format, system_prompt, material_last_updated_time, auto_update_on)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (
                default_config["course_id"],
                default_config["student_access_enabled"],
                default_config["selected_supported_questions"],
                default_config["selected_included_course_content"],
                default_config["custom_response_format"],
                default_config["system_prompt"],
                default_config["material_last_updated_time"],
                default_config["auto_update_on"]
            ))

            connection.commit()

            response_body = {
                "course": default_config["course_id"],
                "studentAccessEnabled": default_config["student_access_enabled"],
                "selectedSupportedQuestions": json.loads(default_config["selected_supported_questions"]),
                "selectedIncludedCourseContent": json.loads(default_config["selected_included_course_content"]),
                "customResponseFormat": default_config["custom_response_format"],
                "systemPrompt": default_config["system_prompt"],
                "materialLastUpdatedTime": default_config["material_last_updated_time"],
                "autoUpdateOn": default_config["auto_update_on"]
            }
        else: 
            response_body = {
                "studentAccessEnabled": row[0],
                "selectedSupportedQuestions": row[1],
                "selectedIncludedCourseContent": row[2],
                "customResponseFormat": row[3],
                "systemPrompt": row[4],
                "materialLastUpdatedTime": row[5].isoformat(),
                "autoUpdateOn": row[6]
            }

        # Close database connection
        cursor.close()
        connection.close()

        return response_body
    except Exception as e:
        print(f"Error: {e}")
        return "Cannot connect to db"