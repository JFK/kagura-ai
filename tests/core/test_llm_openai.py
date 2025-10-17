"""Tests for OpenAI SDK direct backend (llm_openai.py)

Tests cover:
- OpenAI direct API calling
- Tool calling with OpenAI SDK
- Backend routing logic (_should_use_openai_direct)
- Error handling
- Usage tracking
- Parameter passing
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from kagura.core.llm import LLMConfig, LLMResponse, _should_use_openai_direct
from kagura.core.llm_openai import call_openai_direct


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI SDK response object"""

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
            self.completion_tokens = 20
            self.total_tokens = 30

    class MockResponse:
        def __init__(self, content: str):
            self.choices = [MockChoice(content)]
            self.usage = MockUsage()

    async def mock_create(*args, **kwargs):
        # Extract prompt from messages
        messages = kwargs.get("messages", [])
        if messages:
            prompt = messages[0].get("content", "")
            # Simple mapping
            responses = {
                "test prompt": "test response from OpenAI",
                "another prompt": "another response",
                "Hello": "Hi there!",
            }
            return MockResponse(responses.get(prompt, "default OpenAI response"))
        return MockResponse("default OpenAI response")

    return mock_create


class TestBackendRouting:
    """Tests for backend selection logic"""

    def test_should_use_openai_direct_gpt_models(self):
        """Test OpenAI models are detected correctly"""
        assert _should_use_openai_direct("gpt-5-mini") is True
        assert _should_use_openai_direct("gpt-5") is True
        assert _should_use_openai_direct("gpt-5-nano") is True
        assert _should_use_openai_direct("gpt-4o") is True
        assert _should_use_openai_direct("gpt-4o-mini") is True
        assert _should_use_openai_direct("gpt-4-turbo") is True
        assert _should_use_openai_direct("gpt-3.5-turbo") is True

    def test_should_use_openai_direct_o_series(self):
        """Test o-series models are detected"""
        assert _should_use_openai_direct("o1-preview") is True
        assert _should_use_openai_direct("o1-mini") is True
        assert _should_use_openai_direct("o3-mini") is True
        assert _should_use_openai_direct("o4-mini") is True

    def test_should_use_openai_direct_embeddings(self):
        """Test embedding models are detected"""
        assert _should_use_openai_direct("text-embedding-3-small") is True
        assert _should_use_openai_direct("text-embedding-3-large") is True
        assert _should_use_openai_direct("text-embedding-ada-002") is True

    def test_should_use_litellm_for_other_providers(self):
        """Test non-OpenAI models use LiteLLM"""
        assert _should_use_openai_direct("claude-3-5-sonnet-20241022") is False
        assert _should_use_openai_direct("claude-3-opus") is False
        assert _should_use_openai_direct("gemini-1.5-pro") is False
        assert _should_use_openai_direct("gemini/gemini-2.0-flash") is False
        assert _should_use_openai_direct("anthropic/claude-3-sonnet") is False


