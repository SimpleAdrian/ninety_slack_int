import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Slack configuration
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
SLACK_SIGNING_SECRET = os.getenv('SLACK_SIGNING_SECRET')

# Ninety.io configuration
NINETY_EMAIL = os.getenv('NINETY_EMAIL')
NINETY_PASSWORD = os.getenv('NINETY_PASSWORD')

# Validate required environment variables
required_vars = [
    'SLACK_BOT_TOKEN',
    'SLACK_SIGNING_SECRET',
    'NINETY_EMAIL',
    'NINETY_PASSWORD'
]

missing_vars = [var for var in required_vars if not globals()[var]]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Set new values for testing
SLACK_BOT_TOKEN = 'xoxb-your-bot-token'
SLACK_SIGNING_SECRET = 'your-signing-secret'
NINETY_EMAIL = 'your-ninety-email'
NINETY_PASSWORD = 'your-ninety-password' 