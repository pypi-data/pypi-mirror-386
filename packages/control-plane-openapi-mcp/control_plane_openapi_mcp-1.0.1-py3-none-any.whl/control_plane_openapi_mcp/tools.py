import json
import logging
import os

from .config import mcp, OPENAPI_URL, CACHE_TTL, SPEC_ID
from .core.service import OpenAPIService
from .utils.client import api_client
from .utils.schema_extractor import create_safe_operation_output

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the OpenAPI service
openapi_service = OpenAPIService(OPENAPI_URL, SPEC_ID, CACHE_TTL)

# Initialize API client (optional - only for call_control_plane_api tool)
api_client_available = False
try:
    api_client.initialize()
    api_client_available = True
    logger.info("API client initialized successfully")
except Exception as e:
    logger.debug(f"API client initialization failed: {e}")
    logger.info("API client not available - only OpenAPI exploration tools will work")


@mcp.resource(uri="resource://control_plane_api_knowledge", name="Control Plane API Knowledge Base")
def call_always_for_instruction() -> str:
    return FIRST_STEP_get_api_script_guide()


@mcp.tool()
def FIRST_STEP_get_api_script_guide() -> str:
    """
    <important>ALWAYS Call this tool first before calling any other tool of this mcp.</important>
    Loads the API script generation guide that contains comprehensive instructions for creating 
    scripts that interact with Control Plane APIs.

    Returns:
        str: A JSON string containing the content of the API script guide.
    """
    try:
        # Get the directory where this file is located
        current_dir = os.path.dirname(__file__)
        guide_path = os.path.join(current_dir, "prompts", "api_script_guide.md")
        
        # Read the guide content
        with open(guide_path, 'r', encoding='utf-8') as f:
            guide_content = f.read()
        
        return json.dumps({
            "success": True,
            "message": "API script guide loaded successfully.",
            "instructions": "Inform User: API script guide loaded successfully.",
            "data": {
                "api_script_guide.md": guide_content
            }
        }, indent=2)
    
    except FileNotFoundError:
        return json.dumps({
            "success": False,
            "message": "API script guide file not found.",
            "error": f"Could not find api_script_guide.md at {guide_path}"
        }, indent=2)
    
    except Exception as e:
        return json.dumps({
            "success": False,
            "message": "Failed to load API script guide.",
            "error": str(e)
        }, indent=2)


