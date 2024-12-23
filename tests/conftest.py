# tests/conftest.py

import pytest
import asyncio
from unittest.mock import AsyncMock, patch

import pytest_asyncio
from pydantic import BaseModel

from kagura.core.memory import MemoryBackend, MessageHistory
from kagura.core.models import ModelRegistry


@pytest.fixture(scope="session")
def event_loop():
    """セッション全体で共有するイベントループを作成"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop

    # 保留中のタスクをキャンセル
    pending = asyncio.all_tasks(loop)
    for task in pending:
        task.cancel()

    # タスクの完了を待つ
    if pending:
        loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))

    # クリーンアップ
    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def cleanup_redis():
    """Redisのクリーンアップ"""
    backend = None
    try:
        backend = MemoryBackend()
        yield backend
    finally:
        if backend:
            # _running フラグを False に設定してクリーンアップタスクを停止
            backend._running = False
            if backend._cleanup_task and not backend._cleanup_task.done():
                backend._cleanup_task.cancel()
                try:
                    await backend._cleanup_task
                except asyncio.CancelledError:
                    pass
            # Redis接続を閉じる
            await backend.close()


@pytest.fixture(autouse=True)
async def cleanup_async_tasks():
    """各テスト後の非同期タスクのクリーンアップ"""
    yield

    # 現在のタスクを除く全タスクを取得
    current_task = asyncio.current_task()
    tasks = [t for t in asyncio.all_tasks() if t is not current_task]

    # タスクをキャンセルして完了を待つ
    for task in tasks:
        if not task.done() and not task.cancelled():
            task.cancel()

    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)

    # 少し待って、保留中のコールバックを処理
    await asyncio.sleep(0.1)


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
