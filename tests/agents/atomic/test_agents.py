from unittest.mock import AsyncMock, patch

import pytest

from kagura.core.agent import Agent

pytestmark = pytest.mark.asyncio


async def test_chatbot():
    """Test basic chat response"""
    mock_chunks = ["I ", "am ", "Kagura", ", an ", "AI ", "assistant", "."]

    async def mock_astream(*args, **kwargs):
        for chunk in mock_chunks:
            yield chunk

    with patch("kagura.core.agent.LLM") as MockLLM:

        mock_instance = MockLLM.return_value
        mock_instance.astream.side_effect = mock_astream

        agent = Agent.assigner("chat")
        response = await agent.execute("Who are you?")

        collected_response = ""
        async for chunk in response:
            collected_response += chunk

        assert "Kagura" in collected_response
        mock_instance.astream.assert_called_once()


async def test_user_search_intent_extractor():
    """Test user_search_intent_extractor agent"""

    mock_llm_response = '{"user_search_intents": [{"user_intent": "Interest in Kagura (神楽)", "confidence": 0.9}]}'

    async def mock_ainvoke(*args, **kwargs):
        return mock_llm_response

    with patch("kagura.core.agent.LLM") as MockLLM:

        mock_instance = MockLLM.return_value
        mock_instance.ainvoke.side_effect = mock_ainvoke

        state = {"user_query": "I am interested in Kagura(神楽)"}
        agent = Agent.assigner("user_search_intent_extractor", state)
        result = await agent.execute()
        assert result is not None
        assert hasattr(result, "user_search_intents")

        model_dumped_result = result.model_dump()
        assert "user_search_intents" in model_dumped_result
        assert model_dumped_result["user_search_intents"] is not None

        user_search_intents = model_dumped_result["user_search_intents"]
        assert len(user_search_intents) == 1

        user_search_intent = user_search_intents[0]
        assert "user_intent" in user_search_intent
        assert user_search_intent["user_intent"].startswith("Interest in Kagura")
        assert "confidence" in user_search_intent
        assert user_search_intent["confidence"] == 0.9


async def test_summarizer():
    """Test summarizer agent"""

    mock_llm_response = '{"summary": {"content": "Kagura is an AI agent framework enabling easy building and orchestration of AI agents using YAML, focusing on flexibility and modularity."}}'

    async def mock_ainvoke(*args, **kwargs):
        return mock_llm_response

    with patch("kagura.core.agent.LLM") as MockLLM:

        mock_instance = MockLLM.return_value
        mock_instance.ainvoke.side_effect = mock_ainvoke

        text = "Some long text to summarize."
        state = {
            "content": {
                "text": text,
            }
        }
        agent = Agent.assigner("summarizer", state)
        result = await agent.execute()

        assert result.summary.content.startswith("Kagura is an AI agent framework")


async def test_search_planner():
    """Test sequential execution of user_search_intent_extractor and search_planner"""

    mock_llm_responses = {
        "user_search_intent_extractor": """
        {
            "user_search_intents": [
                {
                    "user_intent": "Learn how to fine-tune the learning rate of an AI model",
                    "confidence": 0.9
                }
            ]
        }
        """,
        "search_planner": """
        {
            "search_plan": {
                "goal": "Learn how to fine-tune the learning rate of an AI model",
                "steps": [
                    {
                        "step_number": 1,
                        "search_query": "What is learning rate in machine learning?",
                        "expected_info": "Definition of learning rate and its significance in training AI models.",
                        "search_focus": [
                            "Definition of learning rate",
                            "Role of learning rate in model training",
                            "Effects of learning rate on convergence"
                        ]
                    },
                    {
                        "step_number": 2,
                        "search_query": "How to choose an appropriate learning rate for machine learning models?",
                        "expected_info": "Methods for selecting a suitable learning rate.",
                        "search_focus": [
                            "Common strategies (e.g., grid search, random search)",
                            "Heuristic methods",
                            "Impact of learning rate on overfitting and underfitting"
                        ]
                    }
                ]
            }
        }
        """,
    }

    async def mock_ainvoke_user_search_intent_extractor(*args, **kwargs):
        return mock_llm_responses["user_search_intent_extractor"]

    async def mock_ainvoke_search_planner(*args, **kwargs):
        return mock_llm_responses["search_planner"]

    with patch("kagura.core.agent.LLM") as MockLLM:

        # user_search_intent_extractor の LLM をモック
        mock_instance_user_intent = MockLLM.return_value
        mock_instance_user_intent.ainvoke.side_effect = (
            mock_ainvoke_user_search_intent_extractor
        )

        user_query = (
            "What is the best way to fine-tune the learning rate of an AI model?"
        )
        state = {"user_query": user_query}
        user_intent_agent = Agent.assigner("user_search_intent_extractor", state)
        result = await user_intent_agent.execute()

        model_dumped_result = result.model_dump()
        assert "user_search_intents" in model_dumped_result

        user_search_intents = model_dumped_result["user_search_intents"]
        assert len(user_search_intents) == 1

        user_search_intent = user_search_intents[0]
        assert "user_intent" in user_search_intent
        assert user_search_intent["user_intent"].startswith(
            "Learn how to fine-tune the learning rate"
        )
        assert "confidence" in user_search_intent
        assert user_search_intent["confidence"] == 0.9

        mock_instance_planner = MockLLM.return_value
        mock_instance_planner.ainvoke.side_effect = mock_ainvoke_search_planner

        state = {"user_search_intents": user_search_intents}
        planner_agent = Agent.assigner("search_planner", state)
        search_plan_result = await planner_agent.execute()

        search_plan_dump = search_plan_result.model_dump()
        assert "search_plan" in search_plan_dump

        search_plan = search_plan_dump["search_plan"]
        assert "goal" in search_plan
        assert (
            search_plan["goal"]
            == "Learn how to fine-tune the learning rate of an AI model"
        )

        assert "steps" in search_plan
        assert isinstance(search_plan["steps"], list)
        assert len(search_plan["steps"]) >= 2

        first_step = search_plan["steps"][0]
        assert first_step["step_number"] == 1
        assert (
            first_step["search_query"] == "What is learning rate in machine learning?"
        )
        assert (
            first_step["expected_info"]
            == "Definition of learning rate and its significance in training AI models."
        )
        assert "search_focus" in first_step
        assert isinstance(first_step["search_focus"], list)
        assert "Definition of learning rate" in first_step["search_focus"]

        second_step = search_plan["steps"][1]
        assert second_step["step_number"] == 2
        assert (
            second_step["search_query"]
            == "How to choose an appropriate learning rate for machine learning models?"
        )
        assert (
            second_step["expected_info"]
            == "Methods for selecting a suitable learning rate."
        )
        assert "search_focus" in second_step
        assert isinstance(second_step["search_focus"], list)
        assert (
            "Common strategies (e.g., grid search, random search)"
            in second_step["search_focus"]
        )
