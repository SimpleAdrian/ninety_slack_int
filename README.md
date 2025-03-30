# Ninety.io to Slack Connector

This integration allows you to interact with Ninety.io directly from Slack, making it easier to manage your headlines, to-dos, and issues without leaving your team's communication platform.

## Features

- Create and manage Ninety.io items directly from Slack:
  - Headlines
  - To-dos
  - Issues
- Search for existing items
- Subscribe to items for notifications
- Set due dates
- Attach Slack conversations to items
- Rich previews of Ninety.io items in Slack
- Message context actions for quick access to common functions

## Prerequisites

1. Python 3.8 or higher
2. Chrome browser installed (for Selenium automation)
3. A Slack workspace with admin permissions
4. A Ninety.io account with appropriate permissions

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/ninety-slack-connector.git
cd ninety-slack-connector
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
# Create a .env file with the following variables
SLACK_BOT_TOKEN=your_slack_bot_token
SLACK_SIGNING_SECRET=your_slack_signing_secret
NINETY_EMAIL=your_ninety_email
NINETY_PASSWORD=your_ninety_password
```

## Configuration

1. Create a new Slack app at https://api.slack.com/apps
2. Enable Socket Mode in your Slack app
3. Install the app to your workspace
4. Copy the provided manifest.yml to your Slack app configuration

## Usage

### Slash Commands

- `/ninety create [headline|todo|issue] [title]` - Create a new item
- `/ninety search [query]` - Search for items
- `/ninety help` - Show help information

### Message Actions

Right-click on any message to:
- Create a new item from the message
- Attach the conversation to an existing item

### Global Shortcuts

Access these shortcuts from the lightning bolt (⚡) icon:
- Create Headline
- Create To-do
- Create Issue
- Search Items

### App Mentions

Mention the app (@Ninety.io) followed by:
- `create [headline|todo|issue] [title]` - Create a new item
- `search [query]` - Search for items
- `help` - Show help information

### Interactive Features

- Subscribe to items to receive notifications in Slack
- Set due dates using the date picker
- Attach Slack conversations to items as comments
- View rich previews of Ninety.io items

## Running the App

1. Start the app:
```bash
python app.py
```

2. The app will connect to Slack using Socket Mode and start listening for events

## Troubleshooting

### Common Issues

1. **Selenium Issues**
   - Make sure Chrome is installed
   - Check if chromedriver is compatible with your Chrome version
   - Try running in headless mode if on a server

2. **Slack Connection Issues**
   - Verify your Slack tokens are correct
   - Check if all required scopes are enabled
   - Ensure the app is properly installed to your workspace

3. **Ninety.io Access Issues**
   - Verify your Ninety.io credentials
   - Check if you have the necessary permissions
   - Ensure your account is not locked or restricted

### Debug Mode

To enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please:
1. Check the documentation
2. Search existing issues
3. Create a new issue if needed

## Security

- Never share your credentials
- Use environment variables for sensitive data
- Regularly update dependencies
- Follow Slack's security best practices 