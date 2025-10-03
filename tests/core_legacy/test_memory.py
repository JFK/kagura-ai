# tests/core/test_memory.py
import asyncio
from unittest.mock import patch

import pytest
import pytest_asyncio
from pydantic import BaseModel

from kagura.core.memory import Memory, MemoryBackend, MessageHistory
from kagura.core.utils.logger import get_logger

logger = get_logger(__name__)

pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
async def cleanup_memory():
    """各テスト後にメモリとRedis接続をクリーンアップするフィクスチャ"""
    yield

    # まず実行中のすべてのタスクを取得
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]

    # cleanup_taskを探して停止
    for task in tasks:
        if "_start_cleanup_task" in str(task):
            # タスクをキャンセル
            task.cancel()
            try:
                # タスクの完了を待つ
                await task
            except (asyncio.CancelledError, Exception) as e:
                logger.debug(f"Cleanup task cancelled: {e}")

    # 残りのタスクを処理
    remaining_tasks = [t for t in tasks if not t.done()]
    if remaining_tasks:
        # 残りのタスクもキャンセル
        for task in remaining_tasks:
            task.cancel()
        await asyncio.gather(*remaining_tasks, return_exceptions=True)

    # Redisのクリーンアップ
    try:
        backend = MemoryBackend()
        await backend.close()
    except Exception as e:
        logger.error(f"Error during Redis cleanup: {e}")

    # イベントループのクリーンアップ
    await asyncio.sleep(0.1)


class SampleModel(BaseModel):
    field: str


class TestMemoryBackend:
    @pytest_asyncio.fixture
    async def memory_backend(self):
        backend = MemoryBackend()
        try:
            yield backend
        finally:
            await backend.close()
            # Ensure cleanup task is cancelled
            tasks = [
                t
                for t in asyncio.all_tasks()
                if "MemoryBackend._start_cleanup_task" in str(t)
            ]
            for task in tasks:
                if not task.done():
                    task.cancel()
                    try:
                        await asyncio.wait_for(task, timeout=1.0)
                    except (asyncio.TimeoutError, asyncio.CancelledError):
                        pass

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
        await history.close()

    @pytest.mark.asyncio
    async def test_clear_history(self, message_history):
        # システムプロンプトのみが残ることを確認
        await message_history.clear()
        messages = await message_history.get_messages()
        system_messages = [msg for msg in messages if msg["role"] == "system"]
        assert len(system_messages) == 1

    @pytest.mark.asyncio
    async def test_system_prompt_persistence(self, message_history):
        # システムプロンプトの永続性をテスト
        await message_history.clear()  # まずクリア
        messages = await message_history.get_messages()
        assert len([msg for msg in messages if msg["role"] == "system"]) == 1

    @pytest.mark.asyncio
    async def test_add_and_get_messages(self, message_history):
        await message_history.clear()
        await message_history.add_message("user", "Hello")
        await message_history.add_message("assistant", "Hi there")
        messages = await message_history.get_messages()
        assert len(messages) == 3  # Including system prompt
        assert messages[1]["content"] == "Hello"
        assert messages[2]["content"] == "Hi there"

    @pytest.mark.asyncio
    async def test_context_window_limit(self, message_history):
        """Test context window limitation"""
        await message_history.clear()
        # Add more messages than the context window
        for i in range(10):
            await message_history.add_message("user", f"Message {i}")

        messages = await message_history.get_messages(use_context_window=True)
        context_size = message_history.context_window * 2
        assert len(messages) <= context_size + 1  # +1 for system prompt

    @pytest.mark.asyncio
    async def test_window_size_limit(self, message_history):
        """Test message window size limitation"""
        await message_history.clear()
        # Add more messages than the window size
        for i in range(30):
            await message_history.add_message("user", f"Message {i}")

        messages = await message_history.get_messages(use_context_window=False)
        assert len(messages) <= message_history.window_size + 1  # +1 for system prompt

    @pytest.mark.asyncio
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
    async def memory_instance(self):
        memory = Memory("test")
        try:
            yield memory
        finally:
            await memory._backend.close()
            # Ensure cleanup task is cancelled
            tasks = [
                t
                for t in asyncio.all_tasks()
                if "MemoryBackend._start_cleanup_task" in str(t)
            ]
            for task in tasks:
                if not task.done():
                    task.cancel()
                    try:
                        await asyncio.wait_for(task, timeout=1.0)
                    except (asyncio.TimeoutError, asyncio.CancelledError):
                        pass

    @pytest.mark.asyncio
    async def test_memory_get_and_set(self, memory_instance):
        data = SampleModel(field="test_value")
        await memory_instance.set("test_key", data)
        retrieved_data = await memory_instance.get("test_key", SampleModel)
        assert retrieved_data.field == "test_value"

    @pytest.mark.asyncio
    async def test_memory_list_storage(self, memory_instance):
        """Test storing and retrieving lists of models"""
        data_list = [SampleModel(field="value1"), SampleModel(field="value2")]
        await memory_instance.set("test_list", data_list)
        retrieved_list = await memory_instance.get("test_list", SampleModel)
        assert isinstance(retrieved_list, list)
        assert len(retrieved_list) == 2
        assert all(isinstance(item, SampleModel) for item in retrieved_list)

    @pytest.mark.asyncio
    async def test_memory_json_decode_error(self, memory_instance):
        """Test handling of JSON decode errors"""
        with patch.object(memory_instance._backend, "get", return_value="invalid json"):
            result = await memory_instance.get("test_key", SampleModel)
            assert result is None

    @pytest.mark.asyncio
    async def test_memory_delete(self, memory_instance):
        """Test delete operation"""
        data = SampleModel(field="delete_test")
        await memory_instance.set("delete_key", data)
        assert await memory_instance.get("delete_key", SampleModel) is not None
        await memory_instance.delete("delete_key")
        assert await memory_instance.get("delete_key", SampleModel) is None

    @pytest.mark.asyncio
    async def test_memory_invalid_model_data(self, memory_instance):
        """Test handling of invalid model data"""
        # Set data with missing required field
        invalid_data = {"wrong_field": "test"}
        await memory_instance._backend.set("invalid_key", str(invalid_data))

        result = await memory_instance.get("invalid_key", SampleModel)
        assert result is None

    @pytest.mark.asyncio
    async def test_memory_namespace_isolation(self):
        """Test that different namespaces don't interfere"""
        memory1 = Memory("namespace1")
        memory2 = Memory("namespace2")

        data = SampleModel(field="test")
        await memory1.set("key", data)

        # Should not be accessible from different namespace
        result = await memory2.get("key", SampleModel)
        assert result is None
