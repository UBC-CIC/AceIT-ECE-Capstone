import json
import boto3
import uuid
import datetime
import requests  # to make HTTP requests

dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
messages_table = dynamodb.Table('Messages')  # Replace with your table name
conversations_table = dynamodb.Table('Conversations')  # Replace with your table name

def lambda_handler(event, context):
    try:
        # Parse input from the request body
        body = event.get('body', {})
        if isinstance(body, str):
            body = json.loads(body)
        
        # Validate required fields
        required_fields = ['course_id', 'student_id', 'message']
        for field in required_fields:
            if field not in body:
                raise KeyError(f"Missing required field: {field}")

        course_id = body['course_id']
        student_id = body['student_id']
        message_content = body.get('message', "Random message")
        studnet_name = "Alice Test" #TODO create student and course database to match ids
        new_conversation = False
        conversation_id = body.get("conversation_id", "")
        new_message = {}
        if not conversation_id:
                new_conversation = True
        else:
            try:
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
            except Exception as e:
                print(f"Error checking conversation: {e}")
                return {
                        "statusCode": 404,
                        'headers': {
                            'Access-Control-Allow-Headers': 'Content-Type',
                            'Access-Control-Allow-Origin': '*',
                            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                        },
                        "body": json.dumps({"error": "Conversation not found"})
                    }
        
        past_conversation = ""
        if new_conversation:
            conversation_id = str(uuid.uuid4())
            # generate a system prompt, add to msg
            message_id = str(uuid.uuid4())
            timestamp = datetime.datetime.utcnow().isoformat()
            url = f"https://i6t0c7ypi6.execute-api.us-west-2.amazonaws.com/prod/api/ui/instructor/config?course={course_id}"
            try:
                response = requests.get(url)
                print(f"Sent get request to for a new conversation: {response.json()}")
            except requests.exceptions.RequestException as e:
                print(f"Error sending get request to course {course_id}: {e}")
            res_json = response.json()
            course_config_prompt = res_json.get("db retrieve", {}).get("systemPrompt")
            print("Course config prompt: ", course_config_prompt)
            recentCourseRelated_stuff = "Unavailable now"
            course_config_prompt += f"\n Please respond to all messages in HTML format. \n The student you are talking to is {studnet_name}, and here are some recent course material: {recentCourseRelated_stuff}. You need to first welcome this student, and provide a summary of the recent course updates."
            new_message = {
                "message_id": message_id,
                "content": course_config_prompt,
                "msg_source": "SYSTEM",
                "student_id": student_id,
                "msg_timestamp": timestamp,
                "course_id": course_id
            }
            print("new system message: ", new_message)
            message_content = course_config_prompt
        else:
            # call generate LLM prompt
            url = "https://i6t0c7ypi6.execute-api.us-west-2.amazonaws.com/prod/api/llm/chat/generate"
            payload = {"conversation_id": conversation_id}
            
            try:
                # Send a POST request
                response = requests.post(url, json=payload)  # Use `json` to serialize the body as JSON
                print(f"Sent post request to generate prompt for {conversation_id}: {response.json()}")
            except requests.exceptions.RequestException as e:
                print(f"Error sending post request to {conversation_id}: {e}")
            print(response.json())
            response_json = response.json()
            past_conversation = response_json.get('prompt')
            print("past_conversation: ", past_conversation)

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
            print("new message: ", new_message)

        # Insert the message into the Messages table
        try:
            messages_table.put_item(Item=new_message)
            print(f"Message inserted successfully: {new_message}")
        except Exception as e:
            print(f"Failed to insert message: {e}")

        # Update the Conversations table
        update_conversation(conversation_id, course_id, student_id, message_id, timestamp)

        # Create an AI response (mocked here, replace with real AI logic)
        ai_message_id = str(uuid.uuid4())
        ai_response_dict = generate_ai_response(message_content, past_conversation)
        ai_response_content = ai_response_dict.get('response')
        ai_response_sources = ai_response_dict.get("sources")
        ai_message = {
            "course_id": course_id,
            "message_id": ai_message_id,
            "content": ai_response_content,
            "msg_source": ai_response_sources,
            "msg_timestamp": datetime.datetime.utcnow().isoformat(),
        }

        # Insert AI response into the Messages table
        messages_table.put_item(Item=ai_message)

        # Update the conversation with the AI response
        update_conversation(conversation_id, course_id, student_id, ai_message_id, timestamp)

        return {
            "statusCode": 200,
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            "body": json.dumps({
                "conversation_id": conversation_id,
                "messages": [new_message, ai_message]
            })
        }
    except KeyError as e:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": f"Bad Request: {str(e)}"})
        }
    except Exception as e:
        print(f"Error: {e}")
        return {"statusCode": 500, "body": "Internal Server Error"}

def update_conversation(conversation_id, course_id, student_id, message_id, timestamp):
    """
    Updates the Conversations table with the new message.
    """
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

def generate_ai_response(message_content, past_conversation):
    """
    Mocked AI response generation logic.
    Replace with real AI engine integration.
    """
    # call invoke llm completion
    url = "https://i6t0c7ypi6.execute-api.us-west-2.amazonaws.com/prod/api/llm/completion"
    payload = {"message": message_content, "context":past_conversation}
    print("Payload: ", payload)
    
    try:
        # Send a POST request
        response = requests.post(url, json=payload)  # Use `json` to serialize the body as JSON
        print(f"Sent post request to llm completion for message: {response.json()}")
    except requests.exceptions.RequestException as e:
        print(f"Error sending post request to llm completion: {e}")
    print("AI response: ", response.json())
    response_json = response.json()
    return response_json