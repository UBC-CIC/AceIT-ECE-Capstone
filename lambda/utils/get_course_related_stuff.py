import json
import boto3
import uuid
import datetime
from .get_canvas_secret import get_secret
import requests
from bs4 import BeautifulSoup

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
    
def fetch_syllabus_from_canvas(auth_token, base_url, course_id):
    """
    Fetch syllabus body from Canvas API.
    """
    url = f"{base_url}/{course_id}?include[]=syllabus_body"
    # url = "https://15.157.251.49/api/v1/courses/4?include[]=syllabus_body"
    headers = {"Authorization": f"Bearer {auth_token}"}

    response = requests.get(url, headers=headers, verify=False)
    if response.status_code == 200:
        course_data = response.json()
        syllabus_body = course_data.get("syllabus_body", "")

        if syllabus_body:
            # Convert HTML to plain text
            print("syllabus body: ", syllabus_body)
            soup = BeautifulSoup(syllabus_body, "html.parser")
            print("soup: ", soup.get_text(separator="\n").strip())
            str_syllabus = "syllabus: " + soup.get_text(separator="\n").strip() + "; syllabus link: " + url
            return str_syllabus
    
    print(f"Failed to fetch syllabus: {response.status_code}, {response.text}")
    return None

# if __name__ == "__main__":
#     a = fetch_syllabus_from_canvas("CXekV2e68mxaNx2vB2kWDhAwQ4vXHY63QFXDe6KyePrG7kQMZEaMQ3PxKkrFWfr6", 4)
#     print(type(a))
