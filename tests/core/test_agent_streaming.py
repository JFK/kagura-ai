"""Tests for agent streaming functionality"""

import pytest

from kagura import agent


@pytest.mark.asyncio
async def test_agent_with_stream_parameter():
    """Test that @agent decorator accepts stream parameter"""

    @agent(stream=True)
    async def streaming_agent(query: str) -> str:
        """Answer {{ query }}"""
        pass

    # Check that agent has stream attribute
    assert hasattr(streaming_agent, "stream")
    assert callable(streaming_agent.stream)


@pytest.mark.asyncio
async def test_agent_without_stream_parameter():
    """Test that agent without stream=True has no stream method"""

    @agent
    async def normal_agent(query: str) -> str:
        """Answer {{ query }}"""
        pass

    # Check that agent does NOT have stream attribute
    assert not hasattr(normal_agent, "stream")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_streaming_basic_response():
    """Test basic streaming response (integration test with real API)"""

    @agent(stream=True, model="gpt-4o-mini")
    async def streaming_agent(query: str) -> str:
        """Answer {{ query }} in one sentence"""
        pass

    # Test streaming
    chunks = []
    async for chunk in streaming_agent.stream("Say hello"):
        chunks.append(chunk)

    # Verify we received multiple chunks
    assert len(chunks) > 0

    # Verify full response is coherent
    full_response = "".join(chunks)
    assert len(full_response) > 0
    assert isinstance(full_response, str)


@pytest.mark.asyncio
async def test_streaming_with_mock():
    """Test streaming with mocked LLM response"""
    from unittest.mock import patch

    @agent(stream=True, model="gpt-4o-mini")
    async def streaming_agent(query: str) -> str:
        """Answer {{ query }}"""
        pass

    # Mock the streaming response
    async def mock_stream(*args, **kwargs):
        """Mock async generator that yields chunks"""
        chunks = ["Hello", " ", "World", "!"]
        for chunk in chunks:
            yield chunk

    # Patch the stream_openai_direct function
    with patch("kagura.core.llm_openai.stream_openai_direct", side_effect=mock_stream):
        # Test streaming
        chunks = []
        async for chunk in streaming_agent.stream("Say hello"):
            chunks.append(chunk)

        # Verify chunks
        assert chunks == ["Hello", " ", "World", "!"]
        assert "".join(chunks) == "Hello World!"


@pytest.mark.asyncio
async def test_streaming_with_tools_supported():
    """Test that streaming works with tools (hybrid approach)"""
    from unittest.mock import patch

    def dummy_tool(x: int) -> int:
        """Dummy tool"""
        return x * 2

    @agent(stream=True, model="gpt-4o-mini", tools=[dummy_tool])
    async def streaming_agent_with_tools(query: str) -> str:
        """Answer {{ query }}"""
        pass

    # Mock streaming with tool execution
    async def mock_stream_with_tools(*args, **kwargs):
        """Mock async generator that simulates tool execution + streaming"""
        # Simulate final response after tool execution
        chunks = ["Result: ", "4", " (2 * 2)"]
        for chunk in chunks:
            yield chunk

    # Patch the stream_openai_direct function
    with patch(
        "kagura.core.llm_openai.stream_openai_direct",
        side_effect=mock_stream_with_tools,
    ):
        # Test streaming with tools
        chunks = []
        async for chunk in streaming_agent_with_tools.stream("test with 2"):
            chunks.append(chunk)

        # Verify chunks (should stream final response)
        assert len(chunks) > 0
        assert "".join(chunks) == "Result: 4 (2 * 2)"


@pytest.mark.asyncio
async def test_streaming_with_memory():
    """Test that streaming works with memory enabled"""
    from unittest.mock import patch

    async def mock_stream(*args, **kwargs):
        """Mock async generator"""
        yield "Response with memory"

    @agent(stream=True, enable_memory=True, model="gpt-4o-mini")
    async def streaming_agent_with_memory(query: str, memory) -> str:
        """Answer {{ query }}"""
        pass

    with patch("kagura.core.llm_openai.stream_openai_direct", side_effect=mock_stream):
        chunks = []
        async for chunk in streaming_agent_with_memory.stream("test"):
            chunks.append(chunk)

        assert "".join(chunks) == "Response with memory"


@pytest.mark.asyncio
async def test_non_openai_model_raises_error():
    """Test that streaming with non-OpenAI model raises NotImplementedError"""

    @agent(stream=True, model="claude-3-5-sonnet")
    async def claude_streaming_agent(query: str) -> str:
        """Answer {{ query }}"""
        pass

    # Streaming with Claude should raise NotImplementedError
    with pytest.raises(
        NotImplementedError, match="Streaming is not yet implemented for model"
    ):
        async for _ in claude_streaming_agent.stream("test"):
            pass
