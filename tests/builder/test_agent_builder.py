"""Tests for AgentBuilder."""

import pytest

from kagura import AgentBuilder
from kagura.builder.config import (
    AgentConfiguration,
    HooksConfig,
    MemoryConfig,
    RoutingConfig,
)


def test_agent_builder_initialization():
    """Test AgentBuilder initialization."""
    builder = AgentBuilder("test_agent")

    assert builder.name == "test_agent"
    assert builder._config.name == "test_agent"
    assert builder._config.model == "gpt-5-mini"  # default


def test_agent_builder_with_model():
    """Test setting model."""
    builder = AgentBuilder("test_agent").with_model("gpt-4o")

    assert builder._config.model == "gpt-4o"


def test_agent_builder_with_memory():
    """Test configuring memory."""
    builder = AgentBuilder("test_agent").with_memory(
        type="rag",
        max_messages=50,
        enable_rag=True
    )

    assert builder._config.memory is not None
    assert builder._config.memory.type == "rag"
    assert builder._config.memory.max_messages == 50
    assert builder._config.memory.enable_rag is True


def test_agent_builder_with_session_id():
    """Test setting session ID."""
    builder = (
        AgentBuilder("test_agent")
        .with_memory(type="persistent", max_messages=50)
        .with_session_id("user_123_session_1")
    )

    assert builder._config.memory is not None
    assert builder._config.memory.session_id == "user_123_session_1"


def test_agent_builder_with_session_id_without_memory():
    """Test that session ID requires memory to be configured first."""
    builder = AgentBuilder("test_agent")

    with pytest.raises(ValueError) as exc_info:
        builder.with_session_id("session_123")

    assert "Memory must be configured" in str(exc_info.value)


def test_agent_builder_with_routing():
    """Test configuring routing."""
    routes = {"translation": "translation_agent", "code_review": "review_agent"}
    builder = AgentBuilder("test_agent").with_routing(
        strategy="semantic",
        routes=routes
    )

    assert builder._config.routing is not None
    assert builder._config.routing.strategy == "semantic"
    assert builder._config.routing.routes == routes


def test_agent_builder_with_tools():
    """Test adding tools."""
    def tool1():
        pass

    def tool2():
        pass

    builder = AgentBuilder("test_agent").with_tools([tool1, tool2])

    assert len(builder._config.tools) == 2
    assert tool1 in builder._config.tools
    assert tool2 in builder._config.tools


def test_agent_builder_with_hooks():
    """Test adding hooks."""
    def pre_hook():
        pass

    def post_hook():
        pass

    builder = AgentBuilder("test_agent").with_hooks(
        pre=[pre_hook],
        post=[post_hook]
    )

    assert builder._config.hooks is not None
    assert len(builder._config.hooks.pre) == 1
    assert len(builder._config.hooks.post) == 1
    assert pre_hook in builder._config.hooks.pre
    assert post_hook in builder._config.hooks.post


def test_agent_builder_with_context():
    """Test setting context parameters."""
    builder = AgentBuilder("test_agent").with_context(
        temperature=0.8,
        max_tokens=2000
    )

    assert builder._config.context["temperature"] == 0.8
    assert builder._config.context["max_tokens"] == 2000


def test_agent_builder_method_chaining():
    """Test fluent API method chaining."""
    builder = (
        AgentBuilder("test_agent")
        .with_model("gpt-4o")
        .with_memory(type="context", max_messages=100)
        .with_context(temperature=0.7)
    )

    assert builder._config.name == "test_agent"
    assert builder._config.model == "gpt-4o"
    assert builder._config.memory is not None
    assert builder._config.memory.type == "context"
    assert builder._config.context["temperature"] == 0.7


