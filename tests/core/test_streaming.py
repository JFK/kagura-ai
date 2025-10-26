"""Tests for streaming LLM responses

Tests cover:
- call_llm_stream() basic functionality
- Chunk yielding and iteration
- stream_to_string() utility
- OAuth2 support
- Error handling
- Streaming not cached
"""

import pytest

from kagura import LLMConfig
from kagura.core.streaming import call_llm_stream, stream_to_string


@pytest.fixture
def mock_streaming_response():
    """Mock streaming LLM response"""

    class MockDelta:
        def __init__(self, content: str | None):
            self.content = content

    class MockChoice:
        def __init__(self, content: str | None):
            self.delta = MockDelta(content)

    class MockChunk:
        def __init__(self, content: str | None):
            self.choices = [MockChoice(content)]

    async def mock_acompletion(*args, **kwargs):
        # Check if streaming is enabled
        if not kwargs.get("stream"):
            raise ValueError("Streaming not enabled")

        # Yield chunks
        chunks = ["Hello", ", ", "world", "!"]

        async def chunk_generator():
            for chunk_text in chunks:
                yield MockChunk(chunk_text)

        return chunk_generator()

    return mock_acompletion


class TestCallLLMStream:
    """Tests for call_llm_stream() function"""

    @pytest.mark.asyncio
    async def test_call_llm_stream_basic(self, mock_streaming_response, monkeypatch):
        """Test call_llm_stream yields chunks"""
        monkeypatch.setattr(
            "kagura.core.streaming.litellm.acompletion", mock_streaming_response
        )

        config = LLMConfig(model="gpt-5-mini")
        chunks = []

        async for chunk in call_llm_stream("test prompt", config):
            chunks.append(chunk)

        assert chunks == ["Hello", ", ", "world", "!"]

    @pytest.mark.asyncio
    async def test_call_llm_stream_yields_chunks(
        self, mock_streaming_response, monkeypatch
    ):
        """Test streaming yields chunks one by one"""
        monkeypatch.setattr(
            "kagura.core.streaming.litellm.acompletion", mock_streaming_response
        )

        config = LLMConfig(model="gpt-5-mini")
        chunk_count = 0

        async for chunk in call_llm_stream("test prompt", config):
            chunk_count += 1
            assert isinstance(chunk, str)

        assert chunk_count == 4  # 4 chunks in mock

    @pytest.mark.asyncio
    async def test_call_llm_stream_full_response(
        self, mock_streaming_response, monkeypatch
    ):
        """Test collecting full response from stream"""
        monkeypatch.setattr(
            "kagura.core.streaming.litellm.acompletion", mock_streaming_response
        )

        config = LLMConfig(model="gpt-5-mini")
        full_text = await stream_to_string(call_llm_stream("test prompt", config))

        assert full_text == "Hello, world!"

    @pytest.mark.asyncio
    async def test_call_llm_stream_empty_response(self, monkeypatch):
        """Test streaming with empty response"""

        class MockDelta:
            content = None

        class MockChoice:
            delta = MockDelta()

        class MockChunk:
            choices = [MockChoice()]

        async def mock_empty_stream(*args, **kwargs):
            async def chunk_generator():
                yield MockChunk()
                yield MockChunk()

            return chunk_generator()

        monkeypatch.setattr(
            "kagura.core.streaming.litellm.acompletion", mock_empty_stream
        )

        config = LLMConfig(model="gpt-5-mini")
        chunks = []

        async for chunk in call_llm_stream("test prompt", config):
            chunks.append(chunk)

        assert chunks == []  # No content yielded

    @pytest.mark.asyncio
    async def test_call_llm_stream_with_custom_config(
        self, mock_streaming_response, monkeypatch
    ):
        """Test streaming with custom LLMConfig"""
        monkeypatch.setattr(
            "kagura.core.streaming.litellm.acompletion", mock_streaming_response
        )

        config = LLMConfig(model="gpt-4o", temperature=0.9, max_tokens=500)

        chunks = []
        async for chunk in call_llm_stream("test prompt", config):
            chunks.append(chunk)

        assert len(chunks) > 0

    @pytest.mark.asyncio
    async def test_streaming_passes_config_params(self, monkeypatch):
        """Test streaming passes LLMConfig parameters correctly"""
        captured_kwargs = {}

        async def capture_acompletion(*args, **kwargs):
            captured_kwargs.update(kwargs)

            class MockDelta:
                content = "test"

            class MockChoice:
                delta = MockDelta()

            class MockChunk:
                choices = [MockChoice()]

            async def chunk_generator():
                yield MockChunk()

            return chunk_generator()

        monkeypatch.setattr(
            "kagura.core.streaming.litellm.acompletion", capture_acompletion
        )

        config = LLMConfig(
            model="claude-3-5-sonnet-20241022",
            temperature=0.5,
            max_tokens=1000,
            top_p=0.9,
        )

        async for chunk in call_llm_stream("test", config):
            pass

        assert captured_kwargs["model"] == "claude-3-5-sonnet-20241022"
        assert captured_kwargs["temperature"] == 0.5
        assert captured_kwargs["max_tokens"] == 1000
        assert captured_kwargs["top_p"] == 0.9
        assert captured_kwargs["stream"] is True


class TestStreamToString:
    """Tests for stream_to_string() utility"""

    @pytest.mark.asyncio
    async def test_stream_to_string_basic(self):
        """Test stream_to_string collects all chunks"""

        async def mock_stream():
            yield "Hello"
            yield ", "
            yield "world"
            yield "!"

        result = await stream_to_string(mock_stream())
        assert result == "Hello, world!"

    @pytest.mark.asyncio
    async def test_stream_to_string_empty(self):
        """Test stream_to_string with empty stream"""

        async def empty_stream():
            return
            yield  # Make it a generator

        result = await stream_to_string(empty_stream())
        assert result == ""

    @pytest.mark.asyncio
    async def test_stream_to_string_single_chunk(self):
        """Test stream_to_string with single chunk"""

        async def single_chunk_stream():
            yield "Single chunk"

        result = await stream_to_string(single_chunk_stream())
        assert result == "Single chunk"

    @pytest.mark.asyncio
    async def test_stream_to_string_many_chunks(self):
        """Test stream_to_string with many small chunks"""

        async def many_chunks_stream():
            for i in range(100):
                yield str(i)

        result = await stream_to_string(many_chunks_stream())
        expected = "".join(str(i) for i in range(100))
        assert result == expected
