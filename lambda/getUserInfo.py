import json
import utils
import requests
import boto3
import utils.get_canvas_secret

dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
users_table = dynamodb.Table("Users")
def lambda_handler(event, context):
    headers = event.get("headers", {})
    if not headers:
        return {
            "statusCode": 400,
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': 'https://d2rs0jk5lfd7j4.cloudfront.net',
                'Access-Control-Allow-Methods': '*',
                'Access-Control-Allow-Credentials': 'true'
            },
            "body": json.dumps({"error": "Header is missing"})
        }
    token  = headers.get("Authorization", {})
    if not token:
        return {
            "statusCode": 400,
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': 'https://d2rs0jk5lfd7j4.cloudfront.net',
                'Access-Control-Allow-Methods': '*',
                'Access-Control-Allow-Credentials': 'true'
            },
            "body": json.dumps({"error": "Authorization token is required"})
        }
    
    user = get_user(token)
    if user is None:
        return {
            "statusCode": 500,
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': 'https://d2rs0jk5lfd7j4.cloudfront.net',
                'Access-Control-Allow-Methods': '*',
                'Access-Control-Allow-Credentials': 'true'
            },
            "body": json.dumps({"error": "Failed to fetch user info from Canvas API"})
        }
    
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
    response = {
        "userName": user_name,
        "userId": user_id,
        "preferred_language": preferred_lang
    }

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Origin': 'https://d2rs0jk5lfd7j4.cloudfront.net',
            'Access-Control-Allow-Methods': '*',
            'Access-Control-Allow-Credentials': 'true'
        },
        'body': json.dumps(response)
    }

def get_user(token):
    """
    Fetch user info from canvas lms.
    """
    secret = utils.get_canvas_secret.get_secret()
    credentials = json.loads(secret)
    BASE_URL = credentials['baseURL']
    HEADERS = {"Authorization": f"Bearer {token}"}
    print("Token: ", token)

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
