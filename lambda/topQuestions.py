import os
import json
import boto3
from datetime import datetime, timedelta
import re
from utils.get_user_info import get_user_info
from utils.construct_response import construct_response
from utils.canvas_api_calls import get_instructor_courses
from boto3.dynamodb.types import TypeDeserializer
from utils.scan_all_conversations import scan_all_conversations
deserializer = TypeDeserializer()

# Enable or disable debug statements
DEBUG = True

# Initialize DynamoDB client
dynamodb_client = boto3.client('dynamodb')  # Client needed for batch_get_item
dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION'))
env_prefix = os.environ.get("ENV_PREFIX")
conversations_table = dynamodb.Table(f"{env_prefix}Conversations")
messages_table = dynamodb.Table(f"{env_prefix}Messages")
session = boto3.Session()
bedrock = session.client('bedrock-runtime', region_name=os.getenv('AWS_REGION'))


def lambda_handler(event, context):
    try:
        headers = event.get("headers", {})
        auth_token = headers.get("Authorization", "")
        if not auth_token:
            return construct_response(400, {"error": "Missing required header field: 'Authorization' is required"})

        # Call Canvas API to get user info
        user_info = get_user_info(auth_token)
        if DEBUG:
            print(f"User info received: {user_info}")
        if not user_info:
            return construct_response(500, {"error": "Failed to fetch user info from Canvas"})

        # Extract Canvas user ID
        student_id = str(user_info.get("userId"))
        if not student_id:
            return construct_response(500, {"error": "User ID not found"})

        # Get instructor courses
        courses_as_instructor = get_instructor_courses(auth_token)
        if courses_as_instructor is None:
            return construct_response(500, {"error": "Failed to fetch instructor courses from Canvas"})

        list_of_courses_as_instructor = [course["id"] for course in courses_as_instructor]

        # Extract query parameters
        query_params = event.get("queryStringParameters", {})
        course_id = str(query_params.get("course"))
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
        if DEBUG:
            print(f"Time threshold calculated: {time_threshold}")
        if time_threshold is None:
            return construct_response(400, {"error": "Invalid period value. Must be WEEK, MONTH, or TERM."})

        # Scan Messages table for the course and filter by timestamp
        if DEBUG:
            print(f"Scanning Conversations table for course_id={course_id} and period={period}")
            
        # Scan Conversations table for course_id and time threshold
        conversations = scan_all_conversations(course_id, time_threshold)

        if DEBUG:
            print(f"Conversations scan response: {conversations}")

        message_ids = []

        # Collect all message IDs
        for conversation in conversations:
            message_ids.extend(conversation.get("message_list", []))

        if DEBUG:
            print(f"Total message IDs fetched: {len(message_ids)}")

        # Get all messages using the collected message IDs
        messages = batch_get_messages_student_only(message_ids)

        if DEBUG:
            print(f"Total messages fetched: {len(messages)}")

        # Count the frequency of each question
        # messages = response.get("Items", [])
        # if DEBUG:
        #     print(f"Total messages fetched: {len(messages)}")

        questions = ""
        for msg in messages:
            print("message: ", msg)
            content = msg.get("content", "").strip().lower()
            if content:
                questions += content + ";"

        # Prepare prompt for the LLM
        formatted_prompt = f"""
        <|begin_of_text|><|start_header_id|>system<|end_header_id|>
        You are an AI that extracts the most frequently asked questions from student discussion messages. Analyze and group similar questions together, then return a Valid JSON array containing only top {str(num)} most frequently asked questions, like this: ['The most frequent Question', '2nd Most frequent Question', ..., 'Top nth most frequent Question']. Do NOT include any explanations, descriptions, or extra text. Questions are separated by semicolons (;). If no questions are given, return an empty array. The given questions are separated by semi-colons:
        <|eot_id|>
        <|start_header_id|>user<|end_header_id|>
        Questions: {questions}
        <|eot_id|>
        <|start_header_id|>assistant<|end_header_id|>
        """
        
        if DEBUG:
            print(f"Formatted prompt for LLM: {formatted_prompt}")

        # Call the LLM API to generate a response
        llm_response = call_llm(formatted_prompt)
        if DEBUG:
            print(f"LLM raw response: {llm_response}")

        try:
            faq_list = json.loads(llm_response)  # Convert JSON string to Python list
            if not isinstance(faq_list, list):  # Ensure it's a list
                raise ValueError("LLM output is not a list")
        except json.JSONDecodeError:
            if DEBUG:
                print("Error: LLM output is not valid JSON. Returning empty list.")
            faq_list = []  # Fallback empty list

        if DEBUG:
            print(f"Final extracted FAQ list: {faq_list}")

        return construct_response(200, faq_list)

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


def call_llm(input_text):
    """Invokes the LLM for completion."""
    model_id = "us.meta.llama3-3-70b-instruct-v1:0"

    try:
        response = bedrock.invoke_model(
            modelId=model_id,
            body=json.dumps({"prompt": input_text, "max_gen_len": 150, "temperature": 0.5, "top_p": 0.9})
        )
        
        response_body = response['body'].read().decode('utf-8')
        if not response_body.strip():
            if DEBUG:
                print("LLM response is empty! Returning fallback message.")
            return "Summary not available."

        response_json = json.loads(response_body)
        generated_response = response_json.get("generation", "Summary not available")
        generated_response = re.sub(r"^(ai:|AI:)\s*", "", generated_response).strip()

        if DEBUG:
            print(f"LLM parsed response: {generated_response}")

        return generated_response

    except Exception as e:
        print(f"Error generating answer: {e}")
        return "Sorry, there was an error generating an answer."


def batch_get_messages_student_only(message_ids):
    from boto3.dynamodb.types import TypeDeserializer
    deserializer = TypeDeserializer()

    student_messages = []

    for i in range(0, len(message_ids), 100):  # DynamoDB batch limit
        batch_keys = [{"message_id": {"S": msg_id}} for msg_id in message_ids[i:i+100]]

        if DEBUG:
            print(f"Batch getting messages: {batch_keys}")

        response = dynamodb_client.batch_get_item(
            RequestItems={
                messages_table.table_name: {
                    "Keys": batch_keys,
                    "ProjectionExpression": "message_id, msg_source, content, msg_timestamp, course_id"
                }
            }
        )

        batch_messages = response.get("Responses", {}).get(messages_table.table_name, [])

        # Deserialize and filter
        for msg in batch_messages:
            print("msg: ", msg)
            item = {k: deserializer.deserialize(v) for k, v in msg.items()}
            if item.get("msg_source") == "STUDENT":
                student_messages.append(item)

        if DEBUG:
            print(f"Batch fetched {len(batch_messages)} total; {len(student_messages)} STUDENT messages (cumulative)")

        # Handle unprocessed keys if needed...

    return student_messages
