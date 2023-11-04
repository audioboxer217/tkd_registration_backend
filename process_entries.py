import os
import io
import ssl
import json
import boto3
import stripe
import smtplib
from glob import glob
from time import sleep
from email.message import EmailMessage
from PIL import Image, ImageDraw, ImageFont

stripe.api_key = os.getenv("STRIPE_API_KEY")
badge_bucket = os.getenv("BADGE_BUCKET")
profile_pic_bucket = os.getenv("PROFILE_PIC_BUCKET")
queue_url = os.getenv("SQS_QUEUE_URL")
table_name = os.getenv("DB_TABLE")
s3 = boto3.client("s3")
sqs = boto3.client("sqs")
dynamodb = boto3.client("dynamodb")


def send_email(data):
    """Send email using DB Entry Data"""

    comp_year = os.environ.get("COMPETITION_YEAR")
    comp_name = os.environ.get("COMPETITION_NAME")
    email_sender = os.environ.get("FROM_EMAIL")
    email_password = os.environ.get("EMAIL_PASSWD")
    contact_email = os.environ.get("CONTACT_EMAIL")
    email_receiver = data["email"]["S"]
    subject = f"{comp_year} {comp_name} Registration"

    body_start = f"""
    Dear {data['full_name']['S']},

    Thank you for being a part of {comp_year} {comp_name}!

    Your registration for the {comp_year} {comp_name} has been accepted.
    """

    body_competitor = f""" 
    Your ID-Card has been attached with this email. Print your ID-Card \
    and bring it to the tournament venue in order to compete.
    """

    body_end = f"""
    If you have any questions please contact us at {contact_email}

    Warm Regards,
    Golden Dragon TKD
    """

    em = EmailMessage()
    em["From"] = email_sender
    em["To"] = email_receiver
    em["Subject"] = subject
    if data["reg_type"]["S"] == "competitor":
        em.set_content(body_start + body_competitor + body_end)
        badge_filename = generate_badge(data)
        with open(os.path.join("/tmp", badge_filename), "rb") as badge:
            em.add_attachment(
                badge.read(),
                maintype="image",
                subtype="jpg",
                filename=badge_filename,
            )
    else:
        em.set_content(body_start + body_end)

    # Add SSL (layer of security)
    context = ssl.create_default_context()

    # Log in and send the email
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
        smtp.login(email_sender, email_password)
        smtp.sendmail(email_sender, email_receiver, em.as_string())
        print("Mail Sent!")


def generate_badge(data):
    """Generate an ID Badge using DB Data"""

    # Opening the template image as the main badge
    badge = Image.open(r"img/id_template.png")
    # Opening and resizing the profile image
    profile_img_string = s3.get_object(
        Bucket=profile_pic_bucket,
        Key=data["imgFilename"]["S"],
    )["Body"].read()
    profile_img = Image.open(io.BytesIO(profile_img_string))
    profile_img = profile_img.resize((590, 585))

    # Place profile image on background
    badge.paste(profile_img, (301, 123))

    # Add text items
    font = ImageFont.truetype("img/OpenSans-Regular.ttf", size=65)
    badge_draw = ImageDraw.Draw(badge)
    # Ring Number
    badge_draw.text((150, 175), "1", font=font, fill="white")
    # ID Number
    badge_draw.text((1000, 175), "3", font=font, fill="white")
    # Gender
    badge_draw.text((190, 960), data["gender"]["S"], font=font, fill="black")
    # Age
    badge_draw.text((190, 1050), data["age"]["N"], font=font, fill="black")
    # Belt
    badge_draw.text((925, 960), data["beltRank"]["S"], font=font, fill="black")
    # Weight
    badge_draw.text((925, 1050), f"{data['weight']['N']} kg", font=font, fill="black")
    # Events
    events = data["events"]["S"].split(",")
    y = 1300
    for event in events:
        badge_draw.text((150, y), f"• {event}", font=font, fill="black")
        y += 100

    try:
        # Save the image for email attachment
        badge = badge.convert("RGB")
        badge_filename = f"{data['pk']['S']}_badge.jpg".replace(" ", "_")
        badge.save(os.path.join("/tmp", badge_filename))

        # Save the image to an in-memory file for S3 Upload
        badge_file = io.BytesIO()
        badge.save(badge_file, format="JPEG")
        badge_file.seek(0)

        # Upload to S3
        s3.upload_fileobj(badge_file, badge_bucket, badge_filename)

    except Exception as e:
        print(f"{e = }")

    return badge_filename


def main(response):
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
            checkout = stripe.checkout.Session.retrieve(data["checkout"]["S"])
            if checkout.status == "open":
                print("Waiting for Stripe Checkout")
                raise ValueError("Checkout Not Complete")
            elif checkout.status == "complete":
                school = data["school"]["S"].replace(" ", "-")
                full_name = data["full_name"]["S"].replace(" ", "-")
                data.update(
                    dict(
                        pk={"S": f"{school}_{data['reg_type']['S']}_{full_name}"},
                    )
                )
                dynamodb.put_item(
                    TableName=table_name,
                    Item=data,
                    ConditionExpression="attribute_not_exists(pk)",
                )
                print(
                    f"Entry added for {data['full_name']['S']} as a {data['reg_type']['S']}"
                )
                send_email(data)
                print(f"  {data['full_name']['S']} Processed Successfully")

        sqs_batch_response["batchItemFailures"] = batch_item_failures
        return sqs_batch_response

    else:
        print("Currently no entries to process. Waiting...")


if __name__ == "__main__":
    main(response)
