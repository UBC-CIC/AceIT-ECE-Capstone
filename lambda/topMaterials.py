import boto3
from datetime import datetime, timedelta, timezone
from utils.get_user_info import get_user_info
from utils.construct_response import construct_response

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='us-west-2')
messages_table = dynamodb.Table('Messages')  # Replace with your table name


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

        # TODO: check instructor for course or not

        # Extract query parameters
        query_params = event.get("queryStringParameters", {})
        course_id = query_params.get("course")
        num = query_params.get("num")
        period = query_params.get("period")

        if not course_id or not num or not period:
            return construct_response(400, {"error": "Missing required query parameters: 'course', 'num', and 'period' are required"})

        # Convert num to int
        try:
            num = int(num)
        except ValueError:
            return construct_response(400, {"error": "Invalid value for num, must be an integer"})

        # Determine the time period filter
        time_threshold = calculate_time_threshold(period)
        if time_threshold is None:
            return construct_response(400, {"error": "Invalid period value. Must be WEEK, MONTH, or TERM."})

        # Scan Messages table for the course and filter by timestamp and AI source
        response = messages_table.scan(
            FilterExpression="course_id = :course_id AND msg_timestamp >= :time_threshold AND msg_source <> :excluded_source AND msg_source <> :excluded_source_system",
            ExpressionAttributeValues={
                ":course_id": course_id,
                ":time_threshold": time_threshold,
                ":excluded_source": "STUDENT",  # Exclude messages with this source
                ":excluded_source_system": "SYSTEM"
            }
        )

        # Count the frequency of each material referenced by AI responses
        messages = response.get("Items", [])
        material_dict = {}
        
        for message in messages:
            if message.get("msg_source") == "AI":
                references = message.get("references_en")
                if references is None:
                    references = message.get("references")
                if references and isinstance(references, list):
                    for source in references:
                        doc_url = source.get("sourceUrl")
                        doc_name = source.get("documentName")
                        if doc_name and doc_url:
                            material_dict[(doc_name, doc_url)] = material_dict.get((doc_name, doc_url), 0) + 1
        
        top_materials = sorted(material_dict.items(), key=lambda x: x[1], reverse=True)[:num]
        
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