@mcp.tool()
def refresh_api_catalog() -> str:
    """
    <important>Make Sure you have Called FIRST_STEP_get_api_script_guide first before this tool.</important>
    Refresh the API catalog by fetching the latest OpenAPI specification.
    
    Returns:
        str: Success message confirming the catalog has been refreshed.
    """
    try:
        openapi_service.refresh()
        return json.dumps({
            "success": True,
            "message": "API catalog refreshed successfully"
        })
    except Exception as e:
        logger.error(f"Failed to refresh API catalog: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })


@mcp.tool()
def search_api_operations(query: str) -> str:
    """
    <important>Make Sure you have Called FIRST_STEP_get_api_script_guide first before this tool.</important>
    Search for operations across the OpenAPI specification using fuzzy matching.
    
    Note: Only searches through active (non-deprecated) operations.
    
    Args:
        query (str): Search query to match against operation summaries, descriptions, tags, and operation IDs.
    
    Returns:
        str: JSON string containing matching operations with their details.
    """
    try:
        operations = openapi_service.search_operations(query)
        # Simplified serialization to avoid JsonRef issues
        serialized_operations = []
        for op in operations:
            serialized_operations.append({
                "path": op.path,
                "method": op.method,
                "spec_id": op.spec_id,
                "uri": op.uri,
                "operation_summary": op.operation.get('summary', ''),
                "operation_description": op.operation.get('description', ''),
                "operation_id": op.operation.get('operationId', ''),
                "tags": op.operation.get('tags', [])
            })

        return json.dumps({
            "operations": serialized_operations
        }, indent=2)
    except Exception as e:
        logger.error(f"Failed to search API operations: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })


@mcp.tool()
def search_api_schemas(query: str) -> str:
    """
    <important>Make Sure you have Called FIRST_STEP_get_api_script_guide first before this tool.</important>
    Search for schemas across the OpenAPI specification using fuzzy matching.
    
    Args:
        query (str): Search query to match against schema names and descriptions.
    
    Returns:
        str: JSON string containing matching schemas with their details.
    """
    try:
        schemas = openapi_service.search_schemas(query)
        return json.dumps({
            "schemas": [schema.model_dump() for schema in schemas]
        }, indent=2)
    except Exception as e:
        logger.error(f"Failed to search API schemas: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })


def _format_operation_response(operation) -> str:
    """
    Helper method to format operation response with safe serialization.
    
    Args:
        operation: The operation object to format
    
    Returns:
        str: JSON string containing the formatted operation
    """
    if operation:
        # Get components schemas for matching inline schemas
        components_schemas = openapi_service.get_components_schemas()

        # Create a safe serializable version with schema names included
        safe_operation_data = create_safe_operation_output(
            operation.operation,
            components_schemas
        )

        # Build the complete response
        safe_operation = {
            "path": operation.path,
            "method": operation.method,
            "spec_id": operation.spec_id,
            "uri": operation.uri,
            "operation": safe_operation_data
        }
        return json.dumps(safe_operation, indent=2)
    else:
        return json.dumps(None)


@mcp.tool()
def load_api_operation_by_operationId(operation_id: str) -> str:
    """
    <important>Make Sure you have Called FIRST_STEP_get_api_script_guide first before this tool.</important>
    Load a specific operation by its operationId.
    
    Args:
        operation_id (str): The unique operation ID to load.
    
    Returns:
        str: JSON string containing the complete operation details or null if not found.
    """
    try:
        operation = openapi_service.find_operation_by_id(operation_id)
        return _format_operation_response(operation)
    except Exception as e:
        logger.error(f"Failed to load operation by ID: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })


@mcp.tool()
def load_api_operation_by_path_and_method(path: str, method: str) -> str:
    """
    <important>Make Sure you have Called FIRST_STEP_get_api_script_guide first before this tool.</important>
    Load a specific operation by its path and HTTP method.
    
    Args:
        path (str): The API endpoint path (e.g., '/cc-ui/v1/stacks/{stackName}').
        method (str): The HTTP method (GET, POST, PUT, DELETE, etc.).
    
    Returns:
        str: JSON string containing the complete operation details or null if not found.
    """
    try:
        operation = openapi_service.find_operation_by_path_and_method(path, method)
        return _format_operation_response(operation)
    except Exception as e:
        logger.error(f"Failed to load operation by path and method: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })


@mcp.tool()
def load_api_schema_by_schemaName(schema_name: str) -> str:
    """
    <important>Make Sure you have Called FIRST_STEP_get_api_script_guide first before this tool.</important>
    Load a specific schema by its name.
    
    Args:
        schema_name (str): The name of the schema to load (e.g., 'Stack', 'ErrorDetails').
    
    Returns:
        str: JSON string containing the complete schema details or null if not found.
    """
    try:
        schema = openapi_service.find_schema_by_name(schema_name)
        if schema:
            # Create a safe serializable version
            safe_schema = {
                "name": schema.name,
                "description": schema.description,
                "uri": schema.uri,
                "schema_data": {
                    "type": schema.schema_data.get('type', ''),
                    "description": schema.schema_data.get('description', ''),
                    "properties": schema.schema_data.get('properties', {}),
                    "required": schema.schema_data.get('required', [])
                }
            }
            return json.dumps(safe_schema, indent=2)
        else:
            return json.dumps(None)
    except Exception as e:
        logger.error(f"Failed to load schema by name: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        })


@mcp.tool()
def call_control_plane_api(path: str) -> str:
    """
    <important>Make Sure you have Called FIRST_STEP_get_api_script_guide first before this tool.</important>
    Make a GET request to the Facets Control Plane API.
    
    Args:
        path (str): API path to call (e.g., '/cc-ui/v1/stacks/my-stack' or 'cc-ui/v1/stacks')
    
    Returns:
        str: JSON string containing the API response or error information.
    """
    try:
        if not api_client_available:
            return json.dumps({
                "success": False,
                "error": "API client not initialized. Authentication credentials are required for this tool.",
                "help": "Set CONTROL_PLANE_URL, FACETS_USERNAME, FACETS_TOKEN environment variables or configure ~/.facets/credentials"
            })

        # Make the API call
        response = api_client.get(path)

        # Handle response
        if response.status_code == 200:
            try:
                response_data = response.json()
                return json.dumps({
                    "success": True,
                    "status_code": response.status_code,
                    "data": response_data
                }, indent=2)
            except ValueError:
                # Response is not JSON
                return json.dumps({
                    "success": True,
                    "status_code": response.status_code,
                    "data": response.text
                }, indent=2)
        else:
            # Handle error responses
            try:
                error_data = response.json()
            except ValueError:
                error_data = response.text

            return json.dumps({
                "success": False,
                "status_code": response.status_code,
                "error": error_data,
                "path": path
            }, indent=2)

    except Exception as e:
        logger.error(f"Failed to call Control Plane API: {e}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "path": path
        })
