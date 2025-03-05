import json
import boto3
import re
from utils.get_user_info import get_user_info
from utils.get_course_related_stuff import call_course_activity_stream
from utils.retrieve_course_config import call_get_course_config
from utils.construct_response import construct_response

lambda_client = boto3.client('lambda')
translate_client = boto3.client("translate", region_name="us-west-2")

def lambda_handler(event, context):
    try:
        # authenticate first
        headers = event.get("headers", {})
        auth_token = headers.get("Authorization", "")
        if not auth_token:
            return construct_response(400, {"error": "Missing required fields: 'Authorization' is required"})

        # Call Canvas API to get user info
        user_info = get_user_info(auth_token)
        if not user_info:
            return construct_response(500, {"error": "Failed to fetch user info from Canvas"})
        
        # Extract Canvas user ID
        student_id = user_info.get("userId")
        if not student_id:
            return construct_response(500, {"error": "User ID not found"})
    
        params = event.get("queryStringParameters", {})
        course_id = params.get("course")
        course_id = str(course_id)
        num_suggests = int(params.get("num_suggests", 4))
        
        # Validate required fields
        required_fields = ['course']
        for field in required_fields:
            if field not in params:
                raise KeyError(f"Missing required field: {field}")
        
        student_language_pref = user_info.get("preferred_language","")

        response = call_get_course_config(auth_token, course_id, lambda_client)
        course_config_prompt = response.get("systemPrompt", {})
        recentCourseRelated_stuff = call_course_activity_stream(auth_token, course_id)
        suggested_questions = generate_questions_with_retries(course_config_prompt, str(num_suggests), recentCourseRelated_stuff, course_id, student_language_pref)

        return construct_response(200, suggested_questions)
    
    except KeyError as e:
        return construct_response(400, {"error": f"Bad Request: {str(e)}"})
    
    except Exception as e:
        print(f"Error: {e}")
        return construct_response(500, {"error": "Internal Server Error"})


def generate_suggestions(course_config_str, num_suggestions, course_related_stuff, course_id, student_language_pref):
    """
    Mocked AI response generation logic.
    Replace with real AI engine integration.
    """
    formatted_prompt = f"""
        <|begin_of_text|><|start_header_id|>system<|end_header_id|>
        {course_config_str} \n
        Your Task is:
        Generate {num_suggestions} suggested questions to ask you for the student in this course. Keep each question less than 7 words.
        The questions should be aligned with your role and the course's recent activity.
        Reply only the list of questions in the following format: return ONLY a list like this: ["question 1", "question 2", ..., "question {num_suggestions}"]
        Here are some recent course activity: {course_related_stuff}.
        <|eot_id|>
        <|start_header_id|>assistant<|end_header_id|>
        """
    payload = {
        "body": json.dumps({"message": formatted_prompt, "course": course_id, "language": student_language_pref})
    }
    try:
        response = lambda_client.invoke(
            FunctionName="InvokeLLMCompletionLambda",  # Replace with actual function name
            InvocationType="RequestResponse",  # Use 'Event' for async calls
            Payload=json.dumps(payload)
        )
        response_payload = json.loads(response["Payload"].read().decode("utf-8"))
        body_dict = json.loads(response_payload["body"])
        return body_dict
    except Exception as e:
        print(f"Error invoking Lambda function: {e}")
        return None


def flatten_list(nested_list):
    return [item for sublist in nested_list for item in (sublist if isinstance(sublist, list) else [sublist])]

def generate_questions_with_retries(course_config_prompt, num_suggests, recentCourseRelated_stuff, course_id, student_language_pref):
    """Tries to generate questions up to MAX_RETRIES times if errors occur."""
    MAX_RETRIES = 3  # Number of attempts
    for attempt in range(1, MAX_RETRIES + 1):
        suggested_questions = generate_suggestions(course_config_prompt, str(num_suggests), recentCourseRelated_stuff, course_id, student_language_pref)
        
        faq_list = parse_llm_response(suggested_questions)

        if faq_list:  # If successful, return the list
            return faq_list

    return []  # Return empty list if all retries fail


def parse_llm_response(suggested_questions):
    """Parses and fixes LLM response to ensure it's a valid JSON list."""
    if not isinstance(suggested_questions, dict) or 'response' not in suggested_questions:
        return []

    formatted_response = suggested_questions['response']

    try:
        # Step 1: Fix non-standard quotes (curly, angled French, etc.)
        formatted_response = re.sub(r'[“”«»‘’【】「」]', '"', formatted_response)

        # Step 2: Ensure it's a valid JSON list
        if not formatted_response.startswith("[") or not formatted_response.endswith("]"):
            formatted_response = f"[{formatted_response}]"

        # Step 3: Replace non-standard separators
        formatted_response = re.sub(r'\s*,\s*', ',', formatted_response)  # Normalize commas
        formatted_response = re.sub(r'[“”«»‘’【】「」]', '"', formatted_response)
        formatted_response = re.sub(r'[，、；;]', ',', formatted_response)
        formatted_response = re.sub(r'[;；｜/。，|/]', ',', formatted_response)
        formatted_response = re.sub(r'\s*,\s*', ',', formatted_response).strip()

        # Step 4: Remove extra string wrapping (if JSON list is inside a string)
        while formatted_response.startswith('"') and formatted_response.endswith('"'):
            formatted_response = formatted_response[1:-1]

        formatted_response = formatted_response.strip()
        if not (formatted_response.startswith("[") and formatted_response.endswith("]")):
            formatted_response = "[" + formatted_response + "]"  # Force list format

        # Step 5: Parse JSON
        faq_list = json.loads(formatted_response)
        
        faq_list = flatten_list(faq_list)

        # Step 7: Validate that it's a list
        if not isinstance(faq_list, list):
            raise ValueError("LLM output is not a list")

        return faq_list  # Successfully parsed list

    except json.JSONDecodeError:
        print("Error: LLM output is not valid JSON after formatting:", formatted_response)
    except ValueError as ve:
        print(f"Error: {ve}")

    return []  # Return empty list on failure