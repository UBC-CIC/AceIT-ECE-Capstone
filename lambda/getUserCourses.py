import json
import boto3
import utils
import requests

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    headers = event.get("headers", {})
    token  = headers.get("Authorization")
    id = headers.get("UserID") #TODO: missing this
    if not token:
        return {
            "statusCode": 400,
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            "body": json.dumps({"error": "Authorization token is required"})
        }

    courses = get_courses(token, id)
    availableList = {}
    unavailableList = {}
    for course in courses:
        #construct object
        cur_course = {
            "id": course["uuid"], # TODO: may need id
            "courseCode": course["course_code"],
            "name": course["name"] # TODO: course may have nickname
        }

        # TODO: check course availability in db


        # add into its corresponding list
        # availableList.append(cur_course)

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': json.dumps({"availableCourses": availableList, "unavailableCourses": unavailableList})
    }

# TODO: error handling
def get_courses(token, user_id):
    """
    Fetch all courses for a user from canvas lms.
    """
    secret = utils.get_canvas_secret.get_secret()
    credentials = json.loads(secret)
    BASE_URL = credentials['baseURL']
    HEADERS = {"Authorization": f"Bearer {token}"}

    url = f"{BASE_URL}/api/v1/users/{user_id}/courses"
    response = requests.get(url, headers=HEADERS, verify=False)
    return response.json()