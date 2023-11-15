import os
import io
import ssl
import json
import boto3
import stripe
import smtplib
from email.message import EmailMessage
from PIL import Image, ImageDraw, ImageFont


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
    with smtplib.SMTP_SSL(email_server, email_port, context=context) as smtp:
        smtp.login(email_sender, email_password)
        smtp.sendmail(email_sender, email_receiver, em.as_string())
        print("Mail Sent!")


def generate_badge(data):
    """Generate an ID Badge using DB Data"""

    # S3 Client
    s3 = boto3.client("s3")

    # Opening the template image as the main badge
    # badge = Image.open(r"img/id_template.png")
    badge = Image.new('RGBA', (400, 600), color='white')
    # Opening and resizing the profile image
    profile_img_string = s3.get_object(
        Bucket=os.getenv("PROFILE_PIC_BUCKET"),
        Key=data["imgFilename"]["S"],
    )["Body"].read()
    profile_img = Image.open(io.BytesIO(profile_img_string))
    profile_img = profile_img.resize((250, 250))

    # Place profile image on background
    badge.paste(profile_img, (75, 20))

    # Add text items
    font_name = ImageFont.truetype("img/OpenSans-Regular.ttf", size=30)
    font = ImageFont.truetype("img/OpenSans-Regular.ttf", size=24)
    badge_draw = ImageDraw.Draw(badge)
    # ID Number
    # badge_draw.text((37.5, 20), "ID", font=font, fill="black", anchor="ma")
    # badge_draw.text((37.5, 50), "3", font=font, fill="black", anchor="ma")
    # Ring Number
    # badge_draw.text((362.5, 20), "Ring", font=font, fill="black", anchor="ma")
    # badge_draw.text((362.5, 50), "__", font=font, fill="black", anchor="ma")
    # Name
    badge_draw.text((200, 275), data["full_name"]["S"], font=font_name, fill="black", anchor="mt")
    # School
    badge_draw.text((200, 310), data["school"]["S"], font=font, fill="black", anchor="ma")
    # Gender
    badge_draw.text((50, 350), f'Sex: {data["gender"]["S"]}', font=font, fill="black")
    # Age
    badge_draw.text((50, 380), f'Age: {data["age"]["N"]}', font=font, fill="black")
    # Belt
    badge_draw.text((235, 350), f'Belt: {data["beltRank"]["S"]}', font=font, fill="black")
    # Weight
    badge_draw.text((200, 380), f'Weight: {data["weight"]["N"]} kg', font=font, fill="black")
    # Divider
    badge_draw.line([(0, 420), (600, 420)], fill="black")
    # Events
    badge_draw.text((200, 430), "Events", font=font, fill="black", anchor="mt")
    events = data["events"]["S"].split(",")
    left_y = 450
    left_x = 25
    right_y = 450
    right_x = 175
    for event in events:
        if event in ['sparring','breaking','poomsae']:
            x = left_x
            y = left_y
            left_y += 30
        if event in ['pair poomsae','team poomsae','family poomsae']:
            x = right_x
            y = right_y
            right_y += 30
          
        badge_draw.text((x, y), f"• {event}", font=font, fill="black")

    try:
        # Save the image for email attachment
        badge = badge.resize((250,400), resample=Image.LANCZOS)
        badge = badge.convert("RGB")
        badge_filename = f"{data['pk']['S']}_badge.jpg".replace(" ", "_")
        badge.save(f"/tmp/{badge_filename}")

        # Save the image to an in-memory file for S3 Upload
        badge_file = io.BytesIO()
        badge.save(badge_file, format="JPEG")
        badge_file.seek(0)

        # Upload to S3
        s3.upload_fileobj(badge_file, os.getenv("BADGE_BUCKET"), badge_filename)

    except Exception as e:
        print(f"{e = }")

    return badge_filename


def main(response):
    sqs = boto3.client("sqs")
    dynamodb = boto3.client("dynamodb")

    stripe.api_key = os.getenv("STRIPE_API_KEY")
    queue_url = os.getenv("SQS_QUEUE_URL")
    table_name = os.getenv("DB_TABLE")

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
                school = data["school"]["S"].replace(" ", "_")
                full_name = data["full_name"]["S"].replace(" ", "_")
                data.update(
                    dict(
                        pk={"S": f"{school}-{data['reg_type']['S']}-{full_name}"},
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
