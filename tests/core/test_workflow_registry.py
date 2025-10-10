"""Tests for workflow registry"""
import pytest

from kagura.core.workflow_registry import WorkflowRegistry, workflow_registry


def test_workflow_registry_initialization():
    """Test registry initialization"""
    registry = WorkflowRegistry()
    assert len(registry.list_names()) == 0


def test_register_workflow():
    """Test registering a workflow"""
    registry = WorkflowRegistry()

    async def sample_workflow(x: str) -> str:
        return f"Workflow: {x}"

    registry.register("sample", sample_workflow)
    assert "sample" in registry.list_names()
    assert registry.get("sample") == sample_workflow


def test_register_duplicate_workflow():
    """Test registering duplicate workflow raises error"""
    registry = WorkflowRegistry()

    async def workflow1():
        pass

    async def workflow2():
        pass

    registry.register("duplicate", workflow1)

    with pytest.raises(ValueError, match="already registered"):
        registry.register("duplicate", workflow2)


def test_get_workflow():
    """Test getting a workflow"""
    registry = WorkflowRegistry()

    async def my_workflow():
        return "result"

    registry.register("my_workflow", my_workflow)

    retrieved = registry.get("my_workflow")
    assert retrieved is not None
    assert retrieved == my_workflow


def test_get_nonexistent_workflow():
    """Test getting non-existent workflow returns None"""
    registry = WorkflowRegistry()
    assert registry.get("nonexistent") is None


def test_get_all_workflows():
    """Test getting all workflows"""
    registry = WorkflowRegistry()

    async def workflow1():
        pass

    async def workflow2():
        pass

    registry.register("workflow1", workflow1)
    registry.register("workflow2", workflow2)

    all_workflows = registry.get_all()
    assert len(all_workflows) == 2
    assert "workflow1" in all_workflows
    assert "workflow2" in all_workflows


def test_list_names():
    """Test listing workflow names"""
    registry = WorkflowRegistry()

    async def workflow_a():
        pass

    async def workflow_b():
        pass

    registry.register("workflow_a", workflow_a)
    registry.register("workflow_b", workflow_b)

    names = registry.list_names()
    assert set(names) == {"workflow_a", "workflow_b"}


def test_unregister_workflow():
    """Test unregistering a workflow"""
    registry = WorkflowRegistry()

    async def my_workflow():
        pass

    registry.register("my_workflow", my_workflow)
    assert "my_workflow" in registry.list_names()

    registry.unregister("my_workflow")
    assert "my_workflow" not in registry.list_names()


def test_unregister_nonexistent_workflow():
    """Test unregistering non-existent workflow raises error"""
    registry = WorkflowRegistry()

    with pytest.raises(KeyError, match="not registered"):
        registry.unregister("nonexistent")


def test_clear_registry():
    """Test clearing registry"""
    registry = WorkflowRegistry()

    async def workflow1():
        pass

    async def workflow2():
        pass

    registry.register("workflow1", workflow1)
    registry.register("workflow2", workflow2)

    assert len(registry.list_names()) == 2

    registry.clear()
    assert len(registry.list_names()) == 0


def test_global_workflow_registry():
    """Test global workflow_registry instance"""
    # Clear before test
    workflow_registry.clear()

    async def global_workflow():
        return "global"

    workflow_registry.register("global_workflow", global_workflow)
    assert "global_workflow" in workflow_registry.list_names()

    # Clean up
    workflow_registry.clear()
