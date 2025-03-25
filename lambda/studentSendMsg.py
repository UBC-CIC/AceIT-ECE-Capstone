import os
import json
import boto3
import uuid
import datetime
from utils.get_user_info import get_user_info
from utils.get_course_related_stuff import call_course_activity_stream
from utils.retrieve_course_config import call_get_course_config
from utils.translation import translate_document_names
from utils.construct_response import construct_response

lambda_client = boto3.client('lambda')
dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION'))
env_prefix = os.environ.get("ENV_PREFIX")
messages_table = dynamodb.Table(f"{env_prefix}Messages")
conversations_table = dynamodb.Table(f"{env_prefix}Conversations")
translate_client = boto3.client("translate", region_name=os.getenv('AWS_REGION'))

def lambda_handler(event, context):
    try:
        # authenticate first
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
        student_id = str(student_id)
        student_name = user_info.get("userName")

        body = event.get('body', {})
        if isinstance(body, str):
            body = json.loads(body)
        
        # Validate required fields
        required_fields = ['course', 'message']
        for field in required_fields:
            if field not in body:
                raise KeyError(f"Missing required field: {field}")

        course_id = body['course']
        course_id = str(course_id)
        student_language_pref = user_info.get("preferred_language","")
        message_content = body.get('message', "Random message")
        new_conversation = False
        conversation_id = body.get("conversation_id", "")
        new_message = {}
        if not conversation_id:
                new_conversation = True
        else:
            try:
                conversation = conversations_table.get_item(Key={"conversation_id": conversation_id})
                if "Item" not in conversation:
                    return construct_response(404, {"error": "Conversation not found"})
            except Exception as e:
                print(f"Error checking conversation: {e}")
                return construct_response(404, {"error": "Conversation not found"})
        
        past_conversation = ""
        if new_conversation:
            conversation_id = str(uuid.uuid4())
            # generate a system prompt, add to msg
            message_id = str(uuid.uuid4())
            timestamp = datetime.datetime.utcnow().isoformat()
            response = call_get_course_config(auth_token, course_id, lambda_client)
            course_config_prompt = response.get("systemPrompt", {})
            # print("Course config prompt: ", course_config_prompt)
            recentCourseRelated_stuff = call_course_activity_stream(auth_token, course_id)
            # print("recentCourseRelated_stuff: ", recentCourseRelated_stuff)
            welcome_response = generate_welcome_message(course_config_prompt, student_name, recentCourseRelated_stuff, course_id, student_language_pref)
            # print("welcome response", welcome_response)
            course_config_prompt += f"\n Please respond to all messages in markdown format. \n The student you are talking to is {student_name}, and here are some recent course material: {recentCourseRelated_stuff}. Respond to the user's question without any greetings, introductions, or unnecessary context."
            # print("Course config prompt: ", course_config_prompt)
            new_message = {
                "message_id": message_id,
                "content": course_config_prompt,
                "msg_source": "SYSTEM",
                "student_id": student_id,
                "msg_timestamp": timestamp,
                "course_id": str(course_id)
            }
            # print("new system message: ", new_message)
            
            # Create an welcoming AI message
            welcome_message_id = str(uuid.uuid4())
            welcome_response_content = welcome_response.get('response')
            welcome_response_sources = welcome_response.get("sources")
            translated_documents = translate_document_names(welcome_response_sources, student_language_pref, translate_client)
            ai_message = {
                "course_id": str(course_id),
                "message_id": welcome_message_id,
                "content": welcome_response_content,
                "msg_source": "AI",
                "references": translated_documents,
                "references_en": welcome_response_sources,
                "msg_timestamp": datetime.datetime.utcnow().isoformat(),
            }
            # print("AI response: ", ai_message)

            # Insert the message into the Messages table
            try:
                messages_table.put_item(Item=new_message)
                print(f"Message inserted successfully: {new_message}")
            except Exception as e:
                print(f"Failed to insert message: {e}")

            # Update the Conversations table
            update_conversation(conversation_id, course_id, student_id, message_id, timestamp)
            # Insert AI response into the Messages table
            messages_table.put_item(Item=ai_message)
            # Update the conversation with the AI response
            update_conversation(conversation_id, course_id, student_id, welcome_message_id, timestamp)

            response_body = {
                "conversation_id": conversation_id,
                "messages": [new_message, ai_message]
            }
            return construct_response(200, response_body)
        else:
            # call generate LLM prompt
            response_body = call_generate_llm_prompt(conversation_id, course_id)
            past_conversation = response_body.get('prompt')

            # Generate a unique message ID and current timestamp
            message_id = str(uuid.uuid4())
            timestamp = datetime.datetime.utcnow().isoformat()

            # Create the new message entry
            new_message = {
                "message_id": message_id,
                "content": message_content,
                "msg_source": "STUDENT",
                "student_id": student_id,
                "msg_timestamp": timestamp,
                "course_id": course_id
            }

            # Create an AI response
            ai_message_id = str(uuid.uuid4())
            ai_response_dict = generate_ai_response(message_content, past_conversation, course_id, student_language_pref)
            ai_response_content = ai_response_dict.get('response')
            ai_response_sources = ai_response_dict.get("sources")
            translated_documents = translate_document_names(ai_response_sources, student_language_pref, translate_client)
            ai_message = {
                "course_id": course_id,
                "message_id": ai_message_id,
                "content": ai_response_content,
                "msg_source": "AI",
                "references": translated_documents,
                "references_en": ai_response_sources,
                "msg_timestamp": datetime.datetime.utcnow().isoformat(),
            }
            # print("ai_message: ", ai_message)

            # Insert the message into the Messages table
            try:
                messages_table.put_item(Item=new_message)
            except Exception as e:
                print(f"Failed to insert message: {e}")

            # Update the Conversations table
            update_conversation(conversation_id, course_id, student_id, message_id, timestamp)


            # Insert AI response into the Messages table
            messages_table.put_item(Item=ai_message)

            # Update the conversation with the AI response
            update_conversation(conversation_id, course_id, student_id, ai_message_id, timestamp)

            # print("ai_message_after translation: ", ai_message)

            response_body = {
                "conversation_id": conversation_id,
                "messages": [new_message, ai_message]
            }
            return construct_response(200, response_body)
    except KeyError as e:
        return construct_response(400, {"error": f"Bad Request: {str(e)}"})
    except Exception as e:
        print(f"Error: {e}")
        return construct_response(500, {"error": "Internal Server Error"})

