import json
import boto3
import utils
import requests

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    headers = event.get("headers", {})
    token  = headers.get("Authorization")
    course_id = headers.get("CourseID") # TODO: missing this
    user_id = headers.get("UserID") # TODO: missing this
    if not token or not course_id or not user_id:
        return {
            "statusCode": 400,
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            "body": json.dumps({"error": "Authorization token, courseID, UserID are required"})
        }
    
    user = get_user(token, course_id, user_id)

    # construct response
    response = {
        "userName": user["name"],
        "userId": user["id"], # TODO: this is not a UUID
        "userType": user[""] # TODO: this field is not defined in Canvas
    }

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': json.dumps(response)
    }

# TODO: error handling
def get_user(token, course_id, user_id):
    """
    Fetch user info from canvas lms.
    """
    secret = utils.get_canvas_secret.get_secret()
    credentials = json.loads(secret)
    BASE_URL = credentials['baseURL']
    HEADERS = {"Authorization": f"Bearer {token}"}

    url = f"{BASE_URL}/api/v1/courses/{course_id}/users/{user_id}"
    response = requests.get(url, headers=HEADERS, verify=False)
    return response.json()