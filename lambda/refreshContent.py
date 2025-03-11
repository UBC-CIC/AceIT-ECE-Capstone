import json
import boto3
import psycopg2.extras
import psycopg2
import requests  # to make HTTP requests
import utils
import utils.get_canvas_secret
import utils.get_rds_secret
from utils.construct_response import construct_response
from utils.canvas_api_calls import get_files_by_course_id

s3_client = boto3.client('s3')
bucket_name = 'bucket-for-course-documents'
lambda_client = boto3.client("lambda")

def lambda_handler(event, context):
    body = json.loads(event.get("body", {}))
    course_id = body.get("course", {})  # Read course ID from request body
    course_id = str(course_id)
    running_async = body.get("async", False)

    is_recursive = body.get("recursive", False)
    if running_async and not is_recursive:
        # Asynchronous execution: Invoke itself asynchronously

        body["recursive"] = True  # Prevent further async invocation
        payload = {
            "body": json.dumps(body) 
        }
        try:
            response = lambda_client.invoke(
                FunctionName="RefreshContentLambda",
                InvocationType="Event",
                Payload=json.dumps(payload)
                )
            return construct_response(202, {"message": "Function is executing asynchronously"})

        except Exception as e:
            return construct_response(500, {"message": "Error invoking function asynchronously", "error": str(e)})
        
    else:
        # Synchronous execution
        if not course_id:
            return construct_response(400, {"error": "Missing required fields: 'course' is required"})

        files = get_files_by_course_id(course_id)

        if files is None:
            return construct_response(500, {"error": "Failed to fetch files from Canvas API"})
        
        # Store course documents into S3 buckets
        text_format = {"txt", "md", "c", "cpp", "css", "go", "py", "js", "rtf", "pdf", "docx", "html"}
        for file in files:
            if file["locked"] == False and file['upload_status'] == 'success' and file["hidden"] == False and get_extension(file["display_name"]) in text_format:
                file_name = file["display_name"]
                print("file name: ", file_name)

                file_url = file["url"]  # Canvas file URL
                file_key = f"{course_id}/{file['filename']}"  # Store in "course_id/" folder
                file_updated = file["updated_at"]
            
                try:
                    print(f"Streaming {file_key} to S3...")

                    with requests.get(file_url, stream=True, verify=False) as response:
                        response.raise_for_status()  # Ensure request success

                        # Upload stream directly to S3 with metadata
                        s3_client.upload_fileobj(
                            response.raw,
                            bucket_name,
                            file_key,
                            ExtraArgs={
                                "Metadata": {
                                    "original_url": file_url,
                                    "display_name": file_name,
                                    "updated_at": file_updated,
                                }
                            }
                        )

                    print(f"Successfully uploaded {file_key} to S3 with metadata.")
                
                except Exception as e:
                    print(f"Failed to upload {file_key}: {e}")
                
        secret = utils.get_rds_secret.get_secret()
        credentials = json.loads(secret)
        username = credentials['username']
        password = credentials['password']
        static_db_config = utils.get_rds_secret.load_db_config()
        # Combine static DB config and dynamic credentials
        DB_CONFIG = {
            **static_db_config,
            "user": username,
            "password": password
        }

        # delete this course vector
        del_response = delete_vectors_by_course(DB_CONFIG, course_id)
        if not del_response:
            return construct_response(500, {"message": f"Error while deleting course vector storage"})

        response = call_fetch_read_from_s3(course_id)

        # Check if the status is OK
        if response.get("statusCode") == 200:
            # Update the last_updated time
            update_course_last_update_time(course_id, DB_CONFIG)
            return construct_response(200, {"message": f"Refreshed content for course {course_id}"})
        else:
            return construct_response(500, {"message": f"Content for course {course_id} is not refreshed!"})

def get_extension(file_name):
    parts = file_name.split(".")
    extension = parts[-1]
    return extension

def update_course_last_update_time(course_id, DB_CONFIG):
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()
    update_query = """
    UPDATE course_configuration
    SET material_last_updated_time = NOW()
    WHERE course_id = %s;
    """
    cursor.execute(update_query, (course_id,))
    connection.commit()
    cursor.close()
    connection.close()
    return

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
        return "Success"
    except Exception as e:
        return None
        
def call_fetch_read_from_s3(course_id):
    """
    Calls getcourseconfig.
    """
    payload = {
        "queryStringParameters": {
            "course": course_id
        }
    }
    try:
        response = lambda_client.invoke(
            FunctionName="FetchReadFromS3Function",  # Replace with actual function name
            InvocationType="RequestResponse",  # Use 'Event' for async calls
            Payload=json.dumps(payload)
        )
        response_payload = json.loads(response["Payload"].read().decode("utf-8"))
        return response_payload
    except Exception as e:
        print(f"Error invoking Lambda function: {e}")
        return None