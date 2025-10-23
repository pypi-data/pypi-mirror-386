# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Data Product MCP server that enables AI agents to discover and access data products through the Data Mesh Manager platform. It acts as a bridge between AI systems and data governance infrastructure, allowing agents to find relevant data products, check access permissions, and understand data contracts.

## Key Commands

### Development Setup
```bash
# Install dependencies with dev tools
uv sync --extra dev
uv pip install -e .
```

### Testing
```bash
# Run all tests (uses pytest with async support)
uv run pytest
```

### Running the Server
```bash
# Start MCP server (uses stdio transport)
uv run python -m dataproduct_mcp.server

# Use with MCP Inspector for debugging
npx @modelcontextprotocol/inspector --config config.json --server dataproduct
```

## Architecture

### Core Components

**MCP Server (`server.py`)**
- Built with FastMCP framework
- Exposes tools for data product discovery
- Uses stdio transport for MCP communication
- Implements async tools with proper error handling

**API Client Layer (`datameshmanager/`)**
- `datamesh_manager_client.py`: Async HTTP client using httpx
- `models.py`: Pydantic models for API response validation
- Handles authentication via `DATAMESH_MANAGER_API_KEY` environment variable

### MCP Tools Architecture

The server exposes these tools to AI agents:
1. `dataproduct_list` - List/filter data products by search terms, archetype, status
2. `dataproduct_search` - Semantic search for data products 
3. `dataproduct_get` - Retrieve detailed data product info including access status
4. `datacontract_get` - Get YAML data contract specifications

### Data Flow

1. **Discovery**: AI agents use list/search tools to find relevant data products
2. **Governance**: Check access status and permissions via get tools
3. **Integration**: Use returned server information to connect to actual data sources

## Configuration Requirements

### Environment Variables
- `DATAMESH_MANAGER_API_KEY`: Required API key for authentication
- `DATAMESH_MANAGER_HOST`: Optional API base URL for self-hosted instances (defaults to `https://api.datamesh-manager.com`)
- `QUERY_ACCESS_EVALUATION_ENABLED`: Optional flag to enable/disable query access evaluation (defaults to `true`). Set to `false` to skip AI-based access evaluation when AI is not enabled in Data Mesh Manager.

#### BigQuery Configuration

The BigQuery client supports three authentication methods with automatic fallback:

1. **Service Account JSON** (Recommended for production)
   - Set `BIGQUERY_CREDENTIALS_PATH` to path of service account key file
   - Example: `BIGQUERY_CREDENTIALS_PATH=/path/to/service-account-key.json`

2. **Workload Identity Federation** (Recommended for cloud environments)
   - Set `BIGQUERY_CREDENTIALS_PATH` to path of workload identity federation config
   - Example: `BIGQUERY_CREDENTIALS_PATH=/path/to/wif-config.json`

3. **Application Default Credentials** (Recommended for local development)
   - Do not set `BIGQUERY_CREDENTIALS_PATH` or set it to empty
   - Run `gcloud auth application-default login` for local user credentials
   - Automatically used in cloud environments (GCE, Cloud Run, GKE, etc.)

**Authentication Priority:**
- If `BIGQUERY_CREDENTIALS_PATH` is set, tries service account JSON first, then workload identity federation
- If not set or file not found, falls back to Application Default Credentials

**Note**: Google Cloud Project ID and dataset information are specified in the data product's output port server configuration, not as environment variables.

### Claude Desktop Integration
Configure in `~/Library/Application Support/Claude/claude_desktop_config.json`:

**Example 1: Using Service Account JSON**
```json
{
  "mcpServers": {
    "dataproduct": {
      "command": "uv",
      "args": ["run", "--directory", "<path_to_folder>/dataproduct-mcp", "python", "-m", "dataproduct_mcp.server"],
      "env": {
        "DATAMESH_MANAGER_API_KEY": "dmm_live_...",
        "DATAMESH_MANAGER_HOST": "https://your-self-hosted-instance.com",
        "BIGQUERY_CREDENTIALS_PATH": "/path/to/service-account-key.json",
        "QUERY_ACCESS_EVALUATION_ENABLED": "true"
      }
    }
  }
}
```

**Example 2: Using Application Default Credentials (local development)**
```json
{
  "mcpServers": {
    "dataproduct": {
      "command": "uv",
      "args": ["run", "--directory", "<path_to_folder>/dataproduct-mcp", "python", "-m", "dataproduct_mcp.server"],
      "env": {
        "DATAMESH_MANAGER_API_KEY": "dmm_live_...",
        "DATAMESH_MANAGER_HOST": "https://your-self-hosted-instance.com",
        "QUERY_ACCESS_EVALUATION_ENABLED": "true"
      }
    }
  }
}
```
Note: Run `gcloud auth application-default login` before using ADC.

## Code Patterns

- All tools are async and use proper error handling with try/catch blocks
- Pydantic models validate API responses
- YAML formatting for data product/contract responses
- Logging throughout for debugging and monitoring
- httpx for async HTTP operations with the Data Mesh Manager API

## Testing Setup

- Uses pytest with `pytest-asyncio` for async test support
- Test configuration in `pyproject.toml` with `asyncio_mode = "auto"`
- Tests located in `tests/` directory with fixtures in `conftest.py`