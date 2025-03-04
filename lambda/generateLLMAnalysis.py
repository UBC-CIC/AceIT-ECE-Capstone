import json
import boto3
from utils.construct_response import construct_response
# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
messages_table = dynamodb.Table('Messages')  # Replace with your table name
conversations_table = dynamodb.Table('Conversations')  # Replace with your table name

def lambda_handler(event, context):
    try:
        # Parse input from the request body
        body = event.get("body", {})
        if isinstance(body, str):
            body = json.loads(body)
        
        messages = body.get("messages")

        if not messages:
            return construct_response(400, {"error": "Missing required fields: 'messages' is required"})
        
        system_prompt = f"Please analyze and cluster the following student questions, and generate a list of the most frequently asked questions in JSON format, ranked from most frequent questions to least frequent questions. \nQuestions: "
        for msg in messages:
            content = msg.get("content", "").strip().lower()
            if content:
                system_prompt += (content + ";\n")

        mistral_messages = []
        mistral_messages.append({"role": "system", "content": system_prompt})

        return construct_response(200, {"prompt": mistral_messages})

    except Exception as e:
        print(f"Error: {e}")
        return construct_response(500, {"error": "Internal Server Error"})
