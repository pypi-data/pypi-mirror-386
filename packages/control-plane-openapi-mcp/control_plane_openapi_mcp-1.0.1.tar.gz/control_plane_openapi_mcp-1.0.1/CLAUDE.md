# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development Setup
```bash
# Install dependencies and setup environment
uv sync
source .venv/bin/activate

# Run the MCP server
uv run control-plane-openapi-mcp

# Test all functionality with comprehensive example
uv run python example.py

# Run validation tests
uv run python test_final.py

# Quick function testing
uv run python -c "from control_plane_openapi_mcp.tools import search_api_operations; print(search_api_operations('stack'))"
```

### Common Development Tasks
```bash
# Run individual tool tests
uv run python dev_test.py

# Test server initialization
uv run python -m control_plane_openapi_mcp.server

# Claude Desktop integration testing
npx @modelcontextprotocol/inspector uv run --directory . control-plane-openapi-mcp
```

## Architecture Overview

This is an MCP (Model Context Protocol) server that provides tools for exploring and interacting with the Facets Control Plane OpenAPI specification. The architecture follows a service-oriented design with clear separation of concerns.

### Core Service Architecture
The system is built around `OpenAPIService` (core/service.py:13) which orchestrates all operations:
- **Lazy Loading**: Specs are fetched and cached only when first accessed
- **Smart Caching**: TTL-based caching with configurable duration (default 1 hour)
- **Error Boundaries**: All operations have comprehensive error handling with graceful degradation

### Key Components
1. **Spec Loading Pipeline**: 
   - `SpecLoader` (core/spec_loader.py:14) fetches OpenAPI specs from URLs
   - `SpecProcessor` (core/spec_processor.py:17) extracts and filters operations (excludes deprecated)
   - JSON references are resolved using `jsonref` for proper schema handling

2. **Search Engine**:
   - `SearchEngine` (core/search.py:14) uses fuzzy matching with `fuzzywuzzy`
   - Configurable thresholds for operation (70) and schema (80) matching
   - Searches across names, descriptions, and tags

3. **Authentication**:
   - Supports environment variables or credentials file (~/.facets/credentials)
   - HTTP Basic Auth for all API calls
   - Configuration managed through `Config` (config.py:10)

### MCP Integration
The server exposes 7 tools through FastMCP:
- API exploration tools (search, load operations/schemas)
- API interaction tool (`call_control_plane_api` for GET requests only)
- Catalog refresh capability

## Important Implementation Details

### Authentication Setup
The system uses a two-tier authentication approach:
1. Environment variables: `FACETS_USERNAME` and `FACETS_TOKEN`
2. Credentials file with profile support (default profile: "default")

### API Coverage
The OpenAPI spec includes 566 total operations (549 active after filtering deprecated):
- Stack and project management
- Kubernetes cluster operations
- CI/CD artifact management
- User access control
- Resource and configuration management
- Monitoring and alerting

### Error Handling Patterns
All tools follow consistent error handling:
```python
try:
    # Operation logic
except Exception as e:
    logger.error(f"Error description: {e}")
    return {"error": str(e)}
```

### Caching Strategy
- In-memory caching with configurable TTL
- Separate caches for raw and processed specs
- Manual refresh capability through `refresh_api_catalog` tool

## Development Guidelines

### Adding New Tools
1. Define tool in `tools.py` using `@mcp_server.tool()` decorator
2. Implement logic using `OpenAPIService` methods
3. Follow existing error handling patterns
4. Add comprehensive logging

### Testing New Features
1. Add test cases to `example.py` for comprehensive testing
2. Use `dev_test.py` for quick iterations
3. Validate with Claude Desktop using MCP inspector

### Working with OpenAPI Specs
- The spec includes extensive use of $ref pointers - use `jsonref` for resolution
- Deprecated operations are automatically filtered during processing
- Schema definitions include nested references that must be resolved

### Performance Considerations
- Large spec (>10MB) - use caching to avoid repeated fetches
- Fuzzy search can be expensive - consider threshold tuning
- API calls should respect rate limits of the Control Plane instance