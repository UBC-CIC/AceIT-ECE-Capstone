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
        'body': json.dumps("Deletes all of the vector database contents for a given course.")
    }
