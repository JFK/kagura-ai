"""Observability and telemetry for agent executions.

This module provides telemetry collection, event storage, and monitoring
capabilities for Kagura agents.

Example:
    >>> from kagura.observability import Telemetry, EventStore
    >>>
    >>> # Create telemetry instance
    >>> store = EventStore()
    >>> telemetry = Telemetry(store)
    >>>
    >>> # Instrument an agent
    >>> @telemetry.instrument()
    >>> async def my_agent(query: str) -> str:
    ...     '''Process query: {{ query }}'''
    ...     return f"Result: {query}"
    >>>
    >>> # Execute and collect telemetry
    >>> result = await my_agent("test")
    >>>
    >>> # Query telemetry data
    >>> executions = store.get_executions(agent_name="my_agent")
    >>>
    >>> # Monitor with dashboard
    >>> from kagura.observability import Dashboard
    >>> dashboard = Dashboard(store)
    >>> dashboard.show_stats()
"""

from .collector import TelemetryCollector
from .dashboard import Dashboard
from .instrumentation import (
    Telemetry,
    get_global_telemetry,
    set_global_telemetry,
)
from .store import EventStore

__all__ = [
    "EventStore",
    "TelemetryCollector",
    "Telemetry",
    "Dashboard",
    "get_global_telemetry",
    "set_global_telemetry",
]
