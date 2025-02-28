import json
import boto3
import psycopg2
import psycopg2.extras
from psycopg2.extras import DictCursor
import requests  # to make HTTP requests
import utils
import utils.get_canvas_secret
import utils.get_rds_secret
from utils.retrieve_course_config import call_get_course_config

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
    secret = utils.get_canvas_secret.get_secret()
    credentials = json.loads(secret)
    TOKEN = credentials['adminAccessToken']

    # Invoke refreshCourse for each course
    for course in courses:
        # fetch course config and check if auto update is on
        if course["workflow_state"] == "available":
            course_config = call_get_course_config(TOKEN, course["id"], lambda_client)
            print("course config: ", course_config)
            auto_update_on = course_config.get("autoUpdateOn", False)
            if (auto_update_on):
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
    # access_token = get_server_level_access_token()
    # if access_token is None or not access_token['access_token']:
    #     return {
    #         "statusCode": 500,
    #         'headers': {
    #             'Access-Control-Allow-Headers': '*',
    #             'Access-Control-Allow-Origin': 'https://d2rs0jk5lfd7j4.cloudfront.net',
    #             'Access-Control-Allow-Methods': '*',
    #             'Access-Control-Allow-Credentials': 'true'
    #         },
    #         "body": json.dumps({"error": "Failed to fetch access_token from Canvas"})
    #     }
    # TOKEN = access_token['access_token']
    secret = utils.get_canvas_secret.get_secret()
    credentials = json.loads(secret)
    BASE_URL = credentials['baseURL']
    TOKEN = credentials['adminAccessToken']
    ACCOUNT_ID = credentials['adminAccountID']
    
    HEADERS = {"Authorization": f"Bearer {TOKEN}"}

    url = f"{BASE_URL}/api/v1/accounts/{ACCOUNT_ID}/courses"
    # response = requests.get(url, headers=HEADERS, verify=False)
    # return response.json()
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

# def get_server_level_access_token():
#     secret = utils.get_canvas_secret.get_secret()
#     credentials = json.loads(secret)
#     BASE_URL = credentials['baseURL']
#     CLIENT_ID = credentials['serverKeyId']
#     # CLIENT_SECRET = credentials['serverKey']
#     PRIVATE_KEY = credentials['jwkPrivateKey']
#     KID = credentials['kid']

#     url = f"{BASE_URL}/login/oauth2/token"

#     client_assertion = get_client_assertion(CLIENT_ID, PRIVATE_KEY, KID, url)

#     data = {
#             "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
#             "client_assertion": client_assertion,
#             "grant_type": "client_credentials",
#             "scope": " ".join([
#                                 "https://purl.imsglobal.org/spec/lti-nrps/scope/contextmembership.readonly",
#                                 "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem",
#                                 "https://purl.imsglobal.org/spec/lti-ags/scope/result.readonly",
#                                 "https://purl.imsglobal.org/spec/lti-ags/scope/score",
#                                 # "https://canvas.instructure.com/auth/courses.readonly" 
#                                 # TODO: not able to get the last scope yet, but it's neccesary for getting course info
#                             ])
#             }
#     headers = {"Content-Type": "application/x-www-form-urlencoded"}
#     try:
#         response = requests.post(url, data=data, headers=headers, verify=False)
#         response.raise_for_status()
#         return response.json()
#     except requests.exceptions.HTTPError as http_err:
#         print(f"HTTP error occurred: {http_err}")
#         return None
#     except requests.exceptions.RequestException as req_err:
#         print(f"Request error occurred: {req_err}")
#         return None
  
# def get_client_assertion(client_id, private_key, kid, url):
#     header = {
#         "alg": "RS256",
#         "typ": "JWT",
#         "kid": kid
#     }

#     payload = {
#         "iss": client_id,
#         "sub": client_id,
#         "aud": url,
#         "iat": int(time.time()),
#         "exp": int(time.time()) + 600, # 10 mins expiration
#         "jti": str(uuid.uuid4())
#     }

#     return jwt.encode(payload, private_key, algorithm="RS256", header = header);

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