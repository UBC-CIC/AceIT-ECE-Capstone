import json
import requests
import utils.get_canvas_secret
from utils.construct_response import construct_response
from utils.canvas_api_calls import refresh_token

def lambda_handler(event, context):
    headers = event.get("headers", {})
    if not headers:
        return construct_response(400, {"error": "Header is missing"})
    
    token = headers.get("Authorization", {})
    if not token:
        return construct_response(400, {"error": "Missing required fields: 'Authorization' is required"})

    canvas_response = refresh_token(token)

    if canvas_response is None:
        return construct_response(500, {"error": "Failed to refresh access_token from Canvas"})
    
    response_body = {
        "access_token": canvas_response["access_token"],
        "expires_in": 3600
    }
    
    return construct_response(200, response_body)