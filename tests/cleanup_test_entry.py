import os
import boto3

dynamodb = boto3.client("dynamodb")

table_name = os.getenv("DB_TABLE")

result = dynamodb.delete_item(
    TableName=table_name,
    Key={
        'pk': {'S': 'Golden_Dragon_TKD_-_Owasso-competitor-Test_User'}
    },
)

if result['ResponseMetadata']['HTTPStatusCode'] == 200:
    print("Test User successfully deleted")
else:
    print(result)
    raise SystemError("Deletion Failed!")