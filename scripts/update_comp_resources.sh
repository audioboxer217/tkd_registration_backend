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

BASH_SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${BASH_SOURCE_DIR}/.."

# Login to AWS
export AWS_PROFILE=gdtkd
aws sts get-caller-identity --profile "${AWS_PROFILE}" || aws sso login --profile "${AWS_PROFILE}"

uv run "${BASH_SOURCE_DIR}/generate_all_badges.py"
uv run "${BASH_SOURCE_DIR}/generate_poomsae_schedule.py"
uv run "${BASH_SOURCE_DIR}/generate_sparring_schedule.py"
uv run "${BASH_SOURCE_DIR}/generate_breaking_schedule.py"

# Move badges
mv output/badges/*.jpg ~/Google\ Drive/My\ Drive/Personal/TKD/OKGP_Badges/ && echo "Badges moved successfully."
# Move schedules
mv output/schedules/*.csv ~/Google\ Drive/My\ Drive/Personal/TKD/2026_OKGP/ && echo "Schedules moved successfully."
