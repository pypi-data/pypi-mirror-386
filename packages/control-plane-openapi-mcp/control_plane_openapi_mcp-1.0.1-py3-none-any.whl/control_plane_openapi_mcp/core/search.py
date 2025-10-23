from typing import List, Dict, Any, Optional
from fuzzywuzzy import fuzz
from .models import SpecOperationEntry, SpecSchemaEntry, LoadOperationResult
import logging

logger = logging.getLogger(__name__)


class SearchEngine:
    """Fuzzy search engine for OpenAPI operations and schemas."""
    
    def __init__(self, spec_id: str):
        self.spec_id = spec_id
    
    def search_operations(
        self, 
        operations: List[SpecOperationEntry], 
        query: str, 
        threshold: int = 60
    ) -> List[SpecOperationEntry]:
        """Search operations using fuzzy matching."""
        if not query.strip():
            return operations
        
        scored_operations = []
        query_lower = query.lower()
        
        for operation in operations:
            # Create searchable text from operation fields
            searchable_text = ' '.join(filter(None, [
                operation.operation_id or '',
                operation.summary or '',
                operation.description or '',
                ' '.join(operation.tags),
                operation.path,
                operation.method
            ])).lower()
            
            # Calculate fuzzy match score
            score = fuzz.partial_ratio(query_lower, searchable_text)
            
            if score >= threshold:
                scored_operations.append((score, operation))
        
        # Sort by score (descending) and return operations
        scored_operations.sort(key=lambda x: x[0], reverse=True)
        result = [op for _, op in scored_operations]
        
        logger.info(f"Found {len(result)} operations matching '{query}'")
        return result
    
    def search_schemas(
        self, 
        schemas: List[SpecSchemaEntry], 
        query: str, 
        threshold: int = 60
    ) -> List[SpecSchemaEntry]:
        """Search schemas using fuzzy matching."""
        if not query.strip():
            return schemas
        
        scored_schemas = []
        query_lower = query.lower()
        
        for schema in schemas:
            # Create searchable text from schema fields
            searchable_text = ' '.join(filter(None, [
                schema.name,
                schema.description or ''
            ])).lower()
            
            # Calculate fuzzy match score
            score = fuzz.partial_ratio(query_lower, searchable_text)
            
            if score >= threshold:
                scored_schemas.append((score, schema))
        
        # Sort by score (descending) and return schemas
        scored_schemas.sort(key=lambda x: x[0], reverse=True)
        result = [schema for _, schema in scored_schemas]
        
        logger.info(f"Found {len(result)} schemas matching '{query}'")
        return result
    
    def convert_operation_to_result(self, operation: SpecOperationEntry, operation_data: Dict[str, Any]) -> LoadOperationResult:
        """Convert operation entry to load result."""
        return LoadOperationResult(
            path=operation.path,
            method=operation.method,
            operation=operation_data,
            spec_id=self.spec_id,
            uri=f"apis://{self.spec_id}/operations/{operation.operation_id}"
        )
