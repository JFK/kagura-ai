# tests/core/test_memory.py
import asyncio
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

from kagura.core.memory import Memory, MemoryBackend, MessageHistory

pytestmark = pytest.mark.asyncio


class TestMemoryBackend:
    @pytest_asyncio.fixture
    async def memory_backend(self):
        with patch("redis.asyncio") as mock_redis:
            mock_instance = AsyncMock()
            mock_instance.ping.return_value = True
            mock_instance.get.return_value = None
            mock_instance.setex.return_value = True
            mock_redis.from_url.return_value = mock_instance
            backend = MemoryBackend()
            yield backend
            await backend.close()

    async def test_set_and_get(self, memory_backend):
        await memory_backend.set("test_key", "test_value", ttl=10)
        value = await memory_backend.get("test_key")
        assert value == "test_value"

    async def test_fallback_to_ram(self):
        with patch("kagura.core.memory.MemoryBackend.ping", return_value=False):
            backend = MemoryBackend()
            await backend.set("ram_key", "ram_value", ttl=2)
            value = await backend.get("ram_key")
            assert value == "ram_value"
            # Wait for TTL to expire
            await asyncio.sleep(3)
            value = await backend.get("ram_key")
            assert value is None
            await backend.close()


class TestMessageHistory:
    @pytest_asyncio.fixture
    async def message_history(self):
        history = await MessageHistory.factory(system_prompt="System prompt")
        yield history
        await history.close()

    async def test_add_and_get_messages(self, message_history):
        await message_history.clear()
        await message_history.add_message("user", "Hello")
        await message_history.add_message("assistant", "Hi there")
        messages = await message_history.get_messages()
        assert len(messages) == 3  # Including system prompt
        assert messages[1]["content"] == "Hello"
        assert messages[2]["content"] == "Hi there"

    async def test_clear_history(self, message_history):
        await message_history.add_message("user", "Hello")
        await message_history.clear()
        messages = await message_history.get_messages()
        assert len(messages) == 1  # system prompt shift to 0 internally


class TestMemory:
    @pytest_asyncio.fixture
    def sample_model(self):
        from pydantic import BaseModel

        class SampleModel(BaseModel):
            field: str

        return SampleModel

    async def test_memory_get_and_set(self, sample_model):
        memory = Memory("test_namespace")
        data = sample_model(field="test_value")
        await memory.set("test_key", data)
        retrieved_data = await memory.get("test_key", sample_model)
        assert retrieved_data.field == "test_value"
