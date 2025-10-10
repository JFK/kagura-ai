"""Tests for @tool decorator"""
import pytest

from kagura import tool
from kagura.core.tool_registry import tool_registry


@pytest.fixture(autouse=True)
def clear_tool_registry():
    """Clear tool registry before each test"""
    tool_registry.clear()
    yield
    tool_registry.clear()


def test_tool_decorator_basic():
    """Test basic @tool decorator"""

    @tool
    def add(a: int, b: int) -> int:
        """Add two numbers"""
        return a + b

    result = add(2, 3)
    assert result == 5


def test_tool_decorator_with_defaults():
    """Test @tool with default parameters"""

    @tool
    def greet(name: str, greeting: str = "Hello") -> str:
        """Greet someone"""
        return f"{greeting}, {name}!"

    assert greet("World") == "Hello, World!"
    assert greet("Alice", "Hi") == "Hi, Alice!"


def test_tool_decorator_keyword_args():
    """Test @tool with keyword arguments"""

    @tool
    def calculate(x: float, y: float, operation: str = "add") -> float:
        """Calculate based on operation"""
        if operation == "add":
            return x + y
        elif operation == "multiply":
            return x * y
        return 0.0

    assert calculate(5.0, 3.0) == 8.0
    assert calculate(5.0, 3.0, operation="multiply") == 15.0
    assert calculate(x=10.0, y=2.0, operation="add") == 12.0


def test_tool_decorator_registration():
    """Test tool is registered in tool_registry"""

    @tool
    def registered_tool():
        """A registered tool"""
        return "result"

    assert "registered_tool" in tool_registry.list_names()
    retrieved = tool_registry.get("registered_tool")
    assert retrieved is not None
    assert retrieved() == "result"


def test_tool_decorator_custom_name():
    """Test @tool with custom name"""

    @tool(name="custom_tool_name")
    def my_function():
        """Custom named tool"""
        return "custom"

    assert "custom_tool_name" in tool_registry.list_names()
    assert tool_registry.get("custom_tool_name")() == "custom"


def test_tool_decorator_preserves_metadata():
    """Test @tool preserves function metadata"""

    @tool
    def documented_tool(x: int) -> int:
        """This is a documented tool"""
        return x * 2

    assert documented_tool.__name__ == "documented_tool"
    assert documented_tool.__doc__ == "This is a documented tool"


def test_tool_decorator_has_metadata_attributes():
    """Test @tool adds metadata attributes"""

    @tool
    def meta_tool(a: int, b: int = 5) -> int:
        """Tool with metadata"""
        return a + b

    assert hasattr(meta_tool, "_is_tool")
    assert meta_tool._is_tool is True  # type: ignore
    assert hasattr(meta_tool, "_tool_name")
    assert meta_tool._tool_name == "meta_tool"  # type: ignore
    assert hasattr(meta_tool, "_tool_signature")
    assert hasattr(meta_tool, "_tool_docstring")
    assert meta_tool._tool_docstring == "Tool with metadata"  # type: ignore


def test_tool_decorator_invalid_args():
    """Test @tool with invalid arguments raises error"""

    @tool
    def strict_tool(x: int, y: int) -> int:
        """Requires exactly 2 args"""
        return x + y

    # Valid calls
    assert strict_tool(1, 2) == 3
    assert strict_tool(x=1, y=2) == 3

    # Invalid calls
    with pytest.raises(TypeError, match="invalid arguments"):
        strict_tool(1)  # type: ignore

    with pytest.raises(TypeError, match="invalid arguments"):
        strict_tool(1, 2, 3)  # type: ignore


def test_tool_decorator_no_type_hints():
    """Test @tool works without type hints"""

    @tool
    def untyped_tool(a, b):  # type: ignore
        """Tool without type hints"""
        return a + b

    assert untyped_tool(5, 10) == 15
    assert untyped_tool("Hello", " World") == "Hello World"


def test_tool_decorator_complex_return_type():
    """Test @tool with complex return type"""

    @tool
    def get_user_data(user_id: int) -> dict:
        """Get user data"""
        return {"id": user_id, "name": "Alice", "active": True}

    result = get_user_data(123)
    assert result == {"id": 123, "name": "Alice", "active": True}


def test_tool_decorator_with_exceptions():
    """Test @tool can raise exceptions"""

    @tool
    def divide(a: float, b: float) -> float:
        """Divide two numbers"""
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b

    assert divide(10.0, 2.0) == 5.0

    with pytest.raises(ValueError, match="Cannot divide by zero"):
        divide(10.0, 0.0)


def test_multiple_tools():
    """Test registering multiple tools"""

    @tool
    def tool_one():
        return 1

    @tool
    def tool_two():
        return 2

    @tool
    def tool_three():
        return 3

    assert len(tool_registry.list_names()) == 3
    assert tool_one() == 1
    assert tool_two() == 2
    assert tool_three() == 3
