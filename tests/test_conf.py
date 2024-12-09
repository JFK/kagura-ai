from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from pydantic import BaseModel

from kagura.core.memory import MemoryBackend, MessageHistory
from kagura.core.models import ModelRegistry

# =========================
# Fixtures
# =========================


@pytest_asyncio.fixture
async def redis_mock():
    """Mock Redis connection for testing"""
    with patch("redis.asyncio.Redis") as mock_redis:
        mock_instance = AsyncMock()
        mock_instance.get.return_value = "test_value"
        mock_instance.set.return_value = True
        mock_redis.from_url.return_value = mock_instance
        yield mock_instance


@pytest_asyncio.fixture
async def memory_backend(redis_mock):
    """Mocked memory backend for testing"""
    backend = MemoryBackend()
    yield backend
    await backend.close()


@pytest_asyncio.fixture
async def message_history():
    """Message history instance for testing"""
    history = await MessageHistory.factory(system_prompt="Test System Prompt")
    yield history
    await history.close()


@pytest_asyncio.fixture
def sample_state_model():
    """Sample state model for testing"""

    class TestState(BaseModel):
        input_text: str = ""
        output_text: str = ""
        error_message: str = None
        success: bool = True

    ModelRegistry.register("TestState", TestState)
    return TestState


@pytest_asyncio.fixture
def mock_llm_response():
    """Mock LLM response for testing"""
    return {"choices": [{"message": {"content": "Test response from LLM"}}]}


# =========================
# Tests
# =========================


@pytest.mark.asyncio
async def test_redis_mock_fixture(redis_mock):
    """Test that redis_mock fixture works correctly"""
    redis_mock.ping.return_value = True
    assert await redis_mock.ping() is True

    assert await redis_mock.set("test_key", "test_value") is True
    assert await redis_mock.get("test_key") == "test_value"


@pytest.mark.asyncio
async def test_memory_backend_fixture(memory_backend):
    """Test that memory_backend fixture is properly initialized"""
    assert isinstance(memory_backend, MemoryBackend)
    await memory_backend.set("test_key", "test_value")
    value = await memory_backend.get("test_key")
    assert value == "test_value"


@pytest.mark.asyncio
async def test_message_history_fixture(message_history):
    """Test that message_history fixture works correctly"""
    assert isinstance(message_history, MessageHistory)
    await message_history.add_message("user", "test message")
    messages = await message_history.get_messages()
    assert any(
        msg["role"] == "user" and msg["content"] == "test message" for msg in messages
    )


def test_sample_state_model_fixture(sample_state_model):
    """Test that sample_state_model fixture creates valid model"""
    test_state = sample_state_model(input_text="test input")
    assert test_state.input_text == "test input"
    assert test_state.output_text == ""
    assert test_state.success is True
    assert test_state.error_message is None
