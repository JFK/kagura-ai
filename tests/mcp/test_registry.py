"""Tests for Agent Registry"""

import pytest

from kagura.core.registry import AgentRegistry


@pytest.fixture
def registry():
    """Create fresh registry for each test"""
    reg = AgentRegistry()
    yield reg
    reg.clear()


def test_register_agent(registry):
    """Test agent registration"""

    def my_agent():
        pass

    registry.register("my_agent", my_agent)

    assert registry.get("my_agent") is my_agent
    assert "my_agent" in registry.list_names()


def test_register_duplicate_raises_error(registry):
    """Test that registering duplicate agent name raises error"""

    def agent1():
        pass

    def agent2():
        pass

    registry.register("agent", agent1)

    with pytest.raises(ValueError, match="already registered"):
        registry.register("agent", agent2)


def test_get_nonexistent_agent(registry):
    """Test getting non-existent agent returns None"""
    assert registry.get("nonexistent") is None


def test_get_all_agents(registry):
    """Test getting all agents"""

    def agent1():
        pass

    def agent2():
        pass

    registry.register("agent1", agent1)
    registry.register("agent2", agent2)

    all_agents = registry.get_all()

    assert len(all_agents) == 2
    assert all_agents["agent1"] is agent1
    assert all_agents["agent2"] is agent2


def test_list_names(registry):
    """Test listing agent names"""

    def agent1():
        pass

    def agent2():
        pass

    registry.register("agent1", agent1)
    registry.register("agent2", agent2)

    names = registry.list_names()

    assert len(names) == 2
    assert "agent1" in names
    assert "agent2" in names


def test_unregister_agent(registry):
    """Test unregistering agent"""

    def my_agent():
        pass

    registry.register("my_agent", my_agent)
    assert registry.get("my_agent") is my_agent

    registry.unregister("my_agent")
    assert registry.get("my_agent") is None


def test_unregister_nonexistent_raises_error(registry):
    """Test that unregistering non-existent agent raises error"""
    with pytest.raises(KeyError):
        registry.unregister("nonexistent")


def test_clear_registry(registry):
    """Test clearing all agents from registry"""

    def agent1():
        pass

    def agent2():
        pass

    registry.register("agent1", agent1)
    registry.register("agent2", agent2)

    assert len(registry.list_names()) == 2

    registry.clear()

    assert len(registry.list_names()) == 0
