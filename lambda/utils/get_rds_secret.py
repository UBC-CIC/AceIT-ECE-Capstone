import json
import os
import boto3
import psycopg2
from datetime import datetime
import uuid
import psycopg2.extras

# Caching secrets and DB connection
SECRET_CACHE = None

def get_cached_secret():
    global SECRET_CACHE
    if SECRET_CACHE is None:
        SECRET_CACHE = get_secret()  # Call only once
    return json.loads(SECRET_CACHE)

def get_secret():
    secret_name = "MyRdsSecret"
    region_name = "us-west-2"
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except Exception as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    secret = get_secret_value_response['SecretString']
    return secret