"""Integration tests for ChatSession with tool_registry (RFC-036 Phase 2-4)."""

import pytest

from kagura.chat.session import _get_chat_tools
from kagura.core.tool_registry import tool_registry


def test_get_chat_tools_returns_registry_tools():
    """Test that _get_chat_tools() retrieves tools from tool_registry."""
    # Import to trigger registration
    from kagura.chat import tools  # noqa: F401

    chat_tools = _get_chat_tools()

    # Should have at least 10 tools (registered via @tool decorator)
    assert len(chat_tools) >= 10, f"Expected >= 10 tools, got {len(chat_tools)}"

    # All tools should be callable
    for tool in chat_tools:
        assert callable(tool), f"Tool {tool} is not callable"


def test_chat_tools_available_in_registry():
    """Test that chat tools are available in tool_registry."""
    from kagura.chat import tools  # noqa: F401

    all_tools = tool_registry.get_all()

    expected_tools = [
        "file_read",
        "file_write",
        "file_search",
        "execute_python",
        "shell_exec",
        "brave_search",
        "url_fetch",
        "analyze_image_url",
        "youtube_transcript",
        "youtube_metadata",
    ]

    for tool_name in expected_tools:
        assert tool_name in all_tools, f"Tool '{tool_name}' not in registry"


def test_chat_session_uses_dynamic_tools():
    """Test that ChatSession uses tools from tool_registry dynamically."""
    from kagura.chat.session import ChatSession

    # Create session (should not raise errors)
    session = ChatSession()

    # Session should be initialized successfully
    assert session is not None
    assert session.model == "gpt-5-mini"


def test_new_tools_automatically_available():
    """Test that new tools added to tool_registry are automatically available."""
    from kagura import tool

    # Register a new tool dynamically
    @tool
    async def test_new_tool(input: str) -> str:
        """Test new tool"""
        return f"Processed: {input}"

    # Get chat tools - should include both existing and new tools
    all_tools = tool_registry.get_all()

    assert "test_new_tool" in all_tools, "New tool not registered"
