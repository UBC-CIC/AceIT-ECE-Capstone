import json

def construct_response(status_code, body):
    return {
            "statusCode": f"{status_code}",
            'headers': {
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': '*'
            },
            "body": json.dumps(body)
        }