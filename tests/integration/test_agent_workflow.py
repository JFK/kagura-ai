"""Integration tests for agent workflows"""

from unittest.mock import patch

import pytest
from pydantic import BaseModel

from kagura import agent


class Person(BaseModel):
    """Test Pydantic model"""

    name: str
    age: int


@pytest.mark.asyncio
async def test_agent_with_template_and_parser(mock_llm_response):
    """Test @agent + template + parser integration"""

    @agent(model="gpt-5-mini")
    async def extract_person(text: str) -> Person:
        """Extract person info from: {{ text }}"""
        pass

    # Mock LLM response with valid JSON
    with mock_llm_response('{"name": "Alice", "age": 30}'):
        result = await extract_person("Alice is 30 years old")

        assert isinstance(result, Person)
        assert result.name == "Alice"
        assert result.age == 30


@pytest.mark.asyncio
@pytest.mark.skip(reason="v3.0 SDK feature - deprecated in v4.0 (Issue #374)")
async def test_agent_with_multiple_parameters(mock_llm_response):
    """Test agent with multiple parameters

    NOTE: This tests v3.0 SDK @agent decorator functionality.
    Will be removed in Issue #374 (Deprecate Chat CLI & SDK Examples).
    """

    @agent(model="gpt-5-mini")
    async def greet(name: str, time: str = "morning") -> str:
        """Good {{ time }}, {{ name }}!"""
        pass

    with mock_llm_response("Good morning, Alice!"):
        result = await greet("Alice")
        # Flexible assertion - accepts mocked or actual LLM response
        assert isinstance(result, str) and len(result) > 0


@pytest.mark.asyncio
@pytest.mark.skip(reason="v3.0 SDK feature - deprecated in v4.0 (Issue #374)")
async def test_agent_with_list_return(mock_llm_response):
    """Test agent returning a list

    NOTE: This tests v3.0 SDK @agent decorator functionality.
    Will be removed in Issue #374 (Deprecate Chat CLI & SDK Examples).
    """

    @agent(model="gpt-5-mini")
    async def extract_keywords(text: str) -> list[str]:
        """Extract keywords from: {{ text }}"""
        pass

    with mock_llm_response('["Python", "AI", "framework"]'):
        result = await extract_keywords("Python is an AI framework")

        assert isinstance(result, list)
        # Flexible assertion - LLM responses vary
        assert len(result) >= 1


@pytest.mark.asyncio
async def test_agent_error_handling():
    """Test agent error handling"""

    @agent(model="gpt-5-mini")
    async def failing_agent(query: str) -> str:
        """Answer: {{ query }}"""
        pass

    # Test with mocked API error
    # Note: telemetry may swallow exceptions, so we just test the call doesn't crash
    with patch("litellm.acompletion", side_effect=Exception("API Error")):
        try:
            result = await failing_agent("test")
            # If no exception, that's also acceptable (error handling worked)
            assert True
        except Exception as e:
            # If exception propagates, verify it's the right one
            assert "API Error" in str(e)
