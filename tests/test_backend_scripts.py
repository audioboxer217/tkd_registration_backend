import os
import sys
import json
import boto3
import stripe

base_path = os.path.dirname(os.path.realpath(__file__))
app_path = os.path.dirname(base_path)
sys.path.append(app_path)
import process_entries as pe

class TestBackend:
    record = json.load(open(f'{base_path}/input.json', 'r'))["Records"][0]
    data = json.loads(record["body"])
    # pe = process_entries.main(json.load(open(f'{base_path}/input.json', 'r')))

    def test_db_entry(self):
        assert pe.add_entry_to_db(self.data) == f"Entry added for {self.data['full_name']['S']} as a {self.data['reg_type']['S']}"

    def test_badge_gen(self):
        badge_filename = f"{self.data['pk']['S']}_badge.jpg".replace(" ", "_")
        assert pe.generate_badge(self.data) == f"Badge '{badge_filename}' generated"

    def test_email(self):
        assert pe.send_email(self.data) == "Mail Sent!"

    def test_school_check(self):
        assert pe.check_school(self.data) == "School Found!"

        self.data["school"]["S"] = "Nonexistant School"
        assert pe.check_school(self.data) == "Unknown School - Mail Sent!"

    def test_stripe(self):
        stripe.api_key = os.getenv("STRIPE_API_KEY")
        checkout = stripe.checkout.Session.retrieve(os.getenv("STRIPE_TEST_SESSION"))
        assert checkout.status == "complete"

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
    backend = TestBackend()
    print(backend.data)