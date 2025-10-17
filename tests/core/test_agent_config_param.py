"""Tests for @agent decorator config parameter

Tests that @agent accepts a pre-configured LLMConfig instance.
"""

import pytest

from kagura import LLMConfig, agent


@pytest.mark.asyncio
async def test_agent_with_config_param(monkeypatch):
    """Test @agent decorator accepts config parameter"""

    # Mock LLM response
    class MockMessage:
        def __init__(self):
            self.content = "Hello, World!"
            self.tool_calls = None

    class MockChoice:
        def __init__(self):
            self.message = MockMessage()

    class MockResponse:
        def __init__(self):
            self.choices = [MockChoice()]

    async def mock_completion(*args, **kwargs):
        return MockResponse()

    monkeypatch.setattr("kagura.core.llm.litellm.acompletion", mock_completion)

    # Create config with caching enabled
    config = LLMConfig(
        model="claude-3-5-sonnet-20241022",
        temperature=0.5,
        enable_cache=True,
        cache_ttl=1800
    )

    @agent(config=config)
    async def greeter(name: str) -> str:
        """Say hello to {{ name }}"""
        pass

    result = await greeter("Alice")
    assert result == "Hello, World!"


@pytest.mark.asyncio
async def test_agent_config_overrides_model_temp(monkeypatch):
    """Test config parameter overrides model and temperature"""

    captured_model = None
    captured_temp = None

    async def mock_completion(*args, **kwargs):
        nonlocal captured_model, captured_temp
        captured_model = kwargs.get("model")
        captured_temp = kwargs.get("temperature")

        class MockMessage:
            content = "Response"
            tool_calls = None

        class MockChoice:
            message = MockMessage()

        class MockResponse:
            choices = [MockChoice()]

        return MockResponse()

    monkeypatch.setattr("kagura.core.llm.litellm.acompletion", mock_completion)

    # Config should override decorator parameters
    config = LLMConfig(model="claude-3-opus-20240229", temperature=0.9)

    @agent(
        config=config,
        model="claude-3-5-sonnet-20241022",  # Should be ignored
        temperature=0.5      # Should be ignored
    )
    async def test_agent(query: str) -> str:
        """Answer {{ query }}"""
        pass

    await test_agent("test")

    # Config values should be used, not decorator params
    assert captured_model == "claude-3-opus-20240229"
    assert captured_temp == 0.9


@pytest.mark.asyncio
async def test_agent_without_config_uses_params(monkeypatch):
    """Test decorator parameters work when config not provided"""

    captured_model = None
    captured_temp = None

    async def mock_completion(*args, **kwargs):
        nonlocal captured_model, captured_temp
        captured_model = kwargs.get("model")
        captured_temp = kwargs.get("temperature")

        class MockMessage:
            content = "Response"
            tool_calls = None

        class MockChoice:
            message = MockMessage()

        class MockResponse:
            choices = [MockChoice()]

        return MockResponse()

    monkeypatch.setattr("kagura.core.llm.litellm.acompletion", mock_completion)

    # No config, use decorator params
    @agent(model="claude-3-5-sonnet-20241022", temperature=0.3)
    async def test_agent(query: str) -> str:
        """Answer {{ query }}"""
        pass

    await test_agent("test")

    assert captured_model == "claude-3-5-sonnet-20241022"
    assert captured_temp == 0.3


@pytest.mark.asyncio
async def test_agent_config_caching_works(monkeypatch):
    """Test caching works with config parameter"""
    call_count = 0

    async def mock_completion(*args, **kwargs):
        nonlocal call_count
        call_count += 1

        class MockMessage:
            content = f"Response {call_count}"
            tool_calls = None

        class MockChoice:
            message = MockMessage()

        class MockResponse:
            choices = [MockChoice()]

        return MockResponse()

    monkeypatch.setattr("kagura.core.llm.litellm.acompletion", mock_completion)

    # Enable caching in config
    config = LLMConfig(model="claude-3-5-sonnet-20241022", enable_cache=True)

    @agent(config=config)
    async def cached_agent(query: str) -> str:
        """Answer {{ query }}"""
        pass

    # First call
    result1 = await cached_agent("Hello")
    assert call_count == 1

    # Second call with same query should hit cache
    result2 = await cached_agent("Hello")
    assert call_count == 1  # No additional API call
    assert result1 == result2  # Same result from cache
