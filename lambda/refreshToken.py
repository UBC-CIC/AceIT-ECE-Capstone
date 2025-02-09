import json
import requests
import utils.get_canvas_secret

def lambda_handler(event, context):
    headers = event.get("headers", {})
    if not headers:
        return {
            "statusCode": 400,
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            "body": json.dumps({"error": "Header is missing"})
        }
    token = headers.get("Authorization", {})
    if not token:
        return {
            "statusCode": 400,
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            "body": json.dumps({"error": "Refresh token is required"})
        }
    
    local = str(headers.get("Islocaltesting", "false")).lower() == "true"

    canvas_response = refresh_token(token, local)

    if canvas_response is None:
        return {
            "statusCode": 500,
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            "body": json.dumps({"error": "Failed to refresh access_token from Canvas"})
        }
    
    response = {
        "access_token": canvas_response["access_token"]
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

def refresh_token(refresh_token, local):
    secret = utils.get_canvas_secret.get_secret()
    credentials = json.loads(secret)
    BASE_URL = credentials['baseURL']

    # declare first
    CLIENT_ID = ""
    CLIENT_SECRET = ""
    REDIRECT_URI = ""

    if not local:
        CLIENT_ID = credentials['ltiKeyId']
        CLIENT_SECRET = credentials['ltiKey']
        REDIRECT_URI = credentials['redirectURI']
    if local:
        CLIENT_ID = credentials['localLtiKeyId']
        CLIENT_SECRET = credentials['localLtiKey']
        REDIRECT_URI = credentials['localRedirectURI']

    url = f"{BASE_URL}/login/oauth2/token"

    data = {
            "client_id": f"{CLIENT_ID}",
            "client_secret": f"{CLIENT_SECRET}",
            "grant_type": "refresh_token",
            "redirect_uri": f"{REDIRECT_URI}",
            "refresh_token ": f"{refresh_token}"
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