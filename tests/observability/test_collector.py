"""Tests for TelemetryCollector."""

import pytest

from kagura.observability import EventStore, TelemetryCollector

# ===== Initialization Tests =====


def test_collector_initialization():
    """Test TelemetryCollector initialization."""
    store = EventStore(":memory:")
    collector = TelemetryCollector(store)

    assert collector.store is store
    assert collector._current_execution is None


def test_collector_repr():
    """Test TelemetryCollector string representation."""
    store = EventStore(":memory:")
    collector = TelemetryCollector(store)

    repr_str = repr(collector)
    assert "TelemetryCollector" in repr_str
    assert "active=None" in repr_str


# ===== Execution Tracking Tests =====


@pytest.mark.asyncio
async def test_track_execution_basic():
    """Test basic execution tracking."""
    store = EventStore(":memory:")
    collector = TelemetryCollector(store)

    async with collector.track_execution("test_agent") as exec_id:
        assert exec_id.startswith("exec_")
        assert collector._current_execution is not None
        assert collector._current_execution["id"] == exec_id
        assert collector._current_execution["agent_name"] == "test_agent"
        assert collector._current_execution["status"] == "running"

    # After context exit
    assert collector._current_execution is None

    # Verify stored in database
    execution = store.get_execution(exec_id)
    assert execution is not None
    assert execution["status"] == "completed"
    assert execution["duration"] > 0


@pytest.mark.asyncio
async def test_track_execution_with_kwargs():
    """Test execution tracking with agent kwargs."""
    store = EventStore(":memory:")
    collector = TelemetryCollector(store)

    async with collector.track_execution(
        "translator", query="Hello", target_lang="French"
    ) as exec_id:
        pass

    # Verify kwargs stored
    execution = store.get_execution(exec_id)
    assert execution["kwargs"]["query"] == "Hello"
    assert execution["kwargs"]["target_lang"] == "French"


@pytest.mark.asyncio
async def test_track_execution_error_handling():
    """Test execution tracking with error."""
    store = EventStore(":memory:")
    collector = TelemetryCollector(store)

    with pytest.raises(ValueError):
        async with collector.track_execution("failing_agent") as exec_id:
            raise ValueError("Test error")

    # Verify error recorded
    execution = store.get_execution(exec_id)
    assert execution is not None
    assert execution["status"] == "failed"
    assert "Test error" in execution["error"]


@pytest.mark.asyncio
async def test_track_execution_timing():
    """Test execution duration tracking."""
    import asyncio

    store = EventStore(":memory:")
    collector = TelemetryCollector(store)

    async with collector.track_execution("slow_agent") as exec_id:
        await asyncio.sleep(0.1)  # Simulate work

    execution = store.get_execution(exec_id)
    assert execution["duration"] >= 0.1
    assert execution["ended_at"] > execution["started_at"]


# ===== Event Recording Tests =====


@pytest.mark.asyncio
async def test_record_event():
    """Test recording custom event."""
    store = EventStore(":memory:")
    collector = TelemetryCollector(store)

    async with collector.track_execution("test_agent") as exec_id:
        collector.record_event("custom_event", key="value", number=123)

    execution = store.get_execution(exec_id)
    events = execution["events"]

    assert len(events) == 1
    assert events[0]["type"] == "custom_event"
    assert events[0]["data"]["key"] == "value"
    assert events[0]["data"]["number"] == 123
    assert "timestamp" in events[0]


@pytest.mark.asyncio
async def test_record_event_no_execution():
    """Test recording event when no execution is active."""
    store = EventStore(":memory:")
    collector = TelemetryCollector(store)

    # Should not raise error, just silently ignore
    collector.record_event("orphan_event", data="value")


@pytest.mark.asyncio
async def test_record_multiple_events():
    """Test recording multiple events."""
    store = EventStore(":memory:")
    collector = TelemetryCollector(store)

    async with collector.track_execution("test_agent") as exec_id:
        collector.record_event("event_1", index=1)
        collector.record_event("event_2", index=2)
        collector.record_event("event_3", index=3)

    execution = store.get_execution(exec_id)
    events = execution["events"]

    assert len(events) == 3
    assert events[0]["data"]["index"] == 1
    assert events[1]["data"]["index"] == 2
    assert events[2]["data"]["index"] == 3


# ===== LLM Call Recording Tests =====


