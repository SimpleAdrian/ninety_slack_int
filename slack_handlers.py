from slack_bolt import Bolt
from slack_bolt.adapter.socket_mode import SocketModeHandler
from config import SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET
from ninety_automation import NinetyAutomation
import re
from typing import Dict, List, Optional
from datetime import datetime

# Initialize the Slack Bolt app
app = Bolt(token=SLACK_BOT_TOKEN, signing_secret=SLACK_SIGNING_SECRET)
ninety = None

def get_ninety_instance():
    """Get or create a Ninety.io automation instance"""
    global ninety
    if ninety is None:
        ninety = NinetyAutomation()
        ninety.login()
    return ninety

def create_item_modal(item_type, trigger_id, initial_text=None):
    """Create a modal for item creation"""
    modal = {
        "type": "modal",
        "callback_id": f"create_{item_type}",
        "title": {"type": "plain_text", "text": f"Create {item_type.title()}"},
        "submit": {"type": "plain_text", "text": "Create"},
        "blocks": [
            {
                "type": "input",
                "block_id": "title",
                "label": {"type": "plain_text", "text": "Title"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "title_input",
                    "initial_value": initial_text
                }
            },
            {
                "type": "input",
                "block_id": "description",
                "label": {"type": "plain_text", "text": "Description"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "description_input",
                    "multiline": True
                }
            }
        ]
    }

    if item_type in ['todo', 'issue']:
        modal["blocks"].append({
            "type": "input",
            "block_id": "priority",
            "label": {"type": "plain_text", "text": "Priority"},
            "element": {
                "type": "static_select",
                "action_id": "priority_select",
                "placeholder": {"type": "plain_text", "text": "Select priority"},
                "options": [
                    {"text": {"type": "plain_text", "text": "High"}, "value": "high"},
                    {"text": {"type": "plain_text", "text": "Medium"}, "value": "medium"},
                    {"text": {"type": "plain_text", "text": "Low"}, "value": "low"}
                ]
            }
        })

    if item_type == 'issue':
        modal["blocks"].append({
            "type": "input",
            "block_id": "status",
            "label": {"type": "plain_text", "text": "Status"},
            "element": {
                "type": "static_select",
                "action_id": "status_select",
                "placeholder": {"type": "plain_text", "text": "Select status"},
                "options": [
                    {"text": {"type": "plain_text", "text": "Open"}, "value": "open"},
                    {"text": {"type": "plain_text", "text": "In Progress"}, "value": "in_progress"},
                    {"text": {"type": "plain_text", "text": "Resolved"}, "value": "resolved"}
                ]
            }
        })

    app.client.views_open(trigger_id=trigger_id, view=modal)

@app.action("create_headline")
def handle_create_headline(ack, body, client):
    ack()
    create_item_modal("headline", body["trigger_id"], body["message"]["text"])

@app.action("create_todo")
def handle_create_todo(ack, body, client):
    ack()
    create_item_modal("todo", body["trigger_id"], body["message"]["text"])

@app.action("create_issue")
def handle_create_issue(ack, body, client):
    ack()
    create_item_modal("issue", body["trigger_id"], body["message"]["text"])

@app.view("create_headline")
def handle_create_headline_submission(ack, body, client):
    ack()
    values = body["view"]["state"]["values"]
    title = values["title"]["title_input"]["value"]
    description = values["description"]["description_input"]["value"]
    
    try:
        ninety = get_ninety_instance()
        result = ninety.create_headline(title, description)
        client.chat_postMessage(
            channel=body["user"]["id"],
            text=f"✅ Headline created successfully!\nTitle: {result['title']}"
        )
    except Exception as e:
        client.chat_postMessage(
            channel=body["user"]["id"],
            text=f"❌ Error creating headline: {str(e)}"
        )

@app.view("create_todo")
def handle_create_todo_submission(ack, body, client):
    ack()
    values = body["view"]["state"]["values"]
    title = values["title"]["title_input"]["value"]
    description = values["description"]["description_input"]["value"]
    priority = values["priority"]["priority_select"]["selected_option"]["value"]
    
    try:
        ninety = get_ninety_instance()
        result = ninety.create_todo(title, description, priority)
        client.chat_postMessage(
            channel=body["user"]["id"],
            text=f"✅ To-do created successfully!\nTitle: {result['title']}\nPriority: {priority}"
        )
    except Exception as e:
        client.chat_postMessage(
            channel=body["user"]["id"],
            text=f"❌ Error creating to-do: {str(e)}"
        )

@app.view("create_issue")
def handle_create_issue_submission(ack, body, client):
    ack()
    values = body["view"]["state"]["values"]
    title = values["title"]["title_input"]["value"]
    description = values["description"]["description_input"]["value"]
    priority = values["priority"]["priority_select"]["selected_option"]["value"]
    status = values["status"]["status_select"]["selected_option"]["value"]
    
    try:
        ninety = get_ninety_instance()
        result = ninety.create_issue(title, description, priority, status)
        client.chat_postMessage(
            channel=body["user"]["id"],
            text=f"✅ Issue created successfully!\nTitle: {result['title']}\nPriority: {priority}\nStatus: {status}"
        )
    except Exception as e:
        client.chat_postMessage(
            channel=body["user"]["id"],
            text=f"❌ Error creating issue: {str(e)}"
        )

