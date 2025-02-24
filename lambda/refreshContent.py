import os
import json
import boto3
import psycopg2.extras
import psycopg2
import requests  # to make HTTP requests
import utils
import utils.get_canvas_secret
import utils.get_rds_secret
import utils.retrieve_course_config

s3_client = boto3.client('s3')
bucket_name = 'bucket-for-course-documents'
lambda_client = boto3.client("lambda")

def lambda_handler(event, context):
    body = json.loads(event.get("body", {}))
    course_id = body.get("course", {})  # Read course ID from request body
    course_id = str(course_id)

    if not course_id:
        return {
            "statusCode": 400,
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': 'https://d2rs0jk5lfd7j4.cloudfront.net',
                'Access-Control-Allow-Methods': '*',
                'Access-Control-Allow-Credentials': 'true'
            },
            "body": json.dumps({"error": "Course ID is required"})
        }
    # TODO：filter content based on instructor configuration

    # 1. query database get the config
    # 2. for each selected type get the documents in it
    # course_config = utils.retrieve_course_config(course_id)
    files = get_files(course_id)

    if files is None:
        return {
            "statusCode": 500,
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': 'https://d2rs0jk5lfd7j4.cloudfront.net',
                'Access-Control-Allow-Methods': '*',
                'Access-Control-Allow-Credentials': 'true'
            },
            "body": json.dumps({"error": "Failed to fetch files from Canvas API"})
        }
    # Store course documents into S3 buckets
    text_format = {"txt", "md", "c", "cpp", "css", "go", "py", "js", "rtf", "pdf", "docx", "html"}
    for file in files:
        if file["locked"] == False and file['upload_status'] == 'success' and file["hidden"] == False and get_extension(file["display_name"]) in text_format:
            file_name = file["display_name"]
            print("file name: ", file_name)

            file_url = file["url"]  # Canvas file URL
            file_key = f"{course_id}/{file['filename']}"  # Store in "course_id/" folder
            file_size = file["size"]
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
    print("Delete vector response: ", del_response)

    response = call_fetch_read_from_s3(course_id)
    print("lambda response: ", response)  # Log the response if needed
    print("lambda response: ", type(response))

    # Check if the status is OK
    if response.get("statusCode") == 200:
        # Update the last_updated time
        update_course_last_update_time(course_id, DB_CONFIG)
        print("Status is OK")
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': 'https://d2rs0jk5lfd7j4.cloudfront.net',
                'Access-Control-Allow-Methods': '*',
                'Access-Control-Allow-Credentials': 'true'
            },
            'body': json.dumps({"message": f"Refreshed content for course {course_id}"})
        }
    else:
        print("Status is NOT OK")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': 'https://d2rs0jk5lfd7j4.cloudfront.net',
                'Access-Control-Allow-Methods': '*',
                'Access-Control-Allow-Credentials': 'true'
            },
            'body': json.dumps({"message": f"Content for course {course_id} is not refreshed!"})
        }

def get_files(course_id):
    """
    Fetch all files from canvas lms.
    """
    secret = utils.get_canvas_secret.get_secret()
    credentials = json.loads(secret)
    BASE_URL = credentials['baseURL']
    TOKEN = credentials['adminAccessToken']
    HEADERS = {"Authorization": f"Bearer {TOKEN}"}

    url = f"{BASE_URL}/api/v1/courses/{course_id}/files"
    print("url: ", url)
    print("headers: ", HEADERS)
    print("token: ", TOKEN)

    try:
        response = requests.get(url, headers=HEADERS, verify=False)
        print("response: ", response.json())
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        return None
    except requests.exceptions.RequestException as req_err:
        print(f"Request error occurred: {req_err}")
        return None

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
    

def invoke_fetch_from_s3(course_id):
    payload = {
        "body": json.dumps({"course": course_id}) 
    }
    try:
        response = lambda_client.invoke(
            FunctionName="FetchReadFromS3Function",  # Replace with actual function name
            InvocationType="RequestResponse",  # Use 'Event' for async calls
            # InvocationType="Event",
            Payload=json.dumps(payload)
        )
        response_payload = json.loads(response["Payload"].read().decode("utf-8"))
        print(f"Refreshed course {course_id}: {response_payload}")
        return
    except Exception as e:
        print(f"Error invoking Lambda function: {e}")
        return
    
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
        print("response_payload: ", response_payload)
        # body_dict = json.loads(response_payload["body"])
        # print("Body: ", body_dict, "Type: ", type(body_dict))
        # Create a LambdaResponse object with status_code and body
        return response_payload
    except Exception as e:
        print(f"Error invoking Lambda function: {e}")
        return None