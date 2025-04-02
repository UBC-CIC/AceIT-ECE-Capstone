import os
import json
import re
import boto3
from utils.get_user_info import get_user_info
from utils.construct_response import construct_response

DEBUG = True

lambda_client = boto3.client('lambda')
session = boto3.Session()
bedrock = session.client('bedrock-runtime', region_name=os.getenv('AWS_REGION')) 
# Initialize DynamoDB client
env_prefix = os.environ.get("ENV_PREFIX")
dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION'))
conversations_table = dynamodb.Table(f"{env_prefix}Conversations")   # Replace with your table name
messages_table = dynamodb.Table(f"{env_prefix}Messages")

def lambda_handler(event, context):
    try:
        if DEBUG:
            print(f"Received event: {json.dumps(event)}")

        headers = event.get("headers", {})
        auth_token = headers.get("Authorization", "")
        if not auth_token:
            return construct_response(400, {"error": "Missing required header field: 'Authorization' is required"})

        # Call Canvas API to get user info
        user_info = get_user_info(auth_token)
        if DEBUG:
            print(f"User info received: {user_info}")
        
        if not user_info:
            return construct_response(500, {"error": "Failed to fetch user info from Canvas"})
        
        # Extract Canvas user ID
        student_id = user_info.get("userId")
        if not student_id:
            return construct_response(500, {"error": "User ID not found"})
        student_id = str(student_id)
        
        # Parse input from the request query parameters
        query_params = event.get("queryStringParameters", {})
        course_id = query_params.get("course", "")
        
        if not course_id:
            return construct_response(400, {"error": "Missing required parameter: 'course' is required"})
        
        if DEBUG:
            print(f"Fetching conversations for student_id: {student_id} and course_id: {course_id}")
        
        # Retrieve conversations for the given course ID
        conversations = scan_all_conversations_by_student(course_id, student_id)
        past_conversations = []

        for conversation in conversations:
            summary = conversation.get('summary', "Summary not available")
            message_list = conversation.get('message_list', [])

            if DEBUG:
                print(f"Processing conversation: {conversation.get('conversation_id')}, Messages: {len(message_list)}")

            # Generate AI summary **only if**:
            # - No summary exists for this conversation yet
            # - There are more than 4 messages in the conversation
            updated_sum = "Summary not available"
            if ("summary not available" in summary.lower()) and len(message_list) >= 3:
                if DEBUG:
                    print(f"Calling LLM to generate summary for conversation: {conversation.get('conversation_id')}")
                summary = call_llm(message_list)
                updated_sum = summary
                update_summary_in_db(conversation["conversation_id"], summary)
            else:
                updated_sum = summary
            
            if len(message_list) > 2:
                past_conversations.append({
                    "conversation_id": conversation["conversation_id"],
                    "last_message_timestamp": conversation.get("last_updated"),
                    "summary": updated_sum
                })

        if DEBUG:
            print(f"Returning {len(past_conversations)} conversations")
        
        return construct_response(200, past_conversations)

    except Exception as e:
        print(f"Error: {e}")
        return construct_response(500, {"error": "Internal Server Error"})

def generate_summary_input(message_ids_list):
    """
    Calls an AI service to generate a session summary for a conversation.
    """
    messages = []

    for message_id in message_ids_list:
        message = messages_table.get_item(Key={"message_id": message_id})
        if "Item" in message:
            messages.append(message["Item"])
    
    if DEBUG:
        print(f"Fetched {len(messages)} messages for summary generation.")

    # Sort messages by timestamp
    messages.sort(key=lambda x: x.get("timestamp", ""))
    conversation_hist = ""

    for message in messages:
        msg_source = message.get("msg_source")
        content = message.get("content", "")
        if msg_source == "STUDENT" and content:
            conversation_hist += "STUDENT: " + content + "\n"
        elif msg_source == "AI" and content:
            conversation_hist += "ASSISTANT: " + content + "\n"

    formatted_prompt = f"""
        <|begin_of_text|><|start_header_id|>system<|end_header_id|>
        Summarize the given conversation history in 5 words or less. Respond with ONLY the 1-5 words summary, and nothing else. No introduction, no formatting, no extra words.
        <|eot_id|>
        <|start_header_id|>user<|end_header_id|>
        Conversation history: {conversation_hist}
        <|eot_id|>
        <|start_header_id|>assistant<|end_header_id|>
    """

    if DEBUG:
        print(f"Generated summary prompt: {formatted_prompt}")
    
    return formatted_prompt

def call_llm(message_ids_list):
    """Invokes the LLM for summary."""
    input_text = generate_summary_input(message_ids_list)
    model_id = "us.meta.llama3-3-70b-instruct-v1:0"

    try:
        if DEBUG:
            print("Invoking model with input text...")
        
        response = bedrock.invoke_model(
            modelId=model_id,
            body=json.dumps({"prompt": input_text, "max_gen_len": 16, "temperature": 0.5, "top_p": 0.9})
        )

        response_body = response['body'].read().decode('utf-8')
        if DEBUG:
            print(f"LLM response: {response_body}")
        
        if not response_body.strip():
            return "Summary not available."
        
        response_json = json.loads(response_body)
        generated_summary = response_json.get("generation", "Summary not available")
        generated_summary = re.sub(r"^(Summary:|summary:|ai:|AI:|Course Overview:)\\s*", "", generated_summary).strip()
        generated_summary = re.sub(r"[*#_]", "", generated_summary).strip()

        return generated_summary
    
    except Exception as e:
        print(f"Error generating summary: {e}")
        return "Summary not available."

def update_summary_in_db(conversation_id, summary):
    """
    Updates the conversation with the generated AI summary in DynamoDB.
    """
    try:
        if DEBUG:
            print(f"Updating summary for conversation {conversation_id} in DB.")
        
        conversations_table.update_item(
            Key={"conversation_id": conversation_id},
            UpdateExpression="SET summary = :summary",
            ExpressionAttributeValues={":summary": summary},
            ReturnValues="UPDATED_NEW"
        )
        print("Summary updated to db successfully")
    except Exception as e:
        print(f"Failed to update summary in DynamoDB: {e}")


def scan_all_conversations_by_student(course_id, student_id):
    all_items = []
    start_key = None

    while True:
        scan_kwargs = {
            "FilterExpression": "course_id = :course_id AND student_id = :student_id",
            "ExpressionAttributeValues": {
                ":course_id": str(course_id),
                ":student_id": str(student_id)
            }
        }
        if start_key:
            scan_kwargs["ExclusiveStartKey"] = start_key

        response = conversations_table.scan(**scan_kwargs)
        items = response.get("Items", [])
        all_items.extend(items)

        start_key = response.get("LastEvaluatedKey")
        if not start_key:
            break

    return all_items
