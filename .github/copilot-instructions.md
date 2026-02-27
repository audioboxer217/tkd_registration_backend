# Copilot Instructions for tkd_registration_backend

## Project Overview
This is the backend for the TKD (Taekwondo) Registration Project. It processes competition registrations submitted via a frontend Flask app, verifies Stripe payments, stores entries in DynamoDB, and sends confirmation emails.

## Architecture
- **process_entries.py** – Main Lambda handler: reads SQS records, verifies Stripe checkout sessions, writes to DynamoDB, and sends confirmation emails.
- **scripts/** – Utility scripts for badge generation, database archiving, schedule generation, and syncing badges to Google Drive.
- **tests/** – pytest-based test suite.
- **envs/** – Zappa deployment configuration YAML files per environment.

## Tech Stack
- **Language**: Python ≥ 3.11
- **Package manager**: [uv](https://github.com/astral-sh/uv)
- **Linter/formatter**: [ruff](https://docs.astral.sh/ruff/) (config in `ruff.toml`)
- **Testing**: pytest
- **Deployment**: [Zappa](https://github.com/Zappa/Zappa) (AWS Lambda)
- **AWS services**: DynamoDB, S3, SQS
- **External APIs**: Stripe, Google Drive, Challonge

## Common Commands
```bash
# Install dependencies (first-time setup)
just bootstrap

# Run linter
uv run ruff check .

# Run tests
uv run pytest -qrA --tb=short

# Deploy to an environment
just deploy <acct> <env>

# Update an existing deployment
just update <acct> <env>
```

## Environment Variables
The following environment variables are required at runtime (set in CI via GitHub Actions secrets/vars or locally via a `.env` file):

| Variable | Description |
|---|---|
| `ADMIN_EMAIL` | Email for admin alerts (e.g. unknown school) |
| `AWS_DEFAULT_REGION` | AWS region |
| `AWS_PROFILE` | AWS CLI profile name |
| `BADGE_BUCKET` | S3 bucket for badge files |
| `BADGE_GFOLDER` | Google Drive folder for badge sync |
| `COMPETITION_NAME` | Name of the competition |
| `COMPETITION_YEAR` | Year of the competition |
| `CONFIG_BUCKET` | S3 bucket for config files (e.g. `schools.json`) |
| `CONTACT_EMAIL` | Public contact email |
| `DB_TABLE` | DynamoDB table name |
| `EMAIL_PASSWD` | SMTP password |
| `EMAIL_PORT` | SMTP port |
| `EMAIL_SERVER` | SMTP server hostname |
| `FROM_EMAIL` | Sender email address |
| `PROFILE_PIC_BUCKET` | S3 bucket for profile pictures |
| `SQS_QUEUE_URL` | SQS queue URL for processing |
| `STRIPE_API_KEY` | Stripe API key |
| `STRIPE_TEST_SESSION` | Stripe session ID used in tests |

## Code Style
- Line length: 130 (see `ruff.toml`)
- Ruff rule sets: `E`, `F` (ignoring `E402`)
- Follow existing patterns: use `os.getenv` / `os.environ.get` for environment variables, boto3 clients created inside functions.

## Testing
- Tests live in `tests/test_backend_scripts.py`.
- Test input data is in `tests/input.json`.
- Tests require real AWS credentials (OIDC role assumed in CI).
- Run with: `uv run pytest -qrA --tb=short`

## CI/CD
- GitHub Actions workflow: `.github/workflows/main.yml`
- Runs on push to `main` and all pull requests.
- Uses OIDC to authenticate with AWS (no long-lived credentials).
- Also runs a [Safety](https://pypi.org/project/safety/) vulnerability scan.