@app.action("search_items")
def handle_search_items(ack, body, client):
    ack()
    # Open a modal for search
    modal = {
        "type": "modal",
        "callback_id": "search_items",
        "title": {"type": "plain_text", "text": "Search Ninety.io Items"},
        "submit": {"type": "plain_text", "text": "Search"},
        "blocks": [
            {
                "type": "input",
                "block_id": "search_query",
                "label": {"type": "plain_text", "text": "Search Query"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "search_input"
                }
            },
            {
                "type": "input",
                "block_id": "item_type",
                "label": {"type": "plain_text", "text": "Item Type"},
                "element": {
                    "type": "static_select",
                    "action_id": "type_select",
                    "placeholder": {"type": "plain_text", "text": "Select type"},
                    "options": [
                        {"text": {"type": "plain_text", "text": "All"}, "value": None},
                        {"text": {"type": "plain_text", "text": "Headlines"}, "value": "headline"},
                        {"text": {"type": "plain_text", "text": "To-dos"}, "value": "todo"},
                        {"text": {"type": "plain_text", "text": "Issues"}, "value": "issue"}
                    ]
                }
            }
        ]
    }
    client.views_open(trigger_id=body["trigger_id"], view=modal)

@app.view("search_items")
def handle_search_submission(ack, body, client):
    ack()
    values = body["view"]["state"]["values"]
    query = values["search_query"]["search_input"]["value"]
    item_type = values["item_type"]["type_select"]["selected_option"]["value"]
    
    try:
        ninety = get_ninety_instance()
        results = ninety.search_items(query, item_type)
        if not results:
            client.chat_postMessage(
                channel=body["user"]["id"],
                text="No items found matching your search."
            )
            return
        
        # Format results
        message = "🔍 Search Results:\n\n"
        for item in results[:5]:  # Limit to 5 results
            message += f"• {item['title']}\n"
            if item.get('description'):
                message += f"  {item['description'][:100]}...\n"
            message += f"  Type: {item['type']}\n"
            if item.get('priority'):
                message += f"  Priority: {item['priority']}\n"
            if item.get('status'):
                message += f"  Status: {item['status']}\n"
            message += "\n"
        
        client.chat_postMessage(
            channel=body["user"]["id"],
            text=message
        )
    except Exception as e:
        client.chat_postMessage(
            channel=body["user"]["id"],
            text=f"❌ Error searching items: {str(e)}"
        )

@app.event("link_shared")
def handle_link_shared(event, client):
    """Handle shared Ninety.io links"""
    for link in event.get("links", []):
        if "ninety.io" in link["url"]:
            # Extract item type and ID from URL
            match = re.search(r"ninety\.io/(\w+)/(\w+)", link["url"])
            if match:
                item_type, item_id = match.groups()
                try:
                    ninety = get_ninety_instance()
                    item = ninety.get_item_details(item_id, item_type)
                    
                    # Create unfurl blocks
                    blocks = [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"*{item['title']}*\n{item['description'][:100]}..."
                            }
                        },
                        {
                            "type": "context",
                            "elements": [
                                {
                                    "type": "mrkdwn",
                                    "text": f"Type: {item['type'].title()} | Status: {item['status']} | Due: {item['due_date']}"
                                }
                            ]
                        },
                        {
                            "type": "actions",
                            "elements": [
                                {
                                    "type": "button",
                                    "text": {"type": "plain_text", "text": "Subscribe"},
                                    "action_id": f"subscribe_{item_type}_{item_id}"
                                },
                                {
                                    "type": "button",
                                    "text": {"type": "plain_text", "text": "Set Due Date"},
                                    "action_id": f"set_due_date_{item_type}_{item_id}"
                                },
                                {
                                    "type": "button",
                                    "text": {"type": "plain_text", "text": "Attach Conversation"},
                                    "action_id": f"attach_conversation_{item_type}_{item_id}"
                                }
                            ]
                        }
                    ]
                    
                    # Unfurl the link
                    client.chat_unfurl(
                        channel=event["channel"],
                        ts=event["message_ts"],
                        unfurls={
                            link["url"]: {
                                "blocks": blocks
                            }
                        }
                    )
                except Exception as e:
                    print(f"Error unfurling link: {str(e)}")

@app.command("/ninety")
def handle_ninety_command(ack, command, client):
    """Handle the main /ninety command"""
    ack()
    
    args = command["text"].strip().split()
    subcommand = args[0].lower() if args else "help"
    
    if subcommand == "help":
        help_text = """
*Ninety.io Commands*
• `/ninety help` - Show this help message
• `/ninety create [headline|todo|issue|rock] [title]` - Create a new item
• `/ninety search [query]` - Search for items
• `/ninety list [headlines|todos|issues|rocks]` - List recent items
• `/ninety subscribe [item-id]` - Subscribe to item updates
• `/ninety due [item-id] [date]` - Set or view due dates

*Quick Commands*
• `/ninety-create` - Create new items
• `/ninety-search` - Search items
• `/ninety-list` - List recent items
• `/ninety-rock` - Create a new Rock
• `/ninety-subscribe` - Subscribe to updates
• `/ninety-due` - Manage due dates

*Tips*
• Use message shortcuts (⋮) to create items from messages
• Click on Ninety.io links to see rich previews
• React with 🔗 to quickly attach conversations
"""
        client.chat_postEphemeral(
            channel=command["channel_id"],
            user=command["user_id"],
            text=help_text
        )
        return

    # Handle other subcommands by delegating to specific handlers
    if subcommand == "create":
        handle_create_command(command, client, args[1:])
    elif subcommand == "search":
        handle_search_command(command, client, args[1:])
    elif subcommand == "list":
        handle_list_command(command, client, args[1:])
    elif subcommand == "subscribe":
        handle_subscribe_command(command, client, args[1:])
    elif subcommand == "due":
        handle_due_command(command, client, args[1:])
    elif subcommand == "rock":
        handle_ninety_rock_command(command, client)
    else:
        client.chat_postEphemeral(
            channel=command["channel_id"],
            user=command["user_id"],
            text=f"Unknown command: {subcommand}\nType `/ninety help` for available commands."
        )

