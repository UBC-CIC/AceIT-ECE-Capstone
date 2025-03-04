import json
import utils
import requests
import boto3
import utils.get_canvas_secret
from utils.construct_response import construct_response

dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
users_table = dynamodb.Table("Users")
def lambda_handler(event, context):
    headers = event.get("headers", {})
    if not headers:
        return construct_response(400, {"error": "Header is missing"})
    
    token  = headers.get("Authorization", {})
    if not token:
        return construct_response(400, {"error": "Missing required fields: 'Authorization' is required"})
    
    user = get_user(token)
    if user is None:
        return construct_response(500, {"error": "Failed to fetch user info from Canvas"})
    
    user_name = user["name"]
    user_id = user["id"]
    response = users_table.get_item(Key={"userId": user_id})
    preferred_lang = ""
    if "Item" in response:
        # User does not exist, create a new one with preferred_language=""
        preferred_lang = response["Item"].get("preferred_language", "")
    else:
        users_table.put_item(Item={"userId": user_id, "preferred_language": ""})

    # construct response
    response_body = {
        "userName": user_name,
        "userId": user_id,
        "preferred_language": preferred_lang
    }

    return construct_response(200, response_body)

def get_user(token):
    """
    Fetch user info from canvas lms.
    """
    secret = utils.get_canvas_secret.get_secret()
    credentials = json.loads(secret)
    BASE_URL = credentials['baseURL']
    HEADERS = {"Authorization": f"Bearer {token}"}

    url = f"{BASE_URL}/api/v1/users/self"
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
