import json
import boto3
from datetime import datetime, timedelta

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
messages_table = dynamodb.Table('Messages')  # Replace with your table name
conversations_table = dynamodb.Table('Conversations')  # Replace with your table name

def lambda_handler(event, context):
    try:
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

        # Fetch messages for the course and time period
        response = messages_table.scan(
            FilterExpression="course_id = :course_id AND msg_timestamp >= :time_threshold",
            ExpressionAttributeValues={
                ":course_id": course_id,
                ":time_threshold": time_threshold
            }
        )

        # Aggregate engagement statistics
        messages = response.get("Items", [])
        questions_asked = 0
        unique_students = set()
        sessions = set()

        for message in messages:
            if message.get("msg_source") == "STUDENT":
                questions_asked += 1
                unique_students.add(message.get("student_id"))
                sessions.add(message.get("conversation_id"))

        # Prepare the response
        engagement_stats = {
            "questionsAsked": questions_asked,
            "studentSessions": len(sessions),
            "uniqueStudents": len(unique_students)
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