# MCP Server Template

Opinionated uv-based Python template to bootstrap an MCP server fast. One script updates project/package names and metadata so you can focus on core MCP tools.

## Features

- ✅ **Flexible Transport**: Support for both `stdio` and `streamable-http` transports
- ✅ **Bearer Token Authentication**: Built-in authentication for remote access security
- ✅ **Comprehensive Logging**: Configurable logging levels with structured output  
- ✅ **Environment Configuration**: Support for environment variables and CLI arguments
- ✅ **Error Handling**: Robust error handling and configuration validation
- ✅ **Development Tools**: Built-in scripts for easy development and testing

## Quick start

1) Initialize template (once)

```bash
./scripts/rename-template.sh \
  --name "my-mcp-server" \
  --author "Your Name" \
  --email "you@example.com" \
  --version "0.1.0" \
  --desc "My awesome MCP server"
```

This script:
- Creates dist name (hyphen) and package name (underscore) automatically
- Renames src/mcp_openwebui_demo -> src/<pkg_name> and replaces placeholders (mcp_openwebui_demo, mcp-openwebui-demo, mcp-openwebui-demo)
- Regenerates pyproject.toml (metadata, src layout, console script entrypoint)
- Updates run scripts and workflow URLs
- Optionally runs uv sync (omit with --no-sync)

2) Prepare environment

```bash
uv venv
uv sync
```

3) Configure server (optional)

```bash
# Copy environment template
cp .env.template .env

# Edit configuration as needed
# MCP_LOG_LEVEL=INFO
# FASTMCP_TYPE=stdio
# FASTMCP_HOST=127.0.0.1
# FASTMCP_PORT=8080

# For remote access with authentication (optional)
# REMOTE_AUTH_ENABLE=false
# REMOTE_SECRET_KEY=your-secure-secret-key-here
```

4) Run server

```bash
# Development & Testing (recommended)
./scripts/run-mcp-inspector-local.sh

# Direct execution for debugging
python -m src.mcp_openwebui_demo.mcp_main --log-level DEBUG

# For Claude Desktop integration, add to config:
# {
#   "mcpServers": {
#     "mcp-openwebui-demo": {
#       "command": "uv",
#       "args": ["run", "python", "-m", "src.mcp_openwebui_demo.mcp_main"]
#     }
#   }
# }
```

## Server Configuration

### Command Line Options

```bash
python -m src.mcp_openwebui_demo.mcp_main --help

Options:
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Logging level
  --type {stdio,streamable-http}
                        Transport type (default: stdio)
  --host HOST          Host address for HTTP transport (default: 127.0.0.1)
  --port PORT          Port number for HTTP transport (default: 8080)
  --auth-enable        Enable Bearer token authentication (default: False)
  --secret-key SECRET  Secret key for Bearer token authentication
```

### Environment Variables

| Variable | Description | Default | Usage |
|----------|-------------|---------|--------|
| `MCP_LOG_LEVEL` | Logging level | `INFO` | Development debugging |
| `FASTMCP_TYPE` | Transport type | `stdio` | Rarely needed to change |
| `FASTMCP_HOST` | HTTP host address | `127.0.0.1` | For HTTP mode only |
| `FASTMCP_PORT` | HTTP port number | `8080` | For HTTP mode only |
| `REMOTE_AUTH_ENABLE` | Enable Bearer token authentication | `false` | For secure remote access |
| `REMOTE_SECRET_KEY` | Secret key for authentication | - | Required when auth enabled |

**Note**: MCP servers typically use `stdio` transport. HTTP mode is mainly for testing and development.

## Security & Authentication

### Bearer Token Authentication

For `streamable-http` mode, this MCP server supports Bearer token authentication to secure remote access. This is especially important when running the server in production environments.

#### Configuration

**Enable Authentication:**

```bash
# In .env file
REMOTE_AUTH_ENABLE=true
REMOTE_SECRET_KEY=your-secure-secret-key-here
```

**Or via CLI:**

```bash
python -m src.mcp_openwebui_demo.mcp_main \
  --type streamable-http \
  --auth-enable \
  --secret-key your-secure-secret-key-here
```

#### Security Levels

1. **stdio mode** (Default): Local-only access, no authentication needed
2. **streamable-http + REMOTE_AUTH_ENABLE=false/undefined**: Remote access without authentication ⚠️ **NOT RECOMMENDED for production**
3. **streamable-http + REMOTE_AUTH_ENABLE=true**: Remote access with Bearer token authentication ✅ **RECOMMENDED for production**

> **🔒 Default Policy**: `REMOTE_AUTH_ENABLE` defaults to `false` if undefined, empty, or null. This ensures the server starts even without explicit authentication configuration.

#### Client Configuration

When authentication is enabled, MCP clients must include the Bearer token in the Authorization header:

