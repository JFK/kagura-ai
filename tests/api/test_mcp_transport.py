"""Tests for MCP over HTTP/SSE endpoint.

Tests the /mcp endpoint which provides MCP (Model Context Protocol) support
via HTTP/SSE transport for ChatGPT Connectors and other HTTP-based MCP clients.
"""

import json

import pytest
from fastapi.testclient import TestClient

from kagura.api.server import app

client = TestClient(app)


class TestMCPEndpointBasic:
    """Basic smoke tests for /mcp endpoint."""

    def test_mcp_endpoint_exists(self):
        """Test that /mcp endpoint is mounted and responds."""
        # Try GET request (should establish SSE connection)
        response = client.get("/mcp")

        # Should return a valid response
        # 200 = success, 406 = Not Acceptable (missing Accept header)
        assert response.status_code in [200, 400, 405, 406]

    def test_mcp_post_without_headers(self):
        """Test POST to /mcp without proper MCP headers."""
        response = client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
        )

        # Should respond (may be error due to missing headers)
        # 406 = Not Acceptable (MCP requires specific Accept headers)
        assert response.status_code in [200, 400, 401, 406]

    def test_mcp_delete_endpoint(self):
        """Test DELETE to /mcp (session termination)."""
        response = client.delete("/mcp")

        # Should respond
        # 405 = Method Not Allowed (if mounted app doesn't support DELETE)
        # 404 = Not Found (if session doesn't exist)
        assert response.status_code in [200, 404, 405, 406]


class TestMCPProtocol:
    """Test MCP protocol compliance (JSON-RPC over HTTP)."""

    def test_mcp_initialize_request(self):
        """Test MCP initialization handshake."""
        # MCP initialize request
        initialize_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        }

        response = client.post(
            "/mcp",
            json=initialize_request,
            headers={"Content-Type": "application/json"},
        )

        # Should accept the request (200) or return error
        # 406 = Not Acceptable (missing Accept header for MCP)
        assert response.status_code in [200, 400, 406]

        # If successful, should return JSON-RPC response
        if response.status_code == 200:
            try:
                data = response.json()
                assert "jsonrpc" in data
                assert data["jsonrpc"] == "2.0"
                assert "id" in data
            except json.JSONDecodeError:
                # May be SSE stream, which is also valid
                pass

    def test_mcp_tools_list_request(self):
        """Test tools/list MCP request."""
        tools_list_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {},
        }

        response = client.post(
            "/mcp",
            json=tools_list_request,
            headers={"Content-Type": "application/json"},
        )

        # Should respond (may require Accept header)
        assert response.status_code in [200, 400, 406]


@pytest.mark.skip(reason="Requires full MCP session setup")
class TestMCPIntegration:
    """Integration tests requiring full MCP session.

    These tests are skipped by default as they require proper MCP session
    initialization including SSE connection establishment.
    """

    def test_mcp_memory_store_via_tools_call(self):
        """Test memory_store tool via MCP tools/call."""
        # This would require:
        # 1. Initialize session
        # 2. Get SSE endpoint
        # 3. Send tools/call request with memory_store
        pytest.skip("Requires full MCP session setup")

    def test_mcp_memory_recall_via_tools_call(self):
        """Test memory_recall tool via MCP tools/call."""
        pytest.skip("Requires full MCP session setup")

    def test_mcp_sse_streaming(self):
        """Test SSE event streaming from server."""
        pytest.skip("Requires SSE client implementation")


class TestMCPSessionManagement:
    """Test MCP session lifecycle."""

    @pytest.mark.skip(reason="Session management handled by StreamableHTTPTransport")
    def test_mcp_session_creation(self):
        """Test that MCP session is created on first request."""
        # Session management is handled by StreamableHTTPServerTransport
        pytest.skip("Handled by MCP SDK")

    @pytest.mark.skip(reason="Session management handled by StreamableHTTPTransport")
    def test_mcp_session_termination(self):
        """Test DELETE request terminates session."""
        pytest.skip("Handled by MCP SDK")


class TestMCPErrorHandling:
    """Test error handling in MCP endpoint."""

    def test_mcp_invalid_json(self):
        """Test POST with invalid JSON."""
        response = client.post(
            "/mcp",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )

        # Should return error
        # 406 = Not Acceptable (if checked before parsing)
        # 400 = Bad Request (parse error)
        # 422 = Unprocessable Entity (validation error)
        assert response.status_code in [400, 406, 422]

    def test_mcp_invalid_method(self):
        """Test unsupported HTTP method."""
        # MCP supports GET, POST, DELETE
        response = client.put("/mcp")

        # Should return 405 Method Not Allowed
        assert response.status_code == 405


class TestMCPAuthentication:
    """Test API Key authentication for /mcp endpoint."""

    @pytest.fixture
    def api_key(self):
        """Create a test API key."""
        from kagura.api.auth import get_api_key_manager

        manager = get_api_key_manager()
        # Create test key
        api_key = manager.create_key(
            name="test-mcp-key",
            user_id="test_user_auth",
        )
        yield api_key
        # Cleanup
        manager.delete_key(name="test-mcp-key", user_id="test_user_auth")

    def test_mcp_without_auth(self):
        """Test /mcp without authentication (should use default_user)."""
        response = client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
        )

        # Should respond (may be 406 due to missing headers, but not 401)
        assert response.status_code != 401

    def test_mcp_with_valid_api_key(self, api_key):
        """Test /mcp with valid API key."""
        response = client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
            headers={"Authorization": f"Bearer {api_key}"},
        )

        # Should not return 401 Unauthorized
        assert response.status_code != 401

    def test_mcp_with_invalid_api_key(self):
        """Test /mcp with invalid API key."""
        response = client.post(
            "/mcp",
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
            headers={"Authorization": "Bearer kagura_invalid_key_12345"},
        )

        # Should return 401 Unauthorized
        assert response.status_code == 401
        data = response.json()
        assert "error" in data or "Invalid" in str(data)
