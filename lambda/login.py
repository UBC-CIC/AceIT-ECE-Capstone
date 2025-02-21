import json
import utils.get_canvas_secret
import requests

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
    jwt = headers.get("Authorization", {})
    if not jwt:
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
    
    # local = str(headers.get("Islocaltesting", "false")).lower() == "true"

    canvas_response = get_access_token(jwt)

    if canvas_response is None:
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
    
    response = {
        "access_token": canvas_response["access_token"],
        "refresh_token": canvas_response["refresh_token"],
        "expires_in": 3600
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

def get_access_token(jwt):
    secret = utils.get_canvas_secret.get_secret()
    credentials = json.loads(secret)
    BASE_URL = credentials['baseURL']
    CLIENT_ID = credentials['ltiKeyId']
    CLIENT_SECRET = credentials['ltiKey']
    REDIRECT_URI = credentials['redirectURI']

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