import argparse
import logging
import os
import sys
from typing import Any, Optional
from fastmcp import FastMCP

# Authentication import - resolved for fastmcp v2.12.4+
try:
    from fastmcp.server.auth import StaticTokenVerifier
except ImportError:
    # Fallback for older versions or if module not available
    StaticTokenVerifier = None

# TODO: 필요한 라이브러리들을 여기에 추가하세요
# 예시:
# import httpx          # HTTP 요청
# import sqlite3        # SQLite 데이터베이스
# import json           # JSON 처리

# =============================================================================
# 로깅 설정
# =============================================================================
# Set up logging (initial level from env; may be overridden by --log-level)
logging.basicConfig(
    level=os.environ.get("MCP_LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("MCPServer")

# =============================================================================
# Authentication Setup
# =============================================================================

# Check environment variables for authentication early
_auth_enable = os.environ.get("REMOTE_AUTH_ENABLE", "false").lower() == "true"
_secret_key = os.environ.get("REMOTE_SECRET_KEY", "")

# Initialize the main MCP instance with authentication if configured
if _auth_enable and _secret_key and StaticTokenVerifier:
    logger.info("Initializing MCP instance with Bearer token authentication (from environment)")
    
    # Create token configuration
    tokens = {
        _secret_key: {
            "client_id": "mcp-server-client",
            "user": "admin",
            "scopes": ["read", "write"],
            "description": "MCP Server access token"
        }
    }
    
    auth = StaticTokenVerifier(tokens=tokens)
    # TODO: "your-server-name"을 실제 서버 이름으로 변경하세요
    mcp = FastMCP("mcp-openwebui-demo", auth=auth)
    logger.info("MCP instance initialized with authentication")
elif _auth_enable and _secret_key and not StaticTokenVerifier:
    logger.warning("Authentication requested but StaticTokenVerifier not available - running without authentication")
    # TODO: "your-server-name"을 실제 서버 이름으로 변경하세요
    mcp = FastMCP("mcp-openwebui-demo")
else:
    logger.info("Initializing MCP instance without authentication")
    # TODO: "your-server-name"을 실제 서버 이름으로 변경하세요
    mcp = FastMCP("mcp-openwebui-demo")

#==============================================================================
# MCP Tools
#==============================================================================

@mcp.tool()
def get_sum(a: int, b: int) -> int:
    """
    This tool performs addition of two integers. 
    It is designed to take two numbers as input and return their sum, 
    enabling simple arithmetic operations within workflows.
    """
    return a + b

#==============================================================================
# MCP Resources
#==============================================================================

# Add a dynamic greeing resource
# @mcp.resource("greeting://{name}")
# def get_greeting(name: str) -> str:
#     """Get a personalized greeting"""
#     return f"Hello, {name}!"

# 간단한 문자열 resource
# @mcp.resource("resource://greeting")
# def get_greeting() -> str:
#     """Provides a simple greeting message."""
#     return "Hello from FastMCP Resources!"

# 간단한 문자열 resource
@mcp.resource("resource://greeting")
def get_greeting() -> str:
    """Provides a simple greeting message."""
    return "Hello from FastMCP Resources!"

# JSON 설정 resource
@mcp.resource("data://config")
def get_config() -> dict:
    """Provides application configuration as JSON."""
    return {
        "theme": "dark",
        "version": "1.2.0",
        "features": ["tools", "resources"],
    }

# 템플릿 기반의 resource
@mcp.resource("repos://{owner}/{repo}/info")
def get_repo_info(owner: str, repo: str) -> dict:
    """Retrieves information about a GitHub repository."""
    # In a real implementation, this would call the GitHub API
    return {
        "owner": owner,
        "name": repo,
        "full_name": f"{owner}/{repo}",
        "stars": 120,
        "forks": 48
    }

#==============================================================================
# 기타 함수
#==============================================================================

def validate_config(transport_type: str, host: str, port: int) -> None:
    """서버 설정 검증"""
    if transport_type not in ["stdio", "streamable-http"]:
        raise ValueError(f"Invalid transport type: {transport_type}")
    
    if transport_type == "streamable-http":
        # Host 검증
        if not host:
            raise ValueError("Host is required for streamable-http transport")
        
        # Port 검증
        if not (1 <= port <= 65535):
            raise ValueError(f"Port must be between 1 and 65535, got: {port}")
        
        logger.info(f"Configuration validated for streamable-http: {host}:{port}")
    else:
        logger.info("Configuration validated for stdio transport")

#==============================================================================
# 메인 실행 함수
#==============================================================================

def main(argv: Optional[list] = None) -> None:
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        prog="mcp-server", 
        description="MCP Server with configurable transport"
    )
    parser.add_argument(
        "--log-level",
        dest="log_level",
        help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL). Overrides env var if provided.",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    )
    parser.add_argument(
        "--type",
        dest="transport_type",
        help="Transport type. Default: stdio",
        choices=["stdio", "streamable-http"],
        default="stdio"
    )
    parser.add_argument(
        "--host",
        dest="host",
        help="Host address for streamable-http transport. Default: 127.0.0.1",
        default="127.0.0.1"
    )
    parser.add_argument(
        "--port",
        dest="port",
        type=int,
        help="Port number for streamable-http transport. Default: 8080",
        default=8080
    )
    parser.add_argument(
        "--auth-enable",
        dest="auth_enable",
        action="store_true",
        help="Enable Bearer token authentication for streamable-http mode. Default: False",
    )
    parser.add_argument(
        "--secret-key",
        dest="secret_key",
        help="Secret key for Bearer token authentication. Required when auth is enabled.",
    )
    
    try:
        args = parser.parse_args(argv)
        
        # Determine log level: CLI arg > environment variable > default
        log_level = args.log_level or os.getenv("MCP_LOG_LEVEL", "INFO")
        
        # Set logging level
        numeric_level = getattr(logging, log_level.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError(f'Invalid log level: {log_level}')
        
        logger.setLevel(numeric_level)
        logging.getLogger().setLevel(numeric_level)
        
        # Reduce noise from external libraries at DEBUG level
        logging.getLogger("aiohttp.client").setLevel(logging.WARNING)
        logging.getLogger("asyncio").setLevel(logging.WARNING)
        
        if args.log_level:
            logger.info("Log level set via CLI to %s", args.log_level)
        elif os.getenv("MCP_LOG_LEVEL"):
            logger.info("Log level set via environment variable to %s", log_level)
        else:
            logger.info("Using default log level: %s", log_level)

        # 우선순위: CLI 인수 > 환경변수 > 기본값
        transport_type = args.transport_type or os.getenv("FASTMCP_TYPE", "stdio")
        host = args.host or os.getenv("FASTMCP_HOST", "127.0.0.1") 
        port = args.port if args.port != 8080 else int(os.getenv("FASTMCP_PORT", "8080"))
        
        # Authentication 설정 결정
        auth_enable = args.auth_enable or os.getenv("REMOTE_AUTH_ENABLE", "false").lower() in ("true", "1", "yes", "on")
        secret_key = args.secret_key or os.getenv("REMOTE_SECRET_KEY", "")
        
        # Validation for streamable-http mode with authentication
        if transport_type == "streamable-http":
            if auth_enable:
                if not secret_key:
                    logger.error("ERROR: Authentication is enabled but no secret key provided.")
                    logger.error("Please set REMOTE_SECRET_KEY environment variable or use --secret-key argument.")
                    sys.exit(1)
                logger.info("Authentication enabled for streamable-http transport")
            else:
                logger.warning("WARNING: streamable-http mode without authentication enabled!")
                logger.warning("This server will accept requests without Bearer token verification.")
                logger.warning("Set REMOTE_AUTH_ENABLE=true and REMOTE_SECRET_KEY to enable authentication.")

        # Note: MCP instance with authentication is already initialized at module level
        # based on environment variables. CLI arguments will override if different.
        if auth_enable != _auth_enable or secret_key != _secret_key:
            logger.warning("CLI authentication settings differ from environment variables.")
            logger.warning("Environment settings take precedence during module initialization.")
        
        # 설정 검증
        validate_config(transport_type, host, port)
        
        # Transport 모드에 따른 실행
        if transport_type == "streamable-http":
            logger.info(f"Starting MCP server with streamable-http transport on {host}:{port}")
            mcp.run(transport="streamable-http", host=host, port=port)
        else:
            logger.info("Starting MCP server with stdio transport")
            mcp.run(transport='stdio')
            
    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    """Entrypoint for MCP server.

    Supports optional CLI arguments while remaining backward-compatible 
    with stdio launcher expectations.
    """
    main()