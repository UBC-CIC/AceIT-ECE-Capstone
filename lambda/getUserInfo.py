import json
import utils
import requests

def lambda_handler(event, context):
    headers = event.get("headers", {})
    token  = headers.get("Authorization", {})

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
    
    user = get_user(token)

    # construct response
    response = {
        "userName": user["name"],
        "userId": user["id"]
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
def get_user(token):
    """
    Fetch user info from canvas lms.
    """
    secret = utils.get_canvas_secret.get_secret()
    credentials = json.loads(secret)
    BASE_URL = credentials['baseURL']
    HEADERS = {"Authorization": f"Bearer {token}"}

    url = f"{BASE_URL}/api/v1/users/self"
    response = requests.get(url, headers=HEADERS, verify=False)
    return response.json()