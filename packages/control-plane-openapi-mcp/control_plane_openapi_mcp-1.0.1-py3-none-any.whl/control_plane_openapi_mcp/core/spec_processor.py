from typing import Dict, Any, List, Optional
from .models import SpecCatalogEntry, SpecOperationEntry, SpecSchemaEntry
import logging

logger = logging.getLogger(__name__)


class SpecProcessor:
    """Processes OpenAPI specifications to extract catalog information."""
    
    def __init__(self, spec_id: str):
        self.spec_id = spec_id
    
    def build_catalog(self, spec: Dict[str, Any]) -> SpecCatalogEntry:
        """Build a catalog entry from the OpenAPI specification."""
        operations = self._extract_operations(spec)
        schemas = self._extract_schemas(spec)
        
        return SpecCatalogEntry(
            spec_id=self.spec_id,
            description=spec.get('info', {}).get('description', ''),
            operations=operations,
            schemas=schemas
        )
    
    def _extract_operations(self, spec: Dict[str, Any]) -> List[SpecOperationEntry]:
        """Extract operations from the OpenAPI spec, excluding deprecated ones."""
        operations = []
        deprecated_count = 0
        paths = spec.get('paths', {})
        
        for path, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue
                
            for method, operation in path_item.items():
                if method in ['parameters', '$ref'] or not isinstance(operation, dict):
                    continue
                
                # Skip deprecated operations
                if operation.get('deprecated', False):
                    deprecated_count += 1
                    logger.debug(f"Skipping deprecated operation: {method.upper()} {path} ({operation.get('operationId', 'no-id')})")
                    continue
                
                operations.append(SpecOperationEntry(
                    path=path,
                    method=method.upper(),
                    description=operation.get('description', ''),
                    operation_id=operation.get('operationId'),
                    summary=operation.get('summary', ''),
                    tags=operation.get('tags', [])
                ))
        
        logger.info(f"Extracted {len(operations)} operations ({deprecated_count} deprecated operations excluded)")
        return operations
    
    def _extract_schemas(self, spec: Dict[str, Any]) -> List[SpecSchemaEntry]:
        """Extract schemas from the OpenAPI spec."""
        schemas = []
        components = spec.get('components', {})
        schema_definitions = components.get('schemas', {})
        
        for name, schema in schema_definitions.items():
            if isinstance(schema, dict):
                schemas.append(SpecSchemaEntry(
                    name=name,
                    description=schema.get('description', '')
                ))
        
        logger.info(f"Extracted {len(schemas)} schemas")
        return schemas
    
    def find_operation_by_id(self, spec: Dict[str, Any], operation_id: str) -> Optional[Dict[str, Any]]:
        """Find an operation by its operationId, excluding deprecated operations."""
        paths = spec.get('paths', {})
        
        for path, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue
                
            for method, operation in path_item.items():
                if (method not in ['parameters', '$ref'] and 
                    isinstance(operation, dict) and 
                    operation.get('operationId') == operation_id and
                    not operation.get('deprecated', False)):  # Skip deprecated
                    return {
                        'path': path,
                        'method': method.upper(),
                        'operation': operation
                    }
        return None
    
    def find_operation_by_path_and_method(
        self, 
        spec: Dict[str, Any], 
        path: str, 
        method: str
    ) -> Optional[Dict[str, Any]]:
        """Find an operation by path and method, excluding deprecated operations."""
        paths = spec.get('paths', {})
        path_item = paths.get(path)
        
        if not path_item or not isinstance(path_item, dict):
            return None
            
        operation = path_item.get(method.lower())
        if not operation or not isinstance(operation, dict):
            return None
        
        # Skip deprecated operations
        if operation.get('deprecated', False):
            return None
            
        return {
            'path': path,
            'method': method.upper(),
            'operation': operation
        }
    
    def find_schema_by_name(self, spec: Dict[str, Any], schema_name: str) -> Optional[Dict[str, Any]]:
        """Find a schema by name."""
        components = spec.get('components', {})
        schemas = components.get('schemas', {})
        
        schema = schemas.get(schema_name)
        if schema and isinstance(schema, dict):
            return schema
        return None
