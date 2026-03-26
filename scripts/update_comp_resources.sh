#!/usr/bin/env bash
# This script updates the badges and schedules after DB updates have been made.
# It will execute the following scripts via `uv run`:
# - `scripts/generate_all_badges.py`
# - `scripts/generate_poomsae_schedule.py`
# - `scripts/generate_sparring_schedule.py`
# - `scripts/generate_breaking_schedule.py`
#
# It will then move them to:
# - `~/Google Drive/My Drive/Personal/TKD/OKGP_Badges` for the badges
# - `~/Google Drive/My Drive/Personal/TKD/2026_OKGP` for the schedules

set -e

# Login to AWS
aws sts get-caller-identity || aws sso login --profile gdtkd

BASH_SOURCE_DIR="$(dirname "${BASH_SOURCE[0]}")"

uv run ${BASH_SOURCE_DIR}/generate_all_badges.py
uv run ${BASH_SOURCE_DIR}/generate_poomsae_schedule.py
uv run ${BASH_SOURCE_DIR}/generate_sparring_schedule.py
uv run ${BASH_SOURCE_DIR}/generate_breaking_schedule.py

# Move badges
mv output/badges/*.jpg ~/Google\ Drive/My\ Drive/Personal/TKD/OKGP_Badges/ && echo "Badges moved successfully."
# Move schedules
mv output/schedules/*.csv ~/Google\ Drive/My\ Drive/Personal/TKD/2026_OKGP/ && echo "Schedules moved successfully."
