"""Tests for Dashboard."""

import time

import pytest

from kagura.observability import Dashboard, EventStore, TelemetryCollector

# ===== Fixture =====


@pytest.fixture
def store_with_data():
    """Create store with sample data."""
    store = EventStore(":memory:")
    collector = TelemetryCollector(store)

    # Add some sample executions
    async def create_executions():
        # Execution 1: Completed
        async with collector.track_execution("agent_1", query="test1") as exec_id:
            collector.record_llm_call("gpt-4o", 100, 50, 1.0, 0.003)
            collector.record_tool_call("search_tool", 0.5, query="test")

        # Execution 2: Failed
        try:
            async with collector.track_execution("agent_2", query="test2"):
                collector.record_llm_call("gpt-5-mini", 50, 25, 0.5, 0.001)
                raise ValueError("Test error")
        except ValueError:
            pass

        # Execution 3: Completed
        async with collector.track_execution("agent_1", query="test3"):
            collector.record_llm_call("gpt-4o", 200, 100, 2.0, 0.006)

    import asyncio

    asyncio.run(create_executions())

    return store


# ===== Initialization Tests =====


def test_dashboard_initialization():
    """Test Dashboard initialization."""
    store = EventStore(":memory:")
    dashboard = Dashboard(store)

    assert dashboard.store is store
    assert dashboard.console is not None


# ===== Show List Tests =====


def test_show_list_empty():
    """Test show_list with no data."""
    store = EventStore(":memory:")
    dashboard = Dashboard(store)

    # Should print message about no executions
    dashboard.show_list()


def test_show_list_with_data(store_with_data):
    """Test show_list with data."""
    dashboard = Dashboard(store_with_data)

    # Should display executions
    dashboard.show_list(limit=10)


def test_show_list_filtered_by_agent(store_with_data):
    """Test show_list filtered by agent."""
    dashboard = Dashboard(store_with_data)

    dashboard.show_list(agent_name="agent_1", limit=10)


def test_show_list_filtered_by_status(store_with_data):
    """Test show_list filtered by status."""
    dashboard = Dashboard(store_with_data)

    dashboard.show_list(status="completed", limit=10)


# ===== Show Stats Tests =====


def test_show_stats_empty():
    """Test show_stats with no data."""
    store = EventStore(":memory:")
    dashboard = Dashboard(store)

    dashboard.show_stats()


def test_show_stats_with_data(store_with_data):
    """Test show_stats with data."""
    dashboard = Dashboard(store_with_data)

    dashboard.show_stats()


def test_show_stats_filtered_by_agent(store_with_data):
    """Test show_stats filtered by agent."""
    dashboard = Dashboard(store_with_data)

    dashboard.show_stats(agent_name="agent_1")


# ===== Show Trace Tests =====


def test_show_trace_not_found():
    """Test show_trace with non-existent execution."""
    store = EventStore(":memory:")
    dashboard = Dashboard(store)

    dashboard.show_trace("nonexistent")


def test_show_trace_with_data(store_with_data):
    """Test show_trace with existing execution."""
    dashboard = Dashboard(store_with_data)

    # Get an execution ID
    executions = store_with_data.get_executions(limit=1)
    if executions:
        exec_id = executions[0]["id"]
        dashboard.show_trace(exec_id)


# ===== Show Cost Summary Tests =====


def test_show_cost_summary_empty():
    """Test show_cost_summary with no data."""
    store = EventStore(":memory:")
    dashboard = Dashboard(store)

    dashboard.show_cost_summary()


def test_show_cost_summary_by_agent(store_with_data):
    """Test show_cost_summary grouped by agent."""
    dashboard = Dashboard(store_with_data)

    dashboard.show_cost_summary(group_by="agent")


def test_show_cost_summary_by_date(store_with_data):
    """Test show_cost_summary grouped by date."""
    dashboard = Dashboard(store_with_data)

    dashboard.show_cost_summary(group_by="date")


