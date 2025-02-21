import json
import uuid
import time
import jwt
import boto3
import psycopg2
import psycopg2.extras
from psycopg2.extras import DictCursor
import requests  # to make HTTP requests
import base64
import utils
import utils.get_canvas_secret
import utils.get_rds_secret
from utils.retrieve_course_config import retrieve_course_config

s3_client = boto3.client('s3')
lambda_client = boto3.client("lambda")

def lambda_handler(event, context):
    courses = get_all_courses()
    print("Courses: ", courses)
    if courses is None:
        return {
            "statusCode": 500,
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': 'https://d2rs0jk5lfd7j4.cloudfront.net',
                'Access-Control-Allow-Methods': '*',
                'Access-Control-Allow-Credentials': 'true'
            },
            "body": json.dumps({"error": "Failed to fetch courses from Canvas API"})
        }

    refreshed_courses = []

    # Invoke refreshCourse for each course
    for course in courses:
        # fetch course config and check if auto update is on
        course_config = retrieve_course_config(course)
        print("course config: ", course_config)
        auto_update_on = course_config.get("autoUpdateOn", False)
        if course["workflow_state"] == "available" and auto_update_on:
            invoke_refresh_course(course["id"])
            print(course["id"])
            refreshed_courses.append(course["id"])

    response_message = f"Courses: {', '.join(map(str, refreshed_courses))} have been refreshed."

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Origin': 'https://d2rs0jk5lfd7j4.cloudfront.net',
            'Access-Control-Allow-Methods': '*',
            'Access-Control-Allow-Credentials': 'true'
        },
        'body': json.dumps({"message": response_message})
    }


def get_all_courses():
    """
    Fetch all courses from canvas lms.
    """
    access_token = get_server_level_access_token()
    if access_token is None or not access_token['access_token']:
        return {
            "statusCode": 500,
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': 'https://d2rs0jk5lfd7j4.cloudfront.net',
                'Access-Control-Allow-Methods': '*',
                'Access-Control-Allow-Credentials': 'true'
            },
            "body": json.dumps({"error": "Failed to fetch access_token from Canvas"})
        }
    TOKEN = access_token['access_token']
    secret = utils.get_canvas_secret.get_secret()
    credentials = json.loads(secret)
    BASE_URL = credentials['baseURL']
    
    HEADERS = {"Authorization": f"Bearer {TOKEN}"}

    url = f"{BASE_URL}/api/v1/courses"
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

def get_server_level_access_token():
    secret = utils.get_canvas_secret.get_secret()
    credentials = json.loads(secret)
    BASE_URL = credentials['baseURL']
    CLIENT_ID = credentials['ltiKeyId']
    CLIENT_SECRET = credentials['ltiKey']

    url = f"{BASE_URL}/login/oauth2/token"

    client_assertion = get_client_assertion(CLIENT_ID, url)

    data = {
            "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
            "client_assertion": f"{client_assertion}",
            "grant_type": "client_credentials",
            "scope": " ".join([
                                "https://purl.imsglobal.org/spec/lti-nrps/scope/contextmembership.readonly",
                                "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem",
                                "https://purl.imsglobal.org/spec/lti-ags/scope/result.readonly",
                                "https://purl.imsglobal.org/spec/lti-ags/scope/score",
                                "https://canvas.instructure.com/auth/courses.readonly" # TODO: not able to get this scope yet, neccesary for getting course info
                            ])
            }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    try:
        response = requests.post(url, data=data, headers=headers, verify=False)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        return None
    except requests.exceptions.RequestException as req_err:
        print(f"Request error occurred: {req_err}")
        return None
  
