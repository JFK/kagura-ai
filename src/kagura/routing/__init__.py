"""Agent routing system for intelligent agent selection.

This module provides basic agent routing for personal assistant use cases.

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

from .exceptions import (
    AgentNotRegisteredError,
    InvalidRouterStrategyError,
    NoAgentFoundError,
    RoutingError,
)
from .router import AgentRouter, RegisteredAgent

__all__ = [
    "AgentRouter",
    "RegisteredAgent",
    "RoutingError",
    "NoAgentFoundError",
    "AgentNotRegisteredError",
    "InvalidRouterStrategyError",
]
