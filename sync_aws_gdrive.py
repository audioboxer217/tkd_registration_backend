import io
import os
import boto3
from dotenv import load_dotenv
import process_entries as pe

load_dotenv("../backend.env")
drive = pe.gdrive_auth()


def check_gdrive_files():
    results = (
        drive.files()
        .list(
            q="'" + os.getenv("BADGE_GFOLDER") + "' in parents",
            pageSize=10,
            fields="nextPageToken, files(id, name)",
        )
        .execute()
    )
    items = results.get("files", [])

    return items


def upload_badges(existing_badges):
    existing_badge_names = [f["name"] for f in existing_badges]

    bucket = os.environ.get("BADGE_BUCKET")

    s3 = boto3.client("s3")
    badges = s3.list_objects(Bucket=bucket)["Contents"]

    for badge in badges:
        if badge["Key"] in existing_badge_names:
            print(f"{badge['Key']} Already Exists")
            fileId = next(
                item["id"] for item in existing_badges if item["name"] == badge["Key"]
            )

            drive.files().delete(fileId=fileId).execute()

        file_name = badge["Key"]
        print(f"Syncing {file_name}")

        file_obj = io.BytesIO()
        s3.download_fileobj(Bucket=bucket, Key=file_name, Fileobj=file_obj)
        file_obj.seek(0)

        # Upload to GDrive
        pe.upload_to_gdrive(
            file_obj,
            os.getenv("BADGE_GFOLDER"),
            file_name,
            drive,
        )
        print("  done")


def main():
    existing_badges = check_gdrive_files()
    upload_badges(existing_badges)


if __name__ == "__main__":
    main()