class TestOpenAIDirectBasic:
    """Tests for basic OpenAI direct calling"""

    @pytest.mark.asyncio
    async def test_call_openai_direct_simple(self, mock_openai_response):
        """Test simple OpenAI direct call"""
        with patch("openai.AsyncOpenAI") as mock_client_class:
            mock_client = MagicMock()
            mock_client.chat.completions.create = mock_openai_response
            mock_client_class.return_value = mock_client

            config = LLMConfig(model="gpt-5-mini", temperature=0.7)
            result = await call_openai_direct("test prompt", config)

            assert isinstance(result, LLMResponse)
            assert result.content == "test response from OpenAI"
            assert result.model == "gpt-5-mini"
            assert result.usage["prompt_tokens"] == 10
            assert result.usage["completion_tokens"] == 20
            assert result.usage["total_tokens"] == 30
            assert result.duration > 0

    @pytest.mark.asyncio
    async def test_call_openai_direct_with_max_tokens(self, mock_openai_response):
        """Test OpenAI call with max_tokens parameter"""
        with patch("openai.AsyncOpenAI") as mock_client_class:
            mock_client = MagicMock()
            mock_create = AsyncMock(side_effect=mock_openai_response)
            mock_client.chat.completions.create = mock_create
            mock_client_class.return_value = mock_client

            config = LLMConfig(model="gpt-4o", max_tokens=1000)
            result = await call_openai_direct("Hello", config)

            assert result.content == "Hi there!"
            # Verify max_tokens was passed to API
            call_kwargs = mock_create.call_args[1]
            assert call_kwargs["max_tokens"] == 1000

    @pytest.mark.asyncio
    async def test_call_openai_direct_with_top_p(self, mock_openai_response):
        """Test OpenAI call with top_p parameter"""
        with patch("openai.AsyncOpenAI") as mock_client_class:
            mock_client = MagicMock()
            mock_create = AsyncMock(side_effect=mock_openai_response)
            mock_client.chat.completions.create = mock_create
            mock_client_class.return_value = mock_client

            config = LLMConfig(model="gpt-5-mini", top_p=0.9)
            result = await call_openai_direct("test prompt", config)

            assert result.content == "test response from OpenAI"
            # Verify top_p was passed
            call_kwargs = mock_create.call_args[1]
            assert call_kwargs["top_p"] == 0.9

    @pytest.mark.asyncio
    async def test_call_openai_direct_default_top_p_not_sent(self, mock_openai_response):
        """Test default top_p (1.0) is not sent to API"""
        with patch("openai.AsyncOpenAI") as mock_client_class:
            mock_client = MagicMock()
            mock_create = AsyncMock(side_effect=mock_openai_response)
            mock_client.chat.completions.create = mock_create
            mock_client_class.return_value = mock_client

            config = LLMConfig(model="gpt-5-mini", top_p=1.0)  # Default
            result = await call_openai_direct("test prompt", config)

            assert result.content == "test response from OpenAI"
            # Verify top_p was NOT passed (default)
            call_kwargs = mock_create.call_args[1]
            assert "top_p" not in call_kwargs


class TestOpenAIDirectToolCalling:
    """Tests for tool calling with OpenAI SDK"""

    @pytest.mark.asyncio
    async def test_tool_calling_basic(self):
        """Test basic tool calling"""

        # Define a simple tool
        def get_weather(location: str) -> str:
            return f"Weather in {location}: Sunny, 72°F"

        # Mock OpenAI responses
        class MockToolCall:
            def __init__(self):
                self.id = "call_123"
                self.type = "function"
                self.function = MagicMock()
                self.function.name = "get_weather"
                self.function.arguments = '{"location": "Tokyo"}'

        class MockMessage:
            def __init__(self, has_tools=False):
                if has_tools:
                    self.content = ""
                    self.tool_calls = [MockToolCall()]
                else:
                    self.content = "The weather in Tokyo is sunny and 72°F."
                    self.tool_calls = None

        class MockChoice:
            def __init__(self, has_tools=False):
                self.message = MockMessage(has_tools)

        class MockUsage:
            def __init__(self):
                self.prompt_tokens = 10
                self.completion_tokens = 20
                self.total_tokens = 30

        class MockResponse:
            def __init__(self, has_tools=False):
                self.choices = [MockChoice(has_tools)]
                self.usage = MockUsage()

        call_count = [0]

        async def mock_create(*args, **kwargs):
            call_count[0] += 1
            # First call: LLM wants to call tool
            if call_count[0] == 1:
                return MockResponse(has_tools=True)
            # Second call: LLM returns final answer
            else:
                return MockResponse(has_tools=False)

        with patch("openai.AsyncOpenAI") as mock_client_class:
            mock_client = MagicMock()
            mock_client.chat.completions.create = mock_create
            mock_client_class.return_value = mock_client

            config = LLMConfig(model="gpt-5-mini")
            result = await call_openai_direct(
                "What's the weather in Tokyo?", config, tool_functions=[get_weather]
            )

            assert isinstance(result, LLMResponse)
            assert "sunny" in result.content.lower() or "72" in result.content
            assert call_count[0] == 2  # Two LLM calls (tool call + final response)

    @pytest.mark.asyncio
    async def test_tool_not_found(self):
        """Test handling of unknown tool"""

        class MockToolCall:
            def __init__(self):
                self.id = "call_123"
                self.type = "function"
                self.function = MagicMock()
                self.function.name = "unknown_tool"
                self.function.arguments = "{}"

        class MockMessage:
            def __init__(self, iteration):
                if iteration == 1:
                    self.content = ""
                    self.tool_calls = [MockToolCall()]
                else:
                    self.content = "I couldn't find that tool"
                    self.tool_calls = None

        class MockChoice:
            def __init__(self, iteration):
                self.message = MockMessage(iteration)

        class MockUsage:
            def __init__(self):
                self.prompt_tokens = 5
                self.completion_tokens = 10
                self.total_tokens = 15

        class MockResponse:
            def __init__(self, iteration):
                self.choices = [MockChoice(iteration)]
                self.usage = MockUsage()

        call_count = [0]

        async def mock_create(*args, **kwargs):
            call_count[0] += 1
            return MockResponse(call_count[0])

        with patch("openai.AsyncOpenAI") as mock_client_class:
            mock_client = MagicMock()
            mock_client.chat.completions.create = mock_create
            mock_client_class.return_value = mock_client

            config = LLMConfig(model="gpt-5-mini")
            result = await call_openai_direct("test", config, tool_functions=[])

            assert isinstance(result, LLMResponse)
            # Tool error should be in messages, final response should handle it
            assert call_count[0] == 2


