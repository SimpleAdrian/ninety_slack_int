import os
from dotenv import load_dotenv
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_handlers import app
from monitoring import start_metrics_server, logger

# Load environment variables
load_dotenv()

def main():
    """Initialize and start the Slack app"""
    try:
        # Start metrics server
        start_metrics_server(port=int(os.getenv("METRICS_PORT", 8000)))
        logger.info("app_starting")
        
        # Initialize Socket Mode handler
        handler = SocketModeHandler(
            app_token=os.getenv("SLACK_APP_TOKEN"),
            app=app
        )
        
        # Start the app
        handler.start()
        logger.info("app_started_successfully")
    except Exception as e:
        logger.error("app_startup_failed", error=str(e))
        raise

if __name__ == "__main__":
    main() 