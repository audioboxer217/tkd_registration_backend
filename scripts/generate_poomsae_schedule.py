#!/usr/bin/env python

# import io
import os
import boto3
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

    age_group = next((group for group, ages in age_groups.items() if int(entry["age"]["N"]) in ages))

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
    load_dotenv()
    age_groups = ['dragon', 'tiger', 'youth', 'cadet', 'junior', 'senior', 'ultra']
    entries = get_entries()
    poomsae = [entry for entry in entries if 'poomsae' in entry['events']['S'].split(',')]
    world_class_poomsae = [entry for entry in entries if 'world-class poomsae' in entry['events']['S'].split(',')]
    pair_poomsae = [entry for entry in entries if 'pair poomsae' in entry['events']['S'].split(',')]
    poomsae_groups = divide_age_groups(poomsae)
    world_class_poomsae_groups = divide_age_groups(world_class_poomsae)
    pair_poomsae_groups = divide_age_groups(pair_poomsae)

    print(f"World Class (Total: {len(world_class_poomsae)})")
    for ag in age_groups:
        female = [entry for entry in world_class_poomsae_groups[ag] if entry['gender']['S'] == 'female']
        male = [entry for entry in world_class_poomsae_groups[ag] if entry['gender']['S'] == 'male']
        print(f"  {ag.capitalize()}")
        print(f"    Female: {len(female)}")
        print(f"      Male: {len(male)}")
        print()

    print(f"Individual Poomsae (Total: {len(poomsae)})")
    for ag in age_groups:
        female = [entry for entry in poomsae_groups[ag] if entry['gender']['S'] == 'female']
        male = [entry for entry in poomsae_groups[ag] if entry['gender']['S'] == 'male']
        print(f"  {ag.capitalize()}")
        print(f"    Female: {len(female)}")
        print(f"      Male: {len(male)}")
        print()

    print(f"Pair Poomsae (Total: {len(pair_poomsae)})")
    for ag in age_groups:
        female = [entry for entry in pair_poomsae_groups[ag] if entry['gender']['S'] == 'female']
        male = [entry for entry in pair_poomsae_groups[ag] if entry['gender']['S'] == 'male']
        print(f"  {ag.capitalize()}")
        print(f"    Female: {len(female)}")
        print(f"      Male: {len(male)}")
        print()

    print(f"Team Poomsae (Total: {len(team_poomsae)})")
    for ag in age_groups:
        female = [entry for entry in team_poomsae_groups[ag] if entry['gender']['S'] == 'female']
        male = [entry for entry in team_poomsae_groups[ag] if entry['gender']['S'] == 'male']
        print(f"  {ag.capitalize()}")
        print(f"    Female: {len(female)}")
        print(f"      Male: {len(male)}")
        print()


if __name__ == "__main__":
    main()
