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
