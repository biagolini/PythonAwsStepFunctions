import boto3
from boto3.dynamodb.conditions import Key
import time

dynamodb = boto3.resource('dynamodb')
buffer_table = dynamodb.Table('UserMessageBufferTable')
consolidated_table = dynamodb.Table('ConsolidatedMessagesTable')

def lambda_handler(event, context):
    user_id = event['user_id']
    
    # Query all messages for user
    response = buffer_table.query(
        KeyConditionExpression=Key('user_id').eq(user_id),
        ScanIndexForward=True  # ascending by timestamp
    )
    messages = response.get('Items', [])
    if not messages:
        return {'status': 'no_messages_found'}

    # Build consolidated session payload
    consolidated_session = {
        'user_id': user_id,
        'session_end_timestamp': int(time.time()),
        'messages': messages,
        'channel': messages[-1].get('channel', 'unknown')  # optional: infer from last msg
    }

    # Write to consolidated table
    consolidated_table.put_item(Item=consolidated_session)

    # Delete each message from buffer
    with buffer_table.batch_writer() as batch:
        for msg in messages:
            batch.delete_item(
                Key={
                    'user_id': msg['user_id'],
                    'timestamp': msg['timestamp']
                }
            )

    return {
        'status': 'session_consolidated',
        'message_count': len(messages)
    }