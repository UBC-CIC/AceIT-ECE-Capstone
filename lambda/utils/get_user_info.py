import json
import boto3

lambda_client = boto3.client('lambda')
def get_user_info(auth_token):
    """
    Calls getuser info to get the user info based on the provided authentication token.
    """

    # Query parameter
    # course_id = event.get("queryStringParameters", {}).get("course_id", "default-course")

    # Body message
    # message_content = event.get("body", "{}")
    # if isinstance(message_content, str):
    #     message_content = json.loads(message_content)

    payload = {
        "headers": {
            "Content-Type": "application/json",
            "Authorization": auth_token,
        }
    }
    try:
        response = lambda_client.invoke(
            FunctionName="GetUserInfoLambda",  # Replace with actual function name
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