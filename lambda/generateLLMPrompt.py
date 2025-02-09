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
        
        conversation_id = body.get("conversation_id")
        relevant_source_content = body.get("relevantSourceContent", [])
        # new_conversation = body.get("newConversation", False)

        if not conversation_id:
            return {
                "statusCode": 400,
                "headers": {
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                "body": json.dumps({"error": "Missing required field: conversation_id"})
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
        print("Messages: ", messages)

        # Build the conversation message chain
        mistral_messages = []
        ai_sources = set()

        for message in messages:
            msg_source = message.get("msg_source")
            print("a msg_source: ", msg_source)
            content = message.get("content")
            if msg_source == "STUDENT":
                mistral_messages.append({"role": "user", "content": content})
            elif msg_source == "SYSTEM":
                mistral_messages.append({"role": "system", "content": content})
            else:
                complete_content = content + ";\n Reference materials: "
                if msg_source and isinstance(msg_source, list):
                    for source in msg_source:
                        if source['documentContent'] and source['documentContent'] not in ai_sources:
                            ai_sources.add(source['documentContent'])
                            complete_content += source['documentContent'] + ";\n"
                            # ai_sources_content += source['documentContent'] + ";\n"
                mistral_messages.append({"role": "assistant", "content": complete_content})
            
        print("Conversation chain now:", mistral_messages)

        return {
            "statusCode": 200,
            "headers": {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            "body": json.dumps({"prompt": mistral_messages})
        }

    except Exception as e:
        print(f"Error: {e}")
        return {"statusCode": 500, "body": "Internal Server Error"}