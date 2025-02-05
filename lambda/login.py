import json
import utils.get_canvas_secret
import requests

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
    jwt = headers.get("jwt", {})
    if not jwt:
        return {
            "statusCode": 400,
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            "body": json.dumps({"error": "Authorization token is required"})
        }
    local = headers.get("isLocalTesting", {})
    if not local:
        local = False

    access_token = get_access_token(jwt, local)

    if access_token is None:
        return {
            "statusCode": 500,
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            "body": json.dumps({"error": "Failed to fetch access_token from Canvas API"})
        }
    
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': json.dumps(access_token)
    }

def get_access_token(jwt, local):
    secret = utils.get_canvas_secret.get_secret()
    credentials = json.loads(secret)
    BASE_URL = credentials['baseURL']

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
            "grant_type": "authorization_code",
            "redirect_uri": f"{REDIRECT_URI}",
            "code": f"{jwt}",
            "scope": " ".join([
                                "https://purl.imsglobal.org/spec/lti-nrps/scope/contextmembership.readonly",
                                "https://purl.imsglobal.org/spec/lti-ags/scope/lineitem",
                                "https://purl.imsglobal.org/spec/lti-ags/scope/result.readonly",
                                "https://purl.imsglobal.org/spec/lti-ags/scope/score",
                                "https://canvas.instructure.com/auth/courses.readonly"
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