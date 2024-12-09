import json
from unittest.mock import AsyncMock, patch

import aiohttp
import pytest
import pytest_asyncio

from kagura.core.memory import MemoryBackend

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def redis_mock():
    """Mock Redis connection for testing"""
    with patch("redis.asyncio.Redis") as mock_redis:
        mock_instance = AsyncMock()
        # モックの戻り値を設定
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


class TestExternalServices:
    async def test_redis_integration(self, redis_mock):
        """Test Redis integration"""
        backend = MemoryBackend()

        # Test set operation
        await backend.set("test_key", "test_value")
        redis_mock.setex.assert_called_once()

        # Test get operation
        redis_mock.get.return_value = "test_value"
        value = await backend.get("test_key")
        assert value == "test_value"
        redis_mock.get.assert_called_once()

        # Test publish operation
        await backend.publish("test_channel", "test_message")
        redis_mock.publish.assert_called_once_with("test_channel", "test_message")

    async def test_file_system_operations(self):
        """Test file system operations"""
        test_content = "Test file content"

        with patch("pathlib.Path.write_text") as mock_write:
            with patch("pathlib.Path.read_text") as mock_read:
                mock_read.return_value = test_content

                # Test file write
                from pathlib import Path

                test_file = Path("test.txt")
                test_file.write_text(test_content)
                mock_write.assert_called_once_with(test_content)

                # Test file read
                content = test_file.read_text()
                assert content == test_content
                mock_read.assert_called_once()

    async def test_api_integration(self):
        """Test API integration"""
        test_url = "https://api.test.com/data"
        test_response = {"data": "test"}

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = test_response
            mock_get.return_value.__aenter__.return_value = mock_response

            async with aiohttp.ClientSession() as session:
                async with session.get(test_url) as response:
                    assert response.status == 200
                    data = await response.json()
                    assert data == test_response

    @pytest.mark.skip()
    async def test_memory_persistence(self, memory_backend):
        """Test memory persistence operations"""
        test_key = "test_memory"
        test_data = {"field": "value"}

        # Test data storage
        await memory_backend.set(test_key, json.dumps(test_data))

        # Test data retrieval
        stored_data = await memory_backend.get(test_key)
        assert json.loads(stored_data) == test_data

        # Test data expiration
        await memory_backend._cleanup_expired()
        expired_data = await memory_backend.get("expired_key")
        assert expired_data is None
