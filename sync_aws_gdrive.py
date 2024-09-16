#!/usr/bin/env python

import io
import os
import boto3
import json
from google.oauth2 import service_account
from apiclient import discovery
from apiclient.http import MediaIoBaseUpload # type: ignore

s3 = boto3.client("s3")


def gdrive_auth():
    creds_file = s3.get_object(
        Bucket=os.getenv("CONFIG_BUCKET"),
        Key="tkd-reg_service_account.json",
    )["Body"].read()

    scopes_list = [
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/drive.file",
    ]

    creds_json = json.loads(creds_file)
    credentials = service_account.Credentials.from_service_account_info(
        creds_json, scopes=scopes_list
    )

    service = discovery.build(
        "drive", "v3", credentials=credentials, cache_discovery=False
    )

    return service


def upload_to_gdrive(file_obj, folder_id, file_name, drive_service):
    # media_body = MediaFileUpload(file_obj, mimetype="image/jpeg")
    media_body = MediaIoBaseUpload(
        file_obj, mimetype="image/jpeg", chunksize=1024 * 1024, resumable=True
    )

    body = {
        "name": file_name,
        "title": file_name,
        "description": file_name,
        "mimeType": "image/jpeg",
        "parents": [folder_id],
    }

    # note that supportsAllDrives=True is required or else the file upload will fail
    file = (
        drive_service.files()
        .create(supportsAllDrives=True, body=body, media_body=media_body)
        .execute()
    )

    return file


def check_gdrive_files(drive_service):
    results = (
        drive_service.files()
        .list(
            q="'" + os.getenv("BADGE_GFOLDER") + "' in parents",
            pageSize=1000,
            fields="nextPageToken, files(id, name)",
        )
        .execute()
    )
    items = results.get("files", [])

    return items


def upload_badges(existing_badges, drive_service):
    existing_badge_names = [f["name"] for f in existing_badges]

    bucket = os.environ.get("BADGE_BUCKET")

    s3 = boto3.client("s3")
    badges = s3.list_objects(Bucket=bucket)["Contents"]

    for badge in badges:
        if badge["Key"] in existing_badge_names:
            print(f"Remove existing badge: {badge['Key']}")
            fileId = next(
                item["id"] for item in existing_badges if item["name"] == badge["Key"]
            )

            drive_service.files().delete(fileId=fileId).execute()

        file_name = badge["Key"]
        print(f"Syncing {file_name}")

        file_obj = io.BytesIO()
        s3.download_fileobj(Bucket=bucket, Key=file_name, Fileobj=file_obj)
        file_obj.seek(0)

        # Upload to GDrive
        upload_to_gdrive(
            file_obj,
            os.getenv("BADGE_GFOLDER"),
            file_name,
            drive_service,
        )
        print("  done")


def main():
    drive_service = gdrive_auth()
    existing_badges = check_gdrive_files(drive_service)
    upload_badges(existing_badges, drive_service)


if __name__ == "__main__":
    main()
