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
from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4

from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import Receive, Scope, Send

from kagura.mcp.server import create_mcp_server

logger = logging.getLogger(__name__)


@dataclass
class MCPSession:
    """Represents an active MCP session for a specific client.

    Each session has its own transport, server instance, and background task.
    This allows multiple clients to connect simultaneously without conflicts.
    """
    session_id: str
    user_id: str
    transport: SseServerTransport
    server: Server
    task: asyncio.Task | None = None  # Optional: may not be started yet
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_active_at: datetime = field(default_factory=datetime.utcnow)


class MCPSessionManager:
    """Manages multiple MCP sessions for concurrent clients.

    Fixes Issue #XXX: 409 Conflict error when multiple clients connect to /mcp/sse.

    The previous implementation used a single global StreamableHTTPServerTransport,
    which only allows one SSE connection at a time. This manager creates isolated
    sessions for each client, enabling true multi-client support.
    """

    def __init__(self):
        self._sessions: dict[str, MCPSession] = {}
        self._lock = asyncio.Lock()

    async def get_or_create_session(
        self,
        user_id: str,
        session_id: str | None = None
    ) -> MCPSession:
        """Get existing session or create new one.

        Args:
            user_id: Authenticated user ID
            session_id: Optional session ID from client header

        Returns:
            MCPSession instance (new or existing)
        """
        async with self._lock:
            # Generate session ID if not provided
            if session_id is None:
                session_id = f"mcp-{uuid4().hex[:16]}"

            # Return existing session if found
            if session_id in self._sessions:
                session = self._sessions[session_id]
                session.last_active_at = datetime.utcnow()
                logger.info(f"Reusing existing MCP session: {session_id} (user: {user_id})")
                return session

            # Create new session
            logger.info(f"Creating new MCP session: {session_id} (user: {user_id})")

            # Load built-in MCP tools
            try:
                import kagura.mcp.tools  # noqa: F401  # Auto-register tools
                logger.debug("Loaded built-in MCP tools")
            except ImportError:
                logger.warning("Could not load built-in MCP tools")

            # Create isolated transport for this session
            # Use SSE transport for Claude Code compatibility
            # Use relative path - root_path will be added automatically
            transport = SseServerTransport(
                endpoint=f"/messages/{session_id}/"  # Relative POST endpoint
            )

            # Create isolated server for this session
            server = create_mcp_server(
                name=f"kagura-api-{session_id}",
                context="remote",  # Filter dangerous tools
            )

            # Don't start task yet - will start when SSE connection is established
            task = None

            session = MCPSession(
                session_id=session_id,
                user_id=user_id,
                transport=transport,
                server=server,
                task=task,
            )

            self._sessions[session_id] = session
            logger.info(f"MCP session created: {session_id} (total sessions: {len(self._sessions)})")
            return session

    async def _run_mcp_server(self, session_id: str, server: Server, transport: StreamableHTTPServerTransport):
        """Background task to run MCP server for a session.

        Args:
            session_id: Session identifier for logging
            server: MCP server instance
            transport: StreamableHTTPServerTransport instance
        """
        try:
            logger.info(f"Starting MCP server task for session: {session_id}")
            async with transport.connect() as (read_stream, write_stream):
                await server.run(
                    read_stream,
                    write_stream,
                    server.create_initialization_options(),
                )
        except asyncio.CancelledError:
            logger.info(f"MCP server task cancelled for session: {session_id}")
            raise
        except Exception as e:
            logger.error(f"MCP server error for session {session_id}: {e}", exc_info=True)
        finally:
            logger.info(f"MCP server task ended for session: {session_id}")

    async def remove_session(self, session_id: str):
        """Remove and cleanup session.

        Args:
            session_id: Session ID to remove
        """
        async with self._lock:
            if session_id in self._sessions:
                session = self._sessions.pop(session_id)
                logger.info(f"Removing MCP session: {session_id} (remaining: {len(self._sessions)})")

                # Cancel background task
                session.task.cancel()
                try:
                    await session.task
                except asyncio.CancelledError:
                    pass

                # Terminate transport
                await session.transport.terminate()

    async def cleanup_inactive_sessions(self, timeout_seconds: int = 3600):
        """Remove sessions inactive for more than timeout_seconds.

        Args:
            timeout_seconds: Inactivity timeout (default: 1 hour)
        """
        async with self._lock:
            now = datetime.utcnow()
            to_remove = []

            for session_id, session in self._sessions.items():
                inactive_seconds = (now - session.last_active_at).total_seconds()
                if inactive_seconds > timeout_seconds:
                    to_remove.append(session_id)

            for session_id in to_remove:
                logger.info(f"Cleaning up inactive session: {session_id}")
                await self.remove_session(session_id)


