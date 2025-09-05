#!/usr/bin/env python

# import io
import os
import boto3
import json
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv
from requests import get

script_path = os.path.abspath(__file__)
script_directory = os.path.dirname(script_path)
parent_directory = os.path.dirname(script_directory)
os.chdir(parent_directory)

def get_entries():
    dynamodb = boto3.client("dynamodb")
    table_name = os.getenv("DB_TABLE")
    print(f"Getting entries from {table_name}")
    items = dynamodb.scan(
        TableName=table_name,
        FilterExpression="reg_type = :competitor",
        ExpressionAttributeValues={
            ":competitor": {
                "S": "competitor",
            },
        },
    )["Items"]
    return items


def get_age_group(age):
    age_groups = {
        "4 and under": list(range(0, 4)),
        "4-5": list(range(4, 6)),
        "6-7": list(range(6, 8)),
        "8-9": list(range(8, 10)),
        "10-11": list(range(10, 12)),
        "12-14": list(range(12, 15)),
        "15-16": list(range(15, 17)),
        "17-32": list(range(17, 33)),
        "33 and up": list(range(33, 100)),
    }

    age_group = next((group for group, ages in age_groups.items() if int(age) in ages))

    return age_group


def generate_badge(data):
    """Generate an ID Badge using DB Data"""

    # Opening the template image as the main badge
    badge = Image.new("RGBA", (400, 600), color="white")

    # Add text items
    font_comp = ImageFont.truetype("img/Bonkoff.ttf", size=45)
    font_name = ImageFont.truetype("img/OpenSans-Bold.ttf", size=30)
    font_school = ImageFont.truetype("img/OpenSans-Regular.ttf", size=30)
    font = ImageFont.truetype("img/OpenSans-Regular.ttf", size=20)
    badge_draw = ImageDraw.Draw(badge)

    # Competition Name
    badge_draw.text(
        (200, 20), "OKC TKD", font=font_comp, fill="blue", anchor="mt"
    )
    badge_draw.text(
        (200, 55), "Championship", font=font_comp, fill="blue", anchor="mt"
    )

    # Name
    name_arr = (data["full_name"]["S"]).split()
    capitalized_name_arr = [name.capitalize() for name in name_arr]
    full_name = " ".join(capitalized_name_arr)
    badge_draw.text(
        (200, 100), full_name, font=font_name, fill="black", anchor="mt"
    )
    # School
    badge_draw.text(
        (200, 130), data["school"]["S"], font=font_school, fill="black", anchor="ma"
    )
    # Belt
    if "black" in data["beltRank"]["S"]:
        data["beltRank"]["S"] = "black"
    badge_draw.text(
        (50, 210), f'Belt: {(data["beltRank"]["S"]).capitalize()}', font=font, fill="black"
    )
    # Gender
    badge_draw.text((50, 250), f'Sex: {(data["gender"]["S"]).capitalize()}', font=font, fill="black")
    # Age
    age_group = get_age_group(data["age"]["N"])
    badge_draw.text((235, 210), f'Age: {age_group}', font=font, fill="black")
    # Weight
    badge_draw.text(
        (200, 250), f'Weight: {data["weight"]["N"]} lbs', font=font, fill="black"
    )
    # Divider
    badge_draw.line([(0, 300), (600, 300)], fill="black")
    # Events
    badge_draw.text((200, 330), "Events", font=font, fill="black", anchor="mt")
    events = data["events"]["S"].split(",")
    event_x = 25
    event_y = 350
    for event in events:
        if event == "sparring-gr":
            event = "Grass Roots Sparring"
        elif event == "sparring-wc":
            event = "World Class Sparring"
        elif event == "poomsae":
            event = "Individual Poomsae"
        elif event == "world-class poomsae":
            event = "World Class Poomsae"
        elif event == "little_tiger":
            event = "Little Tiger Showcase"
        else:
            event_name_arr = event.split()
            capitalized_event_name_arr = [name.capitalize() for name in event_name_arr]
            event_name = " ".join(capitalized_event_name_arr)
            event = event_name

        badge_draw.text((event_x, event_y), f"• {event}", font=font, fill="black")
        event_y += 30

    try:
        # Resize and convert to final size/type
        badge = badge.resize((250, 400))
        badge = badge.convert("RGB")
        badge_filename = f"{data['pk']['S']}_badge.jpg".replace(" ", "_")

        # Save the image for email attachment
        badge.save(f"output/{badge_filename}")

        ret_msg = f"Badge '{badge_filename}' generated"

    except Exception as e:
        ret_msg = f"{e = }"


    print(ret_msg)
    return ret_msg


def main():
    load_dotenv()
    entries = get_entries()
    # entries = [
    #     {'poomsae_form': {'S': ''}, 'coach': {'S': 'Master Jung'}, 'pair_poomsae_form': {'S': ''}, 'team_poomsae_form': {'S': ''}, 'full_name': {'S': 'Josiah Salazar'}, 'email': {'S': 'requiredcrio_ministries@hotmail.com'}, 'gender': {'S': 'male'}, 'weight': {'N': '60'}, 'reg_type': {'S': 'competitor'}, 'school': {'S': "Tiger Jung's TKD"}, 'birthdate': {'S': '2016-07-06'}, 'events': {'S': 'breaking,poomsae,world-class poomsae,sparring-wc,little_tiger,family poomsae,team poomsae,sparring-gr'}, 'height': {'N': '48'}, 'payment': {'S': 'pi_3S1E1hGXHNyjORpV1X0hUD3r'}, 'beltRank': {'S': 'yellow'}, 'parent': {'S': 'Rebekah Salazar'}, 'medical_form': {'M': {...}}, 'pk': {'S': "Tiger_Jung's_TKD-competitor-Josiah_Salazar"}, 'phone': {'S': '918-658-5576'}, 'age': {'N': '9'}, 'family_poomsae_form': {'S': ''}}
    # ]

    for entry in entries:
        print(f"Generating badge for {entry['full_name']['S']}")
        generate_badge(entry)


if __name__ == "__main__":
    main()
