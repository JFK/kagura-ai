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


@pytest.fixture(autouse=True)
def mock_openai_sdk():
    """Mock OpenAI SDK for all telemetry tests (default model is gpt-5-mini)"""
    class MockMessage:
        def __init__(self, content: str):
            self.content = content
            self.tool_calls = None

    class MockChoice:
        def __init__(self, content: str):
            self.message = MockMessage(content)

    class MockUsage:
        def __init__(self):
            self.prompt_tokens = 10
            self.completion_tokens = 5
            self.total_tokens = 15

    class MockResponse:
        def __init__(self, content: str):
            self.choices = [MockChoice(content)]
            self.usage = MockUsage()

    async def mock_create(*args, **kwargs):
        messages = kwargs.get("messages", [])
        content = "Mocked response"
        if messages:
            # Extract name from prompt if possible
            prompt_content = messages[0].get("content", "")
            if "Alice" in prompt_content:
                content = "Hello, Alice!"
            elif "test" in prompt_content:
                content = "Response"
        return MockResponse(content)

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(side_effect=mock_create)

    with patch("openai.AsyncOpenAI", return_value=mock_client):
        yield


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
async def test_agent_records_error(mock_telemetry_store):
    """Test that errors are recorded in telemetry"""
    # Patch OpenAI SDK to raise error
    with patch("openai.AsyncOpenAI") as mock_client_class:
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))
        mock_client_class.return_value = mock_client

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

    @agent(model="claude-3-5-sonnet-20241022")
    async def cost_test_agent(query: str) -> str:
        """Process {{ query }}"""
        pass

    await cost_test_agent("test")

    executions = mock_telemetry_store.get_executions()
    cost_executions = [e for e in executions if e["agent_name"] == "cost_test_agent"]
    assert len(cost_executions) == 1

    execution = cost_executions[0]
    assert "total_cost" in execution["metrics"]

    # claude-3-5-sonnet pricing: $3.00/1M prompt, $15.00/1M completion
    # 1000 * 3.00/1M + 500 * 15.00/1M = 0.003 + 0.0075 = 0.0105
    expected_cost = 0.0105
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
