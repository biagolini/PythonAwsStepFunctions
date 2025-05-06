import boto3
from botocore.exceptions import ClientError

TABLE_NAME = 'ConsolidatedMessagesTable'

dynamodb = boto3.client('dynamodb')

def create_consolidated_messages_table():
    try:
        dynamodb.create_table(
            TableName=TABLE_NAME,
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'session_end_timestamp', 'AttributeType': 'N'},  # Use epoch time
                {'AttributeName': 'channel', 'AttributeType': 'S'}
            ],
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                {'AttributeName': 'session_end_timestamp', 'KeyType': 'RANGE'}
            ],
            BillingMode='PAY_PER_REQUEST',
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'gsi_channel',
                    'KeySchema': [
                        {'AttributeName': 'channel', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ]
        )

        print(f"Creating table '{TABLE_NAME}'...")
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(TableName=TABLE_NAME)
        print(f"Table '{TABLE_NAME}' is now ACTIVE.")

    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"Table '{TABLE_NAME}' already exists.")
        else:
            print(f"Error creating table: {e}")

if __name__ == '__main__':
    create_consolidated_messages_table()
