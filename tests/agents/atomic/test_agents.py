import pytest
from unittest.mock import AsyncMock, patch

from kagura.core.agent import Agent

pytestmark = pytest.mark.asyncio


async def test_chatbot():
    """Test basic chat response"""
    mock_chunks = ["I ", "am ", "Kagura", ", an ", "AI ", "assistant", "."]

    async def mock_astream(*args, **kwargs):
        for chunk in mock_chunks:
            yield chunk

    with patch("kagura.core.config.LLM") as MockLLM:

        mock_instance = MockLLM.return_value
        mock_instance.astream.side_effect = mock_astream

        agent = Agent.assigner("chat")
        response = await agent.execute("Who are you?")

        collected_response = ""
        async for chunk in response:
            collected_response += chunk

        assert "Kagura" in collected_response
        mock_instance.astream.assert_called_once()


async def test_content_summarizer():
    """Test content_summarizer workflow agent"""

    # モックするLLMのレスポンスを定義（ネストされた辞書構造）
    mock_llm_responses = {
        "content_fetcher": '{"content": {"text": "This is a content."}}',
        "text_converter": '{"converted_content": "This is a content."}',
        "summarizer": '{"summary": {"content": "This is a summary."}}',
    }

    # 各エージェント用のモック関数を定義
    async def mock_ainvoke_fetcher(*args, **kwargs):
        return mock_llm_responses["content_fetcher"]

    async def mock_ainvoke_converter(*args, **kwargs):
        return mock_llm_responses["text_converter"]

    async def mock_ainvoke_summarizer(*args, **kwargs):
        return mock_llm_responses["summarizer"]

    # LLMクラスをパッチ
    with patch("kagura.core.config.LLM") as MockLLM:

        mock_llm_instance = AsyncMock()
        mock_llm_instance.ainvoke.side_effect = mock_ainvoke_summarizer
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
