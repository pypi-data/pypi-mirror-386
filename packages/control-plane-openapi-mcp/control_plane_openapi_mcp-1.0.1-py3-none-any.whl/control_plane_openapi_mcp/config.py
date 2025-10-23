import os
import configparser
import logging
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

def get_control_plane_url() -> str:
    """
    Get Control Plane URL from environment variable or credentials file.
    
    Returns:
        str: Control Plane URL
    """
    # First try environment variable
    cp_url = os.getenv('CONTROL_PLANE_URL', '')
    
    if cp_url:
        # Ensure URL has proper format
        if not (cp_url.startswith("http://") or cp_url.startswith("https://")):
            cp_url = f"https://{cp_url}"
        return cp_url.rstrip("/")
    
    # Try to load from credentials file using profile
    profile = os.getenv("FACETS_PROFILE", "default")
    try:
        config = configparser.ConfigParser()
        credentials_path = os.path.expanduser("~/.facets/credentials")
        config.read(credentials_path)
        
        if config.has_section(profile):
            cp_url = config.get(profile, "control_plane_url", fallback="")
            if cp_url:
                logger.info(f"Loaded Control Plane URL from profile: {profile}")
                # Ensure URL has proper format
                if not (cp_url.startswith("http://") or cp_url.startswith("https://")):
                    cp_url = f"https://{cp_url}"
                return cp_url.rstrip("/")
        else:
            logger.debug(f"Profile '{profile}' not found in credentials file")
    except Exception as e:
        logger.debug(f"Could not read credentials file: {e}")
    
    # Fallback to demo instance
    logger.info("Using demo Control Plane URL")
    return "https://facetsdemo.console.facets.cloud"

# Configuration
CONTROL_PLANE_URL = get_control_plane_url()
CACHE_TTL = int(os.getenv('CACHE_TTL', '3600'))  # 1 hour default
SPEC_ID = "facets-control-plane"

# Authentication configuration (optional)
FACETS_USERNAME = os.getenv('FACETS_USERNAME', '')
FACETS_TOKEN = os.getenv('FACETS_TOKEN', '')
FACETS_PROFILE = os.getenv('FACETS_PROFILE', 'default')

# Derived URLs
OPENAPI_URL = f"{CONTROL_PLANE_URL}/v3/api-docs"

# Initialize MCP server
mcp = FastMCP("Facets Control Plane OpenAPI")
