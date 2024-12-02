import pytest
from unittest.mock import AsyncMock, patch

from kagura.core.agent import Agent

pytestmark = pytest.mark.asyncio


async def test_content_summarizer():
    """Test content_summarizer workflow agent"""

    mock_llm_response = '{"summary": {"content": "This is a summary."}}'

    async def mock_ainvoke(*args, **kwargs):
        return mock_llm_response

    # LLMクラスをパッチ
    with patch("kagura.core.agent.LLM") as MockLLM:

        mock_llm_instance = AsyncMock()
        mock_llm_instance.ainvoke.side_effect = mock_ainvoke
        MockLLM.return_value = mock_llm_instance

        agent = Agent.assigner(
            "content_summarizer", {"url": "https://www.kagura-ai.com"}
        )

        assert agent.is_workflow is True

        collected_updates = []
        async for update in await agent.execute():
            collected_updates.append(update)

        assert len(collected_updates) > 0

        states = {}
        for update in collected_updates:
            print(update)
            states.update(update)

        required_keys = {"content_fetcher", "text_converter", "summarizer", "END"}
        assert required_keys <= set(states.keys())

        content_fetcher_state = states.get("content_fetcher", {})
        assert "content" in content_fetcher_state
        assert content_fetcher_state["content"] is not None
        assert "text" in content_fetcher_state["content"]
        assert content_fetcher_state["content"]["text"] is not None

        text_converter_state = states.get("text_converter", {})
        assert "converted_content" in text_converter_state
        assert text_converter_state["converted_content"] is not None

        summarizer_state = states.get("summarizer", {})
        assert "summary" in summarizer_state
        assert summarizer_state["summary"] is not None
        assert "content" in summarizer_state["summary"]
        assert summarizer_state["summary"]["content"] is not None

        final_state = collected_updates[-1]
        assert "END" in final_state
        completed = final_state.get("END", {}).get("COMPLETED", False)
        assert completed is True
