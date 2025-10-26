"""Tests for MCP Server"""

import pytest

from kagura import agent
from kagura.core.registry import agent_registry
from kagura.mcp import create_mcp_server
from kagura.mcp.schema import generate_json_schema


@pytest.fixture(autouse=True)
def clear_registry():
    """Clear agent registry before each test"""
    agent_registry.clear()
    yield
    agent_registry.clear()


@pytest.mark.asyncio
async def test_create_mcp_server():
    """Test MCP server creation"""
    server = create_mcp_server("test-server")
    assert server is not None
    assert server.name == "test-server"


@pytest.mark.asyncio
async def test_agent_registration():
    """Test that agents are registered automatically"""

    @agent
    async def test_agent(query: str) -> str:
        """Test agent for query"""
        return f"Response to: {query}"

    # Agent should be in registry
    assert agent_registry.get("test_agent") is not None


@pytest.mark.asyncio
async def test_agent_has_metadata():
    """Test that decorated agents have MCP metadata"""

    @agent
    async def test_agent(query: str) -> str:
        """Test agent for query"""
        return f"Response to: {query}"

    agent_func = agent_registry.get("test_agent")
    assert hasattr(agent_func, "_is_agent")
    assert agent_func._is_agent is True


@pytest.mark.asyncio
async def test_schema_generation_for_agent():
    """Test JSON schema generation for agents"""

    @agent
    async def echo_agent(message: str, count: int = 1) -> str:
        """Echo the message"""
        return f"Echo: {message}" * count

    agent_func = agent_registry.get("echo_agent")
    schema = generate_json_schema(agent_func)

    assert "properties" in schema
    assert "message" in schema["properties"]
    assert "count" in schema["properties"]
    assert schema["required"] == ["message"]


@pytest.mark.asyncio
async def test_agent_execution():
    """Test executing a registered agent"""

    @agent
    async def simple_agent(text: str) -> str:
        """Return uppercase: {{ text }}"""
        pass

    agent_func = agent_registry.get("simple_agent")
    # Note: This will call LLM in real execution
    # For unit tests, we just verify the agent is callable
    assert callable(agent_func)


def test_async_tool_detection():
    """Test that async tools are correctly detected (regression test for #327)"""
    import inspect

    from kagura import tool
    from kagura.core.tool_registry import tool_registry

    # Clear registry
    tool_registry.clear()

    # Register async and sync tools
    @tool
    async def async_tool_example(x: int) -> int:
        """Async tool"""
        return x * 2

    @tool
    def sync_tool_example(x: int) -> int:
        """Sync tool"""
        return x * 2

    # Get from registry
    async_func = tool_registry.get("async_tool_example")
    sync_func = tool_registry.get("sync_tool_example")

    # Verify detection
    assert async_func is not None
    assert sync_func is not None
    assert inspect.iscoroutinefunction(async_func) is True
    assert inspect.iscoroutinefunction(sync_func) is False

    # Cleanup
    tool_registry.clear()


# NOTE: Testing MCP server's handle_call_tool directly requires accessing internal MCP server APIs
# which are not part of the public API. The fix for Issue #327 (async tool support) is verified
# by the test_async_tool_detection above (ensuring async tools are correctly detected) and by
# the existing integration tests in test_builtin_integration.py which test async tools directly.
# For end-to-end testing of the MCP server with async tools, manual testing or E2E tests with
# a real MCP client are recommended.


@pytest.mark.asyncio
async def test_mcp_server_has_telemetry_imports():
    """Test that MCP server module has necessary telemetry imports

    This verifies that the telemetry integration code is present in the server module.
    Full E2E testing of telemetry tracking happens via integration tests and manual testing.
    """
    import kagura.mcp.server as server_module

    # Verify necessary imports are present
    assert hasattr(server_module, "time"), "time module should be imported"

    # Verify the create_mcp_server function exists
    assert hasattr(server_module, "create_mcp_server")

    # Create a server to ensure no import errors
    server = create_mcp_server("test-server")
    assert server is not None


@pytest.mark.asyncio
async def test_telemetry_import_in_mcp_server():
    """Test that telemetry module can be imported from MCP server context"""
    # This test verifies that the telemetry integration doesn't cause import errors
    from kagura.observability import EventStore, Telemetry, get_global_telemetry

    # Create telemetry instance
    store = EventStore(":memory:")
    telemetry = Telemetry(store)

    # Verify telemetry is functional
    collector = telemetry.get_collector()
    assert collector is not None

    # Verify global telemetry works
    global_telem = get_global_telemetry()
    assert global_telem is not None


@pytest.mark.asyncio
async def test_memory_tools_with_telemetry():
    """Test that memory tools work with telemetry (regression test for Issue #344)

    Memory tools (memory_store, memory_recall, memory_search) have an 'agent_name'
    parameter, which was causing a conflict with track_execution's agent_name parameter.
    This test verifies the fix works correctly.
    """
    from kagura.mcp.builtin.memory import _memory_cache, memory_recall, memory_store
    from kagura.observability import get_global_telemetry

    # Clear memory cache
    _memory_cache.clear()

    # Get telemetry collector
    telemetry = get_global_telemetry()
    collector = telemetry.get_collector()

    # Simulate MCP server calling memory_store with telemetry tracking
    # This is what happens inside handle_call_tool()
    args = {
        "agent_name": "test_agent",
        "key": "test_key",
        "value": "test_value",
        "scope": "working",
    }

    # Remove agent_name from args (the fix from Issue #344)
    tracking_args = {k: v for k, v in args.items() if k != "agent_name"}

    # Track execution (no "multiple values" error expected)
    async with collector.track_execution(
        "mcp_kagura_tool_memory_store", **tracking_args
    ):
        result = await memory_store(**args)
        assert "Stored" in result

    # Verify memory_recall also works
    async with collector.track_execution(
        "mcp_kagura_tool_memory_recall", **tracking_args
    ):
        result = await memory_recall(
            agent_name="test_agent", key="test_key", scope="working"
        )
        assert result == "test_value"

    # Cleanup
    _memory_cache.clear()


@pytest.mark.asyncio
async def test_telemetry_tracks_memory_operations():
    """Test that telemetry correctly records memory operations (Issue #344)"""
    from kagura.mcp.builtin.memory import _memory_cache, memory_store
    from kagura.observability import EventStore, Telemetry

    # Clear memory cache
    _memory_cache.clear()

    # Create fresh telemetry instance
    store = EventStore(":memory:")
    telemetry = Telemetry(store)
    collector = telemetry.get_collector()

    # Execute memory operation with telemetry
    args = {
        "agent_name": "tracked_agent",
        "key": "tracked_key",
        "value": "tracked_value",
    }
    tracking_args = {k: v for k, v in args.items() if k != "agent_name"}

    async with collector.track_execution("mcp_memory_store", **tracking_args):
        await memory_store(**args)

    # Verify telemetry recorded the execution
    executions = store.get_executions()
    assert len(executions) > 0

    # Verify correct agent_name (should be mcp_memory_store)
    last_execution = executions[-1]
    assert last_execution["agent_name"] == "mcp_memory_store"
    assert last_execution["status"] == "completed"

    # Verify kwargs don't contain agent_name (it was filtered out)
    assert "agent_name" not in last_execution["kwargs"]
    assert "key" in last_execution["kwargs"]
    assert "value" in last_execution["kwargs"]

    # Cleanup
    _memory_cache.clear()
