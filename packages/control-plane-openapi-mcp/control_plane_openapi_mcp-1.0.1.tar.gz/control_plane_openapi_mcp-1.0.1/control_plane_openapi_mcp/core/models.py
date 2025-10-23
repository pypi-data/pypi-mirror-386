from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class SpecOperationEntry(BaseModel):
    """Entry representing an OpenAPI operation."""
    path: str
    method: str
    description: Optional[str] = None
    operation_id: Optional[str] = None
    summary: Optional[str] = None
    tags: List[str] = []


class SpecSchemaEntry(BaseModel):
    """Entry representing a schema in the OpenAPI spec."""
    name: str
    description: Optional[str] = None


class SpecCatalogEntry(BaseModel):
    """Summary information about an available spec."""
    spec_id: str
    description: Optional[str] = None
    operations: List[SpecOperationEntry] = []
    schemas: List[SpecSchemaEntry] = []


class LoadOperationResult(BaseModel):
    """Result of loading an operation."""
    path: str
    method: str
    operation: Dict[str, Any]
    spec_id: str
    uri: str


class LoadSchemaResult(BaseModel):
    """Result of loading a schema."""
    name: str
    description: str
    schema_data: Dict[str, Any]
    uri: str
