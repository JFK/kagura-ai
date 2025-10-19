"""Tests for unified tool registry (RFC-036)."""

import pytest
from typing import Any
from pydantic import BaseModel, Field

from kagura.chat.tools import ToolRegistry, ToolSource


# Test fixtures
class TestInput(BaseModel):
    """Test Pydantic model for input."""

    name: str = Field(description="Name of the person")
    age: int = Field(description="Age of the person", ge=0)


class TestOutput(BaseModel):
    """Test Pydantic model for output."""

    greeting: str
    is_adult: bool


def custom_function(name: str, age: int) -> str:
    """Custom function for testing.

    Args:
        name: Name of the person
        age: Age of the person

    Returns:
        Greeting message
    """
    return f"Hello {name}, you are {age} years old"


def custom_function_no_docstring(x: int, y: int) -> int:
    return x + y


# Tests
class TestToolRegistry:
    """Test suite for ToolRegistry."""

    def test_init_default(self) -> None:
        """Test initialization with default parameters."""
        registry = ToolRegistry()
        assert registry.name == "default"
        assert len(registry.list_tools()) == 0

    def test_init_with_name(self) -> None:
        """Test initialization with custom name."""
        registry = ToolRegistry(name="custom")
        assert registry.name == "custom"

    def test_register_pydantic_tool(self) -> None:
        """Test registering a Pydantic model as a tool."""
        registry = ToolRegistry()

        def pydantic_handler(input: TestInput) -> TestOutput:
            return TestOutput(
                greeting=f"Hello {input.name}",
                is_adult=input.age >= 18,
            )

        registry.register(
            name="greet",
            handler=pydantic_handler,
            input_schema=TestInput,
            description="Greet a person",
        )

        tools = registry.list_tools()
        assert len(tools) == 1
        assert tools[0]["name"] == "greet"
        assert tools[0]["description"] == "Greet a person"
        assert tools[0]["source"] == ToolSource.PYDANTIC

    def test_register_custom_function(self) -> None:
        """Test registering a custom function as a tool."""
        registry = ToolRegistry()
        registry.register(
            name="greet_function",
            handler=custom_function,
            description="Greet a person with custom function",
        )

        tools = registry.list_tools()
        assert len(tools) == 1
        assert tools[0]["name"] == "greet_function"
        assert tools[0]["description"] == "Greet a person with custom function"
        assert tools[0]["source"] == ToolSource.CUSTOM

    def test_register_custom_function_no_docstring(self) -> None:
        """Test registering a custom function without docstring."""
        registry = ToolRegistry()
        registry.register(
            name="add",
            handler=custom_function_no_docstring,
            description="Add two numbers",
        )

        tools = registry.list_tools()
        assert len(tools) == 1
        assert tools[0]["name"] == "add"
        assert tools[0]["description"] == "Add two numbers"

    def test_register_duplicate_name_raises_error(self) -> None:
        """Test that registering duplicate tool name raises ValueError."""
        registry = ToolRegistry()
        registry.register(
            name="tool1",
            handler=custom_function,
            description="First tool",
        )

        with pytest.raises(ValueError, match="Tool 'tool1' already registered"):
            registry.register(
                name="tool1",
                handler=custom_function_no_docstring,
                description="Duplicate tool",
            )

    def test_get_tool_existing(self) -> None:
        """Test getting an existing tool."""
        registry = ToolRegistry()
        registry.register(
            name="greet",
            handler=custom_function,
            description="Greet a person",
        )

        tool = registry.get_tool("greet")
        assert tool is not None
        assert tool["name"] == "greet"
        assert tool["source"] == ToolSource.CUSTOM

    def test_get_tool_nonexistent(self) -> None:
        """Test getting a non-existent tool returns None."""
        registry = ToolRegistry()
        tool = registry.get_tool("nonexistent")
        assert tool is None

    def test_execute_custom_function(self) -> None:
        """Test executing a custom function tool."""
        registry = ToolRegistry()
        registry.register(
            name="greet",
            handler=custom_function,
            description="Greet a person",
        )

        result = registry.execute("greet", {"name": "Alice", "age": 30})
        assert result == "Hello Alice, you are 30 years old"

    def test_execute_pydantic_tool(self) -> None:
        """Test executing a Pydantic tool."""
        registry = ToolRegistry()

        def pydantic_handler(input: TestInput) -> TestOutput:
            return TestOutput(
                greeting=f"Hello {input.name}",
                is_adult=input.age >= 18,
            )

        registry.register(
            name="greet",
            handler=pydantic_handler,
            input_schema=TestInput,
            description="Greet a person",
        )

        result = registry.execute("greet", {"name": "Alice", "age": 30})
        assert isinstance(result, TestOutput)
        assert result.greeting == "Hello Alice"
        assert result.is_adult is True

    def test_execute_pydantic_tool_invalid_input(self) -> None:
        """Test executing a Pydantic tool with invalid input."""
        registry = ToolRegistry()

        def pydantic_handler(input: TestInput) -> TestOutput:
            return TestOutput(
                greeting=f"Hello {input.name}",
                is_adult=input.age >= 18,
            )

        registry.register(
            name="greet",
            handler=pydantic_handler,
            input_schema=TestInput,
            description="Greet a person",
        )

        with pytest.raises(ValueError, match="validation error"):
            # Age is negative, should fail validation
            registry.execute("greet", {"name": "Alice", "age": -5})

    def test_execute_nonexistent_tool(self) -> None:
        """Test executing a non-existent tool raises ValueError."""
        registry = ToolRegistry()

        with pytest.raises(ValueError, match="Tool 'nonexistent' not found"):
            registry.execute("nonexistent", {})

    def test_list_tools_empty(self) -> None:
        """Test listing tools when registry is empty."""
        registry = ToolRegistry()
        tools = registry.list_tools()
        assert len(tools) == 0
        assert tools == []

    def test_list_tools_multiple(self) -> None:
        """Test listing multiple tools."""
        registry = ToolRegistry()

        registry.register(
            name="tool1",
            handler=custom_function,
            description="Tool 1",
        )
        registry.register(
            name="tool2",
            handler=custom_function_no_docstring,
            description="Tool 2",
        )

        tools = registry.list_tools()
        assert len(tools) == 2
        assert {tool["name"] for tool in tools} == {"tool1", "tool2"}

    def test_to_openai_format_custom_function(self) -> None:
        """Test converting custom function to OpenAI format."""
        registry = ToolRegistry()
        registry.register(
            name="greet",
            handler=custom_function,
            description="Greet a person",
        )

        openai_tools = registry.to_openai_format()
        assert len(openai_tools) == 1

        tool = openai_tools[0]
        assert tool["type"] == "function"
        assert tool["function"]["name"] == "greet"
        assert tool["function"]["description"] == "Greet a person"

        params = tool["function"]["parameters"]
        assert params["type"] == "object"
        assert "name" in params["properties"]
        assert "age" in params["properties"]
        assert params["properties"]["name"]["type"] == "string"
        assert params["properties"]["age"]["type"] == "integer"
        assert params["required"] == ["name", "age"]

    def test_to_openai_format_pydantic_tool(self) -> None:
        """Test converting Pydantic tool to OpenAI format."""
        registry = ToolRegistry()

        def pydantic_handler(input: TestInput) -> TestOutput:
            return TestOutput(
                greeting=f"Hello {input.name}",
                is_adult=input.age >= 18,
            )

        registry.register(
            name="greet",
            handler=pydantic_handler,
            input_schema=TestInput,
            description="Greet a person",
        )

        openai_tools = registry.to_openai_format()
        assert len(openai_tools) == 1

        tool = openai_tools[0]
        assert tool["type"] == "function"
        assert tool["function"]["name"] == "greet"
        assert tool["function"]["description"] == "Greet a person"

        params = tool["function"]["parameters"]
        assert params["type"] == "object"
        assert "name" in params["properties"]
        assert "age" in params["properties"]
        assert params["properties"]["name"]["description"] == "Name of the person"
        assert params["properties"]["age"]["description"] == "Age of the person"
        assert params["properties"]["age"]["minimum"] == 0

    def test_to_openai_format_empty_registry(self) -> None:
        """Test converting empty registry to OpenAI format."""
        registry = ToolRegistry()
        openai_tools = registry.to_openai_format()
        assert len(openai_tools) == 0
        assert openai_tools == []

    def test_to_anthropic_format_custom_function(self) -> None:
        """Test converting custom function to Anthropic format."""
        registry = ToolRegistry()
        registry.register(
            name="greet",
            handler=custom_function,
            description="Greet a person",
        )

        anthropic_tools = registry.to_anthropic_format()
        assert len(anthropic_tools) == 1

        tool = anthropic_tools[0]
        assert tool["name"] == "greet"
        assert tool["description"] == "Greet a person"

        input_schema = tool["input_schema"]
        assert input_schema["type"] == "object"
        assert "name" in input_schema["properties"]
        assert "age" in input_schema["properties"]
        assert input_schema["required"] == ["name", "age"]

    def test_to_anthropic_format_empty_registry(self) -> None:
        """Test converting empty registry to Anthropic format."""
        registry = ToolRegistry()
        anthropic_tools = registry.to_anthropic_format()
        assert len(anthropic_tools) == 0
        assert anthropic_tools == []

    def test_function_signature_extraction(self) -> None:
        """Test that function signatures are correctly extracted."""
        registry = ToolRegistry()
        registry.register(
            name="greet",
            handler=custom_function,
            description="Greet a person",
        )

        tool = registry.get_tool("greet")
        assert tool is not None

        # Check that parameters were extracted correctly
        openai_tools = registry.to_openai_format()
        params = openai_tools[0]["function"]["parameters"]

        assert "name" in params["properties"]
        assert "age" in params["properties"]
        assert params["properties"]["name"]["type"] == "string"
        assert params["properties"]["age"]["type"] == "integer"
        assert set(params["required"]) == {"name", "age"}

    def test_multiple_tool_sources(self) -> None:
        """Test registry with tools from different sources."""
        registry = ToolRegistry()

        # Custom function
        registry.register(
            name="custom_tool",
            handler=custom_function,
            description="Custom function tool",
        )

        # Pydantic tool
        def pydantic_handler(input: TestInput) -> TestOutput:
            return TestOutput(
                greeting=f"Hello {input.name}",
                is_adult=input.age >= 18,
            )

        registry.register(
            name="pydantic_tool",
            handler=pydantic_handler,
            input_schema=TestInput,
            description="Pydantic tool",
        )

        tools = registry.list_tools()
        assert len(tools) == 2

        sources = {tool["source"] for tool in tools}
        assert ToolSource.CUSTOM in sources
        assert ToolSource.PYDANTIC in sources

    def test_execute_with_extra_args(self) -> None:
        """Test executing a tool with extra arguments (should be ignored)."""
        registry = ToolRegistry()
        registry.register(
            name="greet",
            handler=custom_function,
            description="Greet a person",
        )

        # Extra argument 'extra' should be ignored
        result = registry.execute(
            "greet",
            {"name": "Alice", "age": 30, "extra": "ignored"},
        )
        assert result == "Hello Alice, you are 30 years old"

    def test_execute_with_missing_args(self) -> None:
        """Test executing a tool with missing arguments."""
        registry = ToolRegistry()
        registry.register(
            name="greet",
            handler=custom_function,
            description="Greet a person",
        )

        with pytest.raises(TypeError):
            # Missing 'age' argument
            registry.execute("greet", {"name": "Alice"})
