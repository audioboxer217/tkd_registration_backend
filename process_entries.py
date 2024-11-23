import os
import re
import ssl
import json
import boto3
import stripe
import smtplib
from email.message import EmailMessage
from email.utils import formataddr

def add_entry_to_db(data):
    dynamodb = boto3.client("dynamodb")
    table_name = os.getenv("DB_TABLE")

    if "school" in data:
        school = f'{data["school"]["S"].replace(" ", "_")}'
        pk = f"{school}{data['reg_type']['S']}-{data['full_name']['S'].replace(' ', '_')}"
    else:
        pk = f'{data["reg_type"]["S"]}-{data["full_name"]["S"].replace(" ", "_")}'
    data.update(
        dict(
            pk={"S": pk},
        )
    )
    dynamodb.put_item(
        TableName=table_name,
        Item=data,
        ConditionExpression="attribute_not_exists(pk)",
    )

    ret_msg = f"Entry added for {data['full_name']['S']} as a {data['reg_type']['S']}"
    
    print(ret_msg)
    return ret_msg


def send_email(data):
    """Send email using DB Entry Data"""

    comp_year = os.environ.get("COMPETITION_YEAR")
    comp_name = os.environ.get("COMPETITION_NAME")
    email_server = os.environ.get("EMAIL_SERVER")
    email_port = os.environ.get("EMAIL_PORT")
    email_sender = os.environ.get("FROM_EMAIL")
    email_password = os.environ.get("EMAIL_PASSWD")
    contact_email = os.environ.get("CONTACT_EMAIL")
    email_receiver = data["email"]["S"]
    subject = f"{comp_year} {comp_name} Registration"

    reg_details = f"""
        Name: {data["full_name"]["S"]}
        Item: {data["reg_type"]["S"]}
        Email: {data["email"]["S"]}
        Phone: {data["phone"]["S"]}
    """
    if data["reg_type"]["S"] == "seminar":
        reg_details += f"""    
        School: {data["school"]["S"]}
        Parent: {data["parent"]["S"]}
        Birthdate: {data["birthdate"]["S"]}
        Gender: {data["gender"]["S"]}
        Belt: {data["beltRank"]["S"]}"""

    body = f"""
    Dear {data['full_name']['S']},

    Thank you for being a part of the {comp_year} {comp_name}!

    Your registration has been accepted with the following details.
    {reg_details}

    If you have any questions please contact us at {contact_email}

    Warm Regards,
    {comp_name}
    """

    em = EmailMessage()
    em["From"] = formataddr((comp_name, email_sender))
    em["To"] = formataddr((data["full_name"]["S"], email_receiver))
    em["Subject"] = subject
    em.set_content(body)

    # Add SSL (layer of security)
    context = ssl.create_default_context()

    # Log in and send the email
    with smtplib.SMTP_SSL(email_server, email_port, context=context) as smtp:
        smtp.login(email_sender, email_password)
        smtp.sendmail(email_sender, email_receiver, em.as_string())
    
    ret_msg = "Mail Sent!"

    print(ret_msg)
    return ret_msg


def check_school(data):
    # S3 Client
    s3 = boto3.client("s3")
    school_list = json.load(
        s3.get_object(Bucket=os.environ.get("CONFIG_BUCKET"), Key="schools.json")["Body"]
    )
    if data["school"]["S"] not in school_list:
        comp_name = os.environ.get("COMPETITION_NAME")
        email_server = os.environ.get("EMAIL_SERVER")
        email_port = os.environ.get("EMAIL_PORT")
        email_sender = os.environ.get("FROM_EMAIL")
        email_password = os.environ.get("EMAIL_PASSWD")
        admin_email = os.environ.get("ADMIN_EMAIL")

        em = EmailMessage()
        em["From"] = formataddr((comp_name, email_sender))
        em["To"] = formataddr(("Competition Admin", admin_email))
        em["Subject"] = f"Entry added with unknown school - {data['school']['S']}"
        em.set_content(f"Entry Details:\n{data}")

        # Add SSL (layer of security)
        context = ssl.create_default_context()

        # Log in and send the email
        with smtplib.SMTP_SSL(email_server, email_port, context=context) as smtp:
            smtp.login(email_sender, email_password)
            smtp.sendmail(email_sender, admin_email, em.as_string())

        ret_msg = "Unknown School - Mail Sent!"
    else:
        ret_msg = "School Found!"

    print(ret_msg)
    return ret_msg


def main(response):
    stripe.api_key = os.getenv("STRIPE_API_KEY")

    if response:
        batch_item_failures = []
        sqs_batch_response = {}
        entries = response["Records"]
        print(f"Processing {len(entries)} entries")

        for record in entries:
            try:
                data = json.loads(record["body"])
            except Exception:
                batch_item_failures.append({"itemIdentifier": record["messageId"]})
            print(f"  Processing {data['full_name']['S']}")
            if data["checkout"]["S"] == "manual_entry":
                checkout_status = 'complete'
                data["payment"] = {"S": "manual_entry"}
            else:
                checkout = stripe.checkout.Session.retrieve(data["checkout"]["S"])
                checkout_status = checkout.status
            if checkout_status == "open":
                print("Waiting for Stripe Checkout")
                raise ValueError("Checkout Not Complete")
            elif checkout_status == "complete":
                if data["checkout"]["S"] != "manual_entry":
                    data["payment"] = {"S": checkout.payment_intent}
                del data["checkout"]
                add_entry_to_db(data)
                send_email(data)
                print(f"  {data['full_name']['S']} Processed Successfully")

            if data["reg_type"]["S"] == "seminar":
                check_school(data)

        sqs_batch_response["batchItemFailures"] = batch_item_failures
        return sqs_batch_response

    else:
        print("Currently no entries to process. Waiting...")


if __name__ == "__main__":
    with open('tests/input.json', 'r') as input:
        response = json.load(input)
    main(response)
