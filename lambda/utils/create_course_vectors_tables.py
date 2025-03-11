import json
import os
import boto3
import psycopg2
from datetime import datetime
import uuid
import psycopg2.extras
def create_table_if_not_exists(DB_CONFIG, course_id):
    """
    Dynamically create a table for the given course ID if it doesn't exist.
    """
    connection = None
    try:
        connection = psycopg2.connect(**DB_CONFIG)
        cursor = connection.cursor()

        # Dynamically construct table creation query
        # Ensure the extension is created
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")

        create_embeddings_query = f"""
        CREATE TABLE IF NOT EXISTS course_vectors_{course_id} (
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