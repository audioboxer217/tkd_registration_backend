import os
import sys
import json
import boto3


base_path = os.path.dirname(os.path.realpath(__file__))
app_path = os.path.dirname(base_path)
sys.path.append(app_path)
import process_entries

class TestBackend:
    pe = process_entries.main(json.load(open(f'{base_path}/input.json', 'r')))

    def test_process_entry(self):
        assert len(self.pe["batchItemFailures"]) == 0

    def test_cleanup(self):
        dynamodb = boto3.client("dynamodb")
        table_name = os.getenv("DB_TABLE")
        result = dynamodb.delete_item(
            TableName=table_name,
            Key={
                'pk': {'S': 'Golden_Dragon_TKD_-_Owasso-competitor-Test_User'}
            },
        )

        assert result['ResponseMetadata']['HTTPStatusCode'] == 200

if __name__ == "__main__":
    homepage = TestBackend()
    print(homepage.pe)