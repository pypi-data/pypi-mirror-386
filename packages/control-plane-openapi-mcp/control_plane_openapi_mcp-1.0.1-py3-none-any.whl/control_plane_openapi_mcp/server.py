import logging
from .config import mcp
from .tools import *  # Import all tools to register them
from .prompts import *  # Import all prompts to register them

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point for the MCP server."""
    try:
        logger.info("Starting Control Plane OpenAPI MCP server...")
        mcp.run(transport='stdio')
    except Exception as e:
        logger.error(f"Failed to start MCP server: {e}")
        raise


if __name__ == "__main__":
    main()
