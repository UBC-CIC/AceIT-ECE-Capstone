import json
import boto3

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
conversations_table = dynamodb.Table('Conversations')  # Replace with your table name

def lambda_handler(event, context):
    try:
        # Parse input from the request query parameters
        query_params = event.get("queryStringParameters", {})
        course_id = query_params.get("course")

        # TODO: also get the user id/student number
        
        if not course_id:
            return {
                "statusCode": 400,
                'headers': {
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                "body": json.dumps({"error": "Missing required parameter: course"})
            }
        
        # Retrieve conversations for the given course ID
        response = conversations_table.scan(
            FilterExpression="course_id = :course_id",
            ExpressionAttributeValues={":course_id": course_id}
        )

        conversations = response.get("Items", [])
        summaries = []

        for conversation in conversations:
            summaries.append({
                "conversation_id": conversation["conversation_id"],
                "last_message_timestamp": conversation.get("last_updated"),
                "summary": conversation.get("summary", "Summary not available.")
            })

        return {
            "statusCode": 200,
            "headers": {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            "body": json.dumps(summaries)
        }

    except Exception as e:
        print(f"Error: {e}")
        return {"statusCode": 500, "body": "Internal Server Error"}
