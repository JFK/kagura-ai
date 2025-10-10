"""Tests for EventStore."""

import time
from pathlib import Path

import pytest

from kagura.observability import EventStore


# ===== Initialization Tests =====


def test_store_initialization_default():
    """Test EventStore initialization with default path."""
    store = EventStore()

    # Should create at ~/.kagura/telemetry.db
    expected_path = Path.home() / ".kagura" / "telemetry.db"
    assert store.db_path == expected_path
    assert expected_path.exists()

    # Cleanup
    expected_path.unlink()


def test_store_initialization_memory():
    """Test EventStore initialization with in-memory database."""
    store = EventStore(":memory:")

    assert store.db_path == ":memory:"


def test_store_initialization_custom_path(tmp_path):
    """Test EventStore initialization with custom path."""
    db_path = tmp_path / "custom.db"
    store = EventStore(db_path)

    assert store.db_path == db_path
    assert db_path.exists()


# ===== Save and Retrieve Tests =====


@pytest.mark.asyncio
async def test_save_execution_basic():
    """Test saving basic execution record."""
    store = EventStore(":memory:")

    execution = {
        "id": "exec_123",
        "agent_name": "test_agent",
        "started_at": time.time(),
        "ended_at": time.time() + 1.0,
        "duration": 1.0,
        "status": "completed",
    }

    await store.save_execution(execution)

    # Retrieve and verify
    retrieved = store.get_execution("exec_123")
    assert retrieved is not None
    assert retrieved["id"] == "exec_123"
    assert retrieved["agent_name"] == "test_agent"
    assert retrieved["status"] == "completed"


@pytest.mark.asyncio
async def test_save_execution_with_events():
    """Test saving execution with events."""
    store = EventStore(":memory:")

    execution = {
        "id": "exec_456",
        "agent_name": "llm_agent",
        "started_at": time.time(),
        "events": [
            {
                "type": "llm_call",
                "timestamp": time.time(),
                "data": {
                    "model": "gpt-4o",
                    "prompt_tokens": 100,
                    "completion_tokens": 50,
                    "cost": 0.001,
                },
            }
        ],
        "metrics": {"llm_calls": 1, "total_cost": 0.001},
    }

    await store.save_execution(execution)

    # Retrieve and verify
    retrieved = store.get_execution("exec_456")
    assert retrieved is not None
    assert len(retrieved["events"]) == 1
    assert retrieved["events"][0]["type"] == "llm_call"
    assert retrieved["metrics"]["llm_calls"] == 1


@pytest.mark.asyncio
async def test_save_execution_with_kwargs():
    """Test saving execution with agent kwargs."""
    store = EventStore(":memory:")

    execution = {
        "id": "exec_789",
        "agent_name": "translator",
        "started_at": time.time(),
        "kwargs": {"query": "Hello", "target_lang": "French"},
    }

    await store.save_execution(execution)

    # Retrieve and verify
    retrieved = store.get_execution("exec_789")
    assert retrieved is not None
    assert retrieved["kwargs"]["query"] == "Hello"
    assert retrieved["kwargs"]["target_lang"] == "French"


@pytest.mark.asyncio
async def test_save_execution_with_error():
    """Test saving failed execution with error."""
    store = EventStore(":memory:")

    execution = {
        "id": "exec_error",
        "agent_name": "failing_agent",
        "started_at": time.time(),
        "ended_at": time.time() + 0.5,
        "duration": 0.5,
        "status": "failed",
        "error": "ValueError: Invalid input",
    }

    await store.save_execution(execution)

    # Retrieve and verify
    retrieved = store.get_execution("exec_error")
    assert retrieved is not None
    assert retrieved["status"] == "failed"
    assert "ValueError" in retrieved["error"]


# ===== Query Tests =====


@pytest.mark.asyncio
async def test_get_executions_all():
    """Test retrieving all executions."""
    store = EventStore(":memory:")

    # Add multiple executions
    for i in range(3):
        await store.save_execution(
            {
                "id": f"exec_{i}",
                "agent_name": f"agent_{i}",
                "started_at": time.time() + i,
            }
        )

    # Retrieve all
    executions = store.get_executions()
    assert len(executions) == 3