def get_client_assertion(client_id, url):
    header = {
        "alg": "RS256",
        "typ": "JWT",
        "kid":"5W4eOMF-1ORx4aF2utnC3XMHNywQyV6kLoAgxe9hgF4"
    }

    payload = {
        "iss": f"{client_id}",
        "sub": f"{client_id}",
        "aud": f"{url}",
        "iat": int(time.time()),
        "exp": int(time.time()) + 600, # 10 mins expiration
        "jti": str(uuid.uuid4())
    }
    # TODO: store in secrete manager
    private_key = "-----BEGIN PRIVATE KEY-----MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCYVCKsocevxOUI2D41G2+aTdRdPmLfXdlJYlLjjgJ0ExL2xRJU/u9KzMyTSV3y+MJLinVJf+5Q1hQmO7OcVvPwvip+8Yc4ThYcEOU1lXDTG0LRAtBxJW4UuH6wo22li15lq70EO+ppg5Y3jnzmsDzNBilfAtzW6pXiykddr0qJWKUsx73jqIAeZ0LgZAiX0bpwi2SayKISzD5tiuq9fQdz2Sej+d5vVR0r73Yb2HneaAJ1FZtQVPUpkcYnH+GInc/fYM3AVmH3aP88HWd/8Jyt5K6Ya0iVx7m0eYXAlyaiZ3TKo83/41dlvHCxJebXouwevY25S56NsbKBhBlY6IMhAgMBAAECggEAFg+tW+osRPETqKXE0KUyExttg7ma0TXC1+V1Er7I7S2sA/BDuOqZFnC1uikYga10WkNpvCTai3uNvIHN//j56GZqOitZxZZNjnAF+i40AmcC1Ml/Dbv5hue3dXad1SlrmPb374qL5w8nLNGmljR1Ac6AJGICQOAFqCxajJ9sAJsMT51dIPsJCG7VWFilkI1rHbcTmrKQNIIlvz2oPLTfSKFd+krR6xihEWGDZ8UC57DFXDd0U8MlY4IWvz55nWy7YlYmFjzIQZ75LKyZjzhF+efbHalZ+AoI7RsIi4m26yTrYAZ1VEHNTpByLjtsb8IvKEMwi8Ovapbm/+S14wVKqQKBgQDI7czbGE2uTPBHBjvkfMvxdje9hIsY3EdgNA0XtIIaJs6KDxIb76iGeyQpxz9/ixogkiZl3usttAJPJClQFqS0WKANhwDQF2H3AiMh9hJM3BErK36/MSjF2PMIOyps587b6aPsJJ15Co7hlEVe/kwfYH0Y756u7fkKvzzEKI6vtQKBgQDCFEr8FZbigD5j3Oh6Ko8C8xD1AAnOqaMp5WkSBGfTHI5eUNI7Fy9vuuEYzqjKuo9TzQnecMsn2eiSZGRHTaITXZtlvNZb4XpM5FXxA8VG5pXXq6Wm7gbxLv1gasGiCcntcxTpFD8mpLV9IalleAk+2PifblSPHMsFP2TOGIsxPQKBgCcvYS01Tyj37kAbsiB8ShW8FWDLcYkWpIDZhdgipuDMwqjgCYsTMQ2RBFt1dSe9jAngFsb1M25FVdHzXm81C0f0pLoeowTyGnPeodVktOryXBLMN7q3rpjvF256g2qbxpbSuNo7xc4uRfEuRl0hQN05pwvu50Z8OH5lD0e+FR2lAoGADyEv20j/kza2JmjRQrzQm0VBnCfdm9vDmX+F2l63jVCblKSuTub2zrn91EZACFXU2I6SZ2HZpIirRcZHvvtBWEsi0yKOf2krdJUUUg6eMXHGWqLJ7iJ+Lg0guYR5Bd3HfRhMmAL5DVUnxNJ79yoNZnXZo+wg8WsoNIeFnz9wkm0CgYEApzDz1lnG/pO3C3MzDDL6kGhIlSAutoqe1KEMsZlI4nztYbKaj4lvqyiFYepngMdr5VtImEJF4er3UrjFtHTh5eBJxKJWb1/o0RQtfCYFXi5I9IKr90aAcddG6E3MvAbL72cXjYS2vumHHMYnHyFbIVG/7hSm2h0Ptf1CQwXOzns=-----END PRIVATE KEY-----"

    return jwt.encode(payload, private_key, algorithm="RS256", header = header);

def invoke_refresh_course(course_id):
    payload = {
        "body": json.dumps({"course": course_id}) 
    }
    try:
        response = lambda_client.invoke(
            FunctionName="RefreshContentLambda",  # Replace with actual function name
            # InvocationType="RequestResponse",  # Use 'Event' for async calls
            InvocationType="Event",
            Payload=json.dumps(payload)
        )
        print(f"Successfully invoked RefreshContentLambda for course {course_id}")
        return
    except Exception as e:
        print(f"Error invoking Lambda function: {e}")
        return