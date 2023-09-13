import os
import ssl
import json
import stripe
import smtplib
import mysql.connector
from glob import glob
from time import sleep
from email.message import EmailMessage
from PIL import Image, ImageDraw, ImageFont

stripe.api_key = os.getenv("STRIPE_API_KEY")


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
            'Team Poomsae',
            'Demonstration'
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


def send_email(db_obj, id):
    """Send email using DB Entry Data"""
    # Get Data from DB
    db_cursor = db_obj.cursor()
    db_cursor.execute(f"SELECT * FROM competitors WHERE id = '{id}'")
    fields = [i[0] for i in db_cursor.description]
    row = db_cursor.fetchone()
    data = dict(zip(tuple(fields), row))
    badge_filename = f"{data['first_name']}_{data['last_name']}_badge.jpg"

    comp_year = os.environ.get("COMPETITION_YEAR")
    comp_name = os.environ.get("COMPETITION_NAME")
    email_sender = os.environ.get("FROM_EMAIL")
    email_password = os.environ.get("EMAIL_PASSWD")
    contact_email = os.environ.get("CONTACT_EMAIL")
    email_receiver = data["email"]
    subject = f"{comp_year} {comp_name} Registration"

    body = f"""
    Dear {data['first_name']} {data['last_name']},

    Thank you for being a part of {comp_year} {comp_name}!

    Your registration for the {comp_year} {comp_name} has been accepted.

    Your ID-Card has been attached with this email. Print your ID-Card \
    and bring it to the tournament venue in order to compete.

    If you have any questions please contact us at {contact_email}

    Warm Regards,
    Golden Dragon TKD
    """

    em = EmailMessage()
    em["From"] = email_sender
    em["To"] = email_receiver
    em["Subject"] = subject
    em.set_content(body)
    with open(f"/data/badges/{badge_filename}", "rb") as badge:
        em.add_attachment(
            badge.read(),
            maintype="image",
            subtype="jpg",
            filename=badge_filename,
        )

    # Add SSL (layer of security)
    context = ssl.create_default_context()

    # Log in and send the email
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
        smtp.login(email_sender, email_password)
        smtp.sendmail(email_sender, email_receiver, em.as_string())
        print("Mail Sent!")


def generate_badge(db_obj, id):
    """Generate an ID Badge using DB Data"""
    # Get Data from DB
    db_cursor = db_obj.cursor()
    db_cursor.execute(f"SELECT * FROM competitors WHERE id = '{id}'")
    fields = [i[0] for i in db_cursor.description]
    row = db_cursor.fetchone()
    data = dict(zip(tuple(fields), row))

    # Opening the template image as the main badge
    badge = Image.open(r"img/id_template.png")

    # Opening and resizing the profile image
    profile_img = Image.open(f'/data/profile_pics/{data["profile_img"]}')
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
    events = data["events"]
    y = 1300
    for event in events:
        badge_draw.text((150, y), f"• {event}", font=font, fill="black")
        y += 100

    # Save the image
    badge = badge.convert("RGB")
    badge_filename = f"{data['first_name']}_{data['last_name']}_badge.jpg"
    badge.save(os.path.join("/data/badges", badge_filename))


if __name__ == "__main__":
    # Ensure 'processed' dir exists
    processed_dir = "/data/processed"
    if not os.path.exists(processed_dir):
        os.makedirs(processed_dir)

    # Ensure 'failed' dir exists
    failed_dir = "/data/failed"
    if not os.path.exists(failed_dir):
        os.makedirs(failed_dir)

    # Ensure 'badges' dir exists
    badges_dir = "/data/badges"
    if not os.path.exists(badges_dir):
        os.makedirs(badges_dir)

    # Connect to DB
    db_obj = connect_db()

    entries = glob("/data/*.json")
    if len(entries) > 0:
        print(f"Processing {len(entries)} entries")

        for json_file in entries:
            # Read JSON
            with open(json_file, "r") as f:
                data = json.load(f)

            checkout = stripe.checkout.Session.retrieve(data["checkout"])
            if checkout.status == "open":
                print("Waiting for Stripe Checkout")
            elif checkout.status == "complete":
                entry = write_entry(db_obj, data)
                print(f"Entry #{entry} - {data['fname']} {data['lname']} added")
                generate_badge(db_obj, entry)
                send_email(db_obj, entry)
                new_path = f"{processed_dir}/{os.path.basename(json_file)}"
                os.rename(json_file, new_path)
            else:
                print(f"Error processing {data['fname']} {data['lname']}")
                new_path = f"{failed_dir}/{os.path.basename(json_file)}"
                os.rename(json_file, new_path)
    else:
        print("Currently no entries to process. Waiting...")

    sleep(60)
