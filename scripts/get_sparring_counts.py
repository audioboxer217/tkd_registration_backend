#!/usr/bin/env python

# import io
import os
import boto3
from dotenv import load_dotenv

script_path = os.path.abspath(__file__)
script_directory = os.path.dirname(script_path)
parent_directory = os.path.dirname(script_directory)
os.chdir(parent_directory)

load_dotenv()


def get_entries():
    dynamodb = boto3.client("dynamodb")
    table_name = os.getenv("DB_TABLE")
    print(f"Getting entries from {table_name}")
    items: list[dict] = []
    scan_kwargs = {
        "TableName": table_name,
        "FilterExpression": "reg_type = :competitor",
        "ExpressionAttributeValues": {
            ":competitor": {
                "S": "competitor",
            },
        },
    }
    response = dynamodb.scan(**scan_kwargs)
    items.extend(response.get("Items", []))
    while "LastEvaluatedKey" in response:
        scan_kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]
        response = dynamodb.scan(**scan_kwargs)
        items.extend(response.get("Items", []))
    return items


def get_age_group(entry):
    age_groups = {
        "dragon": [4, 5, 6, 7],
        "tiger": [8, 9],
        "youth": [10, 11],
        "cadet": [12, 13, 14],
        "junior": [15, 16],
        "senior": list(range(17, 33)),
        "ultra": list(range(33, 100)),
    }

    try:
        age = int(entry["age"]["N"])
    except (KeyError, TypeError, ValueError):
        # Invalid or missing age; signal no age group
        return None

    age_group = next(
        (group for group, ages in age_groups.items() if age in ages),
        None,
    )
    return age_group


def divide_age_groups(entries):
    dragon = [entry for entry in entries if get_age_group(entry) == 'dragon']
    tiger = [entry for entry in entries if get_age_group(entry) == 'tiger']
    youth = [entry for entry in entries if get_age_group(entry) == 'youth']
    cadet = [entry for entry in entries if get_age_group(entry) == 'cadet']
    junior = [entry for entry in entries if get_age_group(entry) == 'junior']
    senior = [entry for entry in entries if get_age_group(entry) == 'senior']
    ultra = [entry for entry in entries if get_age_group(entry) == 'ultra']
    
    return {
        'dragon': dragon,
        'tiger': tiger,
        'youth': youth,
        'cadet': cadet,
        'junior': junior,
        'senior': senior,
        'ultra': ultra
    }




def main():
    age_groups = ['dragon', 'tiger', 'youth', 'cadet', 'junior', 'senior', 'ultra']
    entries = get_entries()
    sparring = [entry for entry in entries if 'sparring' in entry['events']['S'].split(',')]
    gr_sparring = [entry for entry in entries if 'sparring-gr' in entry['events']['S'].split(',')]
    wc_sparring = [entry for entry in entries if 'sparring-wc' in entry['events']['S'].split(',')]
    sparring_groups = divide_age_groups(sparring)
    gr_sparring_groups = divide_age_groups(gr_sparring)
    wc_sparring_groups = divide_age_groups(wc_sparring)

    print(f"World Class (Total: {len(wc_sparring)})")
    for ag in age_groups:
        female = [entry for entry in wc_sparring_groups[ag] if entry['gender']['S'] == 'female']
        male = [entry for entry in wc_sparring_groups[ag] if entry['gender']['S'] == 'male']
        print(f"  {ag.capitalize()}")
        print(f"    Female: {len(female)}")
        print(f"      Male: {len(male)}")
        print()

    print(f"Grass Roots (Total: {len(gr_sparring)})")
    for ag in age_groups:
        female = [entry for entry in gr_sparring_groups[ag] if entry['gender']['S'] == 'female']
        male = [entry for entry in gr_sparring_groups[ag] if entry['gender']['S'] == 'male']
        print(f"  {ag.capitalize()}")
        print(f"    Female: {len(female)}")
        print(f"      Male: {len(male)}")
        print()

    print(f"Color Belts (Total: {len(sparring)})")
    for ag in age_groups:
        female = [entry for entry in sparring_groups[ag] if entry['gender']['S'] == 'female']
        male = [entry for entry in sparring_groups[ag] if entry['gender']['S'] == 'male']
        print(f"  {ag.capitalize()}")
        print(f"    Female: {len(female)}")
        print(f"      Male: {len(male)}")
        print()

    print(f"Color Belts + Grass Roots (Total: {len(sparring) + len(gr_sparring)})")
    for ag in age_groups:
        female = [entry for entry in sparring_groups[ag] if entry['gender']['S'] == 'female'] + [entry for entry in gr_sparring_groups[ag] if entry['gender']['S'] == 'female']
        male = [entry for entry in sparring_groups[ag] if entry['gender']['S'] == 'male'] + [entry for entry in gr_sparring_groups[ag] if entry['gender']['S'] == 'male']
        print(f"  {ag.capitalize()}")
        print(f"    Female: {len(female)}")
        print(f"      Male: {len(male)}")
        print()


if __name__ == "__main__":
    main()