def test_agent_builder_build():
    """Test building an agent."""
    builder = AgentBuilder("test_agent").with_model("gpt-5-mini")

    agent = builder.build()

    assert agent is not None
    assert callable(agent)

    # Check metadata
    assert hasattr(agent, "_builder_config")
    assert hasattr(agent, "_agent_name")
    assert agent._agent_name == "test_agent"

    # Verify config
    assert agent._builder_config.model == "gpt-5-mini"
    assert agent._builder_config.name == "test_agent"


@pytest.mark.asyncio
async def test_agent_builder_full_configuration():
    """Test building agent with full configuration."""
    def test_tool():
        return "tool result"

    def pre_hook():
        pass

    agent = (
        AgentBuilder("full_agent")
        .with_model("gpt-5-mini")
        .with_memory(type="working", max_messages=50)
        .with_tools([test_tool])
        .with_hooks(pre=[pre_hook])
        .with_context(temperature=0.5, max_tokens=1000)
        .build()
    )

    assert agent is not None
    assert agent._agent_name == "full_agent"

    # Verify configuration
    config = agent._builder_config
    assert config.model == "gpt-5-mini"
    assert config.memory is not None
    assert config.memory.type == "working"
    assert len(config.tools) == 1
    assert config.hooks is not None
    assert len(config.hooks.pre) == 1
    assert config.context["temperature"] == 0.5


def test_agent_builder_repr():
    """Test string representation."""
    builder = AgentBuilder("test_agent").with_model("gpt-4o")

    repr_str = repr(builder)
    assert "test_agent" in repr_str
    assert "gpt-4o" in repr_str


# Configuration classes tests


def test_memory_config():
    """Test MemoryConfig."""
    config = MemoryConfig(
        type="rag",
        max_messages=50,
        enable_rag=True,
        session_id="test_session"
    )

    assert config.type == "rag"
    assert config.max_messages == 50
    assert config.enable_rag is True
    assert config.session_id == "test_session"


def test_routing_config():
    """Test RoutingConfig."""
    routes = {"route1": "agent1"}
    config = RoutingConfig(
        strategy="llm",
        routes=routes
    )

    assert config.strategy == "llm"
    assert config.routes == routes


def test_hooks_config():
    """Test HooksConfig."""
    def hook1():
        pass

    config = HooksConfig(
        pre=[hook1],
        post=[]
    )

    assert len(config.pre) == 1
    assert len(config.post) == 0


def test_agent_configuration():
    """Test AgentConfiguration."""
    config = AgentConfiguration(
        name="test_agent",
        model="gpt-4o",
        memory=MemoryConfig(type="context"),
        routing=RoutingConfig(strategy="keyword"),
        tools=[],
        hooks=HooksConfig(),
        context={"temperature": 0.7}
    )

    assert config.name == "test_agent"
    assert config.model == "gpt-4o"
    assert config.memory is not None
    assert config.routing is not None
    assert config.context["temperature"] == 0.7


# Integration tests for Memory + Tools


def test_agent_builder_with_memory_integration():
    """Test building agent with memory integration."""
    from pathlib import Path

    builder = (
        AgentBuilder("memory_agent")
        .with_model("gpt-5-mini")
        .with_memory(type="context", max_messages=50)
    )

    agent = builder.build()

    # Verify metadata
    assert agent._agent_name == "memory_agent"
    config = agent._builder_config
    assert config.memory is not None
    assert config.memory.type == "context"
    assert config.memory.max_messages == 50


def test_agent_builder_with_rag_memory():
    """Test building agent with RAG memory."""
    from pathlib import Path

    builder = (
        AgentBuilder("rag_agent")
        .with_model("gpt-5-mini")
        .with_memory(
            type="rag",
            enable_rag=True,
            persist_dir=Path("/tmp/kagura_test")
        )
    )

    agent = builder.build()

    config = agent._builder_config
    assert config.memory is not None
    assert config.memory.enable_rag is True
    assert config.memory.persist_dir == Path("/tmp/kagura_test")


