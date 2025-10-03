"""Integration tests for agent workflows"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from pydantic import BaseModel

from kagura import agent


class Person(BaseModel):
    """Test Pydantic model"""
    name: str
    age: int


@pytest.mark.asyncio
async def test_agent_with_template_and_parser(mock_llm_response):
    """Test @agent + template + parser integration"""
    @agent(model="gpt-4o-mini")
    async def extract_person(text: str) -> Person:
        '''Extract person info from: {{ text }}'''
        pass

    # Mock LLM response with valid JSON
    with mock_llm_response('{"name": "Alice", "age": 30}'):
        result = await extract_person("Alice is 30 years old")

        assert isinstance(result, Person)
        assert result.name == "Alice"
        assert result.age == 30


@pytest.mark.asyncio
async def test_agent_with_multiple_parameters(mock_llm_response):
    """Test agent with multiple parameters"""
    @agent(model="gpt-4o-mini")
    async def greet(name: str, time: str = "morning") -> str:
        '''Good {{ time }}, {{ name }}!'''
        pass

    with mock_llm_response("Good morning, Alice!"):
        result = await greet("Alice")
        assert "Alice" in result


@pytest.mark.asyncio
async def test_agent_with_list_return(mock_llm_response):
    """Test agent returning a list"""
    @agent(model="gpt-4o-mini")
    async def extract_keywords(text: str) -> list[str]:
        '''Extract keywords from: {{ text }}'''
        pass

    with mock_llm_response('["Python", "AI", "framework"]'):
        result = await extract_keywords("Python is an AI framework")

        assert isinstance(result, list)
        assert len(result) == 3
        assert "Python" in result


@pytest.mark.asyncio
async def test_agent_error_handling():
    """Test agent error handling"""
    @agent(model="gpt-4o-mini")
    async def failing_agent(query: str) -> str:
        '''Answer: {{ query }}'''
        pass

    # Test with mocked API error
    with patch('litellm.acompletion', side_effect=Exception("API Error")):
        with pytest.raises(Exception) as exc_info:
            await failing_agent("test")
        assert "API Error" in str(exc_info.value)