@app.command("/ninety-create")
def handle_ninety_create_command(ack, command, client):
    """Handle the /ninety-create command"""
    ack()
    
    args = command["text"].strip().split(maxsplit=1)
    if len(args) < 2:
        client.chat_postEphemeral(
            channel=command["channel_id"],
            user=command["user_id"],
            text="Usage: `/ninety-create [headline|todo|issue] [title]`"
        )
        return
    
    item_type = args[0].lower()
    title = args[1]
    
    if item_type not in ["headline", "todo", "issue"]:
        client.chat_postEphemeral(
            channel=command["channel_id"],
            user=command["user_id"],
            text="Invalid item type. Use: headline, todo, or issue"
        )
        return
    
    try:
        ninety = get_ninety_instance()
        if item_type == "headline":
            result = ninety.create_headline(title)
        elif item_type == "todo":
            result = ninety.create_todo(title)
        else:
            result = ninety.create_issue(title)
        
        client.chat_postMessage(
            channel=command["channel_id"],
            text=f"✅ Created {item_type}: {result['title']}\n{result.get('url', '')}"
        )
    except Exception as e:
        client.chat_postEphemeral(
            channel=command["channel_id"],
            user=command["user_id"],
            text=f"❌ Error creating {item_type}: {str(e)}"
        )

@app.command("/ninety-search")
def handle_ninety_search_command(ack, command, client):
    """Handle the /ninety-search command"""
    ack()
    
    query = command["text"].strip()
    try:
        ninety = get_ninety_instance()
        
        # Search across all item types including Rocks
        results = {
            "headlines": ninety.search_items(query, "headlines"),
            "todos": ninety.search_items(query, "todos"),
            "issues": ninety.search_items(query, "issues"),
            "rocks": ninety.search_rocks(query)
        }
        
        if not any(results.values()):
            client.chat_postEphemeral(
                channel=command["channel_id"],
                user=command["user_id"],
                text="No items found matching your search."
            )
            return
        
        # Format results
        blocks = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Search Results for:* {query}"}
            }
        ]
        
        for item_type, items in results.items():
            if items:
                blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*{item_type.title()}*"}
                })
                
                for item in items[:3]:  # Show top 3 results per type
                    blocks.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"• *{item['title']}*\n{item.get('description', '')[:100]}..."
                        },
                        "accessory": {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "View"},
                            "url": item["url"]
                        }
                    })
        
        client.chat_postEphemeral(
            channel=command["channel_id"],
            user=command["user_id"],
            blocks=blocks
        )
    except Exception as e:
        client.chat_postEphemeral(
            channel=command["channel_id"],
            user=command["user_id"],
            text=f"❌ Error searching items: {str(e)}"
        )

@app.command("/ninety-list")
def handle_ninety_list_command(ack, command, client):
    """Handle the /ninety-list command"""
    ack()
    
    item_type = command["text"].strip().lower() if command["text"].strip() else "all"
    valid_types = ["headlines", "todos", "issues", "rocks", "all"]
    
    if item_type not in valid_types:
        client.chat_postEphemeral(
            channel=command["channel_id"],
            user=command["user_id"],
            text=f"Invalid type. Use: {', '.join(valid_types)}"
        )
        return
    
    try:
        ninety = get_ninety_instance()
        results = ninety.search_items("", item_type if item_type != "all" else None)
        
        if not results:
            client.chat_postEphemeral(
                channel=command["channel_id"],
                user=command["user_id"],
                text=f"No recent {item_type} found."
            )
            return
        
        # Format results
        blocks = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Recent {item_type.title()}*"}
            }
        ]
        
        for item in results[:10]:
            status = f" • {item['status']}" if 'status' in item else ""
            due_date = f" • Due: {item['due_date']}" if 'due_date' in item else ""
            
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{item['title']}*{status}{due_date}\n{item.get('description', '')[:100]}..."
                },
                "accessory": {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "View"},
                    "url": item["url"]
                }
            })
        
        client.chat_postEphemeral(
            channel=command["channel_id"],
            user=command["user_id"],
            blocks=blocks
        )
    except Exception as e:
        client.chat_postEphemeral(
            channel=command["channel_id"],
            user=command["user_id"],
            text=f"❌ Error listing items: {str(e)}"
        )

@app.command("/ninety-subscribe")
def handle_ninety_subscribe_command(ack, command, client):
    """Handle the /ninety-subscribe command"""
    ack()
    
    item_id = command["text"].strip()
    if not item_id:
        client.chat_postEphemeral(
            channel=command["channel_id"],
            user=command["user_id"],
            text="Usage: `/ninety subscribe [item-id]`"
        )
        return
    
    try:
        ninety = get_ninety_instance()
        # Extract item type from ID prefix (e.g., HDL-123 -> headline)
        item_type = {
            "HDL": "headline",
            "TODO": "todo",
            "ISS": "issue"
        }.get(item_id.split("-")[0], None)
        
        if not item_type:
            raise ValueError("Invalid item ID format")
        
        result = ninety.subscribe_to_item(item_id, item_type)
        
        client.chat_postMessage(
            channel=command["channel_id"],
            text=f"✅ Subscribed to {item_type} {item_id}"
        )
    except Exception as e:
        client.chat_postEphemeral(
            channel=command["channel_id"],
            user=command["user_id"],
            text=f"❌ Error subscribing to item: {str(e)}"
        )

