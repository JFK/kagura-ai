"""Instrumentation decorators for automatic telemetry collection."""

from __future__ import annotations

import functools
import inspect
from typing import TYPE_CHECKING, Any, Callable, Optional, TypeVar, cast

from .collector import TelemetryCollector

if TYPE_CHECKING:
    from .store import EventStore

T = TypeVar("T", bound=Callable[..., Any])


class Telemetry:
    """Telemetry instrumentation manager.

    Example:
        >>> from kagura.observability import EventStore, Telemetry
        >>> store = EventStore()
        >>> telemetry = Telemetry(store)
        >>>
        >>> @telemetry.instrument()
        >>> async def my_agent(query: str) -> str:
        ...     '''Process query: {{ query }}'''
        ...     return f"Result: {query}"
        >>>
        >>> result = await my_agent("test")
    """

    def __init__(self, store: Optional[EventStore] = None) -> None:
        """Initialize telemetry manager.

        Args:
            store: Event store for persisting telemetry data.
                If None, creates a default store at ~/.kagura/telemetry.db
        """
        from .store import EventStore

        if store is None:
            store = EventStore()
        self.collector = TelemetryCollector(store)

    def instrument(self, agent_name: Optional[str] = None) -> Callable[[T], T]:
        """Decorator to instrument agent with telemetry.

        Args:
            agent_name: Optional custom agent name. If not provided,
                uses the function name.

        Returns:
            Decorator function

        Example:
            >>> @telemetry.instrument()
            >>> async def translator(text: str) -> str:
            ...     return translate(text)
            >>>
            >>> @telemetry.instrument("custom_agent")
            >>> async def processor(data: dict) -> dict:
            ...     return process(data)
        """

        def decorator(func: T) -> T:
            # Determine agent name
            name = agent_name if agent_name else func.__name__

            # Check if function is async
            is_async = inspect.iscoroutinefunction(func)

            if is_async:

                @functools.wraps(func)
                async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                    """Async wrapper with telemetry tracking."""
                    # Track execution
                    async with self.collector.track_execution(
                        name, **kwargs
                    ) as exec_id:
                        # Tag with function signature
                        self.collector.add_tag("function", func.__name__)
                        self.collector.add_tag("execution_id", exec_id)

                        # Execute function
                        result = await func(*args, **kwargs)
                        return result

                return cast(T, async_wrapper)
            else:

                @functools.wraps(func)
                def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                    """Sync wrapper - not supported, raises error."""
                    raise TypeError(
                        f"Telemetry instrumentation requires async function, "
                        f"but {func.__name__} is synchronous. "
                        f"Convert to async or use @agent decorator."
                    )

                return cast(T, sync_wrapper)

        return decorator

    def get_collector(self) -> TelemetryCollector:
        """Get the telemetry collector.

        Returns:
            TelemetryCollector instance

        Example:
            >>> collector = telemetry.get_collector()
            >>> collector.record_llm_call("gpt-4o", 100, 50, 1.0, 0.001)
        """
        return self.collector

    def __repr__(self) -> str:
        """String representation."""
        return f"Telemetry(collector={self.collector!r})"


# Global telemetry instance for convenience
_global_telemetry: Optional[Telemetry] = None


def get_global_telemetry() -> Telemetry:
    """Get or create global telemetry instance.

    Returns:
        Global Telemetry instance

    Example:
        >>> from kagura.observability import get_global_telemetry
        >>> telemetry = get_global_telemetry()
        >>> collector = telemetry.get_collector()
    """
    global _global_telemetry
    if _global_telemetry is None:
        _global_telemetry = Telemetry()
    return _global_telemetry


def set_global_telemetry(telemetry: Telemetry) -> None:
    """Set global telemetry instance.

    Args:
        telemetry: Telemetry instance to use globally

    Example:
        >>> from kagura.observability import EventStore, Telemetry, set_global_telemetry
        >>> store = EventStore(":memory:")
        >>> telemetry = Telemetry(store)
        >>> set_global_telemetry(telemetry)
    """
    global _global_telemetry
    _global_telemetry = telemetry
