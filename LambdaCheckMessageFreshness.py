import boto3
import time
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('UserMessageBufferTable')

WAIT_THRESHOLD_SECONDS = 30  # inactivity threshold

def lambda_handler(event, context):
    user_id = event['user_id']
    
    # Query messages sorted by timestamp DESC (latest first)
    response = table.query(
        KeyConditionExpression=Key('user_id').eq(user_id),
        ScanIndexForward=False,  # descending order
        Limit=1
    )
    
    items = response.get('Items', [])
    if not items:
        return {
            'should_wait': False,
            'wait_seconds': 0,
            'reason': 'No messages found.'
        }

    latest_timestamp = int(items[0]['timestamp'])
    current_timestamp = int(time.time())
    elapsed_time = current_timestamp - latest_timestamp
    remaining_wait = WAIT_THRESHOLD_SECONDS - elapsed_time

    if remaining_wait <= 0:
        return {
            'should_wait': False,
            'wait_seconds': 0,
            'reason': 'Inactivity threshold met.'
        }
    else:
        return {
            'should_wait': True,
            'wait_seconds': remaining_wait,
            'reason': f'{remaining_wait} seconds remaining until inactivity threshold.'
        }
