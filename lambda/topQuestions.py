import json
import boto3
from datetime import datetime, timedelta

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
messages_table = dynamodb.Table('Messages')  # Replace with your table name
session = boto3.Session()
bedrock = session.client('bedrock-runtime', 'us-west-2') 


def lambda_handler(event, context):
    try:
        # Extract query parameters
        query_params = event.get("queryStringParameters", {})
        course_id = query_params.get("course")
        num = query_params.get("num")
        period = query_params.get("period")

        if not course_id or not num or not period:
            return {
                "statusCode": 400,
                'headers': {
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                "body": json.dumps({"error": "Missing required query parameters: course, num, or period"})
            }

        # Convert num to int
        try:
            num = int(num)
        except ValueError:
            return {
                "statusCode": 400,
                'headers': {
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                "body": json.dumps({"error": "Invalid value for num, must be an integer"})
            }

        # Determine the time period filter
        time_threshold = calculate_time_threshold(period)
        if time_threshold is None:
            return {
                "statusCode": 400,
                'headers': {
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                "body": json.dumps({"error": "Invalid period value. Must be WEEK, MONTH, or TERM."})
            }

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
        system_prompt = f"You are an AI that extracts the most frequently asked questions from student discussion messages. Analyze and group similar questions together, then return a Valid JSON array containing only top {str(num)} most frequently asked questions, like this: ['The most frequent Question', '2nd Most frequent Question', ..., 'Top nth most frequent Question']. Do NOT include any explanations, descriptions, or extra text. Questions are separated by semicolons (;). Do not include any explanation or additional text. If no questions are given, return an empty array. The given questions are separated by semi-colons:"
        for msg in messages:
            content = msg.get("content", "").strip().lower()
            if content:
                system_prompt += (content + ";")
        print("system prompt: ", system_prompt)

        mistral_messages = []
        mistral_messages.append({"role": "system", "content": system_prompt})

        compelete_input_txt=json.dumps({
            'messages': mistral_messages
        })

        # Call the LLM API to generate a response
        llm_response = call_llm(compelete_input_txt)

        try:
            faq_list = json.loads(llm_response)  # Convert JSON string to Python list
            if not isinstance(faq_list, list):  # Ensure it's a list
                raise ValueError("LLM output is not a list")
        except json.JSONDecodeError:
            print("Error: LLM output is not valid JSON:", llm_response)
            faq_list = []  # Fallback empty list

        return {
            "statusCode": 200,
            "headers": {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            "body": json.dumps(faq_list)
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


def call_llm(input_text):
    """Invokes the LLM for completion."""
    model_id = "mistral.mistral-large-2407-v1:0"  # Make sure this is the correct model ID for generation

    try:
        response = bedrock.invoke_model(
            modelId=model_id,
            body=input_text,
        )
        print("LLM response: ", response)

        # Read the StreamingBody and decode it to a string
        response_body = response['body'].read().decode('utf-8')

        # Parse the JSON response
        response_json = json.loads(response_body)
        print("Parsed response: ", response_json)

        # Extract the assistant's message content
        assistant_message = response_json['choices'][0]['message']['content']
        assistant_message = assistant_message.strip("```json").strip("```").strip()
    
        return assistant_message
    
    except Exception as e:
        print(f"Error generating answer: {e}")
        return "Sorry, there was an error generating an answer."