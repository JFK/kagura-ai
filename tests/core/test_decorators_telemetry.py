"""Tests for @agent decorator telemetry integration"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from kagura import agent
from kagura.observability import EventStore, Telemetry, set_global_telemetry


@pytest.fixture
def mock_telemetry_store():
    """Create in-memory telemetry store for testing"""
    store = EventStore(":memory:")
    telemetry = Telemetry(store)
    set_global_telemetry(telemetry)
    return store


@pytest.mark.asyncio
@patch("kagura.core.llm.litellm.acompletion", new_callable=AsyncMock)
async def test_agent_records_telemetry(mock_llm, mock_telemetry_store):
    """Test that @agent automatically records telemetry"""
    # Mock LLM response with usage (no tool calls)
    mock_llm.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="Hello, Alice!", tool_calls=None))],
        usage=MagicMock(prompt_tokens=10, completion_tokens=5, total_tokens=15),
    )

    @agent
    async def greeter(name: str) -> str:
        """Say hello to {{ name }}"""
        pass

    result = await greeter("Alice")

    # Check result
    assert "Alice" in str(result)

    # Check telemetry recorded
    executions = mock_telemetry_store.get_executions()
    assert len(executions) == 1

    execution = executions[0]
    assert execution["agent_name"] == "greeter"
    assert execution["status"] == "completed"
    assert "name" in execution["kwargs"]
    assert execution["kwargs"]["name"] == "Alice"

    # Check LLM call recorded
    assert "llm_calls" in execution["metrics"]
    assert execution["metrics"]["llm_calls"] == 1
    assert execution["metrics"]["total_tokens"] == 15

    # Check cost calculated
    assert "total_cost" in execution["metrics"]
    assert execution["metrics"]["total_cost"] > 0


@pytest.mark.asyncio
@patch("kagura.core.llm.litellm.acompletion", new_callable=AsyncMock)
async def test_agent_telemetry_disabled(mock_llm, mock_telemetry_store):
    """Test that telemetry can be disabled"""
    mock_llm.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="Hello"))],
        usage=MagicMock(prompt_tokens=10, completion_tokens=5, total_tokens=15),
    )

    @agent(enable_telemetry=False)
    async def no_telemetry_agent(query: str) -> str:
        """Process {{ query }}"""
        pass

    result = await no_telemetry_agent("test")

    # No telemetry recorded
    executions = mock_telemetry_store.get_executions()
    # Previous test may have recorded, so check for this specific agent
    agent_executions = [e for e in executions if e["agent_name"] == "no_telemetry_agent"]
    assert len(agent_executions) == 0


@pytest.mark.asyncio
@patch("kagura.core.llm.litellm.acompletion", new_callable=AsyncMock)
async def test_agent_records_error(mock_llm, mock_telemetry_store):
    """Test that errors are recorded in telemetry"""
    mock_llm.side_effect = Exception("API Error")

    @agent
    async def faulty_agent(query: str) -> str:
        """Process {{ query }}"""
        pass

    with pytest.raises(Exception):
        await faulty_agent("test")

    # Check error recorded
    executions = mock_telemetry_store.get_executions()
    faulty_executions = [e for e in executions if e["agent_name"] == "faulty_agent"]
    assert len(faulty_executions) == 1

    execution = faulty_executions[0]
    assert execution["status"] == "failed"
    assert "API Error" in execution["error"]


@pytest.mark.asyncio
@patch("kagura.core.llm.litellm.acompletion", new_callable=AsyncMock)
async def test_telemetry_tracks_duration(mock_llm, mock_telemetry_store):
    """Test that execution duration is tracked"""
    mock_llm.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="Done"))],
        usage=MagicMock(prompt_tokens=10, completion_tokens=5, total_tokens=15),
    )

    @agent
    async def timed_agent(query: str) -> str:
        """Process {{ query }}"""
        pass

    await timed_agent("test")

    executions = mock_telemetry_store.get_executions()
    timed_executions = [e for e in executions if e["agent_name"] == "timed_agent"]
    assert len(timed_executions) == 1

    execution = timed_executions[0]
    assert execution["duration"] is not None
    assert execution["duration"] > 0


@pytest.mark.asyncio
@patch("kagura.core.llm.litellm.acompletion", new_callable=AsyncMock)
async def test_telemetry_cost_calculation(mock_llm, mock_telemetry_store):
    """Test that cost is correctly calculated"""
    mock_llm.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="Response", tool_calls=None))],
        usage=MagicMock(prompt_tokens=1000, completion_tokens=500, total_tokens=1500),
    )

    @agent(model="gpt-5-mini")
    async def cost_test_agent(query: str) -> str:
        """Process {{ query }}"""
        pass

    await cost_test_agent("test")

    executions = mock_telemetry_store.get_executions()
    cost_executions = [e for e in executions if e["agent_name"] == "cost_test_agent"]
    assert len(cost_executions) == 1

    execution = cost_executions[0]
    assert "total_cost" in execution["metrics"]

    # gpt-4o-mini pricing: $0.15/1M prompt, $0.60/1M completion
    # 1000 * 0.15/1M + 500 * 0.60/1M = 0.00015 + 0.0003 = 0.00045
    expected_cost = 0.00045
    assert abs(execution["metrics"]["total_cost"] - expected_cost) < 0.000001


@pytest.mark.asyncio
async def test_telemetry_with_memory(mock_telemetry_store):
    """Test telemetry works with memory-enabled agents"""
    from kagura.core.memory import MemoryManager

    with patch("kagura.core.llm.litellm.acompletion", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Hi"))],
            usage=MagicMock(prompt_tokens=10, completion_tokens=5, total_tokens=15),
        )

        @agent(enable_memory=True)
        async def memory_agent(query: str, memory: MemoryManager) -> str:
            """Process {{ query }}"""
            pass

        await memory_agent("test")

        executions = mock_telemetry_store.get_executions()
        memory_executions = [e for e in executions if e["agent_name"] == "memory_agent"]
        assert len(memory_executions) == 1

        # Memory param should not be in kwargs
        execution = memory_executions[0]
        assert "memory" not in execution["kwargs"]
        assert "query" in execution["kwargs"]
