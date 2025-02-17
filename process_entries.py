import os
import io
import ssl
import json
import boto3
import stripe
import smtplib
from email.message import EmailMessage
from email.utils import formataddr
# from PIL import Image, ImageDraw, ImageFont, ImageOps


def add_entry_to_db(data):
    dynamodb = boto3.client("dynamodb")
    table_name = os.getenv("DB_TABLE")

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
        Type: {data["reg_type"]["S"]}
        Email: {data["email"]["S"]}
        Phone: {data["phone"]["S"]}
        School: {data["school"]["S"]}
    """
    if data["reg_type"]["S"] == "competitor":
        reg_details += f"""    Coach: {data["coach"]["S"]}
        Parent: {data["parent"]["S"]}
        Birthdate: {data["birthdate"]["S"]}
        Gender: {data["gender"]["S"]}
        Weight: {data["weight"]["N"]}
        Belt: {data["beltRank"]["S"]}
        {f"T-Shirt size: {data['tshirt']['S']}" if "tshirt" in data else ''}
        Events:"""

        for e in data["events"]["S"].split(','):
            if e == "little_dragon":
                e = "Little Dragon Obstacle Course"
            if e.startswith('sparring'):
                spar_dict = {
                    'wc': 'world class ',
                    'gr': 'grass roots '
                }
                spar_parts = e.split('-')
                if len(spar_parts) > 1:
                    spar_type = spar_dict[spar_parts[1]]
                else:
                    spar_type = ''
                e = f"{spar_type}sparring"

            if e.endswith('poomsae') and e != "freestyle poomsae":
                form_lookup = f"{e.replace(' ','_')}_form"
                form_name = data[form_lookup]["S"]
                if form_name.isnumeric():
                    form_name = f"Taegeuk {form_name} Jang"
                e += f" (Form: {form_name})"
            reg_details += f"\n          • {e.title()}"

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


# def generate_badge(data):
#     """Generate an ID Badge using DB Data"""

#     # S3 Client
#     s3 = boto3.client("s3")

#     # Opening the template image as the main badge
#     # badge = Image.open(r"img/id_template.png")
#     badge = Image.new("RGBA", (400, 600), color="white")
#     # Opening and resizing the profile image
#     profile_img_string = s3.get_object(
#         Bucket=os.getenv("PROFILE_PIC_BUCKET"),
#         Key=data["imgFilename"]["S"],
#     )["Body"].read()
#     profile_img = Image.open(io.BytesIO(profile_img_string))
#     profile_img = profile_img.resize((250, 250))
#     profile_img = ImageOps.exif_transpose(profile_img)

#     # Place profile image on background
#     badge.paste(profile_img, (75, 20))

#     # Add text items
#     font_name = ImageFont.truetype("img/OpenSans-Regular.ttf", size=30)
#     font = ImageFont.truetype("img/OpenSans-Regular.ttf", size=24)
#     badge_draw = ImageDraw.Draw(badge)
#     # ID Number
#     # badge_draw.text((37.5, 20), "ID", font=font, fill="black", anchor="ma")
#     # badge_draw.text((37.5, 50), "3", font=font, fill="black", anchor="ma")
#     # Ring Number
#     # badge_draw.text((362.5, 20), "Ring", font=font, fill="black", anchor="ma")
#     # badge_draw.text((362.5, 50), "__", font=font, fill="black", anchor="ma")
#     # Name
#     badge_draw.text(
#         (200, 275), data["full_name"]["S"], font=font_name, fill="black", anchor="mt"
#     )
#     # School
#     badge_draw.text(
#         (200, 310), data["school"]["S"], font=font, fill="black", anchor="ma"
#     )
#     # Gender
#     badge_draw.text((50, 350), f'Sex: {data["gender"]["S"]}', font=font, fill="black")
#     # Age
#     badge_draw.text((50, 380), f'Age: {data["age"]["N"]}', font=font, fill="black")
#     # Belt
#     badge_draw.text(
#         (235, 350), f'Belt: {data["beltRank"]["S"]}', font=font, fill="black"
#     )
#     # Weight
#     badge_draw.text(
#         (200, 380), f'Weight: {data["weight"]["N"]} lbs', font=font, fill="black"
#     )
#     # Divider
#     badge_draw.line([(0, 420), (600, 420)], fill="black")
#     # Events
#     badge_draw.text((200, 430), "Events", font=font, fill="black", anchor="mt")
#     events = data["events"]["S"].split(",")
#     left_y = 450
#     left_x = 25
#     right_y = 450
#     right_x = 175
#     for event in events:
#         if event in [
#             "sparring",
#             "sparring-gr",
#             "sparring-wc",
#             "breaking",
#             "poomsae",
#             "little_dragon",
#         ]:
#             x = left_x
#             y = left_y
#             left_y += 30
#         if event in ["pair poomsae", "team poomsae", "family poomsae"]:
#             x = right_x
#             y = right_y
#             right_y += 30

#         badge_draw.text((x, y), f"• {event}", font=font, fill="black")

#     try:
#         # Resize and convert to final size/type
#         badge = badge.resize((250, 400), resample=Image.LANCZOS)
#         badge = badge.convert("RGB")
#         badge_filename = f"{data['pk']['S']}_badge.jpg".replace(" ", "_")

#         # Save the image for email attachment
#         # badge.save(f"/tmp/{badge_filename}")

#         # Save the image to an in-memory file for S3 Upload
#         badge_file = io.BytesIO()
#         badge.save(badge_file, format="JPEG")
#         badge_file.seek(0)

#         # Upload to S3
#         s3.upload_fileobj(badge_file, os.getenv("BADGE_BUCKET"), badge_filename)

#     except Exception as e:
#         ret_msg = f"{e = }"

#     ret_msg = f"Badge '{badge_filename}' generated"

#     print(ret_msg)
#     return ret_msg


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
                if data["reg_type"]["S"] == "competitor" and data["checkout"]["S"] != "manual_entry":
                    data["payment"] = {"S": checkout.payment_intent}
                del data["checkout"]
                add_entry_to_db(data)
                # if data["reg_type"]["S"] == "competitor":
                #     generate_badge(data)
                send_email(data)
                print(f"  {data['full_name']['S']} Processed Successfully")

                check_school(data)

        sqs_batch_response["batchItemFailures"] = batch_item_failures
        return sqs_batch_response

    else:
        print("Currently no entries to process. Waiting...")


if __name__ == "__main__":
    with open('tests/input.json', 'r') as input:
        response = json.load(input)
    main(response)
