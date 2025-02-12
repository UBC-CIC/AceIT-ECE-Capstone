import json
import os
import boto3
import psycopg2
from datetime import datetime
import uuid
import psycopg2.extras
from utils.create_course_config_table import create_table_if_not_exists
from utils.get_rds_secret import get_secret
from utils.get_user_info import get_user_info

dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
messages_table = dynamodb.Table('Messages')  # Replace with your table name
conversations_table = dynamodb.Table('Conversations')  # Replace with your table name

def lambda_handler(event, context):
    # Parse and validate the request body
    body = ""
    try:
        body = json.loads(event.get("body", "{}"))
    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': 'https://d2rs0jk5lfd7j4.cloudfront.net',
                'Access-Control-Allow-Methods': '*',
                'Access-Control-Allow-Credentials': 'true'
            },
            "body": json.dumps({"error": "Invalid JSON in request body"})
        }
    
    required_fields = ["course", "system_prompt"]
    
    missing_fields = [field for field in required_fields if field not in body]
    if missing_fields:
        return {
            "statusCode": 400,
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': 'https://d2rs0jk5lfd7j4.cloudfront.net',
                'Access-Control-Allow-Methods': '*',
                'Access-Control-Allow-Credentials': 'true'
            },
            "body": json.dumps({"error": f"Missing required fields: {', '.join(missing_fields)}"})
        }

    course_id = body["course"]
    system_prompt = body["system_prompt"]
    print("course_id: ", course_id)
    print("system_prompt: ", system_prompt)
    
    try:
        # Query all conversations for the given course_id
        response = conversations_table.scan(
            FilterExpression="course_id = :course_id",
            ExpressionAttributeValues={":course_id": course_id}
        )
        
        conversations = response.get("Items", [])
        
        for conversation in conversations:
            conversation_id = conversation["conversation_id"]
            message_list = conversation.get("message_list", [])
            
            for message_id in message_list:
                # Retrieve the message
                message_response = messages_table.get_item(Key={"message_id": message_id})
                message_item = message_response.get("Item")
                
                if message_item and message_item["msg_source"] == "SYSTEM":
                    old_content = message_item["content"]
                    if "Please respond to all messages in markdown format." in old_content:
                        preserved_part = old_content.split("Please respond to all messages in markdown format.", 1)[1]
                    else:
                        preserved_part = ""
                    
                    # Update the SYSTEM message content
                    messages_table.update_item(
                        Key={"message_id": message_id},
                        UpdateExpression="SET content = :new_content",
                        ExpressionAttributeValues={":new_content": new_system_prompt + " Please respond to all messages in markdown format." + preserved_part}
                    )

        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': 'https://d2rs0jk5lfd7j4.cloudfront.net',
                'Access-Control-Allow-Methods': '*',
                'Access-Control-Allow-Credentials': 'true'
            },
            # 'body': json.dumps("Returns the current (updated) course configuration.")
            'body': json.dumps("update system prompt success!")
        }
    except Exception as e:
        print(e)
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': 'https://d2rs0jk5lfd7j4.cloudfront.net',
                'Access-Control-Allow-Methods': '*',
                'Access-Control-Allow-Credentials': 'true'
            },
            # 'body': json.dumps("Returns the current (updated) course configuration.")
            'body': json.dumps("failed to update system prompt...")
        }