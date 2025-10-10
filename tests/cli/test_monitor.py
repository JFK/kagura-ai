"""Tests for monitor CLI commands."""

import pytest
from click.testing import CliRunner

from kagura.cli.monitor import list, stats, cost, trace
from kagura.observability import EventStore, TelemetryCollector


@pytest.fixture
def runner():
    """Create CLI runner."""
    return CliRunner()


@pytest.fixture
def temp_db(tmp_path):
    """Create temporary database with sample data."""
    db_path = tmp_path / "test.db"
    store = EventStore(db_path)
    collector = TelemetryCollector(store)

    # Add sample execution
    async def create_data():
        async with collector.track_execution("test_agent", query="test"):
            collector.record_llm_call("gpt-4o", 100, 50, 1.0, 0.003)

    import asyncio

    asyncio.run(create_data())

    return str(db_path)


# ===== List Command Tests =====


def test_list_command_no_data(runner, tmp_path):
    """Test list command with no data."""
    db_path = tmp_path / "empty.db"
    EventStore(db_path)  # Create empty store

    result = runner.invoke(list, ["--db", str(db_path)])

    assert result.exit_code == 0
    assert "No executions found" in result.output or result.output == ""


def test_list_command_with_data(runner, temp_db):
    """Test list command with data."""
    result = runner.invoke(list, ["--db", temp_db])

    assert result.exit_code == 0


def test_list_command_with_agent_filter(runner, temp_db):
    """Test list command with agent filter."""
    result = runner.invoke(list, ["--agent", "test_agent", "--db", temp_db])

    assert result.exit_code == 0


def test_list_command_with_status_filter(runner, temp_db):
    """Test list command with status filter."""
    result = runner.invoke(list, ["--status", "completed", "--db", temp_db])

    assert result.exit_code == 0


def test_list_command_with_limit(runner, temp_db):
    """Test list command with limit."""
    result = runner.invoke(list, ["--limit", "5", "--db", temp_db])

    assert result.exit_code == 0


# ===== Stats Command Tests =====


def test_stats_command_no_data(runner, tmp_path):
    """Test stats command with no data."""
    db_path = tmp_path / "empty.db"
    EventStore(db_path)

    result = runner.invoke(stats, ["--db", str(db_path)])

    assert result.exit_code == 0


def test_stats_command_with_data(runner, temp_db):
    """Test stats command with data."""
    result = runner.invoke(stats, ["--db", temp_db])

    assert result.exit_code == 0


def test_stats_command_with_agent_filter(runner, temp_db):
    """Test stats command with agent filter."""
    result = runner.invoke(stats, ["--agent", "test_agent", "--db", temp_db])

    assert result.exit_code == 0


# ===== Cost Command Tests =====


def test_cost_command_no_data(runner, tmp_path):
    """Test cost command with no data."""
    db_path = tmp_path / "empty.db"
    EventStore(db_path)

    result = runner.invoke(cost, ["--db", str(db_path)])

    assert result.exit_code == 0


def test_cost_command_with_data(runner, temp_db):
    """Test cost command with data."""
    result = runner.invoke(cost, ["--db", temp_db])

    assert result.exit_code == 0


def test_cost_command_group_by_agent(runner, temp_db):
    """Test cost command grouped by agent."""
    result = runner.invoke(cost, ["--group-by", "agent", "--db", temp_db])

    assert result.exit_code == 0


def test_cost_command_group_by_date(runner, temp_db):
    """Test cost command grouped by date."""
    result = runner.invoke(cost, ["--group-by", "date", "--db", temp_db])

    assert result.exit_code == 0


# ===== Trace Command Tests =====


def test_trace_command_not_found(runner, tmp_path):
    """Test trace command with non-existent ID."""
    db_path = tmp_path / "empty.db"
    EventStore(db_path)

    result = runner.invoke(trace, ["nonexistent", "--db", str(db_path)])

    assert result.exit_code == 0
    assert "not found" in result.output


def test_trace_command_with_valid_id(runner, temp_db):
    """Test trace command with valid execution ID."""
    # Get an execution ID
    store = EventStore(temp_db)
    executions = store.get_executions(limit=1)

    if executions:
        exec_id = executions[0]["id"]
        result = runner.invoke(trace, [exec_id, "--db", temp_db])

        assert result.exit_code == 0
