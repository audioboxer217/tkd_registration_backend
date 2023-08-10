import mysql.connector
import json
import os


def connect_db():
    # Connect to DB
    try:
        mydb = mysql.connector.connect(
            host="db",
            user=os.getenv("MYSQL_ROOT_USER"),
            password=os.getenv("MYSQL_ROOT_PASSWORD"),
            database=os.getenv("MYSQL_DB_NAME"),
        )
        return mydb.cursor()
    except:
        cursor = init_db()
        return cursor


def init_db():
    # Connect to MySQL
    mysql_db = mysql.connector.connect(
        host="db",
        user=os.getenv("MYSQL_ROOT_USER"),
        password=os.getenv("MYSQL_ROOT_PASSWORD"),
    )
    dbcursor = mysql_db.cursor()

    # Create DB
    dbcursor.execute(f"CREATE DATABASE {os.getenv('MYSQL_DB_NAME')}")

    # Connect to DB
    mydb = mysql.connector.connect(
        host="db",
        user="root",
        password=os.getenv("MYSQL_ROOT_PASSWORD"),
        database=os.getenv("MYSQL_DB_NAME"),
    )
    print(mydb)
    mycursor = mydb.cursor()
    # Create Tables
    competitors_table = """
    CREATE TABLE competitors (
        fname VARCHAR(255),
        lname VARCHAR(255),
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
        beltRank VARCHAR(255),
        events SET('Sparring', 'Poomsae', 'Team Poomsae', 'Demonstration')
    """

    coaches_table = """
    CREATE TABLE coaches (
        fname VARCHAR(255),
        lname VARCHAR(255),
        email VARCHAR(255),
        phone VARCHAR(255),
        address1 VARCHAR(255),
        address2 VARCHAR(255),
        city VARCHAR(255),
        state CHAR(2),
        zip int(5),
        school VARCHAR(255)
    """
    mycursor.execute(competitors_table)
    mycursor.execute(coaches_table)

    return mycursor


def write_entry(data):
    # Write entry to DB
    sql = "INSERT INTO competitors (first_name,last_name,email,phone,address1,address2,city,state,zip,birthdate,age,gender,weight,school,coach,belt,events) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
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
    mycursor.execute(sql, val)
    mydb.commit()
    print(mycursor.rowcount, "record inserted.")

    return True


if __name__ == "__main__":
    # Read JSON
    with open("/data/test.json", "r") as f:
        data = json.load(f)
        write_entry(data)
