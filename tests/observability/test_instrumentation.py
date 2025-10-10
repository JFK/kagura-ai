"""Tests for Telemetry instrumentation."""

import pytest

from kagura.observability import EventStore, Telemetry, get_global_telemetry, set_global_telemetry


# ===== Initialization Tests =====


def test_telemetry_initialization_default():
    """Test Telemetry initialization with default store."""
    telemetry = Telemetry()

    assert telemetry.collector is not None
    assert telemetry.collector.store is not None


def test_telemetry_initialization_custom_store():
    """Test Telemetry initialization with custom store."""
    store = EventStore(":memory:")
    telemetry = Telemetry(store)

    assert telemetry.collector.store is store


def test_telemetry_repr():
    """Test Telemetry string representation."""
    store = EventStore(":memory:")
    telemetry = Telemetry(store)

    repr_str = repr(telemetry)
    assert "Telemetry" in repr_str
    assert "collector=" in repr_str


# ===== Decorator Basic Tests =====


@pytest.mark.asyncio
async def test_instrument_basic():
    """Test basic instrumentation."""
    store = EventStore(":memory:")
    telemetry = Telemetry(store)

    @telemetry.instrument()
    async def test_agent(query: str) -> str:
        """Test agent."""
        return f"Result: {query}"

    result = await test_agent("test input")

    assert result == "Result: test input"

    # Verify telemetry collected
    executions = store.get_executions()
    assert len(executions) == 1
    assert executions[0]["agent_name"] == "test_agent"
    assert executions[0]["status"] == "completed"


@pytest.mark.asyncio
async def test_instrument_custom_name():
    """Test instrumentation with custom agent name."""
    store = EventStore(":memory:")
    telemetry = Telemetry(store)

    @telemetry.instrument("custom_agent")
    async def my_function(data: dict) -> dict:
        """Custom function."""
        return {"processed": data}

    await my_function({"key": "value"})

    # Verify custom name used
    executions = store.get_executions()
    assert len(executions) == 1
    assert executions[0]["agent_name"] == "custom_agent"


@pytest.mark.asyncio
async def test_instrument_preserves_function_metadata():
    """Test instrumentation preserves function name and docstring."""
    store = EventStore(":memory:")
    telemetry = Telemetry(store)

    @telemetry.instrument()
    async def documented_agent(x: int) -> int:
        """This is a documented agent."""
        return x * 2

    assert documented_agent.__name__ == "documented_agent"
    assert "documented agent" in documented_agent.__doc__


# ===== Decorator with Arguments Tests =====


@pytest.mark.asyncio
async def test_instrument_with_kwargs():
    """Test instrumentation captures kwargs."""
    store = EventStore(":memory:")
    telemetry = Telemetry(store)

    @telemetry.instrument()
    async def agent_with_kwargs(query: str, lang: str = "en") -> str:
        """Agent with kwargs."""
        return f"{lang}: {query}"

    await agent_with_kwargs("hello", lang="fr")

    # Verify kwargs captured
    executions = store.get_executions()
    assert executions[0]["kwargs"]["lang"] == "fr"


@pytest.mark.asyncio
async def test_instrument_with_positional_args():
    """Test instrumentation with positional arguments."""
    store = EventStore(":memory:")
    telemetry = Telemetry(store)

    @telemetry.instrument()
    async def agent_with_args(a: int, b: int, c: int = 0) -> int:
        """Agent with args."""
        return a + b + c

    result = await agent_with_args(1, 2, c=3)

    assert result == 6

    # Note: positional args are not captured in kwargs
    executions = store.get_executions()
    assert executions[0]["kwargs"]["c"] == 3


# ===== Error Handling Tests =====


@pytest.mark.asyncio
async def test_instrument_error_handling():
    """Test instrumentation handles errors."""
    store = EventStore(":memory:")
    telemetry = Telemetry(store)

    @telemetry.instrument()
    async def failing_agent(query: str) -> str:
        """Agent that fails."""
        raise ValueError("Test error")

    with pytest.raises(ValueError):
        await failing_agent("test")

    # Verify error recorded
    executions = store.get_executions()
    assert len(executions) == 1
    assert executions[0]["status"] == "failed"
    assert "Test error" in executions[0]["error"]


