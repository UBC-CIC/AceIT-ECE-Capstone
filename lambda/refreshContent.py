import json
import boto3
import psycopg2.extras
import psycopg2
import requests  # to make HTTP requests
import utils
import utils.get_canvas_secret
import utils.get_rds_secret

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    body = json.loads(event.get("body", {}))
    course_id = body.get("course", {})  # Read course ID from request body

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
    text_format = {"txt", "md", "c", "cpp", "css", "go", "py", "js", "rtf", "pdf", "docx", "html"}
    files = get_files(course_id)
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
    for file in files:
        if file["locked"] == False and file["hidden"] == False and get_extension(file["display_name"]) in text_format: # TODO: add more checks if needed
            # TODO Store course documents into S3 buckets
            # s3_client.upload_file(
            #     local_file_path,
            #     bucket_name,
            #     s3_key,
            #     ExtraArgs={
            #         "Metadata": {
            #             "source-url": canvas_file_metadata["url"]  # Source URL from Canvas
            #         }
            #     }
            # )
            pass

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
    
    # Check if the response was successful (status code 200)
    if response.status_code == 200:
        # Log the response JSON
        print(f"Response from API: {response.json()}")  # This will print the parsed JSON response
        
        # Assuming the 'Payload' is part of the JSON response, you would access it like this:
        payload_data = response.json()  # Automatically parses the JSON from the response body
        
        print(f"Parsed payload: {payload_data}")
    else:
        print(f"Error: Received status code {response.status_code} from the API.")
    # TODO: delete fetched documents in s3
    # List and delete all objects in the course-specific prefix
    # response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    # if "Contents" in response:
    #     keys_to_delete = [{"Key": obj["Key"]} for obj in response["Contents"]]
    #     s3_client.delete_objects(Bucket=bucket_name, Delete={"Objects": keys_to_delete})
    
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

    try:
        response = requests.get(url, headers=HEADERS, verify=False)
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
        sanitized_course_id = course_id.replace("-", "_")

        # Delete query
        drop_table_query = f"""
        DROP TABLE IF EXISTS course_vectors_{sanitized_course_id};
        """
        cursor.execute(drop_table_query)

        connection.commit()
        cursor.close()
        return "Vectors deleted successfully"

    except Exception as e:
        print(f"Error during deletion: {e}")
        return "Error deleting vectors"