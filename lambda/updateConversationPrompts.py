import os
import json
import boto3
import traceback
from utils.construct_response import construct_response

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION'))
messages_table = dynamodb.Table('Messages')  # Replace with your table name
conversations_table = dynamodb.Table('Conversations')  # Replace with your table name

# Set debug flag (change to False to disable debug statements)
debug = False

def log_debug(message):
    """Print debug messages only if debugging is enabled."""
    if debug:
        print(f"DEBUG: {message}")

def lambda_handler(event, context):
    log_debug(f"Received event: {json.dumps(event, indent=2)}")

    # Parse and validate the request body
    body = ""
    try:
        body = json.loads(event.get("body", "{}"))
        log_debug(f"Parsed request body: {body}")
    except json.JSONDecodeError:
        print("ERROR: Invalid JSON in request body")
        return construct_response(400, {"error": "Invalid JSON in request body"})

    required_fields = ["course", "system_prompt"]
    
    missing_fields = [field for field in required_fields if field not in body]
    if missing_fields:
        print(f"ERROR: Missing required fields: {', '.join(missing_fields)}")
        return construct_response(400, {"error": f"Missing required fields: {', '.join(missing_fields)}"})

    course_id = body["course"]
    system_prompt = body["system_prompt"]

    log_debug(f"course_id={course_id}, system_prompt={system_prompt}")

    try:
        # Query all conversations for the given course_id
        log_debug(f"Querying conversations for course_id: {course_id}")
        response = conversations_table.scan(
            FilterExpression="course_id = :course_id",
            ExpressionAttributeValues={":course_id": str(course_id)}  # Ensure course_id is string
        )
        print(f"DEBUG: Raw scan response: {json.dumps(response, indent=2)}")  # Debugging output

        conversations = response.get("Items", [])
        print(f"DEBUG: Found {len(conversations)} conversations for course_id {course_id}.")

        for conversation in conversations:
            conversation_id = conversation.get("conversation_id")
            message_list = conversation.get("message_list", [])

            log_debug(f"Processing conversation_id={conversation_id}, messages={len(message_list)}")

            for message_id in message_list:
                log_debug(f"Fetching message_id={message_id}")
                
                # Retrieve the message
                message_response = messages_table.get_item(Key={"message_id": message_id})
                message_item = message_response.get("Item")

                if not message_item:
                    log_debug(f"WARNING: message_id={message_id} not found in Messages table.")
                    continue
                
                log_debug(f"Retrieved message_id={message_id}, msg_source={message_item.get('msg_source')}")
                
                if message_item["msg_source"] == "SYSTEM":
                    old_content = message_item["content"]
                    log_debug(f"Old SYSTEM message content: {old_content}")

                    if "Please respond to all messages in markdown format." in old_content:
                        preserved_part = old_content.split("Please respond to all messages in markdown format.", 1)[1]
                        log_debug(f"Preserved content: {preserved_part}")
                    else:
                        preserved_part = ""
                    
                    new_content = system_prompt + " Please respond to all messages in markdown format." + preserved_part
                    log_debug(f"New SYSTEM message content: {new_content}")

                    log_debug(f"Updating message_id={message_id} with new content.")
                    
                    # Update the SYSTEM message content
                    messages_table.update_item(
                        Key={"message_id": message_id},
                        UpdateExpression="SET content = :new_content",
                        ExpressionAttributeValues={":new_content": new_content}
                    )

        log_debug("Successfully processed all conversations.")
        return construct_response(200, {"message": "success"})

    except Exception as e:
        print("ERROR: Exception occurred while updating system prompt.")
        print(traceback.format_exc())  # Print full stack trace for debugging
        return construct_response(500, {"error": "failed to update system prompt"})
