import json
import os
import boto3
import psycopg2
from datetime import datetime
import uuid
import psycopg2.extras

def create_table_if_not_exists(DB_CONFIG):
    """
    Ensure the embeddings table exists in the database.
    """
    connection = None
    
    try:
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor()

        create_course_config_query = """
        CREATE TABLE IF NOT EXISTS course_configuration (
            course_id UUID PRIMARY KEY,                          -- Unique ID for the course
            student_access_enabled BOOLEAN NOT NULL,             -- Whether student access is enabled
            selected_supported_questions JSONB NOT NULL,         -- Supported questions as JSON
            selected_included_course_content JSONB NOT NULL,     -- Included content as JSON
            custom_response_format TEXT,                          -- Instruction for LLM
            last_updated_time TIMESTAMP DEFAULT '1970-01-01 00:00:00'
        );
        """
        cursor.execute(create_course_config_query)
        connection.commit()
        cursor.close()
        return "DBSuccess"
    except Exception as e:
        print(f"Error creating table: {e}")
    finally:
        if connection:
            connection.close()