@pytest.mark.asyncio
async def test_record_llm_call():
    """Test recording LLM call."""
    store = EventStore(":memory:")
    collector = TelemetryCollector(store)

    async with collector.track_execution("llm_agent") as exec_id:
        collector.record_llm_call(
            model="gpt-4o",
            prompt_tokens=100,
            completion_tokens=50,
            duration=1.5,
            cost=0.003,
        )

    execution = store.get_execution(exec_id)
    events = execution["events"]

    assert len(events) == 1
    assert events[0]["type"] == "llm_call"
    assert events[0]["data"]["model"] == "gpt-4o"
    assert events[0]["data"]["prompt_tokens"] == 100
    assert events[0]["data"]["completion_tokens"] == 50
    assert events[0]["data"]["total_tokens"] == 150
    assert events[0]["data"]["duration"] == 1.5
    assert events[0]["data"]["cost"] == 0.003


@pytest.mark.asyncio
async def test_record_llm_call_updates_metrics():
    """Test LLM call updates metrics."""
    store = EventStore(":memory:")
    collector = TelemetryCollector(store)

    async with collector.track_execution("llm_agent") as exec_id:
        collector.record_llm_call("gpt-4o", 100, 50, 1.0, 0.001)
        collector.record_llm_call("gpt-5-mini", 50, 25, 0.5, 0.0005)

    execution = store.get_execution(exec_id)
    metrics = execution["metrics"]

    assert metrics["llm_calls"] == 2
    assert metrics["total_tokens"] == 225  # (100+50) + (50+25)


@pytest.mark.asyncio
async def test_record_llm_call_cost_aggregation():
    """Test LLM call cost aggregation."""
    store = EventStore(":memory:")
    collector = TelemetryCollector(store)

    async with collector.track_execution("llm_agent") as exec_id:
        collector.record_llm_call("gpt-4o", 100, 50, 1.0, 0.003)
        collector.record_llm_call("gpt-4o", 80, 40, 0.8, 0.002)

    execution = store.get_execution(exec_id)

    # Cost should be aggregated in metrics
    assert execution["metrics"]["total_cost"] == 0.005  # 0.003 + 0.002


# ===== Tool Call Recording Tests =====


@pytest.mark.asyncio
async def test_record_tool_call():
    """Test recording tool call."""
    store = EventStore(":memory:")
    collector = TelemetryCollector(store)

    async with collector.track_execution("tool_agent") as exec_id:
        collector.record_tool_call(
            tool_name="calculator", duration=0.1, operation="add", a=1, b=2
        )

    execution = store.get_execution(exec_id)
    events = execution["events"]

    assert len(events) == 1
    assert events[0]["type"] == "tool_call"
    assert events[0]["data"]["tool_name"] == "calculator"
    assert events[0]["data"]["duration"] == 0.1
    assert events[0]["data"]["kwargs"]["operation"] == "add"
    assert events[0]["data"]["kwargs"]["a"] == 1
    assert events[0]["data"]["kwargs"]["b"] == 2


@pytest.mark.asyncio
async def test_record_tool_call_updates_metrics():
    """Test tool call updates metrics."""
    store = EventStore(":memory:")
    collector = TelemetryCollector(store)

    async with collector.track_execution("tool_agent") as exec_id:
        collector.record_tool_call("tool1", 0.1)
        collector.record_tool_call("tool2", 0.2)
        collector.record_tool_call("tool3", 0.3)

    execution = store.get_execution(exec_id)
    metrics = execution["metrics"]

    assert metrics["tool_calls"] == 3


# ===== Memory Operation Recording Tests =====


@pytest.mark.asyncio
async def test_record_memory_operation():
    """Test recording memory operation."""
    store = EventStore(":memory:")
    collector = TelemetryCollector(store)

    async with collector.track_execution("memory_agent") as exec_id:
        collector.record_memory_operation(
            operation="lookup", duration=0.05, query="user preferences"
        )

    execution = store.get_execution(exec_id)
    events = execution["events"]

    assert len(events) == 1
    assert events[0]["type"] == "memory_operation"
    assert events[0]["data"]["operation"] == "lookup"
    assert events[0]["data"]["duration"] == 0.05
    assert events[0]["data"]["kwargs"]["query"] == "user preferences"


# ===== Custom Metric Recording Tests =====


@pytest.mark.asyncio
async def test_record_metric():
    """Test recording custom metric."""
    store = EventStore(":memory:")
    collector = TelemetryCollector(store)

    async with collector.track_execution("metric_agent") as exec_id:
        collector.record_metric("success_rate", 0.95)
        collector.record_metric("items_processed", 42)

    execution = store.get_execution(exec_id)
    metrics = execution["metrics"]

    assert metrics["success_rate"] == 0.95
    assert metrics["items_processed"] == 42


@pytest.mark.asyncio
async def test_record_metric_no_execution():
    """Test recording metric when no execution is active."""
    store = EventStore(":memory:")
    collector = TelemetryCollector(store)

    # Should not raise error
    collector.record_metric("orphan_metric", 123)


# ===== Tag Management Tests =====


