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
        
        conversation_id = body.get("conversation_id")

        if not conversation_id:
            return construct_response(400, {"error": "Missing required fields: 'conversation_id' is required"})

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

        # Build the conversation message chain
        # mistral_messages = []
        ai_sources = set()
        llama_msg = "<|begin_of_text|>"

        for message in messages:
            msg_source = message.get("msg_source")
            content = message.get("content")
            if msg_source == "STUDENT":
                # mistral_messages.append({"role": "user", "content": content})
                llama_msg += f"<|start_header_id|>user<|end_header_id|>{content}<|eot_id|>"
            elif msg_source == "SYSTEM":
                # mistral_messages.append({"role": "system", "content": content})
                llama_msg += f"<|start_header_id|>system<|end_header_id|>{content}<|eot_id|>"
            else: # AI
                complete_content = content + ";\n Reference materials: "
                references = message.get("references")
                if references and isinstance(references, list):
                    for source in references:
                        if source['documentContent'] and source['documentContent'] not in ai_sources:
                            ai_sources.add(source['documentContent'])
                            complete_content += source['documentContent'] + ";\n"
                            # ai_sources_content += source['documentContent'] + ";\n"
                # mistral_messages.append({"role": "assistant", "content": complete_content})
                llama_msg += f"<|start_header_id|>assistant<|end_header_id|>{complete_content}<|eot_id|>"

        return construct_response(200, {"prompt": llama_msg})

    except Exception as e:
        print(f"Error: {e}")
        return construct_response(500, {"error": "Internal Server Error"})