@app.command("/ninety-due")
def handle_ninety_due_command(ack, command, client):
    """Handle the /ninety-due command"""
    ack()
    
    args = command["text"].strip().split()
    if not args:
        client.chat_postEphemeral(
            channel=command["channel_id"],
            user=command["user_id"],
            text="Usage: `/ninety-due [item-id] [date]`"
        )
        return
    
    item_id = args[0]
    due_date = args[1] if len(args) > 1 else None
    
    try:
        ninety = get_ninety_instance()
        # Extract item type from ID prefix
        item_type = {
            "HDL": "headline",
            "TODO": "todo",
            "ISS": "issue"
        }.get(item_id.split("-")[0], None)
        
        if not item_type:
            raise ValueError("Invalid item ID format")
        
        if due_date:
            # Set due date
            result = ninety.update_item(item_id, item_type, {"due_date": due_date})
            message = f"✅ Set due date for {item_type} {item_id} to {due_date}"
        else:
            # Get current due date
            item = ninety.get_item_details(item_id, item_type)
            message = f"Due date for {item_type} {item_id}: {item.get('due_date', 'Not set')}"
        
        client.chat_postMessage(
            channel=command["channel_id"],
            text=message
        )
    except Exception as e:
        client.chat_postEphemeral(
            channel=command["channel_id"],
            user=command["user_id"],
            text=f"❌ Error managing due date: {str(e)}"
        )

@app.command("/ninety-rock")
def handle_ninety_rock_command(ack, command, client):
    """Handle the /ninety-rock command"""
    ack()
    
    args = command["text"].strip().split(maxsplit=1)
    if len(args) < 1:
        client.chat_postEphemeral(
            channel=command["channel_id"],
            user=command["user_id"],
            text="Usage: `/ninety-rock [title]`"
        )
        return
    
    title = args[0]
    description = args[1] if len(args) > 1 else None
    
    try:
        ninety = get_ninety_instance()
        result = ninety.create_rock(title, description)
        
        client.chat_postMessage(
            channel=command["channel_id"],
            text=f"✅ Created Rock: {result['title']}\n{result.get('url', '')}"
        )
    except Exception as e:
        client.chat_postEphemeral(
            channel=command["channel_id"],
            user=command["user_id"],
            text=f"❌ Error creating Rock: {str(e)}"
        )

def handle_create_command(command, client, args):
    """Helper function to handle /ninety create"""
    if len(args) < 2:
        client.chat_postEphemeral(
            channel=command["channel_id"],
            user=command["user_id"],
            text="Usage: `/ninety create [headline|todo|issue] [title]`"
        )
        return
    
    handle_ninety_create_command(lambda: None, command, client)

def handle_search_command(command, client, args):
    """Helper function to handle /ninety search"""
    command["text"] = " ".join(args)
    handle_ninety_search_command(lambda: None, command, client)

def handle_list_command(command, client, args):
    """Helper function to handle /ninety list"""
    command["text"] = args[0] if args else "all"
    handle_ninety_list_command(lambda: None, command, client)

def handle_subscribe_command(command, client, args):
    """Helper function to handle /ninety subscribe"""
    if not args:
        client.chat_postEphemeral(
            channel=command["channel_id"],
            user=command["user_id"],
            text="Usage: `/ninety subscribe [item-id]`"
        )
        return
    
    command["text"] = args[0]
    handle_ninety_subscribe_command(lambda: None, command, client)

def handle_due_command(command, client, args):
    """Helper function to handle /ninety due"""
    command["text"] = " ".join(args)
    handle_ninety_due_command(lambda: None, command, client)

# Add new handlers for global shortcuts
@app.shortcut("create_headline_shortcut")
def handle_create_headline_shortcut(ack, shortcut, client):
    ack()
    create_item_modal("headline", shortcut["trigger_id"])

@app.shortcut("create_todo_shortcut")
def handle_create_todo_shortcut(ack, shortcut, client):
    ack()
    create_item_modal("todo", shortcut["trigger_id"])

@app.shortcut("create_issue_shortcut")
def handle_create_issue_shortcut(ack, shortcut, client):
    ack()
    create_item_modal("issue", shortcut["trigger_id"])

@app.shortcut("search_items_shortcut")
def handle_search_items_shortcut(ack, shortcut, client):
    ack()
    create_search_modal(shortcut["trigger_id"], client)

@app.event("app_mention")
def handle_app_mention(event, client):
    """Handle when the app is mentioned in a channel"""
    text = event["text"].lower()
    user_id = event["user"]
    channel_id = event["channel"]
    
    # Extract command from mention
    # Remove the app mention and leading/trailing whitespace
    command_text = re.sub(r'<@[A-Z0-9]+>', '', text).strip()
    
    if not command_text:
        show_help(client, channel_id)
        return
    
    # Split into command and args
    parts = command_text.split(maxsplit=1)
    command = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""
    
    if command == "create":
        # Handle create command
        try:
            item_type, title = args.split(maxsplit=1)
            if item_type not in ["headline", "todo", "issue"]:
                raise ValueError("Invalid item type")
            
            ninety = get_ninety_instance()
            if item_type == "headline":
                result = ninety.create_headline(title)
            elif item_type == "todo":
                result = ninety.create_todo(title)
            else:
                result = ninety.create_issue(title)
                
            client.chat_postMessage(
                channel=channel_id,
                text=f"✅ Created {item_type}: {result['title']}"
            )
        except Exception as e:
            client.chat_postMessage(
                channel=channel_id,
                text=f"❌ Error creating {item_type}: {str(e)}"
            )
    
    elif command == "search":
        # Handle search command
        try:
            ninety = get_ninety_instance()
            results = ninety.search_items(args)
            format_and_send_results(results, client, channel_id)
        except Exception as e:
            client.chat_postMessage(
                channel=channel_id,
                text=f"❌ Error searching: {str(e)}"
            )
    
    elif command == "help":
        show_help(client, channel_id)
    
    else:
        client.chat_postMessage(
            channel=channel_id,
            text=f"Unknown command: {command}\nType `@Ninety.io help` for available commands."
        )

