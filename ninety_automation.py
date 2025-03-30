from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from typing import Optional, Dict, List, Union
import time
import os
from datetime import datetime, timedelta
from config import NINETY_EMAIL, NINETY_PASSWORD
import logging
from functools import lru_cache
from monitoring import (
    track_timing,
    rate_limit,
    track_ninety_request,
    log_error,
    logger
)
from selenium.webdriver.support.select import Select

class NinetyAutomation:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.base_url = "https://app.ninety.io"
        self.setup_driver()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    @track_timing("setup_driver")
    def setup_driver(self):
        """Set up the Chrome WebDriver with appropriate options"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode by default
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        self.driver.maximize_window()
        logger.info("webdriver_setup_success")

    @track_timing("login")
    @rate_limit(calls=10, period=60)  # Limit login attempts
    def login(self):
        """Log in to Ninety.io"""
        try:
            track_ninety_request("login", "attempt")
            self.driver.get(f"{self.base_url}/login")
            
            # Wait for and fill in email
            email_field = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
            )
            email_field.send_keys(NINETY_EMAIL)
            
            # Fill in password
            password_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            password_field.send_keys(NINETY_PASSWORD)
            
            # Click login button
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            
            # Wait for successful login
            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".dashboard-container"))
            )
            track_ninety_request("login", "success")
            logger.info("login_success", email=NINETY_EMAIL)
            return True
        except TimeoutException:
            track_ninety_request("login", "failure")
            log_error("Login failed - timeout waiting for elements", {"action": "login"})
            raise Exception("Login failed - timeout waiting for elements")
        except Exception as e:
            track_ninety_request("login", "failure")
            log_error(f"Login failed: {str(e)}", {"action": "login", "email": NINETY_EMAIL})
            raise Exception(f"Login failed: {str(e)}")

    @track_timing("create_headline")
    @rate_limit(calls=50, period=60)
    def create_headline(self, title: str, description: Optional[str] = None) -> Dict:
        """Create a new headline in Ninety.io"""
        try:
            track_ninety_request("create_headline", "attempt")
            self._ensure_logged_in()
            
            # Navigate to headlines section
            self.driver.get(f"{self.base_url}/headlines")
            
            # Click create headline button
            create_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='create-headline-button']"))
            )
            create_button.click()
            
            # Fill in title
            title_field = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-testid='headline-title-input']"))
            )
            title_field.send_keys(title)
            
            # Fill in description if provided
            if description:
                description_field = self.driver.find_element(
                    By.CSS_SELECTOR, "textarea[data-testid='headline-description-input']"
                )
                description_field.send_keys(description)
            
            # Click save button
            save_button = self.driver.find_element(By.CSS_SELECTOR, "button[data-testid='save-headline-button']")
            save_button.click()
            
            # Wait for success message
            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".success-message"))
            )
            
            track_ninety_request("create_headline", "success")
            return {"title": title, "description": description}
        except Exception as e:
            track_ninety_request("create_headline", "failure")
            log_error(f"Failed to create headline: {str(e)}", {"action": "create_headline", "title": title})
            raise Exception(f"Failed to create headline: {str(e)}")

    @track_timing("create_todo")
    @rate_limit(calls=50, period=60)
    def create_todo(self, title: str, description: Optional[str] = None, priority: Optional[str] = None) -> Dict:
        """Create a new to-do in Ninety.io"""
        try:
            track_ninety_request("create_todo", "attempt")
            self._ensure_logged_in()
            
            # Navigate to todos section
            self.driver.get(f"{self.base_url}/todos")
            
            # Click create todo button
            create_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='create-todo-button']"))
            )
            create_button.click()
            
            # Fill in title
            title_field = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-testid='todo-title-input']"))
            )
            title_field.send_keys(title)
            
            # Fill in description if provided
            if description:
                description_field = self.driver.find_element(
                    By.CSS_SELECTOR, "textarea[data-testid='todo-description-input']"
                )
                description_field.send_keys(description)
            
            # Set priority if provided
            if priority:
                priority_dropdown = self.driver.find_element(
                    By.CSS_SELECTOR, "select[data-testid='todo-priority-select']"
                )
                priority_dropdown.click()
                priority_option = self.driver.find_element(
                    By.CSS_SELECTOR, f"option[value='{priority.lower()}']"
                )
                priority_option.click()
            
            # Click save button
            save_button = self.driver.find_element(By.CSS_SELECTOR, "button[data-testid='save-todo-button']")
            save_button.click()
            
            # Wait for success message
            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".success-message"))
            )
            
            track_ninety_request("create_todo", "success")
            return {"title": title, "description": description, "priority": priority}
        except Exception as e:
            track_ninety_request("create_todo", "failure")
            log_error(f"Failed to create todo: {str(e)}", {"action": "create_todo", "title": title})
            raise Exception(f"Failed to create todo: {str(e)}")

    @track_timing("create_issue")
    @rate_limit(calls=50, period=60)
    def create_issue(self, title: str, description: Optional[str] = None, 
                    priority: Optional[str] = None, status: Optional[str] = None) -> Dict:
        """Create a new issue in Ninety.io"""
        try:
            track_ninety_request("create_issue", "attempt")
            self._ensure_logged_in()
            
            # Navigate to issues section
            self.driver.get(f"{self.base_url}/issues")
            
            # Click create issue button
            create_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid='create-issue-button']"))
            )
            create_button.click()
            
            # Fill in title
            title_field = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-testid='issue-title-input']"))
            )
            title_field.send_keys(title)
            
            # Fill in description if provided
            if description:
                description_field = self.driver.find_element(
                    By.CSS_SELECTOR, "textarea[data-testid='issue-description-input']"
                )
                description_field.send_keys(description)
            
            # Set priority if provided
            if priority:
                priority_dropdown = self.driver.find_element(
                    By.CSS_SELECTOR, "select[data-testid='issue-priority-select']"
                )
                priority_dropdown.click()
                priority_option = self.driver.find_element(
                    By.CSS_SELECTOR, f"option[value='{priority.lower()}']"
                )
                priority_option.click()
            
            # Set status if provided
            if status:
                status_dropdown = self.driver.find_element(
                    By.CSS_SELECTOR, "select[data-testid='issue-status-select']"
                )
                status_dropdown.click()
                status_option = self.driver.find_element(
                    By.CSS_SELECTOR, f"option[value='{status.lower()}']"
                )
                status_option.click()
            
            # Click save button
            save_button = self.driver.find_element(By.CSS_SELECTOR, "button[data-testid='save-issue-button']")
            save_button.click()
            
            # Wait for success message
            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".success-message"))
            )
            
            track_ninety_request("create_issue", "success")
            return {"title": title, "description": description, "priority": priority, "status": status}
        except Exception as e:
            track_ninety_request("create_issue", "failure")
            log_error(f"Failed to create issue: {str(e)}", {"action": "create_issue", "title": title})
            raise Exception(f"Failed to create issue: {str(e)}")

    @track_timing("search_items")
    @rate_limit(calls=100, period=60)
    def search_items(self, query: str = "", item_type: Optional[str] = None, workspace_id: Optional[str] = None) -> List[Dict]:
        """Search for items in Ninety.io with workspace support"""
        cache_key = f"{query}:{item_type}:{workspace_id}"
        cached_result = self._get_cached_search(cache_key)
        if cached_result:
            return cached_result
            
        try:
            track_ninety_request("search_items", "attempt")
            self._ensure_logged_in()
            
            # Switch workspace if specified
            if workspace_id and workspace_id != "default":
                self._switch_workspace(workspace_id)
            
            # Navigate to search page
            self.driver.get(f"{self.base_url}/search")
            
            # Enter search query if provided
            if query:
                search_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='search-input']"))
                )
                search_field.clear()
                search_field.send_keys(query)
            
            # Select item type if provided
            if item_type and item_type != "all":
                type_dropdown = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='type-filter']"))
                )
                type_dropdown.click()
                
                type_option = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-value='{item_type}']"))
                )
                type_option.click()
            
            # Wait for results
            time.sleep(2)  # Allow time for search results to update
            
            # Extract results
            results = []
            result_elements = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "[data-testid='search-result-item']"))
            )
            
            for element in result_elements:
                item = {
                    "id": element.get_attribute("data-item-id"),
                    "title": element.find_element(By.CSS_SELECTOR, "[data-testid='item-title']").text,
                    "type": element.get_attribute("data-item-type"),
                    "description": element.find_element(By.CSS_SELECTOR, "[data-testid='item-description']").text,
                    "url": element.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                }
                
                # Get additional details if available
                try:
                    item["status"] = element.find_element(By.CSS_SELECTOR, "[data-testid='item-status']").text
                except NoSuchElementException:
                    pass
                    
                try:
                    item["due_date"] = element.find_element(By.CSS_SELECTOR, "[data-testid='item-due-date']").text
                except NoSuchElementException:
                    pass
                
                results.append(item)
            
            # Cache the results
            self._cache_search_results(cache_key, results)
            track_ninety_request("search_items", "success")
            return results
        except Exception as e:
            track_ninety_request("search_items", "failure")
            log_error(f"Error searching items: {str(e)}", {
                "action": "search_items",
                "query": query,
                "item_type": item_type,
                "workspace_id": workspace_id
            })
            raise Exception(f"Failed to search items: {str(e)}")

    @lru_cache(maxsize=100)
    def _get_cached_search(self, cache_key: str) -> Optional[List[Dict]]:
        """Get cached search results"""
        return getattr(self, f"_search_cache_{cache_key}", None)

    def _cache_search_results(self, cache_key: str, results: List[Dict]) -> None:
        """Cache search results for 5 minutes"""
        setattr(self, f"_search_cache_{cache_key}", results)
        # Schedule cache invalidation
        self._schedule_cache_invalidation(cache_key)

    def _schedule_cache_invalidation(self, cache_key: str) -> None:
        """Schedule cache invalidation after 5 minutes"""
        def invalidate():
            time.sleep(300)  # 5 minutes
            delattr(self, f"_search_cache_{cache_key}")
        
        from threading import Thread
        Thread(target=invalidate, daemon=True).start()

    def attach_conversation(self, item_id: str, item_type: str, conversation_text: str) -> bool:
        """Attach a Slack conversation to a Ninety.io item as a comment."""
        try:
            self._ensure_logged_in()
            
            # Navigate to item
            self._navigate_to_item(item_id, item_type)
            
            # Find and click comment field
            comment_field = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='comment-field']"))
            )
            comment_field.click()
            
            # Add header to conversation
            full_text = f"Slack Conversation (attached {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}):\n\n{conversation_text}"
            
            # Input the conversation text
            comment_field.send_keys(full_text)
            
            # Submit comment
            submit_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='submit-comment']"))
            )
            submit_btn.click()
            
            # Wait for save confirmation
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='comment-success']"))
            )
            
            return True
        except Exception as e:
            self.logger.error(f"Error attaching conversation: {str(e)}")
            raise Exception(f"Failed to attach conversation to {item_type}: {str(e)}")

    def set_due_date(self, item_id: str, item_type: str, due_date: str) -> bool:
        """Set the due date for a Ninety.io item."""
        try:
            self._ensure_logged_in()
            
            # Navigate to item
            self._navigate_to_item(item_id, item_type)
            
            # Find and click due date field
            due_date_field = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='due-date-field']"))
            )
            due_date_field.click()
            
            # Input the due date
            date_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='date']"))
            )
            date_input.clear()
            date_input.send_keys(due_date)
            date_input.send_keys(Keys.RETURN)
            
            # Wait for save confirmation
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='save-success']"))
            )
            
            return True
        except Exception as e:
            self.logger.error(f"Error setting due date: {str(e)}")
            raise Exception(f"Failed to set due date for {item_type}: {str(e)}")

    def subscribe_to_item(self, item_id: str, item_type: str) -> bool:
        """Subscribe to a Ninety.io item to receive notifications."""
        try:
            self._ensure_logged_in()
            
            # Navigate to item
            self._navigate_to_item(item_id, item_type)
            
            # Find and click subscribe button
            subscribe_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='subscribe-button']"))
            )
            subscribe_btn.click()
            
            # Wait for confirmation
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='subscribed-indicator']"))
            )
            
            return True
        except Exception as e:
            self.logger.error(f"Error subscribing to item: {str(e)}")
            raise Exception(f"Failed to subscribe to {item_type}: {str(e)}")

    @lru_cache(maxsize=100)
    def get_item_details(self, item_id: str, item_type: str) -> Dict:
        """Get detailed information about a Ninety.io item for link unfurling"""
        try:
            track_ninety_request("get_item_details", "attempt")
            self._ensure_logged_in()
            
            # Navigate to the item
            self.driver.get(f"{self.base_url}/{item_type}s/{item_id}")
            
            # Wait for item details to load
            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".item-details"))
            )
            
            # Extract item details
            title = self.driver.find_element(By.CSS_SELECTOR, ".item-title").text
            description = self.driver.find_element(By.CSS_SELECTOR, ".item-description").text
            status = self.driver.find_element(By.CSS_SELECTOR, ".item-status").text
            due_date = self.driver.find_element(By.CSS_SELECTOR, ".due-date").text
            assignee = self.driver.find_element(By.CSS_SELECTOR, ".assignee").text
            labels = [label.text for label in self.driver.find_elements(By.CSS_SELECTOR, ".label")]
            
            track_ninety_request("get_item_details", "success")
            return {
                "title": title,
                "description": description,
                "status": status,
                "due_date": due_date,
                "assignee": assignee,
                "labels": labels,
                "type": item_type
            }
        except Exception as e:
            track_ninety_request("get_item_details", "failure")
            log_error(f"Failed to get item details: {str(e)}", {"action": "get_item_details", "item_id": item_id})
            raise Exception(f"Failed to get item details: {str(e)}")

    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()

    def _ensure_logged_in(self):
        """Ensure the user is logged in"""
        if not self.logged_in:
            self.logged_in = self.login()

    def _navigate_to_item(self, item_id: str, item_type: str) -> None:
        """Helper method to navigate to a specific item."""
        try:
            # Construct item URL based on type
            item_type_path = {
                "headline": "headlines",
                "todo": "todos",
                "issue": "issues"
            }.get(item_type.lower())
            
            if not item_type_path:
                raise ValueError(f"Invalid item type: {item_type}")
            
            item_url = f"https://app.ninety.io/{item_type_path}/{item_id}"
            self.driver.get(item_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='item-details']"))
            )
        except Exception as e:
            self.logger.error(f"Error navigating to item: {str(e)}")
            raise Exception(f"Failed to navigate to {item_type}: {str(e)}")

    @lru_cache(maxsize=1)
    def get_workspaces(self) -> List[Dict]:
        """Get list of available Ninety.io workspaces"""
        try:
            track_ninety_request("get_workspaces", "attempt")
            self._ensure_logged_in()
            
            # Navigate to workspaces page
            self.driver.get(f"{self.base_url}/workspaces")
            
            # Wait for workspace list to load
            workspace_elements = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "[data-testid='workspace-item']"))
            )
            
            workspaces = []
            for element in workspace_elements:
                workspace_id = element.get_attribute("data-workspace-id")
                workspace_name = element.find_element(By.CSS_SELECTOR, "[data-testid='workspace-name']").text
                workspaces.append({
                    "id": workspace_id,
                    "name": workspace_name
                })
            
            track_ninety_request("get_workspaces", "success")
            return workspaces
        except Exception as e:
            track_ninety_request("get_workspaces", "failure")
            log_error(f"Error getting workspaces: {str(e)}", {"action": "get_workspaces"})
            raise Exception("Failed to get workspaces")

    def update_item(self, item_id: str, item_type: str, updates: Dict) -> bool:
        """Update an existing Ninety.io item"""
        try:
            self._ensure_logged_in()
            
            # Navigate to item
            self._navigate_to_item(item_id, item_type)
            
            # Click edit button
            edit_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='edit-button']"))
            )
            edit_button.click()
            
            # Update title if provided
            if "title" in updates:
                title_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='title-input']"))
                )
                title_field.clear()
                title_field.send_keys(updates["title"])
            
            # Update description if provided
            if "description" in updates:
                description_field = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='description-input']")
                description_field.clear()
                description_field.send_keys(updates["description"])
            
            # Update status if provided (for issues)
            if "status" in updates:
                status_dropdown = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='status-select']")
                status_dropdown.click()
                
                status_option = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-value='{updates['status']}']"))
                )
                status_option.click()
            
            # Update due date if provided
            if "due_date" in updates:
                due_date_field = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='due-date-input']")
                due_date_field.clear()
                due_date_field.send_keys(updates["due_date"])
                due_date_field.send_keys(Keys.RETURN)
            
            # Click save button
            save_button = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='save-button']")
            save_button.click()
            
            # Wait for success message
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='success-message']"))
            )
            
            return True
        except Exception as e:
            self.logger.error(f"Error updating item: {str(e)}")
            raise Exception(f"Failed to update {item_type}: {str(e)}")

    def _switch_workspace(self, workspace_id: str) -> None:
        """Switch to a different workspace"""
        try:
            # Click workspace switcher
            workspace_switcher = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='workspace-switcher']"))
            )
            workspace_switcher.click()
            
            # Select target workspace
            workspace_option = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, f"[data-workspace-id='{workspace_id}']"))
            )
            workspace_option.click()
            
            # Wait for workspace switch to complete
            time.sleep(2)  # Allow time for workspace switch
        except Exception as e:
            self.logger.error(f"Error switching workspace: {str(e)}")
            raise Exception(f"Failed to switch workspace: {str(e)}")

    def __del__(self):
        """Cleanup resources"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("webdriver_cleanup_success")
            except Exception as e:
                log_error(e, {"action": "driver_cleanup"})

    def create_rock(self, title, description=None, due_date=None):
        """Create a new Rock in Ninety.io"""
        try:
            self.driver.find_element(By.LINK_TEXT, "Rocks").click()
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Create Rock')]"))
            ).click()
            
            # Fill in Rock details
            title_input = self.driver.find_element(By.NAME, "title")
            title_input.send_keys(title)
            
            if description:
                desc_input = self.driver.find_element(By.NAME, "description")
                desc_input.send_keys(description)
            
            if due_date:
                due_date_input = self.driver.find_element(By.NAME, "dueDate")
                due_date_input.send_keys(due_date)
            
            # Submit the form
            submit_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Save')]")
            submit_button.click()
            
            # Wait for success notification
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "notification-success"))
            )
            
            # Get the created Rock's URL
            rock_url = self.driver.current_url
            return {"title": title, "url": rock_url}
            
        except Exception as e:
            logger.error(f"Error creating Rock: {str(e)}")
            raise Exception(f"Failed to create Rock: {str(e)}")

    def get_rock_details(self, rock_id):
        """Get details of a specific Rock"""
        try:
            self.driver.get(f"{self.base_url}/rocks/{rock_id}")
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "rock-details"))
            )
            
            title = self.driver.find_element(By.CLASS_NAME, "rock-title").text
            status = self.driver.find_element(By.CLASS_NAME, "rock-status").text
            due_date = self.driver.find_element(By.CLASS_NAME, "rock-due-date").text
            
            return {
                "id": rock_id,
                "title": title,
                "status": status,
                "due_date": due_date,
                "url": self.driver.current_url
            }
        except Exception as e:
            logger.error(f"Error getting Rock details: {str(e)}")
            raise Exception(f"Failed to get Rock details: {str(e)}")

    def update_rock(self, rock_id, updates):
        """Update a Rock's details"""
        try:
            self.driver.get(f"{self.base_url}/rocks/{rock_id}")
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "rock-details"))
            )
            
            # Click edit button
            edit_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Edit')]")
            edit_button.click()
            
            if "title" in updates:
                title_input = self.driver.find_element(By.NAME, "title")
                title_input.clear()
                title_input.send_keys(updates["title"])
            
            if "description" in updates:
                desc_input = self.driver.find_element(By.NAME, "description")
                desc_input.clear()
                desc_input.send_keys(updates["description"])
            
            if "due_date" in updates:
                due_date_input = self.driver.find_element(By.NAME, "dueDate")
                due_date_input.clear()
                due_date_input.send_keys(updates["due_date"])
            
            if "status" in updates:
                status_select = Select(self.driver.find_element(By.NAME, "status"))
                status_select.select_by_visible_text(updates["status"])
            
            # Save changes
            save_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Save')]")
            save_button.click()
            
            # Wait for success notification
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "notification-success"))
            )
            
            return {"message": "Rock updated successfully"}
            
        except Exception as e:
            logger.error(f"Error updating Rock: {str(e)}")
            raise Exception(f"Failed to update Rock: {str(e)}")

    def search_rocks(self, query=None, status=None):
        """Search for Rocks with optional filters"""
        try:
            self.driver.get(f"{self.base_url}/rocks")
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "rocks-list"))
            )
            
            if query:
                search_input = self.driver.find_element(By.NAME, "search")
                search_input.send_keys(query)
                time.sleep(1)  # Wait for search results
            
            if status:
                status_filter = Select(self.driver.find_element(By.NAME, "status-filter"))
                status_filter.select_by_visible_text(status)
                time.sleep(1)  # Wait for filter to apply
            
            rocks = []
            rock_elements = self.driver.find_elements(By.CLASS_NAME, "rock-item")
            
            for element in rock_elements:
                rock_data = {
                    "title": element.find_element(By.CLASS_NAME, "rock-title").text,
                    "status": element.find_element(By.CLASS_NAME, "rock-status").text,
                    "due_date": element.find_element(By.CLASS_NAME, "rock-due-date").text,
                    "url": element.find_element(By.TAG_NAME, "a").get_attribute("href")
                }
                rocks.append(rock_data)
            
            return rocks
            
        except Exception as e:
            logger.error(f"Error searching Rocks: {str(e)}")
            raise Exception(f"Failed to search Rocks: {str(e)}") 