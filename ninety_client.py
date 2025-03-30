import requests
from requests.exceptions import RequestException
from typing import Optional, Dict, List, Union
from config import NINETY_API_KEY, NINETY_ORGANIZATION_ID, NINETY_API_BASE_URL

class NinetyError(Exception):
    """Base exception for Ninety.io API errors"""
    pass

class NinetyClient:
    def __init__(self):
        self.headers = {
            'Authorization': f'Bearer {NINETY_API_KEY}',
            'Content-Type': 'application/json'
        }
        self.base_url = NINETY_API_BASE_URL
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make a request to the Ninety.io API with error handling"""
        url = f'{self.base_url}{endpoint}'
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                raise NinetyError("Rate limit exceeded. Please try again later.")
            elif e.response.status_code == 401:
                raise NinetyError("Invalid API key. Please check your credentials.")
            elif e.response.status_code == 403:
                raise NinetyError("Insufficient permissions to perform this action.")
            else:
                raise NinetyError(f"API request failed: {e.response.text}")
        except requests.exceptions.RequestException as e:
            raise NinetyError(f"Network error: {str(e)}")

    def create_headline(self, title: str, description: Optional[str] = None, 
                       due_date: Optional[str] = None, assignee_id: Optional[str] = None) -> Dict:
        """Create a new headline in Ninety.io"""
        endpoint = f'/organizations/{NINETY_ORGANIZATION_ID}/headlines'
        payload = {
            'title': title,
            'description': description,
            'due_date': due_date,
            'assignee_id': assignee_id
        }
        return self._make_request('POST', endpoint, json=payload)

    def create_todo(self, title: str, description: Optional[str] = None, 
                   priority: Optional[str] = None, due_date: Optional[str] = None,
                   assignee_id: Optional[str] = None) -> Dict:
        """Create a new to-do in Ninety.io"""
        endpoint = f'/organizations/{NINETY_ORGANIZATION_ID}/todos'
        payload = {
            'title': title,
            'description': description,
            'priority': priority,
            'due_date': due_date,
            'assignee_id': assignee_id
        }
        return self._make_request('POST', endpoint, json=payload)

    def create_issue(self, title: str, description: Optional[str] = None, 
                    priority: Optional[str] = None, status: Optional[str] = None,
                    due_date: Optional[str] = None, assignee_id: Optional[str] = None,
                    labels: Optional[List[str]] = None) -> Dict:
        """Create a new issue in Ninety.io"""
        endpoint = f'/organizations/{NINETY_ORGANIZATION_ID}/issues'
        payload = {
            'title': title,
            'description': description,
            'priority': priority,
            'status': status,
            'due_date': due_date,
            'assignee_id': assignee_id,
            'labels': labels
        }
        return self._make_request('POST', endpoint, json=payload)

    def search_items(self, query: str, item_type: Optional[str] = None,
                    status: Optional[str] = None, priority: Optional[str] = None,
                    assignee_id: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Search for items in Ninety.io with advanced filtering"""
        endpoint = f'/organizations/{NINETY_ORGANIZATION_ID}/search'
        params = {
            'q': query,
            'type': item_type,
            'status': status,
            'priority': priority,
            'assignee_id': assignee_id,
            'limit': limit
        }
        return self._make_request('GET', endpoint, params=params)

    def update_item(self, item_id: str, item_type: str, updates: Dict) -> Dict:
        """Update an existing item in Ninety.io"""
        endpoint = f'/organizations/{NINETY_ORGANIZATION_ID}/{item_type}/{item_id}'
        return self._make_request('PATCH', endpoint, json=updates)

    def get_item(self, item_id: str, item_type: str) -> Dict:
        """Get a specific item from Ninety.io"""
        endpoint = f'/organizations/{NINETY_ORGANIZATION_ID}/{item_type}/{item_id}'
        return self._make_request('GET', endpoint)

    def delete_item(self, item_id: str, item_type: str) -> bool:
        """Delete an item from Ninety.io"""
        endpoint = f'/organizations/{NINETY_ORGANIZATION_ID}/{item_type}/{item_id}'
        self._make_request('DELETE', endpoint)
        return True

    def add_comment(self, item_id: str, item_type: str, comment: str) -> Dict:
        """Add a comment to an item in Ninety.io"""
        endpoint = f'/organizations/{NINETY_ORGANIZATION_ID}/{item_type}/{item_id}/comments'
        payload = {'content': comment}
        return self._make_request('POST', endpoint, json=payload)

    def get_comments(self, item_id: str, item_type: str) -> List[Dict]:
        """Get comments for an item in Ninety.io"""
        endpoint = f'/organizations/{NINETY_ORGANIZATION_ID}/{item_type}/{item_id}/comments'
        return self._make_request('GET', endpoint) 