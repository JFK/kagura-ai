# tests/core/test_memory.py
import asyncio
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from pydantic import BaseModel

from kagura.core.memory import Memory, MemoryBackend, MessageHistory

pytestmark = pytest.mark.asyncio


class SampleModel(BaseModel):
    field: str


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

    async def test_redis_connection_error(self):
        """Test handling of Redis connection errors"""
        with patch(
            "redis.asyncio.Redis.from_url", side_effect=Exception("Connection error")
        ):
            backend = MemoryBackend()
            # Should fall back to RAM storage
            await backend.set("test_key", "test_value")
            value = await backend.get("test_key")
            assert value == "test_value"

    async def test_publish_subscribe(self, memory_backend):
        """Test pub/sub functionality"""
        # Test publishing
        success = await memory_backend.publish("test_channel", "test_message")
        assert success is True

        # Test subscribing
        pubsub = await memory_backend.subscribe("test_channel")
        assert pubsub is not None

    async def test_cleanup_task(self):
        """Test cleanup task for RAM storage"""
        backend = MemoryBackend()
        # Add item with short TTL
        await backend.set("cleanup_test", "value", ttl=1)
        assert await backend.get("cleanup_test") == "value"

        # Wait for cleanup
        await asyncio.sleep(2)
        assert await backend.get("cleanup_test") is None


class TestMessageHistory:
    @pytest_asyncio.fixture
    async def message_history(self):
        history = await MessageHistory.factory(system_prompt="System prompt")
        yield history

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
        assert len(messages) == 1  # Only system prompt remains

    async def test_context_window_limit(self, message_history):
        """Test context window limitation"""
        await message_history.clear()
        # Add more messages than the context window
        for i in range(10):
            await message_history.add_message("user", f"Message {i}")

        messages = await message_history.get_messages(use_context_window=True)
        context_size = message_history.context_window * 2
        assert len(messages) <= context_size + 1  # +1 for system prompt

    async def test_window_size_limit(self, message_history):
        """Test message window size limitation"""
        await message_history.clear()
        # Add more messages than the window size
        for i in range(30):
            await message_history.add_message("user", f"Message {i}")

        messages = await message_history.get_messages(use_context_window=False)
        assert len(messages) <= message_history.window_size + 1  # +1 for system prompt

    async def test_system_prompt_persistence(self, message_history):
        """Test system prompt persistence across operations"""
        await message_history.clear()
        messages = await message_history.get_messages()
        assert len(messages) == 1
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "System prompt"

    async def test_save_load_to_redis(self, message_history):
        """Test saving to and loading from Redis"""
        await message_history.clear()
        await message_history.add_message("user", "Test message")
        await message_history._save_to_redis()

        # Create new history instance with same ID
        new_history = await MessageHistory.factory(system_prompt="System prompt")
        new_history.conversation_id = message_history.conversation_id

        messages = await new_history.get_messages()
        assert len(messages) == 2  # System prompt + user message
        assert messages[1]["content"] == "Test message"


class TestMemory:
    @pytest_asyncio.fixture
    async def memory(self):
        memory = Memory("test_namespace")
        yield memory

    async def test_memory_get_and_set(self, memory):
        data = SampleModel(field="test_value")
        await memory.set("test_key", data)
        retrieved_data = await memory.get("test_key", SampleModel)
        assert retrieved_data.field == "test_value"

    async def test_memory_list_storage(self, memory):
        """Test storing and retrieving lists of models"""
        data_list = [SampleModel(field="value1"), SampleModel(field="value2")]
        await memory.set("test_list", data_list)
        retrieved_list = await memory.get("test_list", SampleModel)
        assert isinstance(retrieved_list, list)
        assert len(retrieved_list) == 2
        assert all(isinstance(item, SampleModel) for item in retrieved_list)

    async def test_memory_json_decode_error(self, memory):
        """Test handling of JSON decode errors"""
        with patch.object(memory._backend, "get", return_value="invalid json"):
            result = await memory.get("test_key", SampleModel)
            assert result is None

    async def test_memory_delete(self, memory):
        """Test delete operation"""
        data = SampleModel(field="delete_test")
        await memory.set("delete_key", data)
        assert await memory.get("delete_key", SampleModel) is not None
        await memory.delete("delete_key")
        assert await memory.get("delete_key", SampleModel) is None

    async def test_memory_invalid_model_data(self, memory):
        """Test handling of invalid model data"""
        # Set data with missing required field
        invalid_data = {"wrong_field": "test"}
        await memory._backend.set("invalid_key", str(invalid_data))

        result = await memory.get("invalid_key", SampleModel)
        assert result is None

    async def test_memory_namespace_isolation(self):
        """Test that different namespaces don't interfere"""
        memory1 = Memory("namespace1")
        memory2 = Memory("namespace2")

        data = SampleModel(field="test")
        await memory1.set("key", data)

        # Should not be accessible from different namespace
        result = await memory2.get("key", SampleModel)
        assert result is None
