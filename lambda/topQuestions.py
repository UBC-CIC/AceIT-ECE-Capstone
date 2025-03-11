import json
import boto3
from datetime import datetime, timedelta
import re
from utils.get_user_info import get_user_info
from utils.construct_response import construct_response
from utils.canvas_api_calls import get_instructor_courses

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
messages_table = dynamodb.Table('Messages')  # Replace with your table name
session = boto3.Session()
bedrock = session.client('bedrock-runtime', 'us-west-2') 


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

        # Scan Messages table for the course and filter by timestamp
        response = messages_table.scan(
            FilterExpression="course_id = :course_id AND msg_timestamp >= :time_threshold AND msg_source = :msg_source",
            ExpressionAttributeValues={
                ":course_id": course_id,
                ":time_threshold": time_threshold,
                ":msg_source": "STUDENT"
            }
        )

        # Count the frequency of each question
        messages = response.get("Items", [])
        questions = ""
        # system_prompt = f"You are an AI that extracts the most frequently asked questions from student discussion messages. Analyze and group similar questions together, then return a Valid JSON array containing only top {str(num)} most frequently asked questions, like this: ['The most frequent Question', '2nd Most frequent Question', ..., 'Top nth most frequent Question']. Do NOT include any explanations, descriptions, or extra text. Questions are separated by semicolons (;). Do not include any explanation or additional text. If no questions are given, return an empty array. The given questions are separated by semi-colons:"
        for msg in messages:
            content = msg.get("content", "").strip().lower()
            if content:
                questions += (content + ";")
        formatted_prompt = f"""
        <|begin_of_text|><|start_header_id|>system<|end_header_id|>
        You are an AI that extracts the most frequently asked questions from student discussion messages. Analyze and group similar questions together, then return a Valid JSON array containing only top {str(num)} most frequently asked questions, like this: ['The most frequent Question', '2nd Most frequent Question', ..., 'Top nth most frequent Question']. Do NOT include any explanations, descriptions, or extra text. Questions are separated by semicolons (;). If no questions are given, return an empty array. The given questions are separated by semi-colons:
        <|eot_id|>
        <|start_header_id|>user<|end_header_id|>
        Questions: {questions}
        <|eot_id|>
        <|start_header_id|>assistant<|end_header_id|>
        """
        # print("system prompt: ", formatted_prompt)

        # Call the LLM API to generate a response
        llm_response = call_llm(formatted_prompt)
        # print("llm response: ", llm_response)

        try:
            faq_list = json.loads(llm_response)  # Convert JSON string to Python list
            if not isinstance(faq_list, list):  # Ensure it's a list
                raise ValueError("LLM output is not a list")
        except json.JSONDecodeError:
            # print("Error: LLM output is not valid JSON:", llm_response)
            faq_list = []  # Fallback empty list

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
    model_id = "arn:aws:bedrock:us-west-2:842676002045:inference-profile/us.meta.llama3-3-70b-instruct-v1:0"  # Make sure this is the correct model ID for generation

    try:
        response = bedrock.invoke_model(
            modelId=model_id,
            body=json.dumps({"prompt": input_text, "max_gen_len": 150, "temperature": 0.5, "top_p": 0.9})
        )
        # print("LLM response: ", response)

        response_body = response['body'].read().decode('utf-8')
        if not response_body.strip():
            # print("LLM response is empty!")
            return "Summary not available."
        response_json = json.loads(response_body)
        generated_response = response_json.get("generation", "Summary not available")
        generated_response = re.sub(r"^(ai:|AI:)\s*", "", generated_response).strip()
        
        # generated_response = re.sub(r"[*#_]", "", generated_response).strip()

        return generated_response
    
    except Exception as e:
        print(f"Error generating answer: {e}")
        return "Sorry, there was an error generating an answer."