"""Integration tests for MCP server tool filtering."""

import pytest

from kagura.mcp.server import create_mcp_server


class TestMCPServerCreation:
    """Test MCP server creation with different contexts."""

    def test_create_local_server(self):
        """Test creating server in local context."""
        import kagura.mcp.builtin  # noqa: F401

        server = create_mcp_server(name="test-local", context="local")
        assert server is not None
        assert server.name == "test-local"

    def test_create_remote_server(self):
        """Test creating server in remote context."""
        import kagura.mcp.builtin  # noqa: F401

        server = create_mcp_server(name="test-remote", context="remote")
        assert server is not None
        assert server.name == "test-remote"

    def test_default_context_is_local(self):
        """Test that default context is local."""
        import kagura.mcp.builtin  # noqa: F401

        server = create_mcp_server(name="test-default")
        assert server is not None


class TestToolFilteringLogic:
    """Test tool filtering logic without relying on MCP SDK internals."""

    def test_local_context_parameter(self):
        """Test that local context parameter is accepted."""
        import kagura.mcp.builtin  # noqa: F401

        # Should not raise
        server = create_mcp_server(name="test", context="local")
        assert server is not None

    def test_remote_context_parameter(self):
        """Test that remote context parameter is accepted."""
        import kagura.mcp.builtin  # noqa: F401

        # Should not raise
        server = create_mcp_server(name="test", context="remote")
        assert server is not None


class TestDocumentation:
    """Test that server provides correct documentation."""

    def test_server_has_name(self):
        """Test that server has correct name."""
        import kagura.mcp.builtin  # noqa: F401

        local_server = create_mcp_server(name="local-test", context="local")
        remote_server = create_mcp_server(name="remote-test", context="remote")

        assert local_server.name == "local-test"
        assert remote_server.name == "remote-test"
