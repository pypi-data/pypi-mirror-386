import os
import configparser
import requests
from requests.auth import HTTPBasicAuth
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class ApiClient:
    """Client for making authenticated requests to Facets Control Plane API."""
    
    def __init__(self):
        self.cp_url: Optional[str] = None
        self.username: Optional[str] = None
        self.token: Optional[str] = None
        self.initialized = False
    
    def set_client_config(self, url: str, username: str, token: str):
        """Set client configuration."""
        self.cp_url = url
        self.username = username
        self.token = token
        self.initialized = True
    
    def initialize(self) -> Tuple[str, str, str, str]:
        """
        Initialize configuration from environment variables or credentials file.
        
        Returns:
            tuple: containing cp_url, username, token, and profile.
            
        Raises:
            ValueError: If required credentials are missing.
        """
        profile = os.getenv("FACETS_PROFILE", "default")
        cp_url = os.getenv("CONTROL_PLANE_URL", "")
        username = os.getenv("FACETS_USERNAME", "")
        token = os.getenv("FACETS_TOKEN", "")
        
        # Try to load from credentials file if env vars not set
        if profile and not (cp_url and username and token):
            try:
                config = configparser.ConfigParser()
                config.read(os.path.expanduser("~/.facets/credentials"))
                
                if config.has_section(profile):
                    cp_url = config.get(profile, "control_plane_url", fallback=cp_url)
                    username = config.get(profile, "username", fallback=username)
                    token = config.get(profile, "token", fallback=token)
                    logger.info(f"Loaded credentials from profile: {profile}")
                else:
                    logger.warning(f"Profile '{profile}' not found in credentials file")
            except Exception as e:
                logger.warning(f"Could not read credentials file: {e}")
        
        if not (cp_url and username and token):
            raise ValueError(
                "Control plane URL, username, and token are required. "
                "Set CONTROL_PLANE_URL, FACETS_USERNAME, FACETS_TOKEN environment variables "
                "or configure ~/.facets/credentials file."
            )
        
        # Ensure cp_url has https:// prefix
        if not (cp_url.startswith("http://") or cp_url.startswith("https://")):
            cp_url = f"https://{cp_url}"
        
        # Remove trailing slash if present
        cp_url = cp_url.rstrip("/")
        
        self.set_client_config(cp_url, username, token)
        logger.info(f"API client initialized for {cp_url}")
        
        return cp_url, username, token, profile
    
    def get(self, path: str, timeout: int = 30) -> requests.Response:
        """
        Make a GET request to the Control Plane API.
        
        Args:
            path: API path (e.g., '/cc-ui/v1/stacks/my-stack')
            timeout: Request timeout in seconds
            
        Returns:
            requests.Response object
            
        Raises:
            ValueError: If client not initialized
            requests.RequestException: If request fails
        """
        if not self.initialized:
            raise ValueError("Client not initialized. Call initialize() first.")
        
        # Ensure path starts with /
        if not path.startswith('/'):
            path = f'/{path}'
        
        url = f"{self.cp_url}{path}"
        auth = HTTPBasicAuth(self.username, self.token)
        
        logger.debug(f"Making GET request to: {url}")
        
        try:
            response = requests.get(
                url,
                auth=auth,
                timeout=timeout,
                headers={
                    'Accept': 'application/json',
                    'User-Agent': 'control-plane-openapi-mcp/1.0.0'
                }
            )
            
            logger.info(f"GET {path} -> {response.status_code}")
            return response
            
        except requests.RequestException as e:
            logger.error(f"Request failed for {path}: {e}")
            raise


# Global client instance
api_client = ApiClient()