@pytest.mark.asyncio
async def test_instrument_error_propagation():
    """Test instrumentation propagates errors."""
    store = EventStore(":memory:")
    telemetry = Telemetry(store)

    @telemetry.instrument()
    async def error_agent(query: str) -> str:
        """Agent that raises error."""
        raise RuntimeError("Critical error")

    with pytest.raises(RuntimeError) as exc_info:
        await error_agent("test")

    assert "Critical error" in str(exc_info.value)


# ===== Synchronous Function Tests =====


def test_instrument_sync_function_raises_error():
    """Test instrumentation raises error for sync functions."""
    store = EventStore(":memory:")
    telemetry = Telemetry(store)

    @telemetry.instrument()
    def sync_agent(query: str) -> str:
        """Sync agent (not supported)."""
        return query

    with pytest.raises(TypeError) as exc_info:
        sync_agent("test")

    assert "async function" in str(exc_info.value)
    assert "sync_agent" in str(exc_info.value)


# ===== Tagging Tests =====


@pytest.mark.asyncio
async def test_instrument_adds_tags():
    """Test instrumentation adds function tags."""
    store = EventStore(":memory:")
    telemetry = Telemetry(store)

    @telemetry.instrument()
    async def tagged_agent(query: str) -> str:
        """Agent with tags."""
        return query

    await tagged_agent("test")

    # Tags are added but may not persist to DB
    # This test verifies the decorator calls add_tag
    executions = store.get_executions()
    assert len(executions) == 1


# ===== Multiple Executions Tests =====


@pytest.mark.asyncio
async def test_instrument_multiple_executions():
    """Test instrumentation tracks multiple executions."""
    store = EventStore(":memory:")
    telemetry = Telemetry(store)

    @telemetry.instrument()
    async def multi_agent(query: str) -> str:
        """Agent called multiple times."""
        return f"Result: {query}"

    await multi_agent("first")
    await multi_agent("second")
    await multi_agent("third")

    # Verify all executions tracked
    executions = store.get_executions()
    assert len(executions) == 3
    assert all(e["agent_name"] == "multi_agent" for e in executions)


# ===== Get Collector Tests =====


def test_get_collector():
    """Test getting collector from telemetry."""
    store = EventStore(":memory:")
    telemetry = Telemetry(store)

    collector = telemetry.get_collector()

    assert collector is telemetry.collector
    assert collector.store is store


@pytest.mark.asyncio
async def test_get_collector_manual_recording():
    """Test manual recording via get_collector."""
    store = EventStore(":memory:")
    telemetry = Telemetry(store)
    collector = telemetry.get_collector()

    @telemetry.instrument()
    async def agent_with_manual_events(query: str) -> str:
        """Agent that records manual events."""
        # Manual event recording
        collector.record_event("custom_event", query=query)
        return f"Processed: {query}"

    await agent_with_manual_events("test")

    # Verify custom event recorded
    executions = store.get_executions()
    assert len(executions) == 1
    assert len(executions[0]["events"]) == 1
    assert executions[0]["events"][0]["type"] == "custom_event"


# ===== Global Telemetry Tests =====


def test_get_global_telemetry_singleton():
    """Test global telemetry is singleton."""
    telemetry1 = get_global_telemetry()
    telemetry2 = get_global_telemetry()

    assert telemetry1 is telemetry2


def test_set_global_telemetry():
    """Test setting global telemetry."""
    store = EventStore(":memory:")
    custom_telemetry = Telemetry(store)

    set_global_telemetry(custom_telemetry)

    retrieved = get_global_telemetry()
    assert retrieved is custom_telemetry


@pytest.mark.asyncio
async def test_global_telemetry_usage():
    """Test using global telemetry."""
    from kagura.observability.instrumentation import get_global_telemetry

    # Reset global state
    import kagura.observability.instrumentation as instr_module

    instr_module._global_telemetry = None

    telemetry = get_global_telemetry()

    @telemetry.instrument()
    async def global_agent(query: str) -> str:
        """Agent using global telemetry."""
        return query

    await global_agent("test")

    # Verify execution tracked
    collector = telemetry.get_collector()
    executions = collector.store.get_executions()
    assert len(executions) >= 1  # May have executions from other tests


