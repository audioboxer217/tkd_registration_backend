import mysql.connector
import json
import os
from glob import glob
from time import sleep


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
        weight decimal(5),
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
    # Write entry to DB
    sql = """
    INSERT INTO competitors (
        first_name,
        last_name,
        email,
        phone,
        address1,
        address2,
        city,
        state,
        zip,
        birthdate,
        age,
        gender,
        weight,
        school,
        coach,
        belt,
        events
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    val = (
        data["fname"],
        data["lname"],
        data["email"],
        data["phone"],
        data["address1"],
        data["address2"],
        data["city"],
        data["state"],
        data["zip"],
        data["birthdate"],
        data["age"],
        data["gender"],
        data["weight"],
        data["school"],
        data["coach"],
        data["beltRank"],
        data["events"],
    )
    db_cursor.execute(sql, val)
    db_obj.commit()
    print(db_cursor.rowcount, "record inserted.")

    return True


if __name__ == "__main__":
    # Ensure 'processed' dir exists
    processed_dir = "/data/processed"
    if not os.path.exists(processed_dir):
        os.makedirs(processed_dir)

    # Connect to DB
    db_obj = connect_db()

    entries = glob("/data/*.json")
    print(f"Processing {len(entries)} entries")

    for json_file in entries:
        # Read JSON
        with open(json_file, "r") as f:
            data = json.load(f)
            write_entry(db_obj, data)
            print(f"{data['fname']} {data['lname']} added")
        os.rename(json_file, f"{processed_dir}/{os.path.basename(json_file)}")

    sleep(600)
