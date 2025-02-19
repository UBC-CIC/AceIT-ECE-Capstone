import json
import os
import boto3
import psycopg2
import psycopg2.extras
from .get_rds_secret import get_cached_secret

# Cache for database connection
DB_CONNECTION = None

def get_db_connection():
    """Establishes or retrieves a cached database connection."""
    global DB_CONNECTION
    if DB_CONNECTION is None or DB_CONNECTION.closed:
        credentials = get_cached_secret()
        DB_CONFIG = {
            "host": "myrdsproxy.proxy-czgq6uq2qr6h.us-west-2.rds.amazonaws.com",
            "port": 5432,
            "dbname": "postgres",
            "user": credentials['username'],
            "password": credentials['password'],
        }
        print("Connecting to database")
        DB_CONNECTION = psycopg2.connect(**DB_CONFIG)
    return DB_CONNECTION

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
                    "HOME": False,
                    "ANNOUNCEMENTS": False,
                    "SYLLABUS": False,
                    "ASSIGNMENTS": False,
                    "MODULES": False,
                    "FILES": False,
                    "QUIZZES": False,
                    "DISCUSSIONS": False,
                    "PAGES": False
                }),
                "custom_response_format": ""
                }

            insert_query = """
            INSERT INTO course_configuration (course_id, student_access_enabled, selected_supported_questions, 
                selected_included_course_content, custom_response_format)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (
                default_config["course_id"],
                default_config["student_access_enabled"],
                default_config["selected_supported_questions"],
                default_config["selected_included_course_content"],
                default_config["custom_response_format"]
            ))

            connection.commit()

            response_body = {
                "course": default_config["course_id"],
                "studentAccessEnabled": default_config["student_access_enabled"],
                "selectedSupportedQuestions": json.loads(default_config["selected_supported_questions"]),
                "selectedIncludedCourseContent": json.loads(default_config["selected_included_course_content"]),
                "customResponseFormat": default_config["custom_response_format"],
                "systemPrompt": "",
                "materialLastUpdatedTime": '1970-01-01 00:00:00',
                "autoUpdateOn": False
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