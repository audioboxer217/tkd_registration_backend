# TKD Registration Backend Scripts

This README focuses on how to run and use the helper scripts in `scripts/`.

## Prerequisites

1. Python 3.11+
2. `uv` installed
3. AWS credentials configured locally (profile or environment variables)
4. Environment variables set (via `.env` at repo root, exported vars, or env files)

Install dependencies:

```bash
uv python install
uv sync --all-extras --dev
```

## Running Scripts

Run all scripts from the repository root.

General pattern:

```bash
uv run python scripts/<script_name>.py [options]
```

## Shared Environment Variables

Most scripts use one or more of the following:

- `DB_TABLE`: DynamoDB registrations table name
- `BADGE_IMG_FILENAME`: Source image filename under `img/` (used by `generate_all_badges.py`)
- `BADGE_BUCKET`: S3 bucket containing/generated badges
- `BADGE_GFOLDER`: Google Drive folder ID for badge sync
- `CONFIG_BUCKET`: S3 bucket containing `tkd-reg_service_account.json`

## Script Reference

### `archive_reg_db.py`

Exports competitor registration data from a DynamoDB table to a local JSON file. If the output file already exists, new records are merged into existing content by full name.

Usage:

```bash
uv run python scripts/archive_reg_db.py [--profile AWS_PROFILE] [--output OUTPUT_FILE] TABLE_NAME
```

Examples:

```bash
uv run python scripts/archive_reg_db.py reg_lookup_table
uv run python scripts/archive_reg_db.py --profile personal --output backups/full_lookup.json reg_lookup_table
```

### `load_lookup_db.py`

Loads a previously exported lookup JSON file into a DynamoDB table with `put_item` per entry.

Usage:

```bash
uv run python scripts/load_lookup_db.py [--profile AWS_PROFILE] [--table TABLE_NAME] INPUT_FILE
```

Examples:

```bash
uv run python scripts/load_lookup_db.py backups/full_lookup.json
uv run python scripts/load_lookup_db.py --profile personal --table reg_lookup_table backups/full_lookup.json
```

### `generate_sparring_schedule.py`

Builds sparring groups (2-4 competitors) from DynamoDB competitor entries and writes schedule files.

Inputs:

- Reads competitor data from `DB_TABLE`

Outputs:

- `output/sparring_groups.csv` (default)
- Optional JSON: `output/sparring_groups.json`

Usage:

```bash
uv run python scripts/generate_sparring_schedule.py [--output-format csv|json|both] [--output-dir DIR]
```

Examples:

```bash
uv run python scripts/generate_sparring_schedule.py
uv run python scripts/generate_sparring_schedule.py --output-format both --output-dir output
```

### `generate_poomsae_schedule.py`

Builds grouped poomsae schedule data (individual and world class), prints pair/team/family counts, and writes schedule files.

Inputs:

- Reads competitor data from `DB_TABLE`

Outputs:

- `output/poomsae_schedule_v2.csv` (default)
- Optional JSON: `output/poomsae_schedule_v2.json`

Usage:

```bash
uv run python scripts/generate_poomsae_schedule.py [--output-format csv|json|both] [--output-dir DIR]
```

Examples:

```bash
uv run python scripts/generate_poomsae_schedule.py
uv run python scripts/generate_poomsae_schedule.py --output-format both --output-dir output
```

### `get_sparring_counts.py`

Prints sparring participation totals and age/gender breakdowns for:

- World Class (`sparring-wc`)
- Grass Roots (`sparring-gr`)
- Color Belt (`sparring`)
- Combined Color Belt + Grass Roots

Usage:

```bash
uv run python scripts/get_sparring_counts.py
```

### `get_poomsae_counts.py`

Prints poomsae participation totals and age/gender breakdowns for:

- World Class Poomsae
- Individual Poomsae
- Pair Poomsae
- Team Poomsae

Usage:

```bash
uv run python scripts/get_poomsae_counts.py
```

### `generate_all_badges.py`

Generates all competitor badges from DynamoDB records and saves JPG files locally.

Inputs:

- `DB_TABLE`
- `BADGE_IMG_FILENAME` (used from `img/<BADGE_IMG_FILENAME>`)

Output:

- `output/<pk>_badge.jpg`

Usage:

```bash
uv run python scripts/generate_all_badges.py
```

### `generate_all_badges_okc.py`

Generates all competitor badges using the OKC-specific layout and saves JPG files locally.

Input:

- `DB_TABLE`

Output:

- `output/<pk>_badge.jpg`

Usage:

```bash
uv run python scripts/generate_all_badges_okc.py
```

### `regen_badges.py`

Interactive utility to pick a competitor from DynamoDB, then optionally:

- Regenerate badge
- Resend confirmation email

This script uses functions from `process_entries.py`.

Input:

- `DB_TABLE`

Usage:

```bash
uv run python scripts/regen_badges.py
```

### `sync_aws_gdrive.py`

Syncs badge images from S3 (`BADGE_BUCKET`) into a Google Drive folder (`BADGE_GFOLDER`). If a badge already exists in Drive with the same name, it is deleted first and then re-uploaded.

Inputs:

- `CONFIG_BUCKET` containing `tkd-reg_service_account.json`
- `BADGE_BUCKET`
- `BADGE_GFOLDER`

Usage:

```bash
uv run python scripts/sync_aws_gdrive.py
```

## Troubleshooting

- `botocore.exceptions.NoCredentialsError`:
  - Configure AWS credentials/profile and confirm access to the target table/buckets.
- Missing `DB_TABLE` or other env values:
  - Ensure your `.env` or exported environment variables are loaded.
- Google Drive auth failures in `sync_aws_gdrive.py`:
  - Verify `CONFIG_BUCKET` has `tkd-reg_service_account.json` and that the service account has Drive access.
- Missing image/font files during badge generation:
  - Confirm required files exist under `img/` (for example, fonts and the image named by `BADGE_IMG_FILENAME`).