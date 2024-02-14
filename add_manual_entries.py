#!/usr/bin/env python

import io
import os
import re
import boto3
import json
import gspread
import process_entries as pe

# import googleapiclient.discovery
from dotenv import load_dotenv
from apiclient import discovery
from apiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError
from oauth2client.service_account import ServiceAccountCredentials

load_dotenv("../backend.env")
s3 = boto3.client("s3")


def gdrive_auth():
    creds_file = s3.get_object(
        Bucket=os.getenv("CONFIG_BUCKET"),
        Key="tkd-reg_service_account.json",
    )["Body"].read()

    # Authorize the API
    scope = [
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/drive.file",
    ]
    creds_json = json.loads(creds_file)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)

    service = discovery.build("drive", "v3", credentials=creds, cache_discovery=False)

    client = gspread.authorize(creds)

    return client, service


def send_profile_pic_to_s3(service, file_id, image_name):
    try:
        request = service.files().get_media(fileId=file_id)
        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()

        file.seek(0)
        s3.upload_fileobj(
            file,
            os.getenv("PROFILE_PIC_BUCKET"),
            image_name,
        )

    except HttpError as error:
        print(f"An error occurred: {error}")
        file = None


def main():
    client, service = gdrive_auth()

    # Fetch the sheet
    sheet = client.open("OKGP Input").sheet1
    entries = sheet.get_all_records()
    for row,entry in enumerate(entries):
        row = row + 2
        col = 18
        cell = sheet.cell(row, col)
        if cell.value != 'TRUE':
            imageFileId = re.search(r"\?id=.*", entry["Profile Pic"]).group().strip("?id=")
            imageFile = service.files().get(fileId=imageFileId).execute()
            imageExt = imageFile.get("mimeType").split("/")[-1]
            imgFilename = f"{entry['School'].replace(" ", "-")}_competitor_{entry['Full Name'].replace(" ", "-")}.{imageExt}"
            send_profile_pic_to_s3(service, imageFileId, imgFilename)

            compYear = int(os.getenv("COMPETITION_YEAR"))
            birthYear = int(entry["Birthdate"].split("/")[-1])
            age = str(compYear - birthYear)
            entry_data = dict(
                full_name={"S": f"{entry['Full Name']}"},
                email={"S": f"{entry['Email']}"},
                phone={"S": f"{entry['Phone']}"},
                address1={"S": f"{entry['Address 1']}"},
                address2={"S": f"{entry['Address 2']}"},
                city={"S": f"{entry['City']}"},
                state={"S": f"{entry['State']}"},
                zip={"S": f"{entry['Zip']}"},
                school={"S": f"{entry['School']}"},
                reg_type={"S": "competitor"},
                birthdate={"S": f"{entry['Birthdate']}"},
                age={"N": age},
                gender={"S": f"{entry['Gender']}"},
                weight={"N": f"{entry['Weight (kgs)']}"},
                imgFilename={"S": imgFilename},
                coach={"S": f"{entry['Coach']}"},
                beltRank={"S": f"{entry['Belt']}"},
                events={"S": f"{entry['Events']}"},
            )
            pe.add_entry_to_db(entry_data)
            pe.generate_badge(entry_data)
            pe.send_email(entry_data)
            sheet.update_cell(row, 18,'TRUE')
            print(f"  {entry_data['full_name']['S']} Processed Successfully")
        else:
            print(f"{entry['Full Name']} has already been proceessed.")


if __name__ == "__main__":
    main()