class TestOpenAIDirectUsageTracking:
    """Tests for usage and cost tracking"""

    @pytest.mark.asyncio
    async def test_usage_tracking(self, mock_openai_response):
        """Test token usage is tracked correctly"""
        with patch("openai.AsyncOpenAI") as mock_client_class:
            mock_client = MagicMock()
            mock_client.chat.completions.create = mock_openai_response
            mock_client_class.return_value = mock_client

            config = LLMConfig(model="gpt-5-mini")
            result = await call_openai_direct("test prompt", config)

            # Check usage from mock
            assert result.usage["prompt_tokens"] == 10
            assert result.usage["completion_tokens"] == 20
            assert result.usage["total_tokens"] == 30

    @pytest.mark.asyncio
    async def test_duration_tracking(self, mock_openai_response):
        """Test response duration is tracked"""
        with patch("openai.AsyncOpenAI") as mock_client_class:
            mock_client = MagicMock()
            mock_client.chat.completions.create = mock_openai_response
            mock_client_class.return_value = mock_client

            config = LLMConfig(model="gpt-5-mini")
            result = await call_openai_direct("test prompt", config)

            # Duration should be positive
            assert result.duration > 0
            assert result.duration < 10  # Should be very fast for mock


class TestOpenAIDirectErrorHandling:
    """Tests for error handling"""

    @pytest.mark.asyncio
    async def test_import_error_without_openai_sdk(self):
        """Test error when openai package not installed"""
        with patch.dict("sys.modules", {"openai": None}):
            config = LLMConfig(model="gpt-5-mini")

            with pytest.raises(ImportError, match="openai package is required"):
                await call_openai_direct("test", config)

    @pytest.mark.asyncio
    async def test_max_iterations_reached(self):
        """Test max iterations limit"""

        # Tool that keeps requesting more tool calls
        class MockToolCall:
            def __init__(self):
                self.id = "call_123"
                self.type = "function"
                self.function = MagicMock()
                self.function.name = "endless_tool"
                self.function.arguments = "{}"

        class MockMessage:
            def __init__(self):
                self.content = ""
                self.tool_calls = [MockToolCall()]  # Always wants to call tool

        class MockChoice:
            def __init__(self):
                self.message = MockMessage()

        class MockUsage:
            def __init__(self):
                self.prompt_tokens = 5
                self.completion_tokens = 5
                self.total_tokens = 10

        class MockResponse:
            def __init__(self):
                self.choices = [MockChoice()]
                self.usage = MockUsage()

        async def mock_create(*args, **kwargs):
            return MockResponse()

        def endless_tool():
            return "tool result"

        with patch("openai.AsyncOpenAI") as mock_client_class:
            mock_client = MagicMock()
            mock_client.chat.completions.create = mock_create
            mock_client_class.return_value = mock_client

            config = LLMConfig(model="gpt-5-mini")
            result = await call_openai_direct(
                "test", config, tool_functions=[endless_tool]
            )

            assert isinstance(result, LLMResponse)
            assert "Maximum tool call iterations reached" in result.content
            # Usage should be accumulated (5 iterations × 10 tokens = 50)
            assert result.usage["total_tokens"] == 50


