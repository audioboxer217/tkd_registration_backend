#!/usr/bin/env python

import os
import boto3
from dotenv import load_dotenv
import process_entries as pe

load_dotenv("../backend.env")

dynamodb = boto3.client("dynamodb")
table_name = os.getenv("DB_TABLE")

school_dict = {
    "Golden Dragon TKD - Tulsa": [
        "GDTKD",
        "Golden Dragin",
        "Golden Dragon Taekwando",
        "Golden dragon taekwondo",
        "Golden Dragon Taekwondo",
        "Golden Dragon TKD - Tulsa",
        "Golden Dragon TKD Tulsa",
        "Golden dragon tkd",
        "Golden Dragon TKD",
        "Golden Dragon, Tulsa, OK",
        "Golden dragon",
        "Golden Dragon",
        "GoldenDragons",
    ],
    "Golden Dragon TKD - Midtown": [
        "GDKTD MIDTOWN",
        "GDTKD MIDTOWN",
        "GDTKD - MIDTOWN",
        "GDTKD- MIDTOWN",
        "GOLDEN DRAGON - MIDTOWN",
        "Golden Dragon - Midtown",
        "GOLDEN DRAGON TKD -MIDTOWN",
        "Golden Dragon Midtown",
        "Golden Dragon Teakwondo Midtown",
        "Golden Dragon TKD - Midtown",
    ],
    "Golden Dragon TKD - Owasso": [
        "Golden Dragon -Owasso",
        "Golden Dragon Owasso",
        "Golden Dragon Taekwond-Owasso",
        "Golden Dragon TaeKwonDo - Owasso",
        "Golden Dragon Taekwondo Owasso",
        "Golden Dragon taekwondo- Owasso",
        "Golden dragon Taekwondo Owasso",
        "Golden Dragon TKD - Owasso",
        "Golden Dragon TKD Owasso",
        "Golden Dragon TKD OWASSO",
        "Golden Dragon, Owasso",
        "GoldenDragon Owasso",
        "Golden Dragon/ owasso",
        "Golden Dragon Taekwondo - Owasso",
        "Owasso Golden Dragon",
    ],
    "Wolfe Pack": ["Wolfe Pack"],
    "Poos TKD": [
        "Poos Taekwondo",
        "Poos TKD",
    ],
    "Tiger Cho's TKD Center": ["Tiger Cho's TKD Center"],
    "Oklahoma TKD": ["Oklahoma TKD"],
    "Kim's Academy of Tae Kwon Do": ["Kim's Academy of Tae Kwon Do"],
    "MHCK World Class TKD": [
        "Master H C Kim's World Class Tae Kwon Do Center",
        "Master H C Kim’s World Class Taekwondo Center",
        "Master HC Kim World Class Taekwondo Center",
        "Master HC Kim's Taekwondo school",
        "Master HC Kim's taekwondo",
        "Master HC Kim’s World Class Taekwondo Center",
        "Master HC Kim’s World Class TKD",
        "Master HC Kim's",
        "MHCK World Class TKD",
    ],
    "Jeong's TKD Martial Arts": [
        "Jeong Taekwando",
        "Jeong Teakwando",
        "Jeong's Academy",
        "Jeong’s Martial Art’s",
        "Jeong’s Taekwondo Martial Art",
        "Jeong's Taekwondo Martial Arts",
        "Jeong’s taekwondo martial arts",
        "Jeong’s Taekwondo Martial Arts",
        "Jeong's Taekwondo, Overland park, KS",
        "JEONG'S TAEKWONDO, Overland Park, KS",
        "Jeong's Taekwondo",
        "JEONG'S TAEKWONDO",
        "Jeong’s Taekwondo",
        "Jeong's TKD Martial Arts",
        "Jeong's",
        "Jeongs Taekwondo Martial Arts",
        "Jeong Taekwondo Martial Arts",
        "Jeongs Taekwondo Overland Park",
        "Jeongs Taekwondo",
        "Jeong",
        "Jeong Taekwondo",
        "Jeongs Tae Kwon Do",
    ],
    "Lee's US Academy of TKD": ["Lee's US Academy of TKD"],
    "Pruter's TKD Martial Arts Fitness": ["Pruter's TKD Martial Arts Fitness"],
    "Henrich's US TKD": ["Henrich's US TKD"],
    "Pak's Academy of Martial Arts": ["Pak's Academy of Martial Arts"],
    "Martial Arts Advantage": ["Martial Arts Advantage"],
    "S J Lee's White Tiger Martial Arts": ["S J Lee's White Tiger Martial Arts"],
    "White Tiger TKD - Rockwall": [
        "Rockwall white tiger taekwondo",
        "White Tiger Taekwondo - Rockwall",
        "White Tiger - Rockwall",
        "White Tiger Rockwall",
        "White Tiger Rockwell",
        "White Tiger Taekwondo Rockwall",
        "White Tiger Taekwondo School Rockwall TX",
        "White Tiger Taekwondo- Rockwall",
        "White Tiger Taekwondo-Rockwall TX",
        "White Tiger TKD - Rockwall",
    ],
    "Golden Tiger Martial Arts": [
        "Golden Tiger Martial Arts OKC",
        "Golden Tiger Martial Arts",
        "Golden Tiger",
    ],
    "Golden Eagle TKD": ["Golden Eagle TKD"],
    "HK TKD": ["HK TKD"],
    "US White Tiger Martial Arts and TKD": ["US White Tiger Martial Arts and TKD"],
    "White Tiger TKD": [
        "White Tiger Taekwondo",
        "White Tiger TaeKwonDo",
        "White Tiger TKD",
        "White Tiger",
    ],
    "Lee's Martial Arts - Brandon, MS": ["Lee's Martial Arts - Brandon, MS"],
    "Tiger One Martial Arts": ["Tiger One Martial Arts"],
    "Legacy TKD": ["Legacy TKD"],
    "Geomi TKD": ["Geomi TKD"],
    "Marital Arts Advantage": ["Marital Arts Advantage"],
    "The High Performance Institute of TKD": ["The High Performance Institute of TKD"],
    "Stacey's TKD School LLC": ["Stacey's TKD School LLC"],
    "Iron Horse TKD Academny": [
        "Iron Horse Academy",
        "Iron Horse Taekwondo Academy Inc",
        "Iron Horse Taekwondo Academy",
        "Iron Horse TaeKwonDo Academy",
        "Iron Horse Taekwondo",
        "Iron Horse TKD Academny",
    ],
    "Master Yoo's World Champion TKD": ["Master Yoo's World Champion TKD"],
    "Rock Solid Martial Arts Academy": ["Rock Solid Martial Arts Academy"],
    "Tiger Kyong's Top Class TKD": ["Tiger Kyong's Top Class TKD"],
    "Tiger Jung's TKD": [
        "Tiger Jung Taekwondo",
        "Tiger Jung’s Taekwondo",
        "Tiger Jung’s Tae Kwon Do",
        "Tiger Jung's TKD",
        "Tiger Jung's World Class Taekwondo",
        "Tiger Jung’s World Class Taekwondo",
        "Tiger Jung's",
        "Tiger Jung’s",
        "Tiger jung",
        "Tiger Jung",
        "Tiger Jungs Tae Kwon Do",
        "Tiger Jungs",
    ],
    "Master Shin's Academy TKD": ["Master Shin's Academy TKD"],
    "Jido Kwon TKD": [
        "Jido Kwon TKD",
        "JIDO KWAN TAEKWONDO",
        "Jido Kwan Taekwondo",
        "JIDOKWAN   OKLAHOMA",
        "JIDOKWAN  Oklahoma",
        "Jido kwqn Oklahoma",
    ],
    "Gautreaux's Martial Arts Center": ["Gautreaux's Martial Arts Center"],
    "Master Lee's TKD": ["Master Lee's TKD"],
    "Master Hong's Olympic TKD": [
        "Master Hong Olympic taekwondo",
        "Master Hong's Olympic Taekwondo",
        "Master Hong’s Olympic Taekwondo",
        "Master Hong's Olympic TKD",
        "Mster Hong Olympic Taekwondo",
    ],
    "Farfan's TKD": [
        "Farfan taekwondo",
        "Farfan’s Taekwondo Arkansas",
        "Farfan's Taekwondo",
        "Farfan’s Taekwondo",
        "Farfan's TKD",
        "Farfan’s",
        "Farfans Taekwondo",
        "Farfan Taekwondo",
        "Farfans",
    ],
    "Off The Chain": ["Off The Chain"],
    "GrandMaster Sean Kim's TKD": [
        "GM. Sean Kim’s taekwondo",
        "GrandMaster Sean Kim’s TKD",
        "GrandMaster Sean Kim's TKD",
    ],
    "Master Jung’s Taekwondo": ["Master Jung’s Taekwondo"],
    "Young Moo Taekwondo": ["Young Moo Taekwondo"],
    "Geomi": ["Geomi"]
}