# Global session manager
_session_manager = MCPSessionManager()




async def mcp_asgi_app(scope: Scope, receive: Receive, send: Send) -> None:
    """ASGI app for MCP over HTTP/SSE with multi-client support.

    Supports:
    - GET: SSE streaming (server → client messages)
    - POST: JSON-RPC requests (client → server messages)
    - DELETE: Session termination

    Multi-Client Architecture:
        Each client gets an isolated MCP session with its own:
        - StreamableHTTPServerTransport instance
        - MCP Server instance
        - Background task for server.run()

        This fixes the 409 Conflict error that occurred when multiple
        clients tried to connect to the same global transport.

    Authentication:
        - Authorization header: Bearer {api_key} (recommended for production)
        - If no auth: uses "default_user" (local development only)

    Session Management:
        - Session ID can be provided via mcp-session-id header
        - If not provided, auto-generated UUID is used
        - Sessions are isolated per user_id + session_id
        - Inactive sessions are cleaned up after timeout

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

    Args:
        scope: ASGI scope dict
        receive: ASGI receive callable
        send: ASGI send callable
    """
    # DEBUG: Print to stdout (bypasses logger configuration)
    method = scope.get("method", "UNKNOWN")
    path = scope.get("path", "")
    print(f"\n[MCP_ASGI_APP] ========== NEW REQUEST ==========")
    print(f"[MCP_ASGI_APP] {method} {path}")
    print(f"[MCP_ASGI_APP] Scope type: {scope.get('type')}")
    print(f"[MCP_ASGI_APP] Headers: {dict(scope.get('headers', []))}")
    logger.info(f"=== MCP Request START: {method} {path} ===")

    # Extract headers for authentication and session management
    headers = dict(scope.get("headers", []))

    # Log all headers for debugging
    logger.info(f"Request headers: {[(k.decode() if isinstance(k, bytes) else k, v.decode()[:50] if isinstance(v, bytes) else str(v)[:50]) for k, v in headers.items()]}")

    # Authenticate request (supports OAuth2 and API Key)
    # Issue #674: Unified authentication for ChatGPT (OAuth2) and Claude Code (API Key)
    auth_header = headers.get(b"authorization")
    logger.info(f"Authorization header present: {auth_header is not None}")

    try:
        from kagura.auth.mcp_auth import authenticate_mcp_request

        user_id = await authenticate_mcp_request(
            authorization_header=auth_header,
            allow_anonymous=True,  # Allow default_user for local development
        )
        logger.info(f"Authenticated as user: {user_id}")

    except Exception as auth_error:
        # Authentication failed - send 401 error
        logger.warning(f"Authentication failed: {auth_error}")
        error_response = json.dumps({
            "error": "Unauthorized",
            "message": str(auth_error),
        }).encode("utf-8")
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

    # Extract session ID from headers (or None to auto-generate)
    session_id = headers.get(b"mcp-session-id")
    if session_id:
        session_id = session_id.decode("utf-8")

    # Get or create session for this client
    logger.info(f"Getting/creating session for user: {user_id}, session_id: {session_id}")
    try:
        session = await _session_manager.get_or_create_session(
            user_id=user_id,
            session_id=session_id,
        )
        logger.info(f"Session created/retrieved: {session.session_id}")
    except Exception as e:
        logger.error(f"Failed to create MCP session: {e}", exc_info=True)
        error_response = json.dumps({
            "jsonrpc": "2.0",
            "error": {
                "code": -32603,
                "message": f"Internal error: Failed to create session - {str(e)}"
            }
        }).encode()
        await send({
            "type": "http.response.start",
            "status": 500,
            "headers": [[b"content-type", b"application/json"]],
        })
        await send({"type": "http.response.body", "body": error_response})
        return

    # Wait briefly for server task to initialize (first time only)
    await asyncio.sleep(0.05)  # 50ms

    # Log request
    logger.info(f"Processing MCP request: {method} {path} (user: {user_id}, session: {session.session_id})")

    # Fix path for transport: Remove /mcp prefix if present
    # StreamableHTTPServerTransport expects /sse, /message, etc.
    # But we receive /mcp/sse, /mcp/message from the Mount
    normalized_path = path
    if path.startswith("/mcp/"):
        normalized_path = path[4:]  # Remove "/mcp" prefix
        print(f"[MCP_ASGI_APP] Normalized path: {path} -> {normalized_path}")
    elif path == "/mcp":
        normalized_path = "/"
        print(f"[MCP_ASGI_APP] Normalized path: {path} -> {normalized_path}")

    # Create modified scope with normalized path
    modified_scope = dict(scope)
    modified_scope["path"] = normalized_path
    modified_scope["raw_path"] = normalized_path.encode()
    # Keep root_path for SSE transport to generate correct endpoint URL
    # root_path will be combined with transport endpoint in connect_sse()
    print(f"[MCP_ASGI_APP] Modified scope path: {modified_scope['path']}, root_path: {modified_scope['root_path']}")

    # Delegate to session's transport based on method
    try:
        print(f"[MCP_ASGI_APP] Handling {method} request, normalized_path: {normalized_path}")

        if method == "GET" and normalized_path == "/sse":
            # Handle SSE stream establishment
            print(f"[MCP_ASGI_APP] Establishing SSE connection...")
            request = Request(modified_scope, receive)

            # Use connect_sse context manager
            print(f"[MCP_ASGI_APP] Calling transport.connect_sse()...")
            async with session.transport.connect_sse(
                modified_scope, receive, send
            ) as streams:
                print(f"[MCP_ASGI_APP] SSE connected, got streams")
                # Start MCP server with the streams
                read_stream, write_stream = streams
                print(f"[MCP_ASGI_APP] read_stream type: {type(read_stream)}, write_stream type: {type(write_stream)}")

                # Start MCP server task if not already started
                if session.task is None:
                    print(f"[MCP_ASGI_APP] Creating MCP server task...")
                    session.task = asyncio.create_task(
                        session.server.run(
                            read_stream,
                            write_stream,
                            session.server.create_initialization_options()
                        )
                    )
                    print(f"[MCP_ASGI_APP] MCP server task created, waiting...")

                # Wait for the task to complete (when client disconnects)
                try:
                    await session.task
                    print(f"[MCP_ASGI_APP] MCP server task completed normally")
                except Exception as e:
                    print(f"[MCP_ASGI_APP] MCP server task failed: {type(e).__name__}: {e}")
                    import traceback
                    traceback.print_exc()
                    raise

            print(f"[MCP_ASGI_APP] Exited connect_sse context manager")
            # Return empty response to avoid NoneType error
            return

        elif method == "POST" and normalized_path.startswith("/messages/"):
            # Handle POST message
            # Extract session ID from path: /messages/{session_id}/
            # Example: /messages/mcp-51e68893a1ab45c0/ -> mcp-51e68893a1ab45c0
            parts = normalized_path.strip("/").split("/")
            if len(parts) >= 2:
                post_session_id = parts[1]
                print(f"[MCP_ASGI_APP] POST request for session: {post_session_id}")

                # Get the session for this POST request
                # Note: We need to find the session by ID
                if post_session_id in _session_manager._sessions:
                    post_session = _session_manager._sessions[post_session_id]
                    print(f"[MCP_ASGI_APP] Found session, handling POST message...")
                    try:
                        await post_session.transport.handle_post_message(modified_scope, receive, send)
                        print(f"[MCP_ASGI_APP] POST message handled successfully")
                    except Exception as e:
                        print(f"[MCP_ASGI_APP] POST message failed: {type(e).__name__}: {e}")
                        import traceback
                        traceback.print_exc()
                        raise
                else:
                    print(f"[MCP_ASGI_APP] Session {post_session_id} not found in {list(_session_manager._sessions.keys())}")
                    error_response = Response(f"Session not found: {post_session_id}", status_code=404)
                    await error_response(modified_scope, receive, send)
            else:
                print(f"[MCP_ASGI_APP] Invalid POST path: {normalized_path}")
                error_response = Response("Invalid POST path", status_code=400)
                await error_response(modified_scope, receive, send)

        else:
            # Unsupported path/method
            print(f"[MCP_ASGI_APP] Unsupported: {method} {normalized_path}")
            error_response = Response("Not Found", status_code=404)
            await error_response(modified_scope, receive, send)

        print(f"[MCP_ASGI_APP] === MCP Request END: {method} {path} ===")
    except Exception as e:
        print(f"[MCP_ASGI_APP] Exception: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise
