"""Tests for @agent decorator implementation"""
import pytest
from unittest.mock import AsyncMock, patch
from kagura import agent


@pytest.mark.asyncio
async def test_agent_basic():
    """Test basic @agent functionality"""
    with patch('kagura.core.decorators.call_llm', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = "Hello, Alice!"

        @agent
        async def greet(name: str) -> str:
            '''Say hello to {{ name }}'''
            pass

        result = await greet("Alice")
        assert result == "Hello, Alice!"
        assert mock_llm.called
        # Verify prompt contains the name
        call_args = mock_llm.call_args
        assert "Alice" in call_args[0][0]


@pytest.mark.asyncio
async def test_agent_with_model():
    """Test @agent with model parameter"""
    with patch('kagura.core.decorators.call_llm', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = "This is a summary."

        @agent(model="gpt-4o-mini")
        async def summarize(text: str) -> str:
            '''Summarize this text: {{ text }}'''
            pass

        result = await summarize("This is a test text.")
        assert result == "This is a summary."
        # Verify config has correct model
        call_args = mock_llm.call_args
        assert call_args[0][1].model == "gpt-4o-mini"


@pytest.mark.asyncio
async def test_agent_multiple_params():
    """Test @agent with multiple parameters"""
    with patch('kagura.core.decorators.call_llm', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = "こんにちは"

        @agent
        async def translate(text: str, language: str) -> str:
            '''Translate "{{ text }}" to {{ language }}'''
            pass

        result = await translate("Hello", "Japanese")
        assert result == "こんにちは"
        # Verify prompt contains both parameters
        call_args = mock_llm.call_args
        prompt = call_args[0][0]
        assert "Hello" in prompt
        assert "Japanese" in prompt


@pytest.mark.asyncio
async def test_agent_temperature():
    """Test @agent with temperature parameter"""
    with patch('kagura.core.decorators.call_llm', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = "4"

        @agent(temperature=0.3)
        async def respond(question: str) -> str:
            '''Answer: {{ question }}'''
            pass

        result = await respond("What is 2+2?")
        assert result == "4"
        # Verify config has correct temperature
        call_args = mock_llm.call_args
        assert call_args[0][1].temperature == 0.3
