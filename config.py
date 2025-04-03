import os
import boto3
import json
from dotenv import load_dotenv


def get_secret(secret_name):
    client = boto3.client("secretsmanager")
    response = client.get_secret_value(SecretId=secret_name)
    if "SecretString" in response:
        return json.loads(response["SecretString"])
    else:
        return json.loads(response["SecretBinary"])


# Load environment variables
load_dotenv()

# Fetch secrets from AWS Secrets Manager
secret_json = get_secret(os.getenv("AWS_SECRET_NAME"))
for key, value in secret_json.items():
    os.environ[key] = str(value)

# # Slack configuration
# SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
# SLACK_SIGNING_SECRET = os.getenv('SLACK_SIGNING_SECRET')

# # Ninety.io configuration
# NINETY_EMAIL = os.getenv('NINETY_EMAIL')
# NINETY_PASSWORD = os.getenv('NINETY_PASSWORD')

# Validate required environment variables
required_vars = [
    "SLACK_BOT_TOKEN",
    "SLACK_SIGNING_SECRET",
    "NINETY_EMAIL",
    "NINETY_PASSWORD",
]

missing_vars = [var for var in required_vars if not globals()[var]]
if missing_vars:
    raise ValueError(
        f"Missing required environment variables: {', '.join(missing_vars)}"
    )

# # Set new values for testing
# SLACK_BOT_TOKEN = 'xoxb-your-bot-token'
# SLACK_SIGNING_SECRET = 'your-signing-secret'
# NINETY_EMAIL = 'your-ninety-email'
# NINETY_PASSWORD = 'your-ninety-password'