# Add handlers for interactive components
@app.action("subscribe_.*")
def handle_subscribe_action(ack, body, client):
    ack()
    # Extract item type and ID from action ID
    match = re.match(r"subscribe_(\w+)_(\w+)", body["action_id"])
    if match:
        item_type, item_id = match.groups()
        try:
            ninety = get_ninety_instance()
            result = ninety.subscribe_to_item(item_id, item_type)
            client.chat_postMessage(
                channel=body["user"]["id"],
                text=f"✅ Subscribed to {item_type} successfully!"
            )
        except Exception as e:
            client.chat_postMessage(
                channel=body["user"]["id"],
                text=f"❌ Error subscribing to {item_type}: {str(e)}"
            )

@app.action("set_due_date_.*")
def handle_set_due_date_action(ack, body, client):
    ack()
    # Extract item type and ID from action ID
    match = re.match(r"set_due_date_(\w+)_(\w+)", body["action_id"])
    if match:
        item_type, item_id = match.groups()
        # Open date picker modal
        modal = {
            "type": "modal",
            "callback_id": f"set_due_date_{item_type}_{item_id}",
            "title": {"type": "plain_text", "text": "Set Due Date"},
            "submit": {"type": "plain_text", "text": "Set"},
            "blocks": [
                {
                    "type": "input",
                    "block_id": "due_date",
                    "label": {"type": "plain_text", "text": "Due Date"},
                    "element": {
                        "type": "datepicker",
                        "action_id": "date_picker",
                        "initial_date": datetime.now().strftime("%Y-%m-%d")
                    }
                }
            ]
        }
        client.views_open(trigger_id=body["trigger_id"], view=modal)

@app.action("attach_conversation_.*")
def handle_attach_conversation_action(ack, body, client):
    ack()
    # Extract item type and ID from action ID
    match = re.match(r"attach_conversation_(\w+)_(\w+)", body["action_id"])
    if match:
        item_type, item_id = match.groups()
        try:
            # Get conversation history
            result = client.conversations_history(
                channel=body["channel"]["id"],
                latest=body["message"]["ts"],
                limit=5,
                inclusive=True
            )
            
            # Format conversation
            messages = result["messages"]
            conversation_text = ""
            for msg in reversed(messages):
                user_info = client.users_info(user=msg["user"])["user"]
                conversation_text += f"{user_info['real_name']}: {msg['text']}\n"
            
            # Attach conversation to item
            ninety = get_ninety_instance()
            ninety.attach_conversation(item_id, item_type, conversation_text)
            
            client.chat_postMessage(
                channel=body["user"]["id"],
                text=f"✅ Conversation attached to {item_type} successfully!"
            )
        except Exception as e:
            client.chat_postMessage(
                channel=body["user"]["id"],
                text=f"❌ Error attaching conversation: {str(e)}"
            )

def create_search_modal(trigger_id, client, initial_type=None):
    """Create a modal for searching and selecting Ninety.io items"""
    modal = {
        "type": "modal",
        "callback_id": "search_items",
        "title": {"type": "plain_text", "text": "Find Ninety.io Item"},
        "submit": {"type": "plain_text", "text": "Search"},
        "blocks": [
            {
                "type": "input",
                "block_id": "workspace",
                "label": {"type": "plain_text", "text": "Workspace"},
                "element": {
                    "type": "static_select",
                    "action_id": "workspace_select",
                    "placeholder": {"type": "plain_text", "text": "Select workspace"},
                    "options": [
                        {"text": {"type": "plain_text", "text": workspace}, "value": workspace_id}
                        for workspace_id, workspace in get_workspaces()
                    ]
                }
            },
            {
                "type": "input",
                "block_id": "item_type",
                "label": {"type": "plain_text", "text": "Item Type"},
                "element": {
                    "type": "static_select",
                    "action_id": "type_select",
                    "placeholder": {"type": "plain_text", "text": "Select type"},
                    "initial_option": {"text": {"type": "plain_text", "text": initial_type.title()}, "value": initial_type.lower()} if initial_type else None,
                    "options": [
                        {"text": {"type": "plain_text", "text": "Headlines"}, "value": "headline"},
                        {"text": {"type": "plain_text", "text": "To-dos"}, "value": "todo"},
                        {"text": {"type": "plain_text", "text": "Issues"}, "value": "issue"}
                    ]
                }
            },
            {
                "type": "input",
                "block_id": "search_query",
                "optional": True,
                "label": {"type": "plain_text", "text": "Search (optional)"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "search_input",
                    "placeholder": {"type": "plain_text", "text": "Search by title or description"}
                }
            }
        ]
    }
    client.views_open(trigger_id=trigger_id, view=modal)

def get_workspaces():
    """Get list of Ninety.io workspaces"""
    try:
        ninety = get_ninety_instance()
        workspaces = ninety.get_workspaces()
        return [(w["id"], w["name"]) for w in workspaces]
    except Exception as e:
        return [("default", "Default Workspace")]  # Fallback if can't fetch workspaces

