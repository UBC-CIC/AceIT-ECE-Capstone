import os
import json
import boto3
import psycopg2.extras
import psycopg2
import requests  # to make HTTP requests
import utils
import utils.get_canvas_secret
import utils.get_rds_secret

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
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            "body": json.dumps({"error": "Course ID is required"})
        }
    files = get_files(course_id)
    print("files: ", files)
    if files is None:
        return {
            "statusCode": 500,
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
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
    # Database connection parameters
    DB_CONFIG = {
        "host": "myrdsproxy.proxy-czgq6uq2qr6h.us-west-2.rds.amazonaws.com",
        "port": 5432,
        "dbname": "postgres",
        "user": username,
        "password": password,
    }

    # delete this course vector
    del_response = delete_vectors_by_course(DB_CONFIG, course_id)
    print("Delete vector response: ", del_response)

    url = f"https://i6t0c7ypi6.execute-api.us-west-2.amazonaws.com/prod/api/llm/content/canvas?course={course_id}"
    response = requests.get(url)
    print(response.json())  # Log the response if needed
    
    # # Check if the response was successful (status code 200)
    if response.status_code == 200:
        # Log the response JSON
        print(f"Response from API: {response.json()}")  # This will print the parsed JSON response
        
        # Assuming the 'Payload' is part of the JSON response, you would access it like this:
        payload_data = response.json()  # Automatically parses the JSON from the response body
        
        print(f"Parsed payload: {payload_data}")
    else:
        print(f"Error: Received status code {response.status_code} from the API.")

    # # clear documents in s3
    # bucket_objects = s3_client.list_objects_v2(Bucket=bucket_name)
    # if "Contents" in bucket_objects:
    #     for obj in bucket_objects["Contents"]:
    #         s3_client.delete_objects(Bucket=bucket_name, Key=obj["Key"])
    
    # Update the last_updated time
    update_course_last_update_time(course_id, DB_CONFIG)


    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': json.dumps({"message": f"Refreshed content for course {course_id}"})
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