def get_entries():
    items = dynamodb.scan(
        TableName=table_name,
        # FilterExpression="reg_type = :competitor",
        # ExpressionAttributeValues={
        #     ":competitor": {
        #         "S": "competitor",
        #     },
        # },
    )["Items"]
    return items


def update_entry(pk,key, value):
    response = dynamodb.update_item(
        TableName=table_name,
        Key={'pk': {'S': pk}},
        UpdateExpression=f"set {key} = :s",
        ExpressionAttributeValues={
            ':s': {"S": value},
        },
        ReturnValues="ALL_NEW"
    )

    return response["Attributes"]

def main():
    new_school_names = set()
    counts = {
        "good": 0,
        "updated": 0,
        "skipped": 0
    }
    entries = get_entries()
    for entry in entries:
        entry_updated = False
        school_name = entry["school"]["S"]
        school_name_clean = school_name.strip()
        school_match = next(
            (k for k,v in school_dict.items() if school_name_clean in v),
            None,
        )
        if school_match == None:
            print(f"Add '{school_name}' to list.")
            new_school_names.add(school_name_clean)
            counts["skipped"] += 1
            continue
        elif school_name != school_match:
            entry_updated = True
            data = update_entry(entry["pk"]["S"],"school",school_match)
            print(f"{entry["full_name"]["S"]}: {school_name} => {school_match}")
            
        clean_name = entry["full_name"]["S"].title()
        if entry["full_name"]["S"] != clean_name:
            entry_updated = True
            data = update_entry(entry["pk"]["S"],"full_name",clean_name)
            print(f"{entry["full_name"]["S"]}: {entry["full_name"]["S"]} => {clean_name}")

        if entry["reg_type"]["S"] == 'competitor':
            clean_events = entry["events"]["S"].replace(", ",",")
            if entry["events"]["S"] != clean_events:
                entry_updated = True
                data = update_entry(entry["pk"]["S"],"events",clean_events)
                print(f"{entry["full_name"]["S"]}: {entry["events"]["S"]} => {clean_events}")
        
        if entry_updated:
            counts["updated"] += 1
            if entry["reg_type"]["S"] == 'competitor':
                print(f"Regenerating with:\n{data}")
                pe.generate_badge(data)
        else:
            counts["good"] += 1
    
    print(f"""
Results:
    Good: {counts['good']}
    Updated: {counts['updated']}
    Skipped: {counts['skipped']}

New School Names to Add:
  {'\n  '.join(sorted(new_school_names))}
          """)


if __name__ == "__main__":
    main()
