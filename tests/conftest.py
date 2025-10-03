"""Pytest configuration"""
import pytest


@pytest.fixture
def sample_agent():
    """Sample agent for testing"""
    from kagura import agent

    @agent
    async def hello(name: str) -> str:
        '''Say hello to {{ name }}'''
        return f"Hello, {name}!"

    return hello
