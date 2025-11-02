"""MCP over HTTP/SSE endpoint for ChatGPT Connector support.

Implements MCP Streamable HTTP transport (2025-03-26 spec) for:
- ChatGPT Connectors (https://developers.openai.com/apps-sdk/deploy/connect-chatgpt/)
- Other HTTP-based MCP clients

Endpoint: POST/GET/DELETE /mcp

Note: This module provides an ASGI app that should be mounted in server.py
"""

from __future__ import annotations

import asyncio
import json
import logging
import os

from mcp.server import Server
from mcp.server.streamable_http import StreamableHTTPServerTransport
from starlette.types import Receive, Scope, Send

from kagura.mcp.server import create_mcp_server

logger = logging.getLogger(__name__)

# Global MCP server instance (shared across requests)
_mcp_server: Server | None = None

# Global MCP transport instance (manages HTTP/SSE communication)
_mcp_transport: StreamableHTTPServerTransport | None = None

# Background task for MCP server
_server_task: asyncio.Task | None = None


def get_mcp_server() -> Server:
    """Get or create shared MCP server instance for HTTP/SSE transport.

    Creates a server in "remote" context, which filters out dangerous tools
    like file operations, shell execution, and local app launches.

    Returns:
        Shared MCP Server instance with safe tools only
    """
    global _mcp_server

    if _mcp_server is None:
        # Auto-register built-in MCP tools
        try:
            import kagura.mcp.builtin  # noqa: F401

            logger.info("Loaded built-in MCP tools for HTTP transport")
        except ImportError:
            logger.warning("Could not load built-in MCP tools")

        # Create server in REMOTE context (tool access control enabled)
        _mcp_server = create_mcp_server(
            name="kagura-api-http",
            context="remote",  # Filter dangerous tools
        )
        logger.info("Created MCP server instance for HTTP transport (remote context)")

    return _mcp_server


async def _start_mcp_server():
    """Start MCP server background task.

    Should be called during application startup.
    """
    global _server_task, _mcp_transport

    if _server_task is not None:
        logger.warning("MCP server task already running")
        return

    if _mcp_transport is None:
        logger.error("Transport not initialized before starting server")
        return

    server = get_mcp_server()

    async def run_mcp_server():
        """Background task to run MCP server with transport."""
        try:
            logger.info("Starting MCP server background task")
            assert _mcp_transport is not None
            # Connect server to transport
            async with _mcp_transport.connect() as (
                read_stream,
                write_stream,
            ):
                await server.run(
                    read_stream,
                    write_stream,
                    server.create_initialization_options(),
                )
        except asyncio.CancelledError:
            logger.info("MCP server task cancelled")
            raise
        except Exception as e:
            logger.error(f"MCP server error: {e}", exc_info=True)

    # Create task - runs in background
    _server_task = asyncio.create_task(run_mcp_server())
    logger.info("MCP server background task started")


def get_mcp_transport() -> StreamableHTTPServerTransport:
    """Get or create shared MCP transport instance.

    Returns:
        Shared StreamableHTTPServerTransport instance
    """
    global _mcp_transport

    if _mcp_transport is None:
        # Create transport (no session ID = server generates one)
        _mcp_transport = StreamableHTTPServerTransport(
            mcp_session_id=None,  # Auto-generate session ID
            is_json_response_enabled=True,  # Support JSON responses
        )
        logger.info("Created MCP HTTP transport instance")

        # Note: Background task must be started from async context
        # Call _start_mcp_server() from app lifespan or first request

    return _mcp_transport


async def mcp_asgi_app(scope: Scope, receive: Receive, send: Send) -> None:
    """ASGI app for MCP over HTTP/SSE.

    Supports:
    - GET: SSE streaming (server → client messages)
    - POST: JSON-RPC requests (client → server messages)
    - DELETE: Session termination

    Authentication:
        - Authorization header: Bearer {api_key} (recommended for production)
        - If no auth: uses "default_user" (local development only)

    ChatGPT Connector Setup:
        1. Enable Developer Mode in ChatGPT settings
        2. Go to Settings → Connectors → Advanced → Developer Mode
        3. Add custom connector:
           - Name: Kagura Memory
           - URL: https://your-server.com/mcp
           - Description: Universal AI Memory Platform
           - Authentication: Bearer token (if API key required)

    Note:
        For local development, use ngrok to expose this endpoint:
        ```bash
        ngrok http 8000
        # Use https://xxxxx.ngrok.app/mcp in ChatGPT
        ```

    Implementation:
        Uses MCP SDK's StreamableHTTPServerTransport for protocol handling.
        The transport manages sessions, SSE streaming, and JSON-RPC processing.

        API Key authentication (Phase C Task 2):
        - Checks Authorization header for Bearer token
        - Validates against API key database
        - Extracts user_id from validated key
        - Falls back to default_user if no auth provided

    Args:
        scope: ASGI scope dict
        receive: ASGI receive callable
        send: ASGI send callable
    """
    global _server_task

    # Extract headers for authentication
    headers = dict(scope.get("headers", []))

    # Try to authenticate via API key (optional)
    user_id = "default_user"  # Default if no authentication

    # Check Authorization header
    auth_header = headers.get(b"authorization")
    if auth_header:
        try:
            from kagura.api.auth import get_api_key_manager

            auth_str = auth_header.decode("utf-8")
            if auth_str.startswith("Bearer "):
                api_key = auth_str[7:]  # Remove "Bearer " prefix
                manager = get_api_key_manager()
                validated_user_id = manager.verify_key(api_key)

                if validated_user_id:
                    user_id = validated_user_id
                    logger.info(f"Authenticated as user: {user_id}")
                else:
                    # Invalid API key - send 401 error
                    logger.warning("Invalid API key provided")
                    error_response = b'{"error":"Invalid or expired API key"}'
                    await send(
                        {
                            "type": "http.response.start",
                            "status": 401,
                            "headers": [
                                [b"content-type", b"application/json"],
                                [b"www-authenticate", b"Bearer"],
                            ],
                        }
                    )
                    await send(
                        {
                            "type": "http.response.body",
                            "body": error_response,
                        }
                    )
                    return

        except Exception as e:
            logger.error(f"Authentication error: {e}", exc_info=True)
            # Continue with default_user on auth errors

    # Check if authentication is required (production mode)
    require_auth = os.getenv("KAGURA_REQUIRE_AUTH", "false").lower() == "true"
    if require_auth and (not user_id or user_id == "default_user"):
        # 401 Unauthorized - API key required
        error_response = json.dumps(
            {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32600,
                    "message": "API key required in production mode. "
                    "Set KAGURA_REQUIRE_AUTH=false for local development.",
                },
            }
        ).encode()

        await send(
            {
                "type": "http.response.start",
                "status": 401,
                "headers": [[b"content-type", b"application/json"]],
            }
        )
        await send({"type": "http.response.body", "body": error_response})
        return

    # Store user_id in scope for downstream use (if needed)
    scope["user_id"] = user_id

    # Get or create transport
    transport = get_mcp_transport()

    # Start background server task if not already running
    if _server_task is None:
        logger.info("Starting MCP server task (first request)")
        await _start_mcp_server()

        # Wait briefly for server to initialize
        # The connect() context manager needs time to set up
        await asyncio.sleep(0.1)  # 100ms should be enough

    # Log request
    method = scope.get("method", "UNKNOWN")
    path = scope.get("path", "")
    logger.info(f"MCP request: {method} {path} (user: {user_id})")

    # Delegate to transport's handle_request()
    await transport.handle_request(scope, receive, send)
