import os
import ssl
import json
import smtplib
import mysql.connector
from glob import glob
from time import sleep
from email.message import EmailMessage


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
        first_name VARCHAR(255),
        last_name VARCHAR(255),
        email VARCHAR(255),
        phone VARCHAR(255),
        address1 VARCHAR(255),
        address2 VARCHAR(255),
        city VARCHAR(255),
        state CHAR(2),
        zip int(5),
        birthdate CHAR(10),
        age int(2),
        gender VARCHAR(255),
        weight decimal(5,2),
        school VARCHAR(255),
        coach VARCHAR(255),
        belt VARCHAR(255),
        events SET('Sparring', 'Poomsae', 'Team Poomsae', 'Demonstration')
    )
    """

    coaches_table = """
    CREATE TABLE coaches (
        first_name VARCHAR(255),
        last_name VARCHAR(255),
        email VARCHAR(255),
        phone VARCHAR(255),
        address1 VARCHAR(255),
        address2 VARCHAR(255),
        city VARCHAR(255),
        state CHAR(2),
        zip int(5),
        school VARCHAR(255)
    )
    """
    mycursor.execute(competitors_table)
    mycursor.execute(coaches_table)

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
            "coach",
            "belt",
            "events",
        )
        vals += (
            data["birthdate"],
            data["age"],
            data["gender"],
            data["weight"],
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

    return True


def send_email(data):
    comp_year = os.environ.get("COMPETITION_YEAR")
    comp_name = os.environ.get("COMPETITION_NAME")
    email_sender = os.environ.get("FROM_EMAIL").strip("'")
    email_password = os.environ.get("EMAIL_PASSWD").strip("'")
    email_receiver = data["email"]
    subject = f"{comp_year} {comp_name} Registration"

    body = f"""
        Dear {data['fname']} {data['lname']},

        Thank you for being a part of {comp_year} {comp_name}!

        Your registration for the {comp_year} {comp_name} has been accepted.

        Your ID-Card has been attached with this email. Print your ID-Card and bring it to the tournament venue in order to compete.

        If you have any questions please contact us at contacttulsa@goldendragontkd.com

        Warm Regards,
        Golden Dragon TKD
        """

    em = EmailMessage()
    em["From"] = email_sender
    em["To"] = email_receiver
    em["Subject"] = subject
    em.set_content(body)

    # Add SSL (layer of security)
    context = ssl.create_default_context()

    # Log in and send the email
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
        smtp.login(email_sender, email_password)
        smtp.sendmail(email_sender, email_receiver, em.as_string())
        print("Mail Sent!")


if __name__ == "__main__":
    # Ensure 'processed' dir exists
    processed_dir = "/data/processed"
    if not os.path.exists(processed_dir):
        os.makedirs(processed_dir)

    Connect to DB
    db_obj = connect_db()

    entries = glob("/data/*.json")
    if len(entries) > 0:
        print(f"Processing {len(entries)} entries")

        for json_file in entries:
            # Read JSON
            with open(json_file, "r") as f:
                data = json.load(f)
                write_entry(db_obj, data)
                print(f"{data['fname']} {data['lname']} added")
                send_email(data)
            os.rename(json_file, f"{processed_dir}/{os.path.basename(json_file)}")
    else:
        print("Currently no entries to process. Waiting...")

    sleep(60)
