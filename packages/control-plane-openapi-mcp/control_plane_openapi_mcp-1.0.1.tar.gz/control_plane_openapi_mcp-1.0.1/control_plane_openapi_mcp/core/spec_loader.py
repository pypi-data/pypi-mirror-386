import requests
import jsonref
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class SpecLoader:
    """Loads and processes OpenAPI specifications from URL."""
    
    def __init__(self, url: str):
        self.url = url
        self._raw_spec: Optional[Dict[str, Any]] = None
        self._processed_spec: Optional[Dict[str, Any]] = None
    
    def fetch_spec(self) -> Dict[str, Any]:
        """Fetch OpenAPI specification from URL."""
        try:
            response = requests.get(self.url, timeout=30)
            response.raise_for_status()
            self._raw_spec = response.json()
            logger.info(f"Successfully fetched OpenAPI spec from {self.url}")
            return self._raw_spec
        except requests.RequestException as e:
            logger.error(f"Failed to fetch OpenAPI spec from {self.url}: {e}")
            raise
        except ValueError as e:
            logger.error(f"Failed to parse JSON from {self.url}: {e}")
            raise
    
    def process_spec(self) -> Dict[str, Any]:
        """Process the spec by dereferencing $ref pointers."""
        if not self._raw_spec:
            raise ValueError("No spec loaded. Call fetch_spec() first.")
        
        try:
            # Dereference all $ref pointers
            self._processed_spec = jsonref.loads(
                jsonref.dumps(self._raw_spec)
            )
            
            # Convert any remaining JsonRef objects to plain dict/list
            self._processed_spec = self._deep_jsonref_to_dict(self._processed_spec)
            
            logger.info("Successfully processed OpenAPI spec")
            return self._processed_spec
        except Exception as e:
            logger.error(f"Failed to process OpenAPI spec: {e}")
            raise
    
    def _deep_jsonref_to_dict(self, obj):
        """Recursively convert JsonRef objects to plain Python objects."""
        if isinstance(obj, jsonref.JsonRef):
            # Force resolution and convert to dict
            return self._deep_jsonref_to_dict(dict(obj))
        elif isinstance(obj, dict):
            return {k: self._deep_jsonref_to_dict(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._deep_jsonref_to_dict(item) for item in obj]
        else:
            return obj
    
    def get_processed_spec(self) -> Dict[str, Any]:
        """Get the processed specification."""
        if not self._processed_spec:
            self.fetch_spec()
            self.process_spec()
        return self._processed_spec
    
    def refresh(self) -> Dict[str, Any]:
        """Refresh the specification from the URL."""
        self._raw_spec = None
        self._processed_spec = None
        return self.get_processed_spec()