# ===== Dashboard Layout Tests =====


def test_create_dashboard_layout_empty():
    """Test creating dashboard layout with no data."""
    store = EventStore(":memory:")
    dashboard = Dashboard(store)

    layout = dashboard._create_dashboard_layout()
    assert layout is not None


def test_create_dashboard_layout_with_data(store_with_data):
    """Test creating dashboard layout with data."""
    dashboard = Dashboard(store_with_data)

    layout = dashboard._create_dashboard_layout()
    assert layout is not None


def test_create_dashboard_layout_filtered(store_with_data):
    """Test creating dashboard layout filtered by agent."""
    dashboard = Dashboard(store_with_data)

    layout = dashboard._create_dashboard_layout(agent_name="agent_1")
    assert layout is not None


# ===== Helper Methods Tests =====


def test_format_timestamp():
    """Test timestamp formatting."""
    store = EventStore(":memory:")
    dashboard = Dashboard(store)

    timestamp = time.time()
    formatted = dashboard._format_timestamp(timestamp)

    assert isinstance(formatted, str)
    assert ":" in formatted  # Should contain time separator


def test_format_status():
    """Test status formatting."""
    store = EventStore(":memory:")
    dashboard = Dashboard(store)

    assert "COMPLETED" in dashboard._format_status("completed")
    assert "FAILED" in dashboard._format_status("failed")
    assert "RUNNING" in dashboard._format_status("running")


def test_create_execution_table_empty():
    """Test creating execution table with no data."""
    store = EventStore(":memory:")
    dashboard = Dashboard(store)

    table = dashboard._create_execution_table([])
    assert table is not None


def test_create_execution_table_with_data(store_with_data):
    """Test creating execution table with data."""
    dashboard = Dashboard(store_with_data)

    executions = store_with_data.get_executions(limit=5)
    table = dashboard._create_execution_table(executions)

    assert table is not None


# ===== Representation Test =====


def test_dashboard_repr():
    """Test Dashboard string representation."""
    store = EventStore(":memory:")
    dashboard = Dashboard(store)

    repr_str = repr(dashboard)
    assert "Dashboard" in repr_str


# ===== Integration Tests =====


@pytest.mark.asyncio
async def test_dashboard_full_workflow():
    """Test full dashboard workflow with multiple executions."""
    store = EventStore(":memory:")
    collector = TelemetryCollector(store)
    dashboard = Dashboard(store)

    # Create multiple executions
    for i in range(5):
        async with collector.track_execution(f"agent_{i % 2}", query=f"test{i}"):
            collector.record_llm_call("gpt-4o", 100 * (i + 1), 50, 1.0, 0.003)
            if i % 3 == 0:
                collector.record_tool_call("tool", 0.5)

    # Test all dashboard commands
    dashboard.show_list(limit=10)
    dashboard.show_stats()
    dashboard.show_cost_summary(group_by="agent")
    dashboard.show_cost_summary(group_by="date")

    # Get execution and show trace
    executions = store.get_executions(limit=1)
    if executions:
        dashboard.show_trace(executions[0]["id"])


@pytest.mark.asyncio
async def test_dashboard_with_different_statuses():
    """Test dashboard with various execution statuses."""
    store = EventStore(":memory:")
    collector = TelemetryCollector(store)
    dashboard = Dashboard(store)

    # Completed execution
    async with collector.track_execution("agent_success"):
        collector.record_llm_call("gpt-4o", 100, 50, 1.0, 0.003)

    # Failed execution
    try:
        async with collector.track_execution("agent_fail"):
            collector.record_llm_call("gpt-4o", 100, 50, 1.0, 0.003)
            raise RuntimeError("Test failure")
    except RuntimeError:
        pass

    # Show filtered by status
    dashboard.show_list(status="completed")
    dashboard.show_list(status="failed")

    # Stats should reflect both statuses
    dashboard.show_stats()
