import json
import boto3
from datetime import datetime, timedelta

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
messages_table = dynamodb.Table('Messages')  # Replace with your table name


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
        question_count = {}
        for message in messages:
            content = message.get("content", "").strip().lower()
            if content:
                question_count[content] = question_count.get(content, 0) + 1

        # Sort questions by frequency and get the top N
        top_questions = sorted(question_count.items(), key=lambda x: x[1], reverse=True)[:num]

        # Prepare the response
        top_questions_list = [question[0] for question in top_questions]

        return {
            "statusCode": 200,
            "headers": {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            "body": json.dumps(top_questions_list)
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
