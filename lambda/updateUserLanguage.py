import json
import boto3
import re
from utils.get_user_info import get_user_info

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
users_table = dynamodb.Table("Users")

# Regex to validate language codes (ISO 639-1 or RFC 5646 with country variants)
LANGUAGE_CODE_PATTERN = r"^[a-z]{2}(-[A-Z]{2})?$"

def lambda_handler(event, context):
    try:
        headers = event.get("headers", {})
        auth_token = headers.get("Authorization", "")
        if not auth_token:
            return {
                "statusCode": 400,
                'headers': {
                    'Access-Control-Allow-Headers': '*',
                    'Access-Control-Allow-Origin': 'https://d2rs0jk5lfd7j4.cloudfront.net',
                    'Access-Control-Allow-Methods': '*',
                    'Access-Control-Allow-Credentials': 'true'
                },
                "body": json.dumps({"error": "Missing required Authorization token"})
            }

        # Call Canvas API to get user info
        user_info = get_user_info(auth_token)
        if not user_info:
            return {
                "statusCode": 500,
                'headers': {
                    'Access-Control-Allow-Headers': '*',
                    'Access-Control-Allow-Origin': 'https://d2rs0jk5lfd7j4.cloudfront.net',
                    'Access-Control-Allow-Methods': '*',
                    'Access-Control-Allow-Credentials': 'true'
                },
                "body": json.dumps({"error": "Failed to fetch user info from Canvas"})
            }
        # Extract user ID
        user_id = user_info.get("userId")
        if not user_id:
            return {
                "statusCode": 500,
                'headers': {
                    'Access-Control-Allow-Headers': '*',
                    'Access-Control-Allow-Origin': 'https://d2rs0jk5lfd7j4.cloudfront.net',
                    'Access-Control-Allow-Methods': '*',
                    'Access-Control-Allow-Credentials': 'true'
                },
                "body": json.dumps({"error": "User ID not found"})
            }

        # Extract body
        body = json.loads(event.get("body", "{}"))
        preferred_language = body.get("preferred_language", "")

        # Validate preferred_language format (ISO 639-1 or RFC 5646)
        if preferred_language and not re.match(LANGUAGE_CODE_PATTERN, preferred_language):
            return {
                "statusCode": 400,
                'headers': {
                    'Access-Control-Allow-Headers': '*',
                    'Access-Control-Allow-Origin': 'https://d2rs0jk5lfd7j4.cloudfront.net',
                    'Access-Control-Allow-Methods': '*',
                    'Access-Control-Allow-Credentials': 'true'
                },
                "body": json.dumps({"error": "Invalid preferred_language. Must be an ISO 639-1 code (e.g., 'en', 'es') or an RFC 5646 format with region (e.g., 'es-MX', 'fr-CA')."})
            }

        # Update DynamoDB table
        response = users_table.update_item(
            Key={"userId": user_id},
            UpdateExpression="SET preferred_language = :pl",
            ExpressionAttributeValues={":pl": preferred_language},
            ReturnValues="UPDATED_NEW"
        )
        print("update response from dynamoDB: ", response)

        return {
            "statusCode": 200,
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': 'https://d2rs0jk5lfd7j4.cloudfront.net',
                'Access-Control-Allow-Methods': '*',
                'Access-Control-Allow-Credentials': 'true'
            },
            "body": json.dumps(response)
        }

    except Exception as e:
        print(f"Error: {e}")
        return {"statusCode": 500, 
                'headers': {
                    'Access-Control-Allow-Headers': '*',
                    'Access-Control-Allow-Origin': 'https://d2rs0jk5lfd7j4.cloudfront.net',
                    'Access-Control-Allow-Methods': '*',
                    'Access-Control-Allow-Credentials': 'true'
                },
                "body": "Internal Server Error"}
