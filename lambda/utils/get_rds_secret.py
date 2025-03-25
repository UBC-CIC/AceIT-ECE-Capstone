import os
import json
import boto3

# Caching secrets and DB connection
SECRET_CACHE = None

def get_cached_secret():
    global SECRET_CACHE
    if SECRET_CACHE is None:
        SECRET_CACHE = get_secret()  # Call only once
    return json.loads(SECRET_CACHE)

def get_secret():
    env_prefix = os.environ.get("ENV_PREFIX")
    secret_name = f"{env_prefix}RdsDBSecret"
    region_name = os.getenv('AWS_REGION')
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

def get_rds_proxy_endpoint(proxy_name):
    """
    Fetches the endpoint of the RDS Proxy by its name.
    """
    rds_client = boto3.client('rds')
    try:
        response = rds_client.describe_db_proxies(DBProxyName=proxy_name)
        endpoint = response['DBProxies'][0]['Endpoint']
        return endpoint
    except Exception as e:
        print(f"Error fetching RDS Proxy endpoint: {e}")
        return None

def load_db_config():
    """
    Loads the static database configuration and dynamically fetches the RDS proxy endpoint.
    """
    env_prefix = os.environ.get("ENV_PREFIX")
    proxy_name = f"{env_prefix}RdsProxySG"
    proxy_name = f"{env_prefix}RdsProxy"
    endpoint = get_rds_proxy_endpoint(proxy_name)
    
    if not endpoint:
        raise Exception("Failed to fetch RDS Proxy endpoint.")
    print("fetched endpoint: ", endpoint)
    return {
        "host": endpoint,
        "port": 5432,
        "dbname": "postgres"
    }