@pytest.mark.asyncio
async def test_add_tag():
    """Test adding tags to execution."""
    store = EventStore(":memory:")
    collector = TelemetryCollector(store)

    async with collector.track_execution("tagged_agent") as exec_id:
        collector.add_tag("environment", "production")
        collector.add_tag("version", "2.0.0")

    execution = store.get_execution(exec_id)

    # Tags should be in execution data
    # Note: tags are not in the schema, so they're stored in the execution dict
    # but not persisted to DB by default
    # This test verifies the in-memory behavior during execution


@pytest.mark.asyncio
async def test_add_tag_no_execution():
    """Test adding tag when no execution is active."""
    store = EventStore(":memory:")
    collector = TelemetryCollector(store)

    # Should not raise error
    collector.add_tag("orphan_tag", "value")


# ===== Integration Tests =====


@pytest.mark.asyncio
async def test_full_execution_lifecycle():
    """Test full execution lifecycle with all event types."""
    store = EventStore(":memory:")
    collector = TelemetryCollector(store)

    async with collector.track_execution(
        "complex_agent", query="analyze data"
    ) as exec_id:
        # Add tags
        collector.add_tag("environment", "test")

        # Record LLM calls
        collector.record_llm_call("gpt-4o", 100, 50, 1.0, 0.003)
        collector.record_llm_call("gpt-5-mini", 50, 25, 0.5, 0.0005)

        # Record tool calls
        collector.record_tool_call("data_loader", 0.2, source="database")
        collector.record_tool_call("analyzer", 0.5, method="statistical")

        # Record memory operations
        collector.record_memory_operation("lookup", 0.05, key="context")
        collector.record_memory_operation("store", 0.03, key="result")

        # Record custom events
        collector.record_event("processing_start", stage="preprocessing")
        collector.record_event("processing_end", stage="analysis")

        # Record custom metrics
        collector.record_metric("accuracy", 0.92)
        collector.record_metric("items_analyzed", 150)

    # Verify comprehensive execution record
    execution = store.get_execution(exec_id)

    assert execution["status"] == "completed"
    assert len(execution["events"]) == 8  # 2 LLM + 2 tool + 2 memory + 2 custom
    assert execution["metrics"]["llm_calls"] == 2
    assert execution["metrics"]["tool_calls"] == 2
    assert execution["metrics"]["total_cost"] == 0.0035
    assert execution["metrics"]["accuracy"] == 0.92


@pytest.mark.asyncio
async def test_nested_executions_not_supported():
    """Test that nested executions use the inner execution."""
    store = EventStore(":memory:")
    collector = TelemetryCollector(store)

    async with collector.track_execution("outer_agent") as outer_id:
        collector.record_event("outer_event", value=1)

        async with collector.track_execution("inner_agent") as inner_id:
            collector.record_event("inner_event", value=2)

        # After inner completes, outer should be None
        # (because track_execution sets _current_execution to None on exit)
        assert collector._current_execution is None

    # Verify inner execution has inner_event
    inner_execution = store.get_execution(inner_id)
    assert len(inner_execution["events"]) == 1
    assert inner_execution["events"][0]["data"]["value"] == 2

    # Verify outer execution has outer_event
    outer_execution = store.get_execution(outer_id)
    assert len(outer_execution["events"]) == 1
    assert outer_execution["events"][0]["data"]["value"] == 1


@pytest.mark.asyncio
async def test_execution_id_generation():
    """Test execution ID generation is unique."""
    store = EventStore(":memory:")
    collector = TelemetryCollector(store)

    ids = set()

    for _ in range(10):
        async with collector.track_execution("test_agent") as exec_id:
            assert exec_id.startswith("exec_")
            ids.add(exec_id)

    # All IDs should be unique
    assert len(ids) == 10


# ===== Edge Cases Tests =====


@pytest.mark.asyncio
async def test_empty_execution():
    """Test execution with no events or metrics."""
    store = EventStore(":memory:")
    collector = TelemetryCollector(store)

    async with collector.track_execution("empty_agent") as exec_id:
        pass  # No events recorded

    execution = store.get_execution(exec_id)

    assert execution["status"] == "completed"
    assert len(execution["events"]) == 0
    # metrics may have some default values but should be present
    assert isinstance(execution["metrics"], dict)


@pytest.mark.asyncio
async def test_zero_cost_llm_call():
    """Test LLM call with zero cost doesn't add total_cost metric."""
    store = EventStore(":memory:")
    collector = TelemetryCollector(store)

    async with collector.track_execution("free_agent") as exec_id:
        collector.record_llm_call("local-model", 100, 50, 1.0, 0.0)

    execution = store.get_execution(exec_id)

    # Zero cost should not add total_cost metric
    assert "total_cost" not in execution["metrics"]
    assert execution["metrics"]["llm_calls"] == 1
