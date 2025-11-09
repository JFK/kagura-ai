"""Tests for built-in MCP tools integration"""

import importlib
import sys

import pytest


@pytest.fixture(autouse=True, scope="function")
def reset_and_import_builtin():
    """Reset tool registry and ensure builtin modules are imported before each test

    This is necessary for parallel test execution (pytest-xdist) where each
    worker has its own isolated registry.
    """
    from kagura.core.tool_registry import tool_registry

    # Clear registry to ensure clean state
    tool_registry.clear()

    # Force reload of builtin modules to trigger @tool registration
    # Note: v4.3.0 moved tools to kagura.mcp.tools.*, so import both
    builtin_modules = [
        # v4.3.0: Import actual tool modules first (builtin is now facade)
        "kagura.mcp.tools.memory.storage",
        "kagura.mcp.tools.memory.search",
        "kagura.mcp.tools.memory.list_and_feedback",
        "kagura.mcp.tools.memory.graph",
        "kagura.mcp.tools.memory.user_pattern",
        "kagura.mcp.tools.memory.stats",
        "kagura.mcp.tools.memory.timeline",
        "kagura.mcp.tools.memory.tool_history",
        "kagura.mcp.tools.memory.chunks",
        "kagura.mcp.tools.memory",
        # Builtin facades (for backward compatibility)
        "kagura.mcp.builtin.memory",
        "kagura.mcp.builtin.file_ops",
        "kagura.mcp.builtin.web",
        "kagura.mcp.builtin.youtube",
        "kagura.mcp.builtin.media",
        "kagura.mcp.builtin.fact_check",
        "kagura.mcp.builtin.brave_search",
        "kagura.mcp.builtin.cache",
        "kagura.mcp.builtin.routing",
        "kagura.mcp.builtin.observability",
        "kagura.mcp.builtin.meta",
    ]

    for module_name in builtin_modules:
        if module_name in sys.modules:
            importlib.reload(sys.modules[module_name])
        else:
            importlib.import_module(module_name)

    # Verify import worked
    tools = tool_registry.get_all()
    assert len(tools) > 0, "Builtin tools should be registered after import"

    yield

    # Cleanup after test
    tool_registry.clear()


def test_mcp_server_includes_builtin_tools():
    """Test that MCP server recognizes built-in tools"""
    from kagura.core.tool_registry import tool_registry

    tools = tool_registry.get_all()

    # Check built-in tools are present in registry
    assert "memory_store" in tools
    assert "memory_recall" in tools
    assert "file_read" in tools
    assert "file_write" in tools
    assert "brave_web_search" in tools


@pytest.mark.asyncio
async def test_memory_store_tool():
    """Test memory_store tool"""
    import kagura.mcp.builtin  # noqa: F401
    from kagura.core.tool_registry import tool_registry

    tool_func = tool_registry.get("memory_store")
    assert tool_func is not None

    result = await tool_func(
        user_id="test_user",
        agent_name="test",
        key="user_name",
        value="Alice",
        scope="session",
    )

    assert "Stored" in result
    assert "user_name" in result
    # New compact format: "✓ Stored: user_name (session, local, RAG✗)"
    assert "session" in result or "working" in result


@pytest.mark.asyncio
async def test_file_read_tool():
    """Test file_read tool"""
    import tempfile

    import kagura.mcp.builtin  # noqa: F401
    from kagura.core.tool_registry import tool_registry

    # Create temp file
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("Hello, World!")
        temp_path = f.name

    tool_func = tool_registry.get("file_read")
    assert tool_func is not None

    result = tool_func(path=temp_path)

    assert "Hello, World!" in result

    # Cleanup
    import os

    os.unlink(temp_path)


def test_file_read_via_registry():
    """Test executing file_read via tool registry"""
    import tempfile

    import kagura.mcp.builtin  # noqa: F401
    from kagura.core.tool_registry import tool_registry

    # Create temp file
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("Test content")
        temp_path = f.name

    # Get tool from registry
    file_read_tool = tool_registry.get("file_read")
    assert file_read_tool is not None

    # Execute
    result = file_read_tool(path=temp_path)

    assert "Test content" in result

    # Cleanup
    import os

    os.unlink(temp_path)


def test_builtin_tools_auto_register():
    """Test that builtin module has tools registered"""
    import kagura.mcp.builtin  # noqa: F401
    from kagura.core.tool_registry import tool_registry

    tools = tool_registry.get_all()

    # Check specific built-in tools are registered
    assert "memory_store" in tools
    assert "memory_recall" in tools
    assert "file_read" in tools
    assert "file_write" in tools
    assert "brave_web_search" in tools

    # Should have at least 10 built-in tools
    assert len(tools) >= 10
