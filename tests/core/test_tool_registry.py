"""Tests for tool registry"""
import pytest

from kagura.core.tool_registry import ToolRegistry, tool_registry


def test_tool_registry_initialization():
    """Test registry initialization"""
    registry = ToolRegistry()
    assert len(registry.list_names()) == 0


def test_register_tool():
    """Test registering a tool"""
    registry = ToolRegistry()

    def sample_tool(x: int) -> int:
        return x * 2

    registry.register("sample", sample_tool)
    assert "sample" in registry.list_names()
    assert registry.get("sample") == sample_tool


def test_register_duplicate_tool():
    """Test registering duplicate tool raises error"""
    registry = ToolRegistry()

    def tool1():
        pass

    def tool2():
        pass

    registry.register("duplicate", tool1)

    with pytest.raises(ValueError, match="already registered"):
        registry.register("duplicate", tool2)


def test_get_tool():
    """Test getting a tool"""
    registry = ToolRegistry()

    def my_tool():
        return "result"

    registry.register("my_tool", my_tool)

    retrieved = registry.get("my_tool")
    assert retrieved is not None
    assert retrieved() == "result"


def test_get_nonexistent_tool():
    """Test getting non-existent tool returns None"""
    registry = ToolRegistry()
    assert registry.get("nonexistent") is None


def test_get_all_tools():
    """Test getting all tools"""
    registry = ToolRegistry()

    def tool1():
        pass

    def tool2():
        pass

    registry.register("tool1", tool1)
    registry.register("tool2", tool2)

    all_tools = registry.get_all()
    assert len(all_tools) == 2
    assert "tool1" in all_tools
    assert "tool2" in all_tools


def test_list_names():
    """Test listing tool names"""
    registry = ToolRegistry()

    def tool_a():
        pass

    def tool_b():
        pass

    registry.register("tool_a", tool_a)
    registry.register("tool_b", tool_b)

    names = registry.list_names()
    assert set(names) == {"tool_a", "tool_b"}


def test_unregister_tool():
    """Test unregistering a tool"""
    registry = ToolRegistry()

    def my_tool():
        pass

    registry.register("my_tool", my_tool)
    assert "my_tool" in registry.list_names()

    registry.unregister("my_tool")
    assert "my_tool" not in registry.list_names()


def test_unregister_nonexistent_tool():
    """Test unregistering non-existent tool raises error"""
    registry = ToolRegistry()

    with pytest.raises(KeyError, match="not registered"):
        registry.unregister("nonexistent")


def test_clear_registry():
    """Test clearing registry"""
    registry = ToolRegistry()

    def tool1():
        pass

    def tool2():
        pass

    registry.register("tool1", tool1)
    registry.register("tool2", tool2)

    assert len(registry.list_names()) == 2

    registry.clear()
    assert len(registry.list_names()) == 0


def test_global_tool_registry():
    """Test global tool_registry instance"""
    # Clear before test
    tool_registry.clear()

    def global_tool():
        return "global"

    tool_registry.register("global_tool", global_tool)
    assert "global_tool" in tool_registry.list_names()

    # Clean up
    tool_registry.clear()
