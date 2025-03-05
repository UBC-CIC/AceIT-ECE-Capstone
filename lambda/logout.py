from utils.construct_response import construct_response
from utils.canvas_api_calls import log_out

def lambda_handler(event, context):
    headers = event.get("headers", {})
    if not headers:
        return construct_response(400, {"error": "Header is missing"})
    
    access_token = headers.get("Authorization", {})
    if not access_token:
        return construct_response(400, {"error": "Missing required field: 'Authorization' is required"})
    
    status = log_out(access_token)
    if status is None:
        return construct_response(500, {"error": "Failed to delete access_token from Canvas"})
    
    return construct_response(200)