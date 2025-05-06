import boto3
from botocore.exceptions import ClientError

TABLE_NAME = 'UserMessageBufferTable'
GSI_SESSION_ID = 'gsi_session_id'

dynamodb = boto3.client('dynamodb')

def create_user_message_buffer():
    try:
        # Create the table without 'expiration_time' in AttributeDefinitions
        dynamodb.create_table(
            TableName=TABLE_NAME,
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'timestamp', 'AttributeType': 'N'},
                {'AttributeName': 'session_id', 'AttributeType': 'S'}
            ],
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
            ],
            BillingMode='PAY_PER_REQUEST',
            GlobalSecondaryIndexes=[
                {
                    'IndexName': GSI_SESSION_ID,
                    'KeySchema': [
                        {'AttributeName': 'session_id', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ]
        )

        print(f"Creating table '{TABLE_NAME}'...")
        waiter = dynamodb.get_waiter('table_exists')
        waiter.wait(TableName=TABLE_NAME)
        print(f"Table '{TABLE_NAME}' is now ACTIVE.")

        # Enable TTL on 'expiration_time' (can be defined dynamically in items)
        dynamodb.update_time_to_live(
            TableName=TABLE_NAME,
            TimeToLiveSpecification={
                'Enabled': True,
                'AttributeName': 'expiration_time'
            }
        )
        print("TTL enabled on 'expiration_time' attribute.")

    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"Table '{TABLE_NAME}' already exists.")
        else:
            print(f"Error creating table: {e}")

if __name__ == '__main__':
    create_user_message_buffer()
