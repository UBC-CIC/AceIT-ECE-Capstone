import json
import re
import boto3
from utils.get_user_info import get_user_info

lambda_client = boto3.client('lambda')
session = boto3.Session()
bedrock = session.client('bedrock-runtime', 'us-west-2') 
# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
conversations_table = dynamodb.Table('Conversations')  # Replace with your table name
messages_table = dynamodb.Table('Messages')

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
        # Extract Canvas user ID
        student_id = user_info.get("userId")
        if not student_id:
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
        student_id = str(student_id)

        # Parse input from the request query parameters
        query_params = event.get("queryStringParameters", {})
        course_id = query_params.get("course", "")
        
        if not (course_id):
            return {
                "statusCode": 400,
                'headers': {
                    'Access-Control-Allow-Headers': '*',
                    'Access-Control-Allow-Origin': 'https://d2rs0jk5lfd7j4.cloudfront.net',
                    'Access-Control-Allow-Methods': '*',
                    'Access-Control-Allow-Credentials': 'true'
                },
                "body": json.dumps({"error": "Missing required parameter: need course id"})
            }
        
        # Retrieve conversations for the given course ID
        response = conversations_table.scan(
            FilterExpression="course_id = :course_id AND student_id = :student_id",
            ExpressionAttributeValues={
                ":course_id": course_id,
                ":student_id": student_id
            }
        )

        conversations = response.get("Items", [])
        past_conversations = []

        for conversation in conversations:
            summary = conversation.get('summary', "Summary not available")
            message_list = conversation.get('message_list', [])
            # Generate AI summary **only if**:
            # - No summary exists for this conversation yet
            # - There are more than 4 messages in the conversation
            updated_sum = "Summary not available"
            if ("summary not available" in summary.lower()) and len(message_list) >= 3:
                summary = call_llm(message_list)
                print("Summary: ", summary)
                updated_sum = summary
                update_summary_in_db(conversation["conversation_id"], summary)
            if len(message_list)>2:
                past_conversations.append({
                    "conversation_id": conversation["conversation_id"],
                    "last_message_timestamp": conversation.get("last_updated"),
                    "summary": conversation.get("summary", "Summary not available.")
                })

        return {
            "statusCode": 200,
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': 'https://d2rs0jk5lfd7j4.cloudfront.net',
                'Access-Control-Allow-Methods': '*',
                'Access-Control-Allow-Credentials': 'true'
            },
            "body": json.dumps(past_conversations)
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


def generate_summary_input(message_ids_list):
    """
    Calls an AI service to generate a session summary for a conversation.
    """
    # Fetch all messages in the conversation
    messages = []

    for message_id in message_ids_list:
        message = messages_table.get_item(Key={"message_id": message_id})
        if "Item" in message:
            messages.append(message["Item"])

    # Sort messages by timestamp
    messages.sort(key=lambda x: x.get("timestamp", ""))
    print("Messages to generate summary: ", messages)
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

    # complete_msg = []
    # complete_msg.append({"role": "system", "content": "Summarize given conversation history to 5 words. "})
    # complete_msg.append({"role": "user", "content" : conversation_hist})
    # body=json.dumps({
    #         'messages': complete_msg
    #      })
    
    return formatted_prompt

def call_llm(message_ids_list):
    """Invokes the LLM for summary."""
    input_text = generate_summary_input(message_ids_list)
    model_id = "arn:aws:bedrock:us-west-2:842676002045:inference-profile/us.meta.llama3-3-70b-instruct-v1:0"  # Make sure this is the correct model ID for generation

    try:
        response = bedrock.invoke_model(
            modelId=model_id,
            body=json.dumps({"prompt": input_text, "max_gen_len": 16, "temperature": 0.5, "top_p": 0.9})
        )

        response_body = response['body'].read().decode('utf-8')
        if not response_body.strip():
            print("LLM response is empty!")
            return "Summary not available."
        response_json = json.loads(response_body)
        generated_summary = response_json.get("generation", "Summary not available.")
        generated_summary = re.sub(r"^(Summary:|summary:|ai:|AI:|Course Overview:)\s*", "", generated_summary).strip()
        generated_summary = re.sub(r"[*#_]", "", generated_summary).strip()

        print("Generated summary: ", generated_summary)
        return generated_summary
    
    except Exception as e:
        print(f"Error generating summary: {e}")
        return "Summary not available."

def update_summary_in_db(conversation_id, summary):
    """
    Updates the conversation with the generated AI summary in DynamoDB.
    """
    try:
        conversations_table.update_item(
            Key={"conversation_id": conversation_id},
            UpdateExpression="SET summary = :summary",
            ExpressionAttributeValues={":summary": summary},
            ReturnValues="UPDATED_NEW"
        )
        print("Summary updated to db successfully")
    except Exception as e:
        print(f"Failed to update summary in DynamoDB: {e}")