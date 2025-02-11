import json
import boto3
from datetime import datetime, timedelta
from utils.get_user_info import get_user_info

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
messages_table = dynamodb.Table('Messages')  # Replace with your table name
conversations_table = dynamodb.Table('Conversations')  # Replace with your table name

def lambda_handler(event, context):
    try:
        headers = event.get("headers", {})
        auth_token = headers.get("Authorization", "")
        if not auth_token:
            return {
                "statusCode": 400,
                'headers': {
                    'Access-Control-Allow-Headers': '*',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                "body": json.dumps({"error": "Missing required Authorization token"})
            }

        # Call Canvas API to get user info
        user_info = get_user_info(auth_token)
        if not user_info:
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Failed to fetch user info from Canvas"})
            }
        # Extract Canvas user ID
        student_id = user_info.get("userId")
        if not student_id:
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "User ID not found"})
            }
        student_id = str(student_id)

        # TODO: check instructor for course or not

        # Extract query parameters
        query_params = event.get("queryStringParameters", {})
        course_id = query_params.get("course")
        period = query_params.get("period")

        if not course_id or not period:
            return {
                "statusCode": 400,
                "headers": {
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                "body": json.dumps({"error": "Missing required query parameters: course or period"})
            }

        # Determine the time period filter
        time_threshold = calculate_time_threshold(period)
        if time_threshold is None:
            return {
                "statusCode": 400,
                "headers": {
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                "body": json.dumps({"error": "Invalid period value. Must be WEEK, MONTH, or TERM."})
            }

        # Query the Conversations table for conversations in the given course
        response = conversations_table.scan(
            FilterExpression="course_id = :course_id AND time_created >= :time_threshold",
            ExpressionAttributeValues={
                ":course_id": course_id,
                ":time_threshold": time_threshold
            }
        )

        # Extract relevant data
        conversations = response.get("Items", [])
        unique_students = set()
        total_user_messages = 0

        for conversation in conversations:
            unique_students.add(conversation.get("student_id"))
            message_ids = conversation.get("message_list", [])
            # Batch get messages from the Messages table
            if message_ids:
                keys = [{"message_id": msg_id} for msg_id in message_ids]
                message_response = messages_table.batch_get_item(
                    RequestItems={"Messages": {"Keys": keys}}
                )
                messages = message_response.get("Responses", {}).get("Messages", [])

                # Count only messages from USER
                total_user_messages += sum(1 for msg in messages if msg.get("msg_source") == "USER")

        # Prepare the response
        engagement_stats = {
            "questionsAsked": total_user_messages,  # Total messages from all conversations
            "studentSessions": len(conversations),  # Unique conversations
            "uniqueStudents": len(unique_students)  # Unique students engaged
        }

        return {
            "statusCode": 200,
            "headers": {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            "body": json.dumps(engagement_stats)
        }

    except Exception as e:
        print(f"Error: {e}")
        return {"statusCode": 500, "body": "Internal Server Error"}


def calculate_time_threshold(period):
    """
    Calculates the timestamp threshold for the given period.
    """
    now = datetime.utcnow()
    if period == "WEEK":
        return (now - timedelta(weeks=1)).isoformat()
    elif period == "MONTH":
        return (now - timedelta(days=30)).isoformat()
    elif period == "TERM":
        return (now - timedelta(days=90)).isoformat()
    else:
        return None