from slack_bolt import Bolt
from typing import Dict

def get_app_home_view() -> Dict:
    """Generate the App Home view"""
    return {
        "type": "home",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Welcome to Ninety.io for Slack! 👋"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Connect your Ninety.io workspace with Slack to streamline your workflow."
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Quick Start Guide"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*1. Create Items*\n• Use `/ninety create` command\n• Right-click on messages\n• Share Ninety.io links"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*2. Search and View*\n• Use `/ninety search` to find items\n• Share Ninety.io links to see rich previews\n• Click through to view full details"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*3. Collaborate*\n• Subscribe to item updates\n• Set due dates\n• Attach conversations"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Available Commands"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*/ninety create [headline|todo|issue] <title>*\nCreate a new item directly from Slack"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*/ninety search <query>*\nSearch for existing items"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*/ninety help*\nShow all available commands and features"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Message Actions"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Right-click on any message to:*\n• Create Headlines\n• Create To-dos\n• Create Issues\n• Search Items\n• Attach Conversations"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Need Help?"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "• Type `/ninety help` for command help\n• Visit our <https://support.ninety.io|support site> for documentation\n• Contact <mailto:support@ninety.io|support@ninety.io> for assistance"
                }
            }
        ]
    }

def register_app_home_handlers(app: Bolt):
    """Register App Home related handlers"""
    
    @app.event("app_home_opened")
    def handle_app_home_opened(client, event, logger):
        """Handle when a user opens the app home"""
        try:
            client.views_publish(
                user_id=event["user"],
                view=get_app_home_view()
            )
        except Exception as e:
            logger.error(f"Error publishing app home: {e}") 