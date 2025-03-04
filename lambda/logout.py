import json
import requests
import utils.get_canvas_secret
from utils.construct_response import construct_response

def lambda_handler(event, context):
    headers = event.get("headers", {})
    if not headers:
        return construct_response(400, {"error": "Header is missing"})
    
    access_token = headers.get("Authorization", {})
    if not access_token:
        return construct_response(400, {"error": "Missing required fields: 'Authorization' is required"})
    
    status = log_out(access_token)
    if status is None:
        return construct_response(500, {"error": "Failed to delete access_token from Canvas"})
    
    return construct_response(200)

def log_out(access_token):
    secret = utils.get_canvas_secret.get_secret()
    credentials = json.loads(secret)
    BASE_URL = credentials['baseURL']

    url = f"{BASE_URL}/login/oauth2/token"

    headers = { 
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/x-www-form-urlencoded"
        }
    
    params = {"expire_sessions": "1"}

    try:
        response = requests.delete(url, headers=headers, params=params, verify=False)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        return None
    except requests.exceptions.RequestException as req_err:
        print(f"Request error occurred: {req_err}")
        return None