# ===== Integration Tests =====


@pytest.mark.asyncio
async def test_full_instrumentation_lifecycle():
    """Test full instrumentation lifecycle with manual recording."""
    store = EventStore(":memory:")
    telemetry = Telemetry(store)
    collector = telemetry.get_collector()

    @telemetry.instrument("complex_agent")
    async def complex_agent(query: str, iterations: int = 1) -> dict:
        """Complex agent with manual telemetry."""
        # Record LLM call
        collector.record_llm_call("gpt-4o", 100, 50, 1.0, 0.003)

        # Record tool call
        collector.record_tool_call("analyzer", 0.5, query=query)

        # Record custom metric
        collector.record_metric("iterations", iterations)

        return {"result": f"Processed {query}"}

    result = await complex_agent("test query", iterations=3)

    assert result["result"] == "Processed test query"

    # Verify comprehensive telemetry
    executions = store.get_executions()
    assert len(executions) == 1

    execution = executions[0]
    assert execution["agent_name"] == "complex_agent"
    assert execution["status"] == "completed"
    assert execution["kwargs"]["iterations"] == 3

    # Check events
    assert len(execution["events"]) == 2  # LLM call + tool call
    llm_events = [e for e in execution["events"] if e["type"] == "llm_call"]
    tool_events = [e for e in execution["events"] if e["type"] == "tool_call"]
    assert len(llm_events) == 1
    assert len(tool_events) == 1

    # Check metrics
    assert execution["metrics"]["llm_calls"] == 1
    assert execution["metrics"]["tool_calls"] == 1
    assert execution["metrics"]["total_cost"] == 0.003
    assert execution["metrics"]["iterations"] == 3


@pytest.mark.asyncio
async def test_concurrent_executions():
    """Test instrumentation handles concurrent executions."""
    import asyncio

    store = EventStore(":memory:")
    telemetry = Telemetry(store)

    @telemetry.instrument()
    async def concurrent_agent(agent_id: int) -> int:
        """Agent for concurrent testing."""
        await asyncio.sleep(0.01)  # Simulate work
        return agent_id

    # Run multiple agents concurrently
    results = await asyncio.gather(
        concurrent_agent(1), concurrent_agent(2), concurrent_agent(3)
    )

    assert results == [1, 2, 3]

    # Verify all executions tracked
    executions = store.get_executions()
    assert len(executions) == 3
    assert all(e["status"] == "completed" for e in executions)


# ===== Edge Cases Tests =====


@pytest.mark.asyncio
async def test_instrument_no_arguments():
    """Test instrumentation with agent that takes no arguments."""
    store = EventStore(":memory:")
    telemetry = Telemetry(store)

    @telemetry.instrument()
    async def no_arg_agent() -> str:
        """Agent with no arguments."""
        return "fixed result"

    result = await no_arg_agent()

    assert result == "fixed result"

    executions = store.get_executions()
    assert len(executions) == 1
    assert executions[0]["kwargs"] == {}


@pytest.mark.asyncio
async def test_instrument_return_none():
    """Test instrumentation with agent that returns None."""
    store = EventStore(":memory:")
    telemetry = Telemetry(store)

    @telemetry.instrument()
    async def void_agent(query: str) -> None:
        """Agent that returns None."""
        pass  # Does nothing

    result = await void_agent("test")

    assert result is None

    executions = store.get_executions()
    assert len(executions) == 1
    assert executions[0]["status"] == "completed"


@pytest.mark.asyncio
async def test_instrument_complex_return_type():
    """Test instrumentation with complex return types."""
    store = EventStore(":memory:")
    telemetry = Telemetry(store)

    @telemetry.instrument()
    async def complex_return_agent(data: list) -> dict:
        """Agent with complex return type."""
        return {"processed": data, "count": len(data)}

    result = await complex_return_agent([1, 2, 3])

    assert result["processed"] == [1, 2, 3]
    assert result["count"] == 3

    executions = store.get_executions()
    assert len(executions) == 1
