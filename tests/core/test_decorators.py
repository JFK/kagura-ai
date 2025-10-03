"""Tests for decorators (stub)"""
import pytest
from unittest.mock import AsyncMock, patch
from kagura import agent, tool, workflow


@pytest.mark.asyncio
async def test_agent_decorator_exists():
    """Test that @agent decorator exists"""
    with patch('kagura.core.decorators.call_llm', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = "Hello, World!"

        @agent
        async def hello(name: str) -> str:
            '''Say hello to {{ name }}'''
            pass

        result = await hello("World")
        assert isinstance(result, str)
        assert "World" in result


@pytest.mark.asyncio
async def test_agent_decorator_with_params():
    """Test @agent decorator with parameters"""
    with patch('kagura.core.decorators.call_llm', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = "Greetings, Alice!"

        @agent(model="gpt-4o-mini", temperature=0.5)
        async def greet(name: str) -> str:
            '''Greet {{ name }}'''
            pass

        result = await greet("Alice")
        assert isinstance(result, str)
        assert "Alice" in result


def test_tool_decorator():
    """Test @tool decorator"""
    @tool
    def add(a: int, b: int) -> int:
        return a + b

    result = add(2, 3)
    assert result == 5


def test_tool_decorator_with_parens():
    """Test @tool() decorator with parentheses"""
    @tool()
    def multiply(a: int, b: int) -> int:
        return a * b

    result = multiply(3, 4)
    assert result == 12


@pytest.mark.asyncio
async def test_workflow_decorator():
    """Test @workflow decorator"""
    @workflow
    async def process(data: str) -> str:
        return f"Processed: {data}"

    result = await process("test")
    assert result == "Processed: test"


@pytest.mark.asyncio
async def test_workflow_decorator_with_parens():
    """Test @workflow() decorator with parentheses"""
    @workflow()
    async def pipeline(data: str) -> str:
        return f"Pipeline: {data}"

    result = await pipeline("input")
    assert result == "Pipeline: input"
