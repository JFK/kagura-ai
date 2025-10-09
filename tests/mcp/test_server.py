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
