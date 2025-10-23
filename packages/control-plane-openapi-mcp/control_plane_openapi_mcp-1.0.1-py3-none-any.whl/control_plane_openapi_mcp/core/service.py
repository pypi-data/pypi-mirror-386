from typing import Dict, Any, List, Optional
import logging
from .spec_loader import SpecLoader
from .spec_processor import SpecProcessor
from .search import SearchEngine
from .cache import SimpleCache
from .models import (
    SpecCatalogEntry, 
    LoadOperationResult, 
    LoadSchemaResult,
    SpecOperationEntry,
    SpecSchemaEntry
)

logger = logging.getLogger(__name__)


class OpenAPIService:
    """Main service for managing OpenAPI specifications."""
    
    def __init__(self, url: str, spec_id: str, cache_ttl: int = 3600):
        self.url = url
        self.spec_id = spec_id
        self.cache_ttl = cache_ttl
        
        self.loader = SpecLoader(url)
        self.processor = SpecProcessor(spec_id)
        self.search_engine = SearchEngine(spec_id)
        self.cache = SimpleCache[Dict[str, Any]](cache_ttl)
        
        self._catalog: Optional[SpecCatalogEntry] = None
        self._spec: Optional[Dict[str, Any]] = None
    
    def initialize(self) -> None:
        """Initialize the service by loading and processing the spec."""
        try:
            self._load_spec()
            self._build_catalog()
            logger.info("OpenAPI service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAPI service: {e}")
            raise
    
    def refresh(self) -> None:
        """Refresh the specification from the URL."""
        try:
            self.cache.clear()
            self._spec = None
            self._catalog = None
            self.initialize()
            logger.info("OpenAPI service refreshed successfully")
        except Exception as e:
            logger.error(f"Failed to refresh OpenAPI service: {e}")
            raise
    
    def _load_spec(self) -> None:
        """Load and cache the OpenAPI specification."""
        cached_spec = self.cache.get('spec')
        if cached_spec:
            self._spec = cached_spec
            logger.info("Using cached OpenAPI specification")
        else:
            self._spec = self.loader.get_processed_spec()
            self.cache.set('spec', self._spec)
            logger.info("Loaded and cached OpenAPI specification")
    
    def _build_catalog(self) -> None:
        """Build the catalog from the specification."""
        if not self._spec:
            raise ValueError("No specification loaded")
        
        cached_catalog = self.cache.get('catalog')
        if cached_catalog:
            # Reconstruct catalog from cached data
            self._catalog = SpecCatalogEntry(**cached_catalog)
            logger.info("Using cached catalog")
        else:
            self._catalog = self.processor.build_catalog(self._spec)
            self.cache.set('catalog', self._catalog.model_dump())
            logger.info("Built and cached catalog")
    
    def search_operations(self, query: str) -> List[LoadOperationResult]:
        """Search for operations matching the query."""
        if not self._catalog or not self._spec:
            self.initialize()
        
        # Search operations
        matching_operations = self.search_engine.search_operations(
            self._catalog.operations, query
        )
        
        # Convert to LoadOperationResult
        results = []
        for op in matching_operations:
            # Find the full operation data
            op_data = self.processor.find_operation_by_path_and_method(
                self._spec, op.path, op.method.lower()
            )
            if op_data:
                results.append(LoadOperationResult(
                    path=op.path,
                    method=op.method,
                    operation=op_data['operation'],
                    spec_id=self.spec_id,
                    uri=f"apis://{self.spec_id}/operations/{op.operation_id}"
                ))
        
        return results
    
    def search_schemas(self, query: str) -> List[SpecSchemaEntry]:
        """Search for schemas matching the query."""
        if not self._catalog:
            self.initialize()
        
        return self.search_engine.search_schemas(self._catalog.schemas, query)
    
    def find_operation_by_id(self, operation_id: str) -> Optional[LoadOperationResult]:
        """Find an operation by its operationId."""
        if not self._spec:
            self.initialize()
        
        op_data = self.processor.find_operation_by_id(self._spec, operation_id)
        if not op_data:
            return None
        
        return LoadOperationResult(
            path=op_data['path'],
            method=op_data['method'],
            operation=op_data['operation'],
            spec_id=self.spec_id,
            uri=f"apis://{self.spec_id}/operations/{operation_id}"
        )
    
    def find_operation_by_path_and_method(
        self, 
        path: str, 
        method: str
    ) -> Optional[LoadOperationResult]:
        """Find an operation by path and method."""
        if not self._spec:
            self.initialize()
        
        op_data = self.processor.find_operation_by_path_and_method(
            self._spec, path, method
        )
        if not op_data:
            return None
        
        operation_id = op_data['operation'].get('operationId', '')
        return LoadOperationResult(
            path=path,
            method=method.upper(),
            operation=op_data['operation'],
            spec_id=self.spec_id,
            uri=f"apis://{self.spec_id}/operations/{operation_id}"
        )
    
    def find_schema_by_name(self, schema_name: str) -> Optional[LoadSchemaResult]:
        """Find a schema by name."""
        if not self._spec:
            self.initialize()
        
        schema_data = self.processor.find_schema_by_name(self._spec, schema_name)
        if not schema_data:
            return None
        
        return LoadSchemaResult(
            name=schema_name,
            description=schema_data.get('description', ''),
            schema_data=schema_data,
            uri=f"apis://{self.spec_id}/schemas/{schema_name}"
        )
    
    def get_components_schemas(self) -> Dict[str, Any]:
        """Get all schemas from components/schemas."""
        if not self._spec:
            self.initialize()
        
        return self._spec.get('components', {}).get('schemas', {})
