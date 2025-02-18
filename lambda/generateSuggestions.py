import json
import boto3
import re
from utils.get_user_info import get_user_info
from utils.get_course_related_stuff import call_course_activity_stream

lambda_client = boto3.client('lambda')
translate_client = boto3.client("translate", region_name="us-west-2")

def lambda_handler(event, context):
    try:
        # authenticate first
        headers = event.get("headers", {})
        auth_token = headers.get("Authorization", "")
        if not auth_token:
            return {
                "statusCode": 400,
                'headers': {
                    'Access-Control-Allow-Headers': '*',
                    'Access-Control-Allow-Origin': 'https://d2rs0jk5lfd7j4.cloudfront.net',
                    'Access-Control-Allow-Methods': '*',
                    'Access-Control-Allow-Credentials': 'true'
                },
                "body": json.dumps({"error": "Missing required Authorization token"})
            }

        # Call Canvas API to get user info
        user_info = get_user_info(auth_token)
        if not user_info:
            return {
                "statusCode": 500,
                'headers': {
                    'Access-Control-Allow-Headers': '*',
                    'Access-Control-Allow-Origin': 'https://d2rs0jk5lfd7j4.cloudfront.net',
                    'Access-Control-Allow-Methods': '*',
                    'Access-Control-Allow-Credentials': 'true'
                },
                "body": json.dumps({"error": "Failed to fetch user info from Canvas"})
            }
        # Extract Canvas user ID
        student_id = user_info.get("userId")
        if not student_id:
            return {
                "statusCode": 500,
                'headers': {
                    'Access-Control-Allow-Headers': '*',
                    'Access-Control-Allow-Origin': 'https://d2rs0jk5lfd7j4.cloudfront.net',
                    'Access-Control-Allow-Methods': '*',
                    'Access-Control-Allow-Credentials': 'true'
                },
                "body": json.dumps({"error": "User ID not found"})
            }
        student_id = str(student_id)

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

        response = call_get_course_config(auth_token, course_id)
        course_config_prompt = response.get("systemPrompt", {})
        # print("Course config prompt: ", course_config_prompt)
        recentCourseRelated_stuff = call_course_activity_stream(auth_token, course_id)
        # print("recentCourseRelated_stuff: ", recentCourseRelated_stuff)
        suggested_questions = generate_suggestions(course_config_prompt, str(num_suggests), recentCourseRelated_stuff, course_id, student_language_pref)
        print("suggestion response", suggested_questions)

        if isinstance(suggested_questions, dict) and 'response' in suggested_questions:
            try:
                # Fix non-standard quotes before parsing JSON
                formatted_response = suggested_questions['response']
                formatted_response = re.sub(r'[“”]', '"', formatted_response)  # Convert curly quotes to standard quotes

                faq_list = json.loads(formatted_response)  # Convert JSON string inside 'response' key to Python list

                if not isinstance(faq_list, list):  # Ensure it's a list
                    raise ValueError("LLM output is not a list")
            except json.JSONDecodeError:
                print("Error: LLM output is not valid JSON after formatting:", formatted_response)
                faq_list = []  # Fallback empty list
        else:
            print("Error: LLM response format is incorrect.")
            faq_list = []  # Fallback empty list

        return {
            "statusCode": 200,
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': 'https://d2rs0jk5lfd7j4.cloudfront.net',
                'Access-Control-Allow-Methods': '*',
                'Access-Control-Allow-Credentials': 'true'
            },
            "body": json.dumps(suggested_questions.get("response"))
        }
    except KeyError as e:
        return {
            "statusCode": 400,
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': 'https://d2rs0jk5lfd7j4.cloudfront.net',
                'Access-Control-Allow-Methods': '*',
                'Access-Control-Allow-Credentials': 'true'
            },
            "body": json.dumps({"error": f"Bad Request: {str(e)}"})
        }
    except Exception as e:
        print(f"Error: {e}")
        return {"statusCode": 500, 
                'headers': {
                    'Access-Control-Allow-Headers': '*',
                    'Access-Control-Allow-Origin': 'https://d2rs0jk5lfd7j4.cloudfront.net',
                    'Access-Control-Allow-Methods': '*',
                    'Access-Control-Allow-Credentials': 'true'
                },
                "body": "Internal Server Error"}


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
            FunctionName="InvokeLLMComletionLambda",  # Replace with actual function name
            InvocationType="RequestResponse",  # Use 'Event' for async calls
            Payload=json.dumps(payload)
        )
        response_payload = json.loads(response["Payload"].read().decode("utf-8"))
        print("response_payload: ", response_payload)
        body_dict = json.loads(response_payload["body"])
        print("Body: ", body_dict, "Type: ", type(body_dict))
        return body_dict
    except Exception as e:
        print(f"Error invoking Lambda function: {e}")
        return None


def call_get_course_config(auth_token, course_id):
    """
    Calls getcourseconfig.
    """
    payload = {
        "headers": {
            "Content-Type": "application/json",
            "Authorization": auth_token,
        },
        "queryStringParameters": {
            "course": course_id
        },
    }
    try:
        response = lambda_client.invoke(
            FunctionName="GetCourseConfigLambda",  # Replace with actual function name
            InvocationType="RequestResponse",  # Use 'Event' for async calls
            Payload=json.dumps(payload)
        )
        response_payload = json.loads(response["Payload"].read().decode("utf-8"))
        print("response_payload: ", response_payload)
        body_dict = json.loads(response_payload["body"])
        print("Body: ", body_dict, "Type: ", type(body_dict))
        return body_dict
    except Exception as e:
        print(f"Error invoking Lambda function: {e}")
        return None


def translate_text(text, target_language):
    """Translates text to the student's preferred language using Amazon Translate."""
    try:
        response = translate_client.translate_text(
            Text=text,
            SourceLanguageCode="auto",  # Auto-detect source language
            TargetLanguageCode=target_language
        )
        return response["TranslatedText"]
    except Exception as e:
        print(f"Error translating text: {e}")
        return text  # Return original text if translation fails