@pytest.mark.asyncio
async def test_get_executions_by_agent_name():
    """Test filtering executions by agent name."""
    store = EventStore(":memory:")

    # Add executions for different agents
    await store.save_execution(
        {
            "id": "exec_1",
            "agent_name": "translator",
            "started_at": time.time(),
        }
    )
    await store.save_execution(
        {
            "id": "exec_2",
            "agent_name": "translator",
            "started_at": time.time() + 1,
        }
    )
    await store.save_execution(
        {
            "id": "exec_3",
            "agent_name": "reviewer",
            "started_at": time.time() + 2,
        }
    )

    # Filter by agent name
    translator_execs = store.get_executions(agent_name="translator")
    assert len(translator_execs) == 2
    assert all(e["agent_name"] == "translator" for e in translator_execs)


@pytest.mark.asyncio
async def test_get_executions_by_status():
    """Test filtering executions by status."""
    store = EventStore(":memory:")

    # Add executions with different statuses
    await store.save_execution(
        {
            "id": "exec_1",
            "agent_name": "agent_1",
            "started_at": time.time(),
            "status": "completed",
        }
    )
    await store.save_execution(
        {
            "id": "exec_2",
            "agent_name": "agent_2",
            "started_at": time.time() + 1,
            "status": "failed",
        }
    )
    await store.save_execution(
        {
            "id": "exec_3",
            "agent_name": "agent_3",
            "started_at": time.time() + 2,
            "status": "completed",
        }
    )

    # Filter by status
    completed = store.get_executions(status="completed")
    assert len(completed) == 2
    assert all(e["status"] == "completed" for e in completed)

    failed = store.get_executions(status="failed")
    assert len(failed) == 1
    assert failed[0]["status"] == "failed"


@pytest.mark.asyncio
async def test_get_executions_since():
    """Test filtering executions by time."""
    store = EventStore(":memory:")

    now = time.time()

    # Add executions at different times
    await store.save_execution(
        {"id": "exec_1", "agent_name": "agent_1", "started_at": now - 100}
    )
    await store.save_execution(
        {"id": "exec_2", "agent_name": "agent_2", "started_at": now - 50}
    )
    await store.save_execution(
        {"id": "exec_3", "agent_name": "agent_3", "started_at": now}
    )

    # Filter by time
    recent = store.get_executions(since=now - 60)
    assert len(recent) == 2
    assert all(e["started_at"] >= now - 60 for e in recent)


@pytest.mark.asyncio
async def test_get_executions_limit():
    """Test limiting number of results."""
    store = EventStore(":memory:")

    # Add many executions
    for i in range(10):
        await store.save_execution(
            {
                "id": f"exec_{i}",
                "agent_name": "agent",
                "started_at": time.time() + i,
            }
        )

    # Limit results
    limited = store.get_executions(limit=5)
    assert len(limited) == 5


@pytest.mark.asyncio
async def test_get_executions_order():
    """Test executions are returned in reverse chronological order."""
    store = EventStore(":memory:")

    # Add executions with incrementing timestamps
    for i in range(3):
        await store.save_execution(
            {
                "id": f"exec_{i}",
                "agent_name": "agent",
                "started_at": time.time() + i,
            }
        )

    executions = store.get_executions()

    # Should be in reverse chronological order (newest first)
    assert executions[0]["id"] == "exec_2"
    assert executions[1]["id"] == "exec_1"
    assert executions[2]["id"] == "exec_0"


# ===== Summary Statistics Tests =====


@pytest.mark.asyncio
async def test_get_summary_stats_empty():
    """Test summary stats with no data."""
    store = EventStore(":memory:")

    stats = store.get_summary_stats()

    assert stats["total_executions"] == 0
    assert stats["completed"] == 0
    assert stats["failed"] == 0
    assert stats["avg_duration"] == 0.0


@pytest.mark.asyncio
async def test_get_summary_stats_basic():
    """Test summary stats calculation."""
    store = EventStore(":memory:")

    # Add various executions
    await store.save_execution(
        {
            "id": "exec_1",
            "agent_name": "agent_1",
            "started_at": time.time(),
            "duration": 1.0,
            "status": "completed",
        }
    )
    await store.save_execution(
        {
            "id": "exec_2",
            "agent_name": "agent_2",
            "started_at": time.time() + 1,
            "duration": 2.0,
            "status": "completed",
        }
    )
    await store.save_execution(
        {
            "id": "exec_3",
            "agent_name": "agent_3",
            "started_at": time.time() + 2,
            "duration": 3.0,
            "status": "failed",
        }
    )

    stats = store.get_summary_stats()

    assert stats["total_executions"] == 3
    assert stats["completed"] == 2
    assert stats["failed"] == 1
    assert stats["avg_duration"] == 2.0  # (1.0 + 2.0 + 3.0) / 3