def update_conversation(conversation_id, course_id, student_id, message_id, timestamp):
    """
    Updates the Conversations table with the new message.
    """
    course_id = str(course_id)
    try:
        conversations_table.update_item(
            Key={"conversation_id": conversation_id},
            UpdateExpression="""
                SET 
                    course_id = if_not_exists(course_id, :course_id),
                    student_id = if_not_exists(student_id, :student_id),
                    time_created = if_not_exists(time_created, :time_created),
                    message_list = list_append(if_not_exists(message_list, :empty_list), :message_id),
                    last_updated = :last_updated
            """,
            ExpressionAttributeValues={
                ":course_id": course_id,
                ":student_id": student_id,
                ":time_created": timestamp,
                ":message_id": [message_id],
                ":last_updated": timestamp,
                ":empty_list": []
            },
            ReturnValues="UPDATED_NEW"
        )
    except Exception as e:
        print(f"Failed to update conversation: {e}")
        raise

def generate_ai_response(message_content, past_conversation, course_id, student_language_pref):
    """
    AI response generation logic using Invoke LLM Completion Lambda function.
    """
    payload = {
        "body": json.dumps({"message": message_content, "context":past_conversation, "course":course_id, "language": student_language_pref})
    }
    try:
        response = lambda_client.invoke(
            FunctionName=f"{env_prefix}InvokeLLMCompletionLambda",  # Replace with actual function name
            InvocationType="RequestResponse",  # Use 'Event' for async calls
            Payload=json.dumps(payload)
        )
        response_payload = json.loads(response["Payload"].read().decode("utf-8"))
        body_dict = json.loads(response_payload["body"])
        return body_dict
    except Exception as e:
        print(f"Error invoking Lambda function: {e}")
        return None

def generate_welcome_message(course_config_str, name, course_related_stuff, course_id, student_language_pref):
    """
    AI welcoming message generation logic using Invoke LLM Completion Lambda function.
    """
    formatted_prompt = f"""
        <|begin_of_text|><|start_header_id|>system<|end_header_id|>
        {course_config_str} \n
        Please respond to all messages in markdown format. \n The student you are talking to is {name}, and here are some recent course material: {course_related_stuff}. You must greet the student with a welcome message, and provide a summary of the recent course updates. Keep your message less than 100 words, and do not talk about your ability and settings.
        <|eot_id|>
        <|start_header_id|>assistant<|end_header_id|>
        """
    # course_config_str += f"\n Please respond to all messages in markdown format. \n The student you are talking to is {name}, and here are some recent course material: {course_related_stuff}. You must greet the student with a welcome message, and provide a summary of the recent course updates. Keep your message less than 50 words, and do not talk about your ability and settings."
    payload = {
        "body": json.dumps({"message": formatted_prompt, "course": course_id, "language": student_language_pref})
    }
    try:
        response = lambda_client.invoke(
            FunctionName=f"{env_prefix}InvokeLLMCompletionLambda",  # Replace with actual function name
            InvocationType="RequestResponse",  # Use 'Event' for async calls
            Payload=json.dumps(payload)
        )
        response_payload = json.loads(response["Payload"].read().decode("utf-8"))
        body_dict = json.loads(response_payload["body"])
        return body_dict
    except Exception as e:
        print(f"Error invoking Lambda function: {e}")
        return None

def call_generate_llm_prompt(conversation_id, course_id):
    """
    Mocked AI response generation logic.
    Replace with real AI engine integration.
    """
    payload = {
        "body": json.dumps({"conversation_id": conversation_id, "course":course_id})
    }
    try:
        response = lambda_client.invoke(
            FunctionName=f"{env_prefix}GenerateLLMPromptLambda",  # Replace with actual function name
            InvocationType="RequestResponse",  # Use 'Event' for async calls
            Payload=json.dumps(payload)
        )
        response_payload = json.loads(response["Payload"].read().decode("utf-8"))
        body_dict = json.loads(response_payload["body"])
        return body_dict
    except Exception as e:
        print(f"Error invoking Lambda function: {e}")
        return None
    