@app.view("search_items")
def handle_search_submission(ack, body, client):
    ack()
    values = body["view"]["state"]["values"]
    workspace_id = values["workspace"]["workspace_select"]["selected_option"]["value"]
    item_type = values["item_type"]["type_select"]["selected_option"]["value"]
    query = values.get("search_query", {}).get("search_input", {}).get("value", "")
    
    try:
        ninety = get_ninety_instance()
        results = ninety.search_items(query, item_type, workspace_id)
        
        if not results:
            client.chat_postMessage(
                channel=body["user"]["id"],
                text="No items found matching your search."
            )
            return
        
        # Create blocks for item selection
        blocks = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "*Select an item to update:*"}
            }
        ]
        
        for item in results[:10]:  # Limit to 10 results
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{item['title']}*\n{item.get('description', '')[:100]}..."
                },
                "accessory": {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Select"},
                    "value": f"{item['id']}",
                    "action_id": f"select_item_{item_type}_{item['id']}"
                }
            })
        
        client.views_push(
            trigger_id=body["trigger_id"],
            view={
                "type": "modal",
                "callback_id": "item_selection",
                "title": {"type": "plain_text", "text": "Select Item"},
                "blocks": blocks
            }
        )
    except Exception as e:
        client.chat_postMessage(
            channel=body["user"]["id"],
            text=f"❌ Error searching items: {str(e)}"
        )

@app.action(re.compile("select_item_.*"))
def handle_item_selection(ack, body, client):
    ack()
    # Extract item type and ID from action ID
    match = re.match(r"select_item_(\w+)_(\w+)", body["action_id"])
    if match:
        item_type, item_id = match.groups()
        try:
            ninety = get_ninety_instance()
            item = ninety.get_item_details(item_id, item_type)
            
            # Create update modal
            modal = {
                "type": "modal",
                "callback_id": f"update_{item_type}_{item_id}",
                "title": {"type": "plain_text", "text": f"Update {item_type.title()}"},
                "submit": {"type": "plain_text", "text": "Update"},
                "blocks": [
                    {
                        "type": "input",
                        "block_id": "title",
                        "label": {"type": "plain_text", "text": "Title"},
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "title_input",
                            "initial_value": item["title"]
                        }
                    },
                    {
                        "type": "input",
                        "block_id": "description",
                        "label": {"type": "plain_text", "text": "Description"},
                        "element": {
                            "type": "plain_text_input",
                            "action_id": "description_input",
                            "multiline": True,
                            "initial_value": item.get("description", "")
                        }
                    }
                ]
            }
            
            # Add status field for issues
            if item_type == "issue":
                modal["blocks"].append({
                    "type": "input",
                    "block_id": "status",
                    "label": {"type": "plain_text", "text": "Status"},
                    "element": {
                        "type": "static_select",
                        "action_id": "status_select",
                        "initial_option": {"text": {"type": "plain_text", "text": item["status"]}, "value": item["status"].lower()},
                        "options": [
                            {"text": {"type": "plain_text", "text": "Open"}, "value": "open"},
                            {"text": {"type": "plain_text", "text": "In Progress"}, "value": "in_progress"},
                            {"text": {"type": "plain_text", "text": "Resolved"}, "value": "resolved"}
                        ]
                    }
                })
            
            # Add due date field for todos and issues
            if item_type in ["todo", "issue"]:
                modal["blocks"].append({
                    "type": "input",
                    "block_id": "due_date",
                    "optional": True,
                    "label": {"type": "plain_text", "text": "Due Date"},
                    "element": {
                        "type": "datepicker",
                        "action_id": "due_date_picker",
                        "initial_date": item.get("due_date", datetime.now().strftime("%Y-%m-%d"))
                    }
                })
            
            client.views_update(
                view_id=body["view"]["id"],
                view=modal
            )
        except Exception as e:
            client.chat_postMessage(
                channel=body["user"]["id"],
                text=f"❌ Error loading item details: {str(e)}"
            )

@app.view(re.compile("update_.*"))
def handle_item_update(ack, body, client):
    ack()
    match = re.match(r"update_(\w+)_(\w+)", body["view"]["callback_id"])
    if match:
        item_type, item_id = match.groups()
        values = body["view"]["state"]["values"]
        
        try:
            ninety = get_ninety_instance()
            updates = {
                "title": values["title"]["title_input"]["value"],
                "description": values["description"]["description_input"]["value"]
            }
            
            if item_type == "issue":
                updates["status"] = values["status"]["status_select"]["selected_option"]["value"]
            
            if item_type in ["todo", "issue"]:
                updates["due_date"] = values["due_date"]["due_date_picker"]["selected_date"]
            
            result = ninety.update_item(item_id, item_type, updates)
            
            client.chat_postMessage(
                channel=body["user"]["id"],
                text=f"✅ {item_type.title()} updated successfully!"
            )
        except Exception as e:
            client.chat_postMessage(
                channel=body["user"]["id"],
                text=f"❌ Error updating {item_type}: {str(e)}"
            )

# Add message shortcut handlers
@app.shortcut("create_headline_message")
def handle_create_headline_message(ack, shortcut, client):
    ack()
    message = shortcut["message"]["text"]
    create_item_modal("headline", shortcut["trigger_id"], message)

@app.shortcut("create_todo_message")
def handle_create_todo_message(ack, shortcut, client):
    ack()
    message = shortcut["message"]["text"]
    create_item_modal("todo", shortcut["trigger_id"], message)

@app.shortcut("create_issue_message")
def handle_create_issue_message(ack, shortcut, client):
    ack()
    message = shortcut["message"]["text"]
    create_item_modal("issue", shortcut["trigger_id"], message)

@app.shortcut("attach_to_item_message")
def handle_attach_to_item_message(ack, shortcut, client):
    ack()
    # Store message details in state for later use
    message_ts = shortcut["message"]["ts"]
    channel_id = shortcut["channel"]["id"]
    
    # Create modal for selecting an item to attach to
    modal = {
        "type": "modal",
        "callback_id": f"attach_message_{channel_id}_{message_ts}",
        "title": {"type": "plain_text", "text": "Attach to Ninety.io Item"},
        "submit": {"type": "plain_text", "text": "Search"},
        "blocks": [
            {
                "type": "input",
                "block_id": "workspace",
                "label": {"type": "plain_text", "text": "Workspace"},
                "element": {
                    "type": "static_select",
                    "action_id": "workspace_select",
                    "placeholder": {"type": "plain_text", "text": "Select workspace"},
                    "options": [
                        {"text": {"type": "plain_text", "text": workspace}, "value": workspace_id}
                        for workspace_id, workspace in get_workspaces()
                    ]
                }
            },
            {
                "type": "input",
                "block_id": "item_type",
                "label": {"type": "plain_text", "text": "Item Type"},
                "element": {
                    "type": "static_select",
                    "action_id": "type_select",
                    "placeholder": {"type": "plain_text", "text": "Select type"},
                    "options": [
                        {"text": {"type": "plain_text", "text": "Headlines"}, "value": "headline"},
                        {"text": {"type": "plain_text", "text": "To-dos"}, "value": "todo"},
                        {"text": {"type": "plain_text", "text": "Issues"}, "value": "issue"}
                    ]
                }
            },
            {
                "type": "input",
                "block_id": "search_query",
                "optional": True,
                "label": {"type": "plain_text", "text": "Search (optional)"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "search_input",
                    "placeholder": {"type": "plain_text", "text": "Search by title or description"}
                }
            }
        ]
    }
    client.views_open(trigger_id=shortcut["trigger_id"], view=modal)

@app.view(re.compile("attach_message_.*"))
def handle_attach_message_search(ack, body, client):
    ack()
    # Extract channel_id and message_ts from callback_id
    match = re.match(r"attach_message_([^_]+)_(.+)", body["view"]["callback_id"])
    if not match:
        return
    
    channel_id, message_ts = match.groups()
    values = body["view"]["state"]["values"]
    workspace_id = values["workspace"]["workspace_select"]["selected_option"]["value"]
    item_type = values["item_type"]["type_select"]["selected_option"]["value"]
    query = values.get("search_query", {}).get("search_input", {}).get("value", "")
    
    try:
        ninety = get_ninety_instance()
        results = ninety.search_items(query, item_type, workspace_id)
        
        if not results:
            client.chat_postMessage(
                channel=body["user"]["id"],
                text="No items found matching your search."
            )
            return
        
        # Create blocks for item selection
        blocks = [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "*Select an item to attach the message to:*"}
            }
        ]
        
        for item in results[:10]:  # Limit to 10 results
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{item['title']}*\n{item.get('description', '')[:100]}..."
                },
                "accessory": {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Select"},
                    "value": f"{channel_id}|{message_ts}",
                    "action_id": f"attach_to_{item_type}_{item['id']}"
                }
            })
        
        client.views_update(
            view_id=body["view"]["id"],
            view={
                "type": "modal",
                "callback_id": "item_selection",
                "title": {"type": "plain_text", "text": "Select Item"},
                "blocks": blocks
            }
        )
    except Exception as e:
        client.chat_postMessage(
            channel=body["user"]["id"],
            text=f"❌ Error searching items: {str(e)}"
        )

@app.action(re.compile("attach_to_.*"))
def handle_attach_to_item(ack, body, client):
    ack()
    # Extract item type and ID from action ID
    match = re.match(r"attach_to_(\w+)_(\w+)", body["action_id"])
    if match:
        item_type, item_id = match.groups()
        channel_id, message_ts = body["actions"][0]["value"].split("|")
        
        try:
            # Get conversation history
            result = client.conversations_history(
                channel=channel_id,
                latest=message_ts,
                limit=1,
                inclusive=True
            )
            
            if not result["messages"]:
                raise Exception("Message not found")
            
            message = result["messages"][0]
            user_info = client.users_info(user=message["user"])["user"]
            
            # Format the message
            conversation_text = f"{user_info['real_name']}: {message['text']}"
            
            # Attach to item
            ninety = get_ninety_instance()
            ninety.attach_conversation(item_id, item_type, conversation_text)
            
            # Send confirmation
            client.chat_postMessage(
                channel=body["user"]["id"],
                text=f"✅ Message attached to {item_type} successfully!"
            )
            
            # Add a reaction to the original message to indicate it was attached
            client.reactions_add(
                channel=channel_id,
                timestamp=message_ts,
                name="link"
            )
        except Exception as e:
            client.chat_postMessage(
                channel=body["user"]["id"],
                text=f"❌ Error attaching message: {str(e)}"
            )

@app.shortcut("create_from_message")
def handle_create_from_message(ack, shortcut, client):
    """Handle creating new items from messages"""
    ack()
    
    message_text = shortcut["message"]["text"]
    message_link = shortcut["message"]["permalink"]
    
    # Show item creation modal
    client.views_open(
        trigger_id=shortcut["trigger_id"],
        view={
            "type": "modal",
            "title": {"type": "plain_text", "text": "Create in Ninety.io"},
            "submit": {"type": "plain_text", "text": "Create"},
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"Create an item from:\n>{message_text}"
                    }
                },
                {
                    "type": "input",
                    "block_id": "item_type",
                    "label": {"type": "plain_text", "text": "Item Type"},
                    "element": {
                        "type": "static_select",
                        "options": [
                            {"text": {"type": "plain_text", "text": "Rock"}, "value": "rock"},
                            {"text": {"type": "plain_text", "text": "To-do"}, "value": "todo"},
                            {"text": {"type": "plain_text", "text": "Issue"}, "value": "issue"},
                            {"text": {"type": "plain_text", "text": "Headline"}, "value": "headline"}
                        ]
                    }
                },
                {
                    "type": "input",
                    "block_id": "title",
                    "label": {"type": "plain_text", "text": "Title"},
                    "element": {
                        "type": "plain_text_input",
                        "initial_value": message_text[:100]
                    }
                },
                {
                    "type": "input",
                    "block_id": "team",
                    "label": {"type": "plain_text", "text": "Team"},
                    "element": {
                        "type": "static_select",
                        "options": [
                            {"text": {"type": "plain_text", "text": "Leadership Team"}, "value": "leadership"},
                            {"text": {"type": "plain_text", "text": "Development"}, "value": "development"},
                            # Add other teams as needed
                        ]
                    }
                }
            ]
        }
    )

