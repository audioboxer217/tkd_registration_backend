#!/usr/bin/env python

# import io
import os
import boto3
from PIL import Image, ImageDraw, ImageFont, ImageOps
from dotenv import load_dotenv

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


def generate_badge(data):
    """Generate an ID Badge using DB Data"""

    # S3 Client
    # s3 = boto3.client("s3")

    # Opening the template image as the main badge
    # badge = Image.open(r"img/id_template.png")
    badge = Image.new("RGBA", (400, 600), color="white")
    # Opening and resizing the profile image
    profile_img = Image.open(f"img/{os.getenv('BADGE_IMG_FILENAME')}")
    profile_img = profile_img.resize((400, 250))
    profile_img = ImageOps.exif_transpose(profile_img)

    # Place profile image on background
    badge.paste(profile_img, (10, 20))

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
    badge_draw.text(
        (200, 275), data["full_name"]["S"], font=font_name, fill="black", anchor="mt"
    )
    # School
    badge_draw.text(
        (200, 310), data["school"]["S"], font=font, fill="black", anchor="ma"
    )
    # Gender
    badge_draw.text((50, 350), f'Sex: {data["gender"]["S"]}', font=font, fill="black")
    # Age
    badge_draw.text((50, 380), f'Age: {data["age"]["N"]}', font=font, fill="black")
    # Belt
    if "black" in data["beltRank"]["S"]:
        data["beltRank"]["S"] = "black"
    badge_draw.text(
        (235, 350), f'Belt: {data["beltRank"]["S"]}', font=font, fill="black"
    )
    # Weight
    badge_draw.text(
        (200, 380), f'Weight: {data["weight"]["N"]} lbs', font=font, fill="black"
    )
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
        if event in [
            "sparring",
            "sparring-gr",
            "sparring-wc",
            "breaking",
            "poomsae",
            "freestyle poomsae",
            "little_dragon",
            "little_tiger",
        ]:
            x = left_x
            y = left_y
            left_y += 30
        if event in ["world-class poomsae", "pair poomsae", "team poomsae", "family poomsae"]:
            x = right_x
            y = right_y
            right_y += 30

        badge_draw.text((x, y), f"• {event}", font=font, fill="black")

    try:
        # Resize and convert to final size/type
        badge = badge.resize((250, 400), resample=Image.Resampling.LANCZOS)
        badge = badge.convert("RGB")
        badge_filename = f"{data['pk']['S']}_badge.jpg".replace(" ", "_")

        # Save the image for email attachment
        badge.save(f"output/{badge_filename}")

        # Save the image to an in-memory file for S3 Upload
        # badge_file = io.BytesIO()
        # badge.save(badge_file, format="JPEG")
        # badge_file.seek(0)

        # Upload to S3
        # s3.upload_fileobj(badge_file, os.getenv("BADGE_BUCKET"), badge_filename)

        ret_msg = f"Badge '{badge_filename}' generated"

    except Exception as e:
        ret_msg = f"{e = }"


    print(ret_msg)
    return ret_msg


def main():
    load_dotenv()
    entries = get_entries()

    for entry in entries:
        print(f"Generating badge for {entry['full_name']['S']}")
        generate_badge(entry)


if __name__ == "__main__":
    main()
