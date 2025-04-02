import os
import boto3
from datetime import datetime, timedelta
from utils.get_user_info import get_user_info
from utils.construct_response import construct_response
from utils.canvas_api_calls import get_instructor_courses
from utils.scan_all_conversations import scan_all_conversations

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION'))
env_prefix = os.environ.get("ENV_PREFIX")
messages_table = dynamodb.Table(f"{env_prefix}Messages")
dynamodb_client = boto3.client('dynamodb')  # Client needed for batch_get_item
conversations_table = dynamodb.Table(f"{env_prefix}Conversations")
DEBUG = True

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

        courses_as_instructor = get_instructor_courses(auth_token)
        if courses_as_instructor is None:
            return construct_response(500, {"error": "Failed to fetch instructor courses from Canvas"})
        
        list_of_courses_as_instructor = [course["id"] for course in courses_as_instructor]
        print("List of courses as instructor: ", list_of_courses_as_instructor)

        # Extract query parameters
        query_params = event.get("queryStringParameters", {})
        course_id = query_params.get("course")
        num = query_params.get("num")
        period = query_params.get("period")

        if not course_id or not num or not period:
            return construct_response(400, {"error": "Missing required query parameters: 'course', 'num', and 'period' are required"})

        if int(course_id) not in list_of_courses_as_instructor:
            return construct_response(400, {"error": "You are not the instructor for this course."})

        # Convert num to int
        try:
            num = int(num)
        except ValueError:
            return construct_response(400, {"error": "Invalid value for num, must be an integer"})

        # Determine the time period filter
        time_threshold = calculate_time_threshold(period)
        if time_threshold is None:
            return construct_response(400, {"error": "Invalid period value. Must be WEEK, MONTH, or TERM."})

        # Scan Conversations table for course_id and time threshold
        conversations = scan_all_conversations(course_id, time_threshold)
        message_ids = []

        # Collect all message IDs
        for conversation in conversations:
            message_ids.extend(conversation.get("message_list", []))

        if DEBUG:
            print(f"Total message IDs fetched: {len(message_ids)}")

        # Get all messages using the collected message IDs
        messages = batch_get_messages_ai_only(message_ids)

        if DEBUG:
            print(f"Total messages fetched: {len(messages)}")
        
        material_dict = {}
        
        for message in messages:
            print("Message: ", message)
            references = message.get("references_en") or message.get("references")
            if references and isinstance(references, list):
                for source in references:
                    doc_url = source.get("sourceUrl")
                    doc_name = source.get("documentName")
                    if doc_name and doc_url:
                        material_dict[(doc_name, doc_url)] = material_dict.get((doc_name, doc_url), 0) + 1
        
        top_materials = sorted(material_dict.items(), key=lambda x: x[1], reverse=True)[:num]
        print(f"Top materials: {top_materials}")
        
        top_materials_list = [{"title": material[0], "link": material[1]} for (material, _count) in top_materials]

        return construct_response(200, top_materials_list)

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


def batch_get_messages_ai_only(message_ids):
    from boto3.dynamodb.types import TypeDeserializer
    deserializer = TypeDeserializer()

    ai_messages = []

    for i in range(0, len(message_ids), 100):
        batch_keys = [{"message_id": {"S": msg_id}} for msg_id in message_ids[i:i+100]]

        response = dynamodb_client.batch_get_item(
            RequestItems={
                messages_table.table_name: {
                    "Keys": batch_keys,
                    "ProjectionExpression": "message_id, msg_source, content, msg_timestamp, references_en, #r",
                    "ExpressionAttributeNames": {
                        "#r": "references"
                    }
                }
            }
        )

        batch_messages = response.get("Responses", {}).get(messages_table.table_name, [])

        for msg in batch_messages:
            deserialized = {k: deserializer.deserialize(v) for k, v in msg.items()}
            if deserialized.get("msg_source") == "AI":
                ai_messages.append(deserialized)

    return ai_messages