@app.shortcut("link_to_item")
def handle_link_to_item(ack, shortcut, client):
    """Handle linking messages to existing items"""
    ack()
    
    message_text = shortcut["message"]["text"]
    message_link = shortcut["message"]["permalink"]
    
    # Show search modal
    client.views_open(
        trigger_id=shortcut["trigger_id"],
        view={
            "type": "modal",
            "title": {"type": "plain_text", "text": "Link to Ninety.io Item"},
            "submit": {"type": "plain_text", "text": "Link"},
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"Link this message to an existing item:\n>{message_text}"
                    }
                },
                {
                    "type": "input",
                    "block_id": "search",
                    "label": {"type": "plain_text", "text": "Search Items"},
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "search_input",
                        "placeholder": {"type": "plain_text", "text": "Search by title or ID"}
                    }
                }
            ]
        }
    )

@app.shortcut("add_as_comment")
def handle_add_as_comment(ack, shortcut, client):
    """Handle adding messages as comments"""
    ack()
    
    message_text = shortcut["message"]["text"]
    message_link = shortcut["message"]["permalink"]
    user = shortcut["user"]["id"]
    
    # Show item selection modal
    client.views_open(
        trigger_id=shortcut["trigger_id"],
        view={
            "type": "modal",
            "title": {"type": "plain_text", "text": "Add as Comment"},
            "submit": {"type": "plain_text", "text": "Add"},
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"Add this message as a comment:\n>{message_text}"
                    }
                },
                {
                    "type": "input",
                    "block_id": "item_search",
                    "label": {"type": "plain_text", "text": "Select Item"},
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "search_input",
                        "placeholder": {"type": "plain_text", "text": "Search by title or ID"}
                    }
                }
            ]
        }
    )

@app.shortcut("add_as_milestone")
def handle_add_as_milestone(ack, shortcut, client):
    """Handle adding messages as Rock milestones"""
    ack()
    
    message_text = shortcut["message"]["text"]
    message_link = shortcut["message"]["permalink"]
    
    # Show Rock selection modal
    client.views_open(
        trigger_id=shortcut["trigger_id"],
        view={
            "type": "modal",
            "title": {"type": "plain_text", "text": "Add as Rock Milestone"},
            "submit": {"type": "plain_text", "text": "Add"},
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"Add this message as a milestone:\n>{message_text}"
                    }
                },
                {
                    "type": "input",
                    "block_id": "rock_search",
                    "label": {"type": "plain_text", "text": "Select Rock"},
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "search_input",
                        "placeholder": {"type": "plain_text", "text": "Search Rocks"}
                    }
                },
                {
                    "type": "input",
                    "block_id": "due_date",
                    "label": {"type": "plain_text", "text": "Milestone Due Date"},
                    "element": {
                        "type": "datepicker",
                        "initial_date": datetime.now().strftime("%Y-%m-%d")
                    }
                }
            ]
        }
    )

@app.shortcut("update_definition_of_done")
def handle_update_definition_of_done(ack, shortcut, client):
    """Handle updating Rock's Definition of Done"""
    ack()
    
    message_text = shortcut["message"]["text"]
    message_link = shortcut["message"]["permalink"]
    
    # Show Rock selection modal
    client.views_open(
        trigger_id=shortcut["trigger_id"],
        view={
            "type": "modal",
            "title": {"type": "plain_text", "text": "Update Definition of Done"},
            "submit": {"type": "plain_text", "text": "Update"},
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"Add this message to Definition of Done:\n>{message_text}"
                    }
                },
                {
                    "type": "input",
                    "block_id": "rock_search",
                    "label": {"type": "plain_text", "text": "Select Rock"},
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "search_input",
                        "placeholder": {"type": "plain_text", "text": "Search Rocks"}
                    }
                }
            ]
        }
    )

# Add view submission handlers
@app.view("create_from_message")
def handle_create_submission(ack, body, client):
    """Handle submission of create item modal"""
    ack()
    
    values = body["view"]["state"]["values"]
    item_type = values["item_type"]["static_select"]["selected_option"]["value"]
    title = values["title"]["plain_text_input"]["value"]
    team = values["team"]["static_select"]["selected_option"]["value"]
    
    try:
        ninety = get_ninety_instance()
        if item_type == "rock":
            result = ninety.create_rock(title, team=team)
        elif item_type == "todo":
            result = ninety.create_todo(title, team=team)
        elif item_type == "issue":
            result = ninety.create_issue(title, team=team)
        else:  # headline
            result = ninety.create_headline(title, team=team)
        
        # Notify user of success
        client.chat_postEphemeral(
            channel=body["user"]["id"],
            user=body["user"]["id"],
            text=f"✅ Created {item_type}: {result['title']}\n{result.get('url', '')}"
        )
    except Exception as e:
        client.chat_postEphemeral(
            channel=body["user"]["id"],
            user=body["user"]["id"],
            text=f"❌ Error creating {item_type}: {str(e)}"
        )

# Add other view submission handlers similarly
# ... existing code ... 