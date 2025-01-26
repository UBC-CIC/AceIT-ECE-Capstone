import json
import boto3
import uuid
import datetime

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
        conversation_id = body.get('conversation_id', str(uuid.uuid4()))
        message_content = body['message']

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
        ai_response_content = generate_ai_response(message_content)
        ai_message = {
            "course_id": course_id,
            "message_id": ai_message_id,
            "content": ai_response_content,
            "msg_source": "AI", # TODO Replace with actual document source
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

def generate_ai_response(message_content):
    """
    Mocked AI response generation logic.
    Replace with real AI engine integration.
    """
    return f"AI Response to: {message_content}"