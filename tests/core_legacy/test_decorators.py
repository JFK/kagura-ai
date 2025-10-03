"""Tests for decorators (stub)"""
import pytest
from kagura import agent


@pytest.mark.asyncio
async def test_agent_decorator_exists():
    """Test that @agent decorator exists"""
    @agent
    async def hello(name: str) -> str:
        '''Say hello to {{ name }}'''
        return f"Hello, {name}!"

    # Stub test: just check it doesn't crash
    result = await hello("World")
    assert result == "Hello, World!"
