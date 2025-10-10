"""
Global registry for Kagura tools

This module provides a centralized registry for all Kagura tools,
enabling MCP integration and tool discovery.
"""

import importlib
import inspect
from typing import Any, Callable


class ToolRegistry:
    """Global registry for all Kagura tools

    This registry stores all tools decorated with @tool,
    allowing them to be discovered and exposed via MCP.

    Example:
        >>> from kagura.core.tool_registry import tool_registry
        >>> tool_registry.register("calculate_tax", tax_func)
        >>> tool = tool_registry.get("calculate_tax")
    """

    def __init__(self) -> None:
        """Initialize empty registry"""
        self._tools: dict[str, Callable[..., Any]] = {}

    def register(self, name: str, func: Callable[..., Any]) -> None:
        """Register a tool

        Args:
            name: Tool name (must be unique)
            func: Tool function (decorated with @tool)

        Raises:
            ValueError: If tool name is already registered
        """
        if name in self._tools:
            raise ValueError(f"Tool '{name}' is already registered")

        self._tools[name] = func

    def get(self, name: str) -> Callable[..., Any] | None:
        """Get tool by name

        Args:
            name: Tool name

        Returns:
            Tool function, or None if not found
        """
        return self._tools.get(name)

    def get_all(self) -> dict[str, Callable[..., Any]]:
        """Get all registered tools

        Returns:
            Dictionary of tool_name -> tool_function
        """
        return self._tools.copy()

    def list_names(self) -> list[str]:
        """List all tool names

        Returns:
            List of tool names
        """
        return list(self._tools.keys())

    def unregister(self, name: str) -> None:
        """Unregister a tool

        Args:
            name: Tool name to remove

        Raises:
            KeyError: If tool name is not registered
        """
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' is not registered")

        del self._tools[name]

    def clear(self) -> None:
        """Clear all tools from registry"""
        self._tools.clear()

    def auto_discover(self, module_path: str) -> None:
        """Auto-discover tools in a module

        Scans a module for functions decorated with @tool
        and automatically registers them.

        Args:
            module_path: Python module path (e.g., "my_package.tools")

        Example:
            >>> tool_registry.auto_discover("my_package.tools")
        """
        try:
            module = importlib.import_module(module_path)
        except ModuleNotFoundError as e:
            raise ValueError(f"Module '{module_path}' not found") from e

        for name, obj in inspect.getmembers(module):
            # Check if object is a tool (has _is_tool flag)
            if callable(obj) and getattr(obj, "_is_tool", False):
                # Use function name as tool name
                tool_name = name
                self.register(tool_name, obj)


# Global tool registry instance
tool_registry = ToolRegistry()


__all__ = ["ToolRegistry", "tool_registry"]
