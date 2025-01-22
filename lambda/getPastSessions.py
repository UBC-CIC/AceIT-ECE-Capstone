import json
import boto3

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    bucket_name = 'bucketfortextextract'
    file_name = 'sample.txt'

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': json.dumps("Returns a list of past sessions the user has had for a given course, providing the timestamp of the last message in the session and a AI-generated summary of the session (which should only be generated once and stored in the database to prevent excessive AI generation, unless new messages are sent in the session).")
    }
