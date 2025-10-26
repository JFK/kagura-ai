"""MCP over HTTP/SSE endpoint for ChatGPT Connector support.

Implements MCP Streamable HTTP transport (2025-03-26 spec) for:
- ChatGPT Connectors (https://developers.openai.com/apps-sdk/deploy/connect-chatgpt/)
- Other HTTP-based MCP clients

Endpoint: POST/GET /mcp
"""

from typing import Any

from fastapi import APIRouter, Header, Request
from fastapi.responses import StreamingResponse
from mcp.server import Server
from mcp.server.sse import SseServerTransport

from kagura.mcp.server import create_mcp_server

router = APIRouter()

# Global MCP server instance (shared across requests)
_mcp_server: Server | None = None


def get_mcp_server() -> Server:
    """Get or create shared MCP server instance.

    Returns:
        Shared MCP Server instance with all Kagura tools registered
    """
    global _mcp_server

    if _mcp_server is None:
        _mcp_server = create_mcp_server(name="kagura-api")

    return _mcp_server


@router.post("/mcp")
@router.get("/mcp")
async def mcp_endpoint(
    request: Request,
    x_user_id: str | None = Header(None),
    authorization: str | None = Header(None),
) -> Any:
    """MCP over HTTP/SSE endpoint.

    Supports both POST (JSON-RPC requests) and GET (SSE streaming).

    Authentication:
        - X-User-ID header: User identifier (optional, default="default_user")
        - Authorization header: Bearer {api_key} (Phase C.2, optional for now)

    ChatGPT Connector Setup:
        1. Enable Developer Mode in ChatGPT settings
        2. Go to Settings → Connectors → Advanced → Developer Mode
        3. Add custom connector:
           - Name: Kagura Memory
           - URL: https://your-server.com/mcp
           - Description: Universal AI Memory Platform

    Args:
        request: FastAPI request object
        x_user_id: User ID from header (optional)
        authorization: API key from header (optional, future)

    Returns:
        StreamingResponse (SSE) or JSONResponse

    Raises:
        HTTPException: If authentication fails or invalid request

    Note:
        For local development, use ngrok to expose this endpoint:
        ```bash
        ngrok http 8000
        # Use https://xxxxx.ngrok.app/mcp in ChatGPT
        ```
    """
    # Extract user_id (default to "default_user")
    _user_id = x_user_id or "default_user"  # TODO: Use in Task 2 (auth)

    # TODO: API Key authentication (Phase C Task 2)
    # if authorization:
    #     api_key = authorization.replace("Bearer ", "")
    #     if not verify_api_key(api_key):
    #         raise HTTPException(status_code=401, detail="Invalid API key")

    # Get MCP server
    _server = get_mcp_server()  # TODO: Use in request handling

    # Create SSE transport
    # TODO: Switch to StreamableHTTPTransport when available in SDK
    _transport = SseServerTransport(endpoint="/mcp")  # TODO: Use in SSE setup

    # Handle request based on method
    if request.method == "POST":
        # JSON-RPC request
        body = await request.json()

        # TODO: Process JSON-RPC request via MCP server
        # This requires integrating with MCP server's request handling

        return {
            "jsonrpc": "2.0",
            "id": body.get("id"),
            "result": {"status": "not_implemented", "message": "Phase C Task 1 WIP"},
        }

    else:  # GET
        # SSE streaming
        async def event_generator():
            """Generate SSE events for MCP streaming."""
            # TODO: Implement SSE event streaming
            yield "data: {}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",  # Disable nginx buffering
            },
        )
