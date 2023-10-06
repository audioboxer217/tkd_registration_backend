import os
import io
import ssl
import json
import boto3
import stripe
import smtplib
import mysql.connector
from glob import glob
from time import sleep
from email.message import EmailMessage
from PIL import Image, ImageDraw, ImageFont

stripe.api_key = os.getenv("STRIPE_API_KEY")
badge_bucket = os.getenv("BADGE_BUCKET")
profile_pic_bucket = os.getenv("PROFILE_PIC_BUCKET")
queue_url = os.getenv("SQS_QUEUE_URL")
s3 = boto3.client('s3')
sqs = boto3.client('sqs')

def connect_db():
    db_user = os.getenv("MYSQL_ROOT_USER")
    db_pass = os.getenv("MYSQL_ROOT_PASSWORD")
    db_name = os.getenv("MYSQL_DB_NAME")

    # Connect to DB
    try:
        mydb = mysql.connector.connect(
            host="db",
            user=db_user,
            password=db_pass,
            database=db_name,
        )
        return mydb
    except mysql.connector.Error:
        mydb = init_db(db_name, db_user, db_pass)
        return mydb


def init_db(db_name, db_user, db_pass):
    # Connect to MySQL
    mysql_db = mysql.connector.connect(
        host="db",
        user=db_user,
        password=db_pass,
    )
    dbcursor = mysql_db.cursor()

    # Create DB
    dbcursor.execute(f"CREATE DATABASE {db_name}")

    # Connect to DB
    mydb = mysql.connector.connect(
        host="db",
        user=db_user,
        password=db_pass,
        database=db_name,
    )
    mycursor = mydb.cursor()
    # Create Tables
    competitors_table = """
    CREATE TABLE competitors (
        id int(3) UNIQUE NOT NULL AUTO_INCREMENT,
        first_name VARCHAR(255) NOT NULL,
        last_name VARCHAR(255) NOT NULL,
        email VARCHAR(255) NOT NULL,
        phone VARCHAR(255) NOT NULL,
        address1 VARCHAR(255) NOT NULL,
        address2 VARCHAR(255),
        city VARCHAR(255) NOT NULL,
        state CHAR(2) NOT NULL,
        zip int(5) NOT NULL,
        birthdate CHAR(10) NOT NULL,
        age int(2) NOT NULL,
        gender VARCHAR(255) NOT NULL,
        weight decimal(5,2) NOT NULL,
        profile_img VARCHAR(255) NOT NULL,
        school VARCHAR(255) NOT NULL,
        coach VARCHAR(255) NOT NULL,
        belt VARCHAR(255) NOT NULL,
        events SET(
            'Sparring',
            'Poomsae',
            'Pair Poomsae',
            'Team Poomsae'
            ) NOT NULL,
        PRIMARY KEY (id),
        CONSTRAINT full_name UNIQUE (first_name,last_name)
    )
    """

    coaches_table = """
    CREATE TABLE coaches (
        id int(3) UNIQUE NOT NULL AUTO_INCREMENT,
        first_name VARCHAR(255) NOT NULL,
        last_name VARCHAR(255) NOT NULL,
        email VARCHAR(255) NOT NULL,
        phone VARCHAR(255) NOT NULL,
        address1 VARCHAR(255) NOT NULL,
        address2 VARCHAR(255),
        city VARCHAR(255) NOT NULL,
        state CHAR(2) NOT NULL,
        zip int(5) NOT NULL,
        school VARCHAR(255) NOT NULL,
        PRIMARY KEY (id),
        CONSTRAINT full_name UNIQUE (first_name,last_name)
    )
    """
    mycursor.execute(competitors_table)
    mycursor.execute("ALTER TABLE competitors AUTO_INCREMENT=100")
    mycursor.execute(coaches_table)
    mycursor.execute("ALTER TABLE coaches AUTO_INCREMENT=900")

    return mydb


def write_entry(db_obj, data):
    db_cursor = db_obj.cursor()
    # Generate SQL
    fields = (
        "first_name",
        "last_name",
        "email",
        "phone",
        "address1",
        "address2",
        "city",
        "state",
        "zip",
        "school",
    )
    vals = (
        data["fname"],
        data["lname"],
        data["email"],
        data["phone"],
        data["address1"],
        data["address2"],
        data["city"],
        data["state"],
        data["zip"],
        data["school"],
    )
    if data["reg_type"] == "competitor":
        db_name = "competitors"
        fields += (
            "birthdate",
            "age",
            "gender",
            "weight",
            "profile_img",
            "coach",
            "belt",
            "events",
        )
        vals += (
            data["birthdate"],
            data["age"],
            data["gender"],
            data["weight"],
            data["imgFilename"],
            data["coach"],
            data["beltRank"],
            data["events"],
        )
    else:
        db_name = "coaches"

    # Write entry to DB
    sql = f"""
    INSERT INTO {db_name} ({','.join(fields)})
    VALUES ('{"','".join(vals)}')
    """
    db_cursor.execute(sql)
    db_obj.commit()
    print(db_cursor.rowcount, "record inserted.")

    return db_cursor.lastrowid


def send_email(data):
    """Send email using DB Entry Data"""
    # Get Data from DB
    db_dict = {
        "coach": "coaches",
        "competitor": "competitors",
    }
    # db_cursor = db_obj.cursor()
    # db_cursor.execute(f"SELECT * FROM {db_dict[reg_type]} WHERE id = '{id}'")
    # fields = [i[0] for i in db_cursor.description]
    # row = db_cursor.fetchone()
    # data = dict(zip(tuple(fields), row))

    comp_year = os.environ.get("COMPETITION_YEAR")
    comp_name = os.environ.get("COMPETITION_NAME")
    email_sender = os.environ.get("FROM_EMAIL")
    email_password = os.environ.get("EMAIL_PASSWD")
    contact_email = os.environ.get("CONTACT_EMAIL")
    email_receiver = data["email"]
    subject = f"{comp_year} {comp_name} Registration"

    body_start = f"""
    Dear {data['fname']} {data['lname']},

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
    if data["reg_type"] == "competitor":
        em.set_content(body_start + body_competitor + body_end)
        badge_filename = generate_badge(data)
        with open(os.path.join("/tmp",badge_filename), "rb") as badge:
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
    # Get Data from DB
    # db_cursor = db_obj.cursor()
    # db_cursor.execute(f"SELECT * FROM competitors WHERE id = '{id}'")
    # fields = [i[0] for i in db_cursor.description]
    # row = db_cursor.fetchone()
    # data = dict(zip(tuple(fields), row))

    # Opening the template image as the main badge
    badge = Image.open(r"img/id_template.png")
    # Opening and resizing the profile image
    # profile_img = Image.open(f'/data/profile_pics/{data["profile_img"]}'
    profile_img_string = s3.get_object(
        Bucket=profile_pic_bucket,
        Key=data["imgFilename"],
    )['Body'].read()
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
    badge_draw.text((190, 960), "F", font=font, fill="black")
    # Age
    badge_draw.text((190, 1050), "11", font=font, fill="black")
    # Belt
    badge_draw.text((925, 960), "Black", font=font, fill="black")
    # Weight
    badge_draw.text((925, 1050), "77 kg", font=font, fill="black")
    # Events
    events = data["events"].split(',')
    y = 1300
    for event in events:
        badge_draw.text((150, y), f"• {event}", font=font, fill="black")
        y += 100

    try:
        # Save the image for email attachment
        badge = badge.convert("RGB")
        badge_filename = f"{data['fname']}_{data['lname']}_badge.jpg"
        badge.save(os.path.join("/tmp",badge_filename))

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
        entries = response['Records']
        print(f"Processing {len(entries)} entries")

        # Connect to DB
        # db_obj = connect_db()

        for record in entries:
            try:
                data = json.loads(record['body'])
            except Exception as e:
                batch_item_failures.append({"itemIdentifier": record['messageId']})
            print(f"  Processing {data['fname']} {data['lname']}")
            checkout = stripe.checkout.Session.retrieve(data["checkout"])
            if checkout.status == "open":
                print("Waiting for Stripe Checkout")
                raise ValueError("Checkout Not Complete")
            elif checkout.status == "complete":
                # entry = write_entry(db_obj, data)
                # print(f"Entry #{entry} - {data['fname']} {data['lname']} added")
                send_email(data)

            print(f"  {data['fname']} {data['lname']} Processed Successfully")
        
        sqs_batch_response["batchItemFailures"] = batch_item_failures
        return sqs_batch_response

    else:
        print("Currently no entries to process. Waiting...")

if __name__ == "__main__":
    main(response)