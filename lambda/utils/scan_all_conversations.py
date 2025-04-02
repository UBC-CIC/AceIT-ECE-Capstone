import os
import json
import re
import boto3

DEBUG = True

lambda_client = boto3.client('lambda')
session = boto3.Session()
env_prefix = os.environ.get("ENV_PREFIX")
dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION'))
conversations_table = dynamodb.Table(f"{env_prefix}Conversations")   # Replace with your table name
messages_table = dynamodb.Table(f"{env_prefix}Messages")

def scan_all_conversations_by_student(course_id, student_id):
    all_items = []
    start_key = None

    while True:
        scan_kwargs = {
            "FilterExpression": "course_id = :course_id AND student_id = :student_id",
            "ExpressionAttributeValues": {
                ":course_id": str(course_id),
                ":student_id": str(student_id)
            }
        }
        if start_key:
            scan_kwargs["ExclusiveStartKey"] = start_key

        response = conversations_table.scan(**scan_kwargs)
        items = response.get("Items", [])
        all_items.extend(items)

        start_key = response.get("LastEvaluatedKey")
        if not start_key:
            break

    return all_items


def scan_all_conversations(course_id, time_threshold):
    items = []
    exclusive_start_key = None

    while True:
        scan_kwargs = {
            "FilterExpression": "course_id = :course_id AND time_created >= :time_threshold",
            "ExpressionAttributeValues": {
                ":course_id": course_id,
                ":time_threshold": time_threshold
            }
        }
        if exclusive_start_key:
            scan_kwargs["ExclusiveStartKey"] = exclusive_start_key

        response = conversations_table.scan(**scan_kwargs)
        items.extend(response.get("Items", []))

        if DEBUG:
            print(f"Fetched {len(response.get('Items', []))} conversations in this page")

        exclusive_start_key = response.get("LastEvaluatedKey")
        if not exclusive_start_key:
            break

    return items


def scan_all_conversations_for_course(course_id):
    all_items = []
    last_evaluated_key = None

    while True:
        scan_kwargs = {
            "FilterExpression": "course_id = :course_id",
            "ExpressionAttributeValues": {":course_id": str(course_id)}
        }

        if last_evaluated_key:
            scan_kwargs["ExclusiveStartKey"] = last_evaluated_key

        response = conversations_table.scan(**scan_kwargs)
        items = response.get("Items", [])
        all_items.extend(items)

        last_evaluated_key = response.get("LastEvaluatedKey")
        if not last_evaluated_key:
            break

    return all_items