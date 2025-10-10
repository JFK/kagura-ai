"""Agent routing system for intelligent agent selection.

This module provides automatic agent selection based on user input patterns.

Example:
    >>> from kagura import agent
    >>> from kagura.routing import AgentRouter
    >>>
    >>> @agent
    >>> async def code_reviewer(code: str) -> str:
    ...     '''Review code: {{ code }}'''
    ...     pass
    >>>
    >>> router = AgentRouter()
    >>> router.register(code_reviewer, intents=["review", "check"])
    >>> result = await router.route("Please review this code")
"""

from .context_analyzer import ContextAnalyzer
from .exceptions import (
    AgentNotRegisteredError,
    InvalidRouterStrategyError,
    NoAgentFoundError,
    RoutingError,
)
from .memory_aware_router import MemoryAwareRouter
from .router import AgentRouter, RegisteredAgent

__all__ = [
    "AgentRouter",
    "RegisteredAgent",
    "ContextAnalyzer",
    "MemoryAwareRouter",
    "RoutingError",
    "NoAgentFoundError",
    "AgentNotRegisteredError",
    "InvalidRouterStrategyError",
]
