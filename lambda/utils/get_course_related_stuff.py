import json
import boto3
import uuid
import datetime
from .get_canvas_secret import get_secret
import requests

lambda_client = boto3.client('lambda')
def call_course_activity_stream(auth_token, course_id):
    secret = get_secret()
    credentials = json.loads(secret)
    BASE_URL = credentials['baseURL']
    HEADERS = {"Authorization": f"Bearer {auth_token}"}
    print("Token: ", auth_token)

    url = f"{BASE_URL}/api/v1/courses/{course_id}/activity_stream"
    try:
        response = requests.get(url, headers=HEADERS, verify=False)
        response.raise_for_status()
        # Lambda function to extract and format the data
        response = response.json()
        format_data = lambda entries: "\n".join(
            [f"Type: {entry['type']}\nTitle: {entry['title']}\nMessage: {entry['message']}\n" for entry in entries]
        )
        result = format_data(response)
        print("Result ", result)
        print("result type", type(result))
        return result
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        return None
    except requests.exceptions.RequestException as req_err:
        print(f"Request error occurred: {req_err}")
        return None