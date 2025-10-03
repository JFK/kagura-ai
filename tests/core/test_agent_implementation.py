"""Tests for @agent decorator implementation"""
import pytest
from kagura import agent


@pytest.mark.asyncio
async def test_agent_basic():
    """Test basic @agent functionality"""
    @agent
    async def greet(name: str) -> str:
        '''Say hello to {{ name }}'''
        pass

    result = await greet("Alice")
    assert "Alice" in result
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_agent_with_model():
    """Test @agent with model parameter"""
    @agent(model="gpt-4o-mini")
    async def summarize(text: str) -> str:
        '''Summarize this text: {{ text }}'''
        pass

    result = await summarize("This is a test text.")
    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_agent_multiple_params():
    """Test @agent with multiple parameters"""
    @agent
    async def translate(text: str, language: str) -> str:
        '''Translate "{{ text }}" to {{ language }}'''
        pass

    result = await translate("Hello", "Japanese")
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_agent_temperature():
    """Test @agent with temperature parameter"""
    @agent(temperature=0.3)
    async def respond(question: str) -> str:
        '''Answer: {{ question }}'''
        pass

    result = await respond("What is 2+2?")
    assert isinstance(result, str)
    assert len(result) > 0