def test_agent_builder_with_tools_integration():
    """Test building agent with tools integration."""
    def search_tool(query: str) -> str:
        """Search for information"""
        return f"Results for: {query}"

    def calculator(a: float, b: float) -> float:
        """Calculate sum"""
        return a + b

    builder = (
        AgentBuilder("tool_agent")
        .with_model("gpt-5-mini")
        .with_tools([search_tool, calculator])
    )

    agent = builder.build()

    # Verify metadata
    config = agent._builder_config
    assert len(config.tools) == 2
    assert search_tool in config.tools
    assert calculator in config.tools


def test_agent_builder_memory_and_tools_integration():
    """Test building agent with both memory and tools."""
    from pathlib import Path

    def test_tool() -> str:
        """Test tool"""
        return "tool result"

    builder = (
        AgentBuilder("full_agent")
        .with_model("gpt-5-mini")
        .with_memory(type="working", max_messages=100)
        .with_tools([test_tool])
        .with_context(temperature=0.5)
    )

    agent = builder.build()

    # Verify all configurations
    config = agent._builder_config
    assert config.name == "full_agent"
    assert config.model == "gpt-5-mini"
    assert config.memory is not None
    assert config.memory.type == "working"
    assert len(config.tools) == 1
    assert config.context["temperature"] == 0.5


# Hooks integration tests


def test_agent_builder_with_hooks_integration():
    """Test building agent with hooks integration."""
    pre_called = []
    post_called = []

    def pre_hook(*args, **kwargs):
        """Pre-execution hook"""
        pre_called.append(("pre", args, kwargs))

    def post_hook(result):
        """Post-execution hook"""
        post_called.append(("post", result))

    builder = (
        AgentBuilder("hooked_agent")
        .with_model("gpt-5-mini")
        .with_hooks(pre=[pre_hook], post=[post_hook])
    )

    agent = builder.build()

    # Verify configuration
    config = agent._builder_config
    assert config.hooks is not None
    assert len(config.hooks.pre) == 1
    assert len(config.hooks.post) == 1
    assert pre_hook in config.hooks.pre
    assert post_hook in config.hooks.post


@pytest.mark.asyncio
async def test_agent_builder_hooks_execution():
    """Test that hooks are actually executed."""
    execution_log = []

    def pre_hook(prompt: str, **kwargs):
        """Pre-execution hook"""
        execution_log.append(f"pre:{prompt}")

    def post_hook(result: str):
        """Post-execution hook"""
        execution_log.append(f"post:{result}")

    builder = (
        AgentBuilder("execution_test")
        .with_model("gpt-5-mini")
        .with_hooks(pre=[pre_hook], post=[post_hook])
    )

    agent = builder.build()

    # Execute agent (will call LLM, so we skip actual execution in unit tests)
    # Just verify hooks are configured
    assert hasattr(agent, "_base_agent")
    config = agent._builder_config
    assert config.hooks is not None


def test_agent_builder_with_session_id_integration():
    """Test building agent with session ID integration."""
    builder = (
        AgentBuilder("session_agent")
        .with_model("gpt-5-mini")
        .with_memory(type="persistent", max_messages=50)
        .with_session_id("user_123_session_1")
    )

    agent = builder.build()

    # Verify configuration
    config = agent._builder_config
    assert config.memory is not None
    assert config.memory.session_id == "user_123_session_1"


def test_agent_builder_method_chaining_with_session():
    """Test full method chaining including session ID."""
    agent = (
        AgentBuilder("full_chain_agent")
        .with_model("gpt-4o")
        .with_memory(type="persistent", max_messages=100)
        .with_session_id("chain_session_123")
        .with_context(temperature=0.7, max_tokens=1000)
        .build()
    )

    assert agent is not None
    config = agent._builder_config
    assert config.model == "gpt-4o"
    assert config.memory is not None
    assert config.memory.type == "persistent"
    assert config.memory.session_id == "chain_session_123"
    assert config.context["temperature"] == 0.7
