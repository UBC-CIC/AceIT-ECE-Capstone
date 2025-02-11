import json
import boto3

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
            return {
                "statusCode": 400,
                "headers": {
                    'Access-Control-Allow-Headers': '*',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': '*'
                },
                "body": json.dumps({"error": "Missing required field: messages"})
            }
        
        system_prompt = f"Please analyze and cluster the following student questions, and generate a list of the most frequently asked questions in JSON format, ranked from most frequent questions to least frequent questions. \nQuestions: "
        for msg in messages:
            content = msg.get("content", "").strip().lower()
            if content:
                system_prompt += (content + ";\n")
        print("system prompt: ", system_prompt)

        mistral_messages = []
        mistral_messages.append({"role": "system", "content": system_prompt})

        return {
            "statusCode": 200,
            "headers": {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': '*'
            },
            "body": json.dumps({"prompt": mistral_messages})
        }

    except Exception as e:
        print(f"Error: {e}")
        return {"statusCode": 500, 
                'headers': {
                    'Access-Control-Allow-Headers': '*',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': '*'
                },
                "body": "Internal Server Error"}
