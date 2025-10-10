"""Telemetry collector for agent executions."""

from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Optional

from .store import EventStore


class TelemetryCollector:
    """Collect telemetry data from agent executions.

    Example:
        >>> collector = TelemetryCollector(EventStore(":memory:"))
        >>> async with collector.track_execution("my_agent") as exec_id:
        ...     collector.record_llm_call("gpt-4o", 100, 50, 1.0, 0.001)
        >>> execution = collector.store.get_execution(exec_id)
    """

    def __init__(self, store: EventStore) -> None:
        """Initialize telemetry collector.

        Args:
            store: Event store for persisting telemetry data
        """
        self.store = store
        self._current_execution: Optional[dict[str, Any]] = None

    @asynccontextmanager
    async def track_execution(
        self, agent_name: str, **kwargs: Any
    ) -> AsyncIterator[str]:
        """Track agent execution.

        Args:
            agent_name: Name of the agent being executed
            **kwargs: Agent arguments

        Yields:
            execution_id: Unique execution ID

        Example:
            >>> async with collector.track_execution("my_agent", query="test"):
            ...     # Agent execution code here
            ...     collector.record_event("custom_event", data="value")
        """
        execution_id = self._generate_id()
        execution = {
            "id": execution_id,
            "agent_name": agent_name,
            "started_at": time.time(),
            "kwargs": kwargs,
            "events": [],
            "metrics": {},
            "status": "running",
        }

        self._current_execution = execution

        try:
            yield execution_id
        except Exception as e:
            execution["status"] = "failed"
            execution["error"] = str(e)
            raise
        else:
            execution["status"] = "completed"
        finally:
            execution["ended_at"] = time.time()
            execution["duration"] = execution["ended_at"] - execution["started_at"]

            # Calculate total cost from LLM calls
            total_cost = sum(
                event["data"].get("cost", 0.0)
                for event in execution["events"]
                if event["type"] == "llm_call"
            )
            if total_cost > 0:
                execution["metrics"]["total_cost"] = total_cost

            await self.store.save_execution(execution)
            self._current_execution = None

    def record_event(self, event_type: str, **data: Any) -> None:
        """Record an event in current execution.

        Args:
            event_type: Type of event
            **data: Event data
        """
        if not self._current_execution:
            return

        event = {
            "type": event_type,
            "timestamp": time.time(),
            "data": data,
        }
        self._current_execution["events"].append(event)

    def record_llm_call(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        duration: float,
        cost: float,
    ) -> None:
        """Record LLM call.

        Args:
            model: Model name (e.g., "gpt-4o")
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            duration: Call duration in seconds
            cost: Call cost in USD
        """
        self.record_event(
            "llm_call",
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            duration=duration,
            cost=cost,
        )

        # Update metrics
        if self._current_execution:
            metrics = self._current_execution["metrics"]
            metrics["llm_calls"] = metrics.get("llm_calls", 0) + 1
            metrics["total_tokens"] = (
                metrics.get("total_tokens", 0) + prompt_tokens + completion_tokens
            )

    def record_tool_call(self, tool_name: str, duration: float, **kwargs: Any) -> None:
        """Record tool call.

        Args:
            tool_name: Name of the tool
            duration: Call duration in seconds
            **kwargs: Tool arguments
        """
        self.record_event(
            "tool_call", tool_name=tool_name, duration=duration, kwargs=kwargs
        )

        # Update metrics
        if self._current_execution:
            metrics = self._current_execution["metrics"]
            metrics["tool_calls"] = metrics.get("tool_calls", 0) + 1

    def record_memory_operation(
        self, operation: str, duration: float, **kwargs: Any
    ) -> None:
        """Record memory operation.

        Args:
            operation: Operation type (e.g., "lookup", "store")
            duration: Operation duration in seconds
            **kwargs: Operation details
        """
        self.record_event(
            "memory_operation", operation=operation, duration=duration, kwargs=kwargs
        )

    def record_metric(self, name: str, value: Any) -> None:
        """Record custom metric.

        Args:
            name: Metric name
            value: Metric value
        """
        if self._current_execution:
            self._current_execution["metrics"][name] = value

    def add_tag(self, key: str, value: str) -> None:
        """Add tag to current execution.

        Args:
            key: Tag key
            value: Tag value
        """
        if self._current_execution:
            if "tags" not in self._current_execution:
                self._current_execution["tags"] = {}
            self._current_execution["tags"][key] = value

    def _generate_id(self) -> str:
        """Generate unique execution ID.

        Returns:
            Execution ID (e.g., "exec_abc123")
        """
        return f"exec_{uuid.uuid4().hex[:8]}"

    def __repr__(self) -> str:
        """String representation."""
        active = self._current_execution["id"] if self._current_execution else None
        return f"TelemetryCollector(store={self.store!r}, active={active!r})"
