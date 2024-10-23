import argparse
import json
import os

import boto3


def convert_json(input_json):
    filter_json = dict()
    for entry in input_json:
        filter_json[entry["full_name"]["S"]] = dict(
            name=entry.get("full_name", dict(S="")),
            email=entry.get("email", dict(S="")),
            pk=entry.get("pk", dict(S="")),
            phone=entry.get("phone", dict(S="")),
            coach=entry.get("coach", dict(S="")),
            gender=entry.get("gender", dict(S="")),
            school=entry.get("school", dict(S="")),
            birthdate=entry.get("birthdate", dict(S="")),
            parent=entry.get("parent", dict(S="")),
        )
    return filter_json


def main():
    parser = argparse.ArgumentParser(
        prog="Archive Registration DB",
        description="Archives the 'Registration' DynamoDB table",
    )
    parser.add_argument(
        "-p",
        "--profile",
        metavar="AWS_PROFILE",
        default="personal",
        help="AWS Profile where DynamoDB is located",
    )
    parser.add_argument(
        "-o",
        "--output",
        metavar="OUTPUT_FILE",
        default="full_lookup.json",
        help="Filename to store output JSON",
    )
    parser.add_argument(
        "table",
        metavar="TABLE_NAME",
        help="DynamoDB Table used for Lookups",
    )
    args = parser.parse_args()

    session = boto3.Session(profile_name=args.profile)
    dynamodb = session.client("dynamodb")

    if os.path.exists(args.output):
        with open(args.output, "r") as existing_file:
            existing_json = json.load(existing_file)
    else:
        existing_json = {}

    output_json = dynamodb.scan(TableName=args.table)["Items"]
    output_json = convert_json(output_json)

    existing_json = {**existing_json, **output_json}

    with open(args.output, "w") as output_file:
        json.dump(existing_json, output_file, indent=4)

    print(f"Export Completed Successfully!\nFile is: {args.output}")


if __name__ == "__main__":
    main()