```json
{
  "mcpServers": {
    "mcp-openwebui-demo": {
      "type": "streamable-http",
      "url": "http://your-server:8080/mcp",
      "headers": {
        "Authorization": "Bearer your-secure-secret-key-here"
      }
    }
  }
}
```

#### Security Best Practices

- **Always enable authentication** when using streamable-http mode in production
- **Use strong, randomly generated secret keys** (32+ characters recommended)
- **Use HTTPS** when possible (configure reverse proxy with SSL/TLS)
- **Restrict network access** using firewalls or network policies
- **Rotate secret keys regularly** for enhanced security
- **Monitor access logs** for unauthorized access attempts

## Project structure

```
.
├── main.py
├── MANIFEST.in
├── pyproject.toml
├── README.md
├── uv.lock
├── .env.template                   # Environment configuration template
├── docs/
├── scripts/
│   ├── rename-template.sh          # one-shot rename/customize
│   ├── run-mcp-inspector-local.sh  # development & testing (recommended)
│   └── run-mcp-inspector-pypi.sh   # test published package
└── src/
    └── mcp_openwebui_demo/                   # will be renamed to snake_case package
        ├── __init__.py
        ├── functions.py            # utility/helper functions with logging
        ├── mcp_main.py             # FastMCP server with auth & transport config
        └── prompt_template.md
```

## Development

### Adding Tools

Edit `src/<pkg_name>/mcp_main.py` to add new MCP tools:

```python
@mcp.tool()
async def my_tool(param: str) -> str:
    """
    [도구 역할]: Tool description
    [정확한 기능]: What it does
    [필수 사용 상황]: When to use it
    """
    logger.info(f"Tool called with param: {param}")
    return f"Result: {param}"
```

### Helper Functions

Add utility functions to `src/<pkg_name>/functions.py`:

```python
async def my_helper_function(data: dict) -> str:
    """Helper function with logging support"""
    logger.debug(f"Processing data: {data}")
    # Implementation here
    return result
```

## Usage Examples

### Development & Testing
```bash
# Best way to test your MCP server
./scripts/run-mcp-inspector-local.sh

# Debug with verbose logging
MCP_LOG_LEVEL=DEBUG ./scripts/run-mcp-inspector-local.sh

# Direct execution for quick testing
python -m src.mcp_openwebui_demo.mcp_main --log-level DEBUG
```

### Claude Desktop Integration
Add to your Claude Desktop configuration file:

```json
{
  "mcpServers": {
    "mcp-openwebui-demo": {
      "command": "uv",
      "args": ["run", "python", "-m", "src.mcp_openwebui_demo.mcp_main"],
      "cwd": "/path/to/your/project"
    }
  }
}
```

### HTTP Mode (Advanced)
For special testing scenarios only:

```bash
# Run HTTP server for testing (without authentication)
python -m src.mcp_openwebui_demo.mcp_main \
  --type streamable-http \
  --host 127.0.0.1 \
  --port 8080 \
  --log-level DEBUG

# Run HTTP server with authentication (recommended for production)
python -m src.mcp_openwebui_demo.mcp_main \
  --type streamable-http \
  --host 0.0.0.0 \
  --port 8080 \
  --auth-enable \
  --secret-key your-secure-secret-key-here
```

### Remote Access with Authentication

**Method 1: Local MCP (transport="stdio")**

```json
{
  "mcpServers": {
    "mcp-openwebui-demo": {
      "command": "uv",
      "args": ["run", "python", "-m", "src.mcp_openwebui_demo.mcp_main"],
      "env": {
        "MCP_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

**Method 2: Remote MCP (transport="streamable-http")**

```json
{
  "mcpServers": {
    "mcp-openwebui-demo": {
      "type": "streamable-http",
      "url": "http://your-server:8080/mcp",
      "headers": {
        "Authorization": "Bearer your-secure-secret-key-here"
      }
    }
  }
}
```

### Testing & Development

```bash
# Test with MCP Inspector
./scripts/run-mcp-inspector-local.sh

# Direct execution for debugging
python -m src.mcp_openwebui_demo.mcp_main --log-level DEBUG

# Run tests (if you add any)
uv run pytest
```

## Logging

The server provides structured logging with configurable levels:

```
2024-08-19 10:30:15 - mcp_main - INFO - Starting MCP server with stdio transport
2024-08-19 10:30:15 - mcp_main - INFO - Log level set via CLI to INFO
2024-08-19 10:30:16 - functions - DEBUG - Fetching data from source: example.com
```

## Notes

- The script replaces mcp_openwebui_demo (underscore), mcp-openwebui-demo (hyphen), and mcp-openwebui-demo (display name)
- Configuration validation ensures proper setup before server start
- If you need to rename again, revert changes or re-clone and re-run
- A backup `pyproject.toml.bak` is created when overwriting pyproject
