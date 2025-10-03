import pytest

from kagura.core.agent import Agent

pytestmark = pytest.mark.asyncio


async def test_content_fetcher():
    """Test content_fetcher agent"""
    state = {"url": "https://www.kagura-ai.com"}
    agent = Agent.assigner("test_tools_agent", state)
    result = await agent.execute()

    assert result.content.text == "Mocked content from URL."
    assert result.content.content_type == "webpage"
    assert result.content.url == "https://www.kagura-ai.com"
