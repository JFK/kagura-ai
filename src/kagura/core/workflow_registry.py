"""
Global registry for Kagura workflows

This module provides a centralized registry for all Kagura workflows,
enabling MCP integration and workflow discovery.
"""

import importlib
import inspect
from typing import Any, Callable


class WorkflowRegistry:
    """Global registry for all Kagura workflows

    This registry stores all workflows decorated with @workflow,
    allowing them to be discovered and exposed via MCP.

    Example:
        >>> from kagura.core.workflow_registry import workflow_registry
        >>> workflow_registry.register("my_workflow", workflow_func)
        >>> workflow = workflow_registry.get("my_workflow")
    """

    def __init__(self) -> None:
        """Initialize empty registry"""
        self._workflows: dict[str, Callable[..., Any]] = {}

    def register(self, name: str, func: Callable[..., Any]) -> None:
        """Register a workflow

        Args:
            name: Workflow name (must be unique)
            func: Workflow function (decorated with @workflow)

        Raises:
            ValueError: If workflow name is already registered
        """
        if name in self._workflows:
            raise ValueError(f"Workflow '{name}' is already registered")

        self._workflows[name] = func

    def get(self, name: str) -> Callable[..., Any] | None:
        """Get workflow by name

        Args:
            name: Workflow name

        Returns:
            Workflow function, or None if not found
        """
        return self._workflows.get(name)

    def get_all(self) -> dict[str, Callable[..., Any]]:
        """Get all registered workflows

        Returns:
            Dictionary of workflow_name -> workflow_function
        """
        return self._workflows.copy()

    def list_names(self) -> list[str]:
        """List all workflow names

        Returns:
            List of workflow names
        """
        return list(self._workflows.keys())

    def unregister(self, name: str) -> None:
        """Unregister a workflow

        Args:
            name: Workflow name to remove

        Raises:
            KeyError: If workflow name is not registered
        """
        if name not in self._workflows:
            raise KeyError(f"Workflow '{name}' is not registered")

        del self._workflows[name]

    def clear(self) -> None:
        """Clear all workflows from registry"""
        self._workflows.clear()

    def auto_discover(self, module_path: str) -> None:
        """Auto-discover workflows in a module

        Scans a module for functions decorated with @workflow
        and automatically registers them.

        Args:
            module_path: Python module path (e.g., "my_package.workflows")

        Example:
            >>> workflow_registry.auto_discover("my_package.workflows")
        """
        try:
            module = importlib.import_module(module_path)
        except ModuleNotFoundError as e:
            raise ValueError(f"Module '{module_path}' not found") from e

        for name, obj in inspect.getmembers(module):
            # Check if object is a workflow (has _is_workflow flag)
            if callable(obj) and getattr(obj, "_is_workflow", False):
                # Use function name as workflow name
                workflow_name = name
                self.register(workflow_name, obj)


# Global workflow registry instance
workflow_registry = WorkflowRegistry()


__all__ = ["WorkflowRegistry", "workflow_registry"]
