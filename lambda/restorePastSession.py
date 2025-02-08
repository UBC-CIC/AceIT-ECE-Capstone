import json
import boto3
from utils.get_user_info import get_user_info

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
messages_table = dynamodb.Table('Messages')  # Replace with your table name
conversations_table = dynamodb.Table('Conversations')  # Replace with your table name


def lambda_handler(event, context):
    try:
        headers = event.get("headers", {})
        auth_token = headers.get("Authorization", "")
        if not auth_token:
            return {
                "statusCode": 400,
                'headers': {
                    'Access-Control-Allow-Headers': '*',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                "body": json.dumps({"error": "Missing required Authorization token"})
            }

        # Call Canvas API to get user info
        user_info = get_user_info(auth_token)
        if not user_info:
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Failed to fetch user info from Canvas"})
            }
        # Extract Canvas user ID
        student_id = user_info.get("userId")
        if not student_id:
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "User ID not found"})
            }
        student_id = str(student_id)

        # Extract path parameters to get conversation_id
        query_params = event.get("queryStringParameters", {})
        conversation_id = query_params.get("conversation_id")
        
        if not conversation_id:
            return {
                "statusCode": 400,
                'headers': {
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                "body": json.dumps({"error": "Missing required parameter: conversationId"})
            }
        
        # Fetch conversation details
        conversation = conversations_table.get_item(Key={"conversation_id": conversation_id})
        if "Item" not in conversation:
            return {
                "statusCode": 404,
                'headers': {
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                "body": json.dumps({"error": "Conversation not found"})
            }
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

        return {
            "statusCode": 200,
            "headers": {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            "body": json.dumps({
                "conversation_id": conversation_data,
                "messages": messages
            })
        }

    except Exception as e:
        print(f"Error: {e}")
        return {"statusCode": 500, "body": "Internal Server Error"}