class TestOpenAIDirectParameters:
    """Tests for parameter passing"""

    @pytest.mark.asyncio
    async def test_custom_parameters(self, mock_openai_response):
        """Test passing custom OpenAI parameters"""
        with patch("openai.AsyncOpenAI") as mock_client_class:
            mock_client = MagicMock()
            mock_create = AsyncMock(side_effect=mock_openai_response)
            mock_client.chat.completions.create = mock_create
            mock_client_class.return_value = mock_client

            config = LLMConfig(model="gpt-5-mini")
            result = await call_openai_direct(
                "test prompt",
                config,
                response_format={"type": "json_object"},
                seed=42,
            )

            assert result.content == "test response from OpenAI"

            # Verify custom parameters were passed
            call_kwargs = mock_create.call_args[1]
            assert call_kwargs["response_format"] == {"type": "json_object"}
            assert call_kwargs["seed"] == 42

    @pytest.mark.asyncio
    async def test_config_parameters_priority(self, mock_openai_response):
        """Test config parameters are used correctly"""
        with patch("openai.AsyncOpenAI") as mock_client_class:
            mock_client = MagicMock()
            mock_create = AsyncMock(side_effect=mock_openai_response)
            mock_client.chat.completions.create = mock_create
            mock_client_class.return_value = mock_client

            config = LLMConfig(
                model="gpt-5-mini", temperature=0.9, max_tokens=500, top_p=0.95
            )
            result = await call_openai_direct("test prompt", config)

            assert result.content == "test response from OpenAI"

            # Verify parameters
            call_kwargs = mock_create.call_args[1]
            assert call_kwargs["model"] == "gpt-5-mini"
            assert call_kwargs["temperature"] == 0.9
            assert call_kwargs["max_tokens"] == 500
            assert call_kwargs["top_p"] == 0.95


class TestOpenAIDirectIntegration:
    """Integration tests with call_llm() routing"""

    @pytest.mark.asyncio
    async def test_call_llm_routes_to_openai_direct(self, mock_openai_response):
        """Test call_llm() routes gpt-* models to OpenAI SDK"""
        from kagura.core.llm import call_llm

        with patch("openai.AsyncOpenAI") as mock_client_class:
            mock_client = MagicMock()
            mock_create = AsyncMock(side_effect=mock_openai_response)
            mock_client.chat.completions.create = mock_create
            mock_client_class.return_value = mock_client

            config = LLMConfig(model="gpt-5-mini")
            result = await call_llm("test prompt", config)

            # Should use OpenAI SDK (mock was called)
            assert "OpenAI" in str(result)
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_llm_routes_to_litellm(self, monkeypatch):
        """Test call_llm() routes non-OpenAI models to LiteLLM"""
        from kagura.core.llm import call_llm

        # Mock LiteLLM response
        class MockLiteLLMMessage:
            def __init__(self):
                self.content = "Response from Claude"
                self.tool_calls = None

        class MockLiteLLMChoice:
            def __init__(self):
                self.message = MockLiteLLMMessage()

        class MockLiteLLMUsage:
            def __init__(self):
                self.prompt_tokens = 15
                self.completion_tokens = 25
                self.total_tokens = 40

        class MockLiteLLMResponse:
            def __init__(self):
                self.choices = [MockLiteLLMChoice()]
                self.usage = MockLiteLLMUsage()

        async def mock_litellm_completion(*args, **kwargs):
            return MockLiteLLMResponse()

        monkeypatch.setattr("kagura.core.llm.litellm.acompletion", mock_litellm_completion)

        config = LLMConfig(model="claude-3-5-sonnet-20241022")
        result = await call_llm("test prompt", config)

        # Should use LiteLLM (Claude model)
        assert "Claude" in str(result) or isinstance(result, LLMResponse)
