import json
import os
import time
import webbrowser
from typing import Dict, List, Optional
from loguru import logger
import requests

# Configuration - support environment variable override
DEFAULT_POLARION_BASE_URL = "http://dev.polarion.atoms.tech/polarion"
POLARION_BASE_URL = os.getenv("POLARION_BASE_URL", DEFAULT_POLARION_BASE_URL)
LOGIN_URL = POLARION_BASE_URL
TOKEN_PAGE_URL = f"{POLARION_BASE_URL}/#/user_tokens?id=admin"
TOKEN_FILE = "polarion_token.json"

REQUEST_TIMEOUT_SECONDS = 8
WORK_ITEM_MIN_FIELDS = "id,title,type,description"

# Log the configured URL on module load
logger.info(f"Polarion MCP Server configured for: {POLARION_BASE_URL}")
if POLARION_BASE_URL != DEFAULT_POLARION_BASE_URL:
    logger.info(f"Using custom URL from POLARION_BASE_URL environment variable")


class PolarionClient:
    def __init__(self):
        self.session = requests.Session()
        self.token = None
    
    def _ensure_token(self):
        if not self.token:
            self.token = self.load_token()
        if not self.token:
            raise Exception("No token available. Please set or generate a token first.")
    
    def _handle_api_response(self, response, operation_name: str):
        """Handle API response and provide meaningful error messages with workflow guidance."""
        if response.status_code == 200:
            return True
        
        if response.status_code == 401:
            raise Exception(f"""
Authentication failed: Token may be expired or invalid.

NEXT STEPS:
1. Use check_polarion_status() to verify token status
2. Use open_polarion_login() to get new token  
3. Use set_polarion_token() to update token
4. Then retry {operation_name}
""")
        elif response.status_code == 403:
            raise Exception(f"""
Access denied: You don't have permission to {operation_name}.

TROUBLESHOOTING:
1. Verify you have access to this project/resource
2. Check if project_id is correct using get_polarion_projects()
3. Contact administrator for permissions
""")
        elif response.status_code == 404:
            raise Exception(f"""
Resource not found: {operation_name} failed.

TROUBLESHOOTING:
1. Use get_polarion_projects() to verify project exists
2. Use get_polarion_work_items() to discover available work items
3. Check spelling of IDs and names - they are case-sensitive
4. For documents: Space names must be provided by user or found in work item references
""")
        elif response.status_code == 500:
            raise Exception(f"""
Polarion server error: {operation_name} failed.

NEXT STEPS:
1. Wait a moment and retry
2. Check if Polarion instance is accessible
3. Try with smaller page sizes or simpler queries
""")
        else:
            raise Exception(f"API error {response.status_code}: {response.text}")
    
    def _headers(self) -> Dict[str, str]:
        return {
            'Authorization': f'Bearer {self.token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    
    def open_login_page(self) -> str:
        """Open Polarion login page in user's browser for manual authentication"""
        try:
            webbrowser.open(LOGIN_URL)
            
            return json.dumps({
                "status": "success",
                "message": f"Polarion login page opened in your browser: {LOGIN_URL}",
                "instructions": [
                    "1. Complete the login form in your browser",
                    "2. After successful login, navigate to: " + TOKEN_PAGE_URL,
                    "3. Generate a new token manually",
                    "4. Copy the token and use it with the 'set_polarion_token' command"
                ],
                "login_url": LOGIN_URL,
                "token_page_url": TOKEN_PAGE_URL,
                "note": "If you get an 'Internal server error', try refreshing the page or check if the Polarion instance is accessible"
            }, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to open login page: {e}")
            return json.dumps({
                "status": "error",
                "message": f"Failed to open login page: {e}",
                "manual_url": LOGIN_URL
            }, indent=2)
    
    def set_token_manually(self, token: str) -> str:
        """Set token manually (after user generates it in browser)"""
        try:
            self.token = token
            self.save_token(token)
            return json.dumps({
                "status": "success",
                "message": "Token set successfully. Please test it by fetching work items or projects.",
                "token_preview": f"{token[:10]}...{token[-10:]}"
            }, indent=2)
        except Exception as e:
            logger.error(f"Failed to set token: {e}")
            return json.dumps({
                "status": "error",
                "message": f"Failed to set token: {e}"
            }, indent=2)
    
    def save_token(self, token: str):
        """Save token to file"""
        try:
            token_data = {"token": token, "generated_at": time.time()}
            with open(TOKEN_FILE, 'w') as f:
                json.dump(token_data, f)
        except Exception as e:
            logger.error(f"Failed to save token: {e}")
    
    def load_token(self) -> Optional[str]:
        """Load token from file"""
        try:
            if os.path.exists(TOKEN_FILE):
                with open(TOKEN_FILE, 'r') as f:
                    token_data = json.load(f)
                    return token_data.get("token")
        except Exception as e:
            logger.error(f"Failed to load token: {e}")
        return None
    
    def get_projects(self, limit: int = 10) -> List[Dict]:
        """Fetch projects from Polarion REST API (lightweight fields)."""
        try:
            self._ensure_token()
            api_url = f"{POLARION_BASE_URL}/rest/v1/projects"
            params = {
                'fields[projects]': '@basic',
                'page[size]': limit
            }
            response = self.session.get(api_url, params=params, headers=self._headers(), timeout=REQUEST_TIMEOUT_SECONDS)
            self._handle_api_response(response, "fetch projects")
            data = response.json()
            projects = (data.get('data') or [])[:limit]
            logger.info(f"Fetched {len(projects)} projects")
            return projects
        except Exception as e:
            logger.error(f"Failed to fetch projects: {e}")
            return []

    def get_project(self, project_id: str, fields: str = "@basic") -> Optional[Dict]:
        """Fetch specific project details from Polarion REST API."""
        try:
            self._ensure_token()
            api_url = f"{POLARION_BASE_URL}/rest/v1/projects/{project_id}"
            params = {'fields[projects]': fields}
            response = self.session.get(api_url, params=params, headers=self._headers(), timeout=REQUEST_TIMEOUT_SECONDS)
            if response.status_code == 404:
                logger.warning(f"Project not found: {project_id}")
                return None
            self._handle_api_response(response, f"fetch project {project_id}")
            project_data = response.json()
            logger.info(f"Fetched project: {project_id}")
            return project_data
        except Exception as e:
            logger.error(f"Failed to fetch project {project_id}: {e}")
            return None

    def get_work_items(self, project_id: str, limit: int = 10, query: str = "") -> List[Dict]:
        """Fetch work items (minimal fields). Parameters: project_id, limit, optional query."""
        try:
            self._ensure_token()
            api_url = f"{POLARION_BASE_URL}/rest/v1/projects/{project_id}/workitems"
            params = {
                'fields[workitems]': WORK_ITEM_MIN_FIELDS,
                'page[size]': limit
            }
            if query:
                params['query'] = query
            response = self.session.get(api_url, params=params, headers=self._headers(), timeout=REQUEST_TIMEOUT_SECONDS)
            self._handle_api_response(response, f"fetch work items from project {project_id}")
            data = response.json()
            work_items = (data.get('data') or [])[:limit]
            logger.info(f"Fetched {len(work_items)} work items from {project_id}")
            return work_items
        except Exception as e:
            logger.error(f"Failed to fetch work items from {project_id}: {e}")
            return []
    
    def get_work_item(self, project_id: str, work_item_id: str, fields: str = "@basic") -> Optional[Dict]:
        """Fetch a specific work item by ID from Polarion REST API."""
        try:
            self._ensure_token()
            api_url = f"{POLARION_BASE_URL}/rest/v1/projects/{project_id}/workitems/{work_item_id}"
            params = {'fields[workitems]': fields}
            response = self.session.get(api_url, params=params, headers=self._headers(), timeout=REQUEST_TIMEOUT_SECONDS)
            if response.status_code == 404:
                logger.warning(f"Work item not found: {work_item_id} in project: {project_id}")
                return None
            self._handle_api_response(response, f"fetch work item {work_item_id} from project {project_id}")
            work_item_data = response.json()
            logger.info(f"Fetched work item: {work_item_id} from project: {project_id}")
            return work_item_data
        except Exception as e:
            logger.error(f"Failed to fetch work item {work_item_id} from project {project_id}: {e}")
            return None

    def get_document(self, project_id: str, space_id: str, document_name: str, fields: str = "@basic") -> Optional[Dict]:
        """Fetch a specific document from Polarion REST API."""
        try:
            self._ensure_token()
            api_url = f"{POLARION_BASE_URL}/rest/v1/projects/{project_id}/spaces/{space_id}/documents/{document_name}"
            params = {'fields[documents]': fields}
            response = self.session.get(api_url, params=params, headers=self._headers(), timeout=REQUEST_TIMEOUT_SECONDS)
            if response.status_code == 404:
                logger.warning(f"Document not found: {document_name} in space: {space_id} of project: {project_id}")
                return None
            self._handle_api_response(response, f"fetch document {document_name} from space {space_id} in project {project_id}")
            document_data = response.json()
            logger.info(f"Fetched document: {document_name} from space: {space_id} in project: {project_id}")
            return document_data
        except Exception as e:
            logger.error(f"Failed to fetch document {document_name} from space {space_id} in project {project_id}: {e}")
            return None
