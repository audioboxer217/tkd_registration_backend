import argparse
import json

import boto3


def main():
    parser = argparse.ArgumentParser(
        prog="Load Lookup DB", description="Loads the 'Lookup' DynamoDB table"
    )
    parser.add_argument(
        "-p",
        "--profile",
        metavar="AWS_PROFILE",
        default="personal",
        help="AWS Profile where DynamoDB is located",
    )
    parser.add_argument(
        "-t",
        "--table",
        metavar="TABLE_NAME",
        default="reg_lookup_table",
        help="DynamoDB Table used for Lookups",
    )
    parser.add_argument(
        "input_file",
        metavar="INPUT_FILE",
        help="JSON file generated with `archive_entries.py`",
    )
    args = parser.parse_args()

    session = boto3.Session(profile_name=args.profile)
    dynamodb = session.client("dynamodb")

    with open(args.input_file, "r") as input:
        input_json = json.load(input)

    for name, entry in input_json.items():
        dynamodb.put_item(
            TableName=args.table,
            Item=entry,
        )

        print(f"Entry added for {name}")


if __name__ == "__main__":
    main()
