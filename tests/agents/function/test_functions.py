from unittest.mock import AsyncMock, patch

import pytest
from pydantic import BaseModel

from kagura.core.agent import Agent
from kagura.core.models import get_custom_model

pytestmark = pytest.mark.asyncio


async def test_content_fetcher():
    """Test content_fetcher agent"""

    async def mock_fetch_content(state: BaseModel):
        ContentItem = get_custom_model("ContentItem")
        state.content = ContentItem(text="Mocked content from URL.")
        return state

    with patch("kagura.agents.content_fetcher.tools.fetch", new=mock_fetch_content):
        state = {"url": "https://github.com/"}
        agent = Agent.assigner("content_fetcher", state)
        result = await agent.execute()

        assert result.content.text == "Mocked content from URL."
