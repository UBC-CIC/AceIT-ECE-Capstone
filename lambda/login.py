from utils.construct_response import construct_response
from utils.canvas_api_calls import get_access_token

def lambda_handler(event, context):
    headers = event.get("headers", {})
    if not headers:
        return construct_response(400, {"error": "Header is missing"})
    
    authorization_code = headers.get("Authorization", {})
    if not authorization_code:
        return construct_response(400, {"error": "Missing required field: 'Authorization' is required"})
    
    canvas_response = get_access_token(authorization_code)

    if canvas_response is None:
        return construct_response(500, {"error": "Failed to fetch access_token from Canvas"})
    
    response_body = {
        "access_token": canvas_response["access_token"],
        "refresh_token": canvas_response["refresh_token"],
        "expires_in": canvas_response.get("expires_in", 3600)
    }

    return construct_response(200, response_body)