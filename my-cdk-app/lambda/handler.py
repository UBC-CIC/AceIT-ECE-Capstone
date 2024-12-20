def handler(event, context):
    print("Lambda function invoked!")
    return {
        "statusCode": 200,
        "body": "Hello from AWS Lambda!"
    }
