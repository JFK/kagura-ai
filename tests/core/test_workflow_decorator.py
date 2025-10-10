"""Tests for @workflow decorator"""
import pytest

from kagura import workflow
from kagura.core.workflow_registry import workflow_registry


@pytest.fixture(autouse=True)
def clear_workflow_registry():
    """Clear workflow registry before each test"""
    workflow_registry.clear()
    yield
    workflow_registry.clear()


@pytest.mark.asyncio
async def test_workflow_decorator_basic():
    """Test basic @workflow decorator"""

    @workflow
    async def simple_workflow(x: int, y: int) -> int:
        """Add two numbers"""
        return x + y

    result = await simple_workflow(2, 3)
    assert result == 5


@pytest.mark.asyncio
async def test_workflow_decorator_with_defaults():
    """Test @workflow with default parameters"""

    @workflow
    async def greet_workflow(name: str, greeting: str = "Hello") -> str:
        """Greet someone"""
        return f"{greeting}, {name}!"

    assert await greet_workflow("World") == "Hello, World!"
    assert await greet_workflow("Alice", "Hi") == "Hi, Alice!"


@pytest.mark.asyncio
async def test_workflow_decorator_keyword_args():
    """Test @workflow with keyword arguments"""

    @workflow
    async def calculate_workflow(
        x: float, y: float, operation: str = "add"
    ) -> float:
        """Calculate based on operation"""
        if operation == "add":
            return x + y
        elif operation == "multiply":
            return x * y
        return 0.0

    assert await calculate_workflow(5.0, 3.0) == 8.0
    assert await calculate_workflow(5.0, 3.0, operation="multiply") == 15.0
    assert await calculate_workflow(x=10.0, y=2.0, operation="add") == 12.0


@pytest.mark.asyncio
async def test_workflow_decorator_registration():
    """Test workflow is registered in workflow_registry"""

    @workflow
    async def registered_workflow():
        """A registered workflow"""
        return "result"

    assert "registered_workflow" in workflow_registry.list_names()
    retrieved = workflow_registry.get("registered_workflow")
    assert retrieved is not None
    assert await retrieved() == "result"


@pytest.mark.asyncio
async def test_workflow_decorator_custom_name():
    """Test @workflow with custom name"""

    @workflow(name="custom_workflow_name")
    async def my_function():
        """Custom named workflow"""
        return "custom"

    assert "custom_workflow_name" in workflow_registry.list_names()
    assert await workflow_registry.get("custom_workflow_name")() == "custom"


@pytest.mark.asyncio
async def test_workflow_decorator_preserves_metadata():
    """Test @workflow preserves function metadata"""

    @workflow
    async def documented_workflow(x: int) -> int:
        """This is a documented workflow"""
        return x * 2

    assert documented_workflow.__name__ == "documented_workflow"
    assert documented_workflow.__doc__ == "This is a documented workflow"


@pytest.mark.asyncio
async def test_workflow_decorator_has_metadata_attributes():
    """Test @workflow adds metadata attributes"""

    @workflow
    async def meta_workflow(a: int, b: int = 5) -> int:
        """Workflow with metadata"""
        return a + b

    assert hasattr(meta_workflow, "_is_workflow")
    assert meta_workflow._is_workflow is True  # type: ignore
    assert hasattr(meta_workflow, "_workflow_name")
    assert meta_workflow._workflow_name == "meta_workflow"  # type: ignore
    assert hasattr(meta_workflow, "_workflow_signature")
    assert hasattr(meta_workflow, "_workflow_docstring")
    assert meta_workflow._workflow_docstring == "Workflow with metadata"  # type: ignore


@pytest.mark.asyncio
async def test_workflow_decorator_complex_return_type():
    """Test @workflow with complex return type"""

    @workflow
    async def get_data_workflow(user_id: int) -> dict:
        """Get user data"""
        return {"id": user_id, "name": "Alice", "active": True}

    result = await get_data_workflow(123)
    assert result == {"id": 123, "name": "Alice", "active": True}


@pytest.mark.asyncio
async def test_workflow_decorator_with_exceptions():
    """Test @workflow can raise exceptions"""

    @workflow
    async def divide_workflow(a: float, b: float) -> float:
        """Divide two numbers"""
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b

    assert await divide_workflow(10.0, 2.0) == 5.0

    with pytest.raises(ValueError, match="Cannot divide by zero"):
        await divide_workflow(10.0, 0.0)


@pytest.mark.asyncio
async def test_multiple_workflows():
    """Test registering multiple workflows"""

    @workflow
    async def workflow_one():
        return 1

    @workflow
    async def workflow_two():
        return 2

    @workflow
    async def workflow_three():
        return 3

    assert len(workflow_registry.list_names()) == 3
    assert await workflow_one() == 1
    assert await workflow_two() == 2
    assert await workflow_three() == 3


@pytest.mark.asyncio
async def test_workflow_orchestration():
    """Test workflow orchestrating multiple operations"""

    @workflow
    async def orchestration_workflow(x: int) -> dict:
        """Orchestrate multiple steps"""
        # Step 1: Double the value
        doubled = x * 2

        # Step 2: Add 10
        added = doubled + 10

        # Step 3: Return result
        return {"input": x, "doubled": doubled, "result": added}

    result = await orchestration_workflow(5)
    assert result == {"input": 5, "doubled": 10, "result": 20}


@pytest.mark.asyncio
async def test_workflow_with_async_operations():
    """Test workflow with async operations"""

    # Mock async function
    async def async_operation(value: int) -> int:
        return value * 2

    @workflow
    async def async_workflow(x: int) -> int:
        """Workflow with async operations"""
        result1 = await async_operation(x)
        result2 = await async_operation(result1)
        return result2

    result = await async_workflow(5)
    assert result == 20  # 5 * 2 * 2
