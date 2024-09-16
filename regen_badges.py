#!/usr/bin/env python

import os
import boto3
import process_entries as pe

CONFIRM_CHOICES = ["y", "Y", "yes", "Yes"]


def get_entries():
    dynamodb = boto3.client("dynamodb")
    table_name = os.getenv("DB_TABLE")
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


def prompt_user(entry_names):
    print("\nWhich entry do you want to work with?")
    for i, name in enumerate(entry_names):
        print(f"{i+1}. {name}")
    print("q. Quit")
    choice = input("Selection: ")
    return choice


def main():
    entries = get_entries()
    entry_names = [e["full_name"]["S"] for e in entries]
    choice = prompt_user(entry_names)

    while choice != "q":
        pk = int(choice) - 1
        if pk not in range(0, len(entries)):
            raise ("Please choose from the list of choices!")

        data = next(
            (item for item in entries if item["full_name"]["S"] == entry_names[pk]),
            None,
        )

        regenerate_badge = input(
            f"Do you want to regenerate a badge for {entry_names[pk]}? "
        )
        if regenerate_badge in CONFIRM_CHOICES:
            print(f"Regenerating with:\n{data}")
            pe.generate_badge(data)

        resend_email = input(f"Do you want to resend an email to {entry_names[pk]}? ")
        if resend_email in CONFIRM_CHOICES:
            print(f"Resending email to:\n{data['email']['S']}")
            pe.send_email(data)

        choice = prompt_user(entry_names)


if __name__ == "__main__":
    main()
