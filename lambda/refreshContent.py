import json
import boto3
import psycopg2.extras
import psycopg2
import requests  # to make HTTP requests

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    body = json.loads(event.get("body", "{}"))
    course_id = body.get("course")  # Read course ID from request body

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
    
    # TODO Fetch Documents from Canvas
    
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

    secret = get_secret()
    credentials = json.loads(secret)
    username = credentials['username']
    password = credentials['password']
    # Database connection parameters
    DB_CONFIG = {
        "host": "privaceitececapstonemainstack-t4grdsdb098395df-k9zj5cjjmn4b.czgq6uq2qr6h.us-west-2.rds.amazonaws.com",
        "port": 5432,
        "dbname": "postgres",
        "user": username,
        "password": password,
    }
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
    # TODO: delete fetched documents
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


def update_course_last_update_time(course_id, DB_CONFIG):
    connection = psycopg2.connect(**DB_CONFIG)
    cursor = connection.cursor()
    update_query = """
    UPDATE course_configuration
    SET last_updated_time = NOW()
    WHERE course_id = %s;
    """
    cursor.execute(update_query, (course_id,))
    connection.commit()
    cursor.close()
    connection.close()

def get_secret():
    secret_name = "MyRdsSecretF2FB5411-AMahlTQtUobh"
    region_name = "us-west-2"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except Exception as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    secret = get_secret_value_response['SecretString']
    return secret