import os
import boto3
from datetime import datetime, timedelta, timezone
from utils.get_user_info import get_user_info
from utils.construct_response import construct_response
from utils.canvas_api_calls import get_instructor_courses

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION'))
env_prefix = os.environ.get("ENV_PREFIX")
messages_table = dynamodb.Table(f"{env_prefix}Messages")
conversations_table = dynamodb.Table(f"{env_prefix}Conversations")
dynamodb_client = boto3.client('dynamodb')  # Client needed for batch_get_item

def lambda_handler(event, context):
    try:
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

        courses_as_instructor = get_instructor_courses(auth_token)
        print("courses_as_instructor", courses_as_instructor)
        if courses_as_instructor is None:
            return construct_response(500, {"error": "Failed to fetch instructor courses from Canvas"})
        
        list_of_courses_as_instructor = [course["id"] for course in courses_as_instructor]
        print("List of courses as instructor: ", list_of_courses_as_instructor)

        # Extract query parameters
        query_params = event.get("queryStringParameters", {})
        course_id = query_params.get("course")
        period = query_params.get("period")

        if not course_id or not period:
            return construct_response(400, {"error": "Missing required query parameters: 'course' and 'period' are required"})
        
        print("course_id", course_id)
        if int(course_id) not in list_of_courses_as_instructor:
            return construct_response(400, {"error": "You are not the instructor for this course."})

        # Determine the time period filter
        time_threshold = calculate_time_threshold(period)
        if time_threshold is None:
            return construct_response(400, {"error": "Invalid period value. Must be WEEK, MONTH, or TERM."})

        # Query the Conversations table for conversations in the given course
        response = conversations_table.scan(
            FilterExpression="course_id = :course_id AND time_created >= :time_threshold",
            ExpressionAttributeValues={
                ":course_id": course_id,
                ":time_threshold": time_threshold
            }
        )

        conversations = response.get("Items", [])
        unique_students = set()
        total_user_messages = 0
        message_ids = []
        num_valid_conversations = 0

        for conversation in conversations:
            unique_students.add(conversation.get("student_id"))
            message_ids.extend(conversation.get("message_list", []))
            if len(message_ids)>2:
                num_valid_conversations+=1

        # Process messages in batches (DynamoDB limits batch_get_item to 100 items per request)
        def batch_get_messages(message_ids):
            total_user_messages = 0
            for i in range(0, len(message_ids), 100):  # Batch size: 100
                batch_keys = [{"message_id": {"S": msg_id}} for msg_id in message_ids[i:i+100]]

                response = dynamodb_client.batch_get_item(
                    RequestItems={
                        "Messages": {
                            "Keys": batch_keys,
                            "ProjectionExpression": "message_id, msg_source"
                        }
                    }
                )

                messages = response.get("Responses", {}).get("Messages", [])

                # Count only messages from USER
                total_user_messages += sum(1 for msg in messages if msg.get("msg_source", {}).get("S") == "STUDENT")

                # Handle UnprocessedKeys (DynamoDB might not process all items in one batch)
                unprocessed_keys = response.get("UnprocessedKeys", {}).get("Messages", {}).get("Keys", [])
                while unprocessed_keys:
                    retry_response = dynamodb_client.batch_get_item(
                        RequestItems={"Messages": {"Keys": unprocessed_keys, "ProjectionExpression": "message_id, msg_source"}}
                    )
                    retry_messages = retry_response.get("Responses", {}).get("Messages", [])
                    total_user_messages += sum(1 for msg in retry_messages if msg.get("msg_source", {}).get("S") == "STUDENT")
                    unprocessed_keys = retry_response.get("UnprocessedKeys", {}).get("Messages", {}).get("Keys", [])

            return total_user_messages

        # Count only messages from USER
        total_user_messages = batch_get_messages(message_ids)
        # Prepare the response
        engagement_stats = {
            "questionsAsked": total_user_messages,  # Total messages from all conversations
            "studentSessions": num_valid_conversations,  # Unique conversations > 2
            "uniqueStudents": len(unique_students)  # Unique students engaged,
        }

        return construct_response(200, engagement_stats)

    except Exception as e:
        print(f"Error: {e}")
        return construct_response(500, {"error": "Internal Server Error"})

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