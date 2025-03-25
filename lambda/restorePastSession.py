import os
import boto3
from utils.get_user_info import get_user_info
from utils.construct_response import construct_response

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION'))
env_prefix = os.environ.get("ENV_PREFIX")
messages_table = dynamodb.Table(f"{env_prefix}Messages")
conversations_table = dynamodb.Table(f"{env_prefix}Conversations")


def lambda_handler(event, context):
    try:
        headers = event.get("headers", {})
        auth_token = headers.get("Authorization", "")
        if not auth_token:
            return construct_response(400, {"error": "Missing required header field: 'Authorization' is required"})

        # Call Canvas API to get user info
        user_info = get_user_info(auth_token)
        if not user_info:
            return construct_response(500, {"error": "Failed to fetch user info from Canvas"})
        # Extract Canvas user ID
        student_id = user_info.get("userId")
        if not student_id:
            return construct_response(500, {"error": "User ID not found"})

        # Extract path parameters to get conversation_id
        query_params = event.get("queryStringParameters", {})
        conversation_id = query_params.get("conversation_id")
        
        if not conversation_id:
            return construct_response(400, {"error": "Missing required query parameter: 'conversation_id' is required"})
        
        # Fetch conversation details
        conversation = conversations_table.get_item(Key={"conversation_id": conversation_id})
        if "Item" not in conversation:
            return construct_response(404, {"error": "Conversation not found"})
        
        conversation_data = conversation["Item"]

        # Fetch all messages in the conversation
        message_ids = conversation_data.get("message_list", [])
        messages = []

        for message_id in message_ids:
            message = messages_table.get_item(Key={"message_id": message_id})
            if "Item" in message:
                messages.append(message["Item"])

        # Sort messages by timestamp
        messages.sort(key=lambda x: x.get("timestamp", ""))

        response_body = {
            "conversation": conversation_data,
            "messages": messages
        }

        return construct_response(200, response_body)

    except Exception as e:
        print(f"Error: {e}")
        return construct_response(500, {"error": "Internal Server Error"})