@pytest.mark.asyncio
async def test_get_summary_stats_by_agent():
    """Test summary stats filtered by agent."""
    store = EventStore(":memory:")

    # Add executions for different agents
    await store.save_execution(
        {
            "id": "exec_1",
            "agent_name": "translator",
            "started_at": time.time(),
            "status": "completed",
        }
    )
    await store.save_execution(
        {
            "id": "exec_2",
            "agent_name": "translator",
            "started_at": time.time() + 1,
            "status": "completed",
        }
    )
    await store.save_execution(
        {
            "id": "exec_3",
            "agent_name": "reviewer",
            "started_at": time.time() + 2,
            "status": "failed",
        }
    )

    # Get stats for translator only
    stats = store.get_summary_stats(agent_name="translator")

    assert stats["total_executions"] == 2
    assert stats["completed"] == 2
    assert stats["failed"] == 0


@pytest.mark.asyncio
async def test_get_summary_stats_since():
    """Test summary stats filtered by time."""
    store = EventStore(":memory:")

    now = time.time()

    # Add old and recent executions
    await store.save_execution(
        {
            "id": "exec_1",
            "agent_name": "agent_1",
            "started_at": now - 100,
            "status": "completed",
        }
    )
    await store.save_execution(
        {
            "id": "exec_2",
            "agent_name": "agent_2",
            "started_at": now,
            "status": "completed",
        }
    )

    # Get stats for recent executions only
    stats = store.get_summary_stats(since=now - 10)

    assert stats["total_executions"] == 1
    assert stats["completed"] == 1


# ===== Delete Operations Tests =====


@pytest.mark.asyncio
async def test_delete_old_executions():
    """Test deleting old executions."""
    store = EventStore(":memory:")

    now = time.time()

    # Add old and recent executions
    await store.save_execution(
        {"id": "exec_old", "agent_name": "agent_1", "started_at": now - 100}
    )
    await store.save_execution(
        {"id": "exec_recent", "agent_name": "agent_2", "started_at": now}
    )

    # Delete old executions
    deleted_count = store.delete_old_executions(older_than=now - 50)

    assert deleted_count == 1

    # Verify only recent execution remains
    executions = store.get_executions()
    assert len(executions) == 1
    assert executions[0]["id"] == "exec_recent"


@pytest.mark.asyncio
async def test_clear_all():
    """Test clearing all executions."""
    store = EventStore(":memory:")

    # Add executions
    for i in range(5):
        await store.save_execution(
            {
                "id": f"exec_{i}",
                "agent_name": "agent",
                "started_at": time.time(),
            }
        )

    # Clear all
    store.clear_all()

    # Verify empty
    executions = store.get_executions()
    assert len(executions) == 0


# ===== Edge Cases Tests =====


def test_get_execution_not_found():
    """Test retrieving non-existent execution."""
    store = EventStore(":memory:")

    result = store.get_execution("nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_save_execution_minimal():
    """Test saving execution with minimal data."""
    store = EventStore(":memory:")

    execution = {
        "id": "exec_min",
        "agent_name": "minimal_agent",
        "started_at": time.time(),
    }

    await store.save_execution(execution)

    # Retrieve and verify
    retrieved = store.get_execution("exec_min")
    assert retrieved is not None
    assert retrieved["id"] == "exec_min"
    assert retrieved["ended_at"] is None
    assert retrieved["duration"] is None
    assert retrieved["status"] is None


@pytest.mark.asyncio
async def test_json_serialization_complex():
    """Test JSON serialization of complex data structures."""
    store = EventStore(":memory:")

    execution = {
        "id": "exec_complex",
        "agent_name": "complex_agent",
        "started_at": time.time(),
        "kwargs": {
            "nested": {"deep": {"value": 123}},
            "list": [1, 2, 3],
            "mixed": {"a": [1, 2], "b": {"c": "d"}},
        },
        "events": [
            {
                "type": "custom",
                "data": {"complex": [{"key": "value"}]},
            }
        ],
    }

    await store.save_execution(execution)

    # Retrieve and verify
    retrieved = store.get_execution("exec_complex")
    assert retrieved is not None
    assert retrieved["kwargs"]["nested"]["deep"]["value"] == 123
    assert retrieved["kwargs"]["list"] == [1, 2, 3]


# ===== Representation Test =====


def test_store_repr():
    """Test EventStore string representation."""
    store = EventStore(":memory:")

    repr_str = repr(store)
    assert "EventStore" in repr_str
    assert ":memory:" in repr_str
