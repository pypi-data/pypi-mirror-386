"""
Utilities for extracting and matching OpenAPI schemas.
"""

from typing import Optional, Dict, Any


def extract_schema_name_from_ref(ref: str) -> Optional[str]:
    """
    Extract schema name from a $ref reference.
    
    Args:
        ref: The $ref string (e.g., '#/components/schemas/PromotionWorkflow')
    
    Returns:
        The schema name or None if not a valid schema reference
    """
    if ref and isinstance(ref, str) and ref.startswith('#/components/schemas/'):
        return ref.split('/')[-1]
    return None


def match_inline_schema_to_component(
        inline_schema: Dict[str, Any],
        components_schemas: Dict[str, Any]
) -> Optional[str]:
    """
    Try to match an inline schema to a named schema in components.
    
    Args:
        inline_schema: The inline schema definition
        components_schemas: All schemas from components/schemas
    
    Returns:
        The name of the matching schema or None
    """
    if not inline_schema or not isinstance(inline_schema, dict):
        return None

    # Only match object types with properties
    if inline_schema.get('type') != 'object' or 'properties' not in inline_schema:
        return None

    inline_props = set(inline_schema['properties'].keys())

    # Try to find a matching schema in components
    for schema_name, schema_def in components_schemas.items():
        if not isinstance(schema_def, dict):
            continue
        if schema_def.get('type') != 'object' or 'properties' not in schema_def:
            continue

        component_props = set(schema_def['properties'].keys())

        # Check if properties match exactly
        if inline_props == component_props:
            return schema_name

    return None


def get_schema_name(schema: Dict[str, Any], components_schemas: Dict[str, Any]) -> Optional[str]:
    """
    Get the schema name from either a $ref or by matching inline schema.
    
    Args:
        schema: The schema object (may contain $ref or be inline)
        components_schemas: All schemas from components/schemas
    
    Returns:
        The schema name or None
    """
    if not schema or not isinstance(schema, dict):
        return None

    # First check for $ref
    if '$ref' in schema:
        return extract_schema_name_from_ref(schema['$ref'])

    # Try to match inline schema
    return match_inline_schema_to_component(schema, components_schemas)


def enrich_operation_with_schemas(
        operation: Dict[str, Any],
        components_schemas: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Enrich an operation with schema names for request body and responses.
    
    Args:
        operation: The operation dictionary
        components_schemas: All schemas from components/schemas
    
    Returns:
        Enriched operation dictionary with schema names included
    """
    enriched = operation.copy()

    # Enrich request body
    request_body = enriched.get('requestBody')
    if request_body and isinstance(request_body, dict):
        content = request_body.get('content', {})
        if 'application/json' in content:
            schema = content['application/json'].get('schema', {})
            schema_name = get_schema_name(schema, components_schemas)
            if schema_name:
                # Add schema name to the requestBody
                if 'requestBody' not in enriched:
                    enriched['requestBody'] = {}
                enriched['requestBody']['schemaName'] = schema_name

    # Enrich responses
    responses = enriched.get('responses', {})
    for status_code, response in responses.items():
        if isinstance(response, dict):
            content = response.get('content', {})
            if 'application/json' in content:
                schema = content['application/json'].get('schema', {})
                schema_name = get_schema_name(schema, components_schemas)
                if schema_name:
                    # Add schema name to the response
                    if 'responses' not in enriched:
                        enriched['responses'] = {}
                    if status_code not in enriched['responses']:
                        enriched['responses'][status_code] = {}
                    enriched['responses'][status_code]['schemaName'] = schema_name

    return enriched


def create_safe_operation_output(
        operation: Dict[str, Any],
        components_schemas: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create a safe, serializable operation output with schema names included.
    
    Args:
        operation: The full operation dictionary
        components_schemas: All schemas from components/schemas
    
    Returns:
        Safe operation dictionary with schema names
    """
    # Extract request body info with schema name
    request_body_output = None
    request_body = operation.get('requestBody', {})
    if request_body:
        request_body_output = {
            "description": request_body.get('description', ''),
            "required": request_body.get('required', False)
        }

        # Add schema name if available
        content = request_body.get('content', {})
        if 'application/json' in content:
            schema = content['application/json'].get('schema', {})
            schema_name = get_schema_name(schema, components_schemas)
            if schema_name:
                request_body_output['schemaName'] = schema_name

    # Extract responses with schema names
    responses_output = {}
    responses = operation.get('responses', {})
    for status_code, response in responses.items():
        if isinstance(response, dict):
            response_output = {
                "description": response.get('description', '')
            }

            # Add schema name if available
            content = response.get('content', {})
            if 'application/json' in content:
                schema = content['application/json'].get('schema', {})
                schema_name = get_schema_name(schema, components_schemas)
                if schema_name:
                    response_output['schemaName'] = schema_name

            responses_output[status_code] = response_output
        else:
            responses_output[status_code] = str(response)

    return {
        "operationId": operation.get('operationId', ''),
        "summary": operation.get('summary', ''),
        "description": operation.get('description', ''),
        "tags": operation.get('tags', []),
        "parameters": operation.get('parameters', []),
        "requestBody": request_body_output,
        "responses": responses_output
    }
