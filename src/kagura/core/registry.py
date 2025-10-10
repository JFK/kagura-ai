"""
Global registry for Kagura agents

This module provides a centralized registry for all Kagura agents,
enabling MCP integration and agent discovery.
"""

import importlib
import inspect
from typing import Any, Callable


class AgentRegistry:
    """Global registry for all Kagura agents

    This registry stores all agents decorated with @agent,
    allowing them to be discovered and exposed via MCP.

    Example:
        >>> from kagura.core.registry import agent_registry
        >>> agent_registry.register("my_agent", agent_func)
        >>> agent = agent_registry.get("my_agent")
    """

    def __init__(self) -> None:
        """Initialize empty registry"""
        self._agents: dict[str, Callable[..., Any]] = {}

    def register(self, name: str, func: Callable[..., Any]) -> None:
        """Register an agent

        Args:
            name: Agent name (must be unique)
            func: Agent function (decorated with @agent)

        Raises:
            ValueError: If agent name is already registered
        """
        if name in self._agents:
            raise ValueError(f"Agent '{name}' is already registered")

        self._agents[name] = func

    def get(self, name: str) -> Callable[..., Any] | None:
        """Get agent by name

        Args:
            name: Agent name

        Returns:
            Agent function, or None if not found
        """
        return self._agents.get(name)

    def get_all(self) -> dict[str, Callable[..., Any]]:
        """Get all registered agents

        Returns:
            Dictionary of agent_name -> agent_function
        """
        return self._agents.copy()

    def list_names(self) -> list[str]:
        """List all agent names

        Returns:
            List of agent names
        """
        return list(self._agents.keys())

    def unregister(self, name: str) -> None:
        """Unregister an agent

        Args:
            name: Agent name to remove

        Raises:
            KeyError: If agent name is not registered
        """
        if name not in self._agents:
            raise KeyError(f"Agent '{name}' is not registered")

        del self._agents[name]

    def clear(self) -> None:
        """Clear all agents from registry"""
        self._agents.clear()

    def auto_discover(self, module_path: str) -> None:
        """Auto-discover agents in a module

        Scans a module for functions decorated with @agent
        and automatically registers them.

        Args:
            module_path: Python module path (e.g., "my_package.agents")

        Example:
            >>> agent_registry.auto_discover("my_package.agents")
        """
        try:
            module = importlib.import_module(module_path)
        except ModuleNotFoundError as e:
            raise ValueError(f"Module '{module_path}' not found") from e

        for name, obj in inspect.getmembers(module):
            # Check if object is an agent (has _is_agent flag)
            if callable(obj) and getattr(obj, "_is_agent", False):
                # Use function name as agent name
                agent_name = name
                self.register(agent_name, obj)


# Global agent registry instance
agent_registry = AgentRegistry()


__all__ = ["AgentRegistry", "agent_registry"]
