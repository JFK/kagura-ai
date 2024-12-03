# tests/core/test_agent.py

from unittest.mock import patch

import pytest

from kagura.core.agent import Agent
from kagura.core.config import AgentConfigManager
from kagura.core.models import BaseResponseModel
from kagura.core.prompts import BasePrompt
from kagura.core.utils.llm import LLM

pytestmark = pytest.mark.asyncio


class TestAgent:
    @pytest.fixture
    def agent_config_mock(self):
        """Mock agent configuration"""
        return {
            "llm": {"model": "openai/gpt-4o-mini", "max_tokens": 1024},
            "instructions": [
                {"language": "en", "description": "Summarize the input text."}
            ],
            "prompt": [
                {
                    "language": "en",
                    "template": "Summarize the following text:\n{QUERY}",
                }
            ],
            "response_fields": ["SUMMARY"],
        }

    @pytest.fixture
    def state_model_mock(self):
        """Mock state model configuration"""
        return {
            "state_fields": [
                {
                    "name": "QUERY",
                    "type": "str",
                    "description": [{"language": "en", "text": "Input query"}],
                },
                {
                    "name": "SUMMARY",
                    "type": "str",
                    "description": [{"language": "en", "text": "Summary of the input"}],
                },
            ]
        }

    @pytest.fixture
    def agent_instance(self, agent_config_mock, state_model_mock):
        with patch.object(
            AgentConfigManager,
            "load_yaml_config",
            side_effect=[agent_config_mock, state_model_mock],
        ):
            agent = Agent("test_agent", state={"QUERY": "Test input text."})
            yield agent

    @pytest.mark.skip()
    async def test_agent_initialization(self, agent_instance):
        """Test agent initialization"""
        assert agent_instance.agent_name == "test_agent"
        assert agent_instance.state.QUERY == "Test input text."
        assert agent_instance.state.SUCCESS is True
        assert agent_instance.llm is not None
        assert isinstance(agent_instance.prompt, BasePrompt)

    @pytest.mark.skip()
    async def test_agent_llm_invoke(self, agent_instance):
        """Test LLM invocation"""
        llm_response = '{"SUMMARY": "This is a summary."}'

        with patch.object(LLM, "ainvoke", return_value=llm_response):
            new_state = await agent_instance.llm_ainvoke()
            assert new_state.SUMMARY == "This is a summary."
            assert new_state.SUCCESS is True

    @pytest.mark.skip()
    async def test_agent_execute(self, agent_instance):
        """Test agent execution"""
        llm_response = '{"SUMMARY": "This is a summary."}'

        with patch.object(LLM, "ainvoke", return_value=llm_response):
            result = await agent_instance.execute()
            assert result.SUMMARY == "This is a summary."
            assert result.SUCCESS is True

    @pytest.mark.skip()
    async def test_agent_execute_with_error(self, agent_instance):
        """Test agent execution with LLM error"""
        with patch.object(LLM, "ainvoke", side_effect=Exception("LLM error")):
            result = await agent_instance.execute()
            assert result.SUCCESS is False
            assert "LLM error" in result.ERROR_MESSAGE

    @pytest.mark.skip()
    async def test_agent_skip_llm_invoke(self, agent_config_mock, state_model_mock):
        """Test agent execution when skip_llm_invoke is True"""
        agent_config_mock["skip_llm_invoke"] = True

        with patch.object(
            AgentConfigManager,
            "load_yaml_config",
            side_effect=[agent_config_mock, state_model_mock],
        ):
            agent = Agent("test_agent", state={"QUERY": "Test input text."})
            result = await agent.execute()
            # Since skip_llm_invoke is True, state should remain unchanged
            assert result.QUERY == "Test input text."
            assert result.SUCCESS is True

    @pytest.mark.skip()
    async def test_agent_workflow_execution(self, agent_config_mock):
        """Test agent workflow execution"""
        # Mock workflow configuration
        agent_config_mock.update(
            {
                "nodes": ["node1", "node2"],
                "edges": [{"from": "node1", "to": "node2"}],
                "entry_point": "node1",
            }
        )
        state_model_mock = {}

        with patch.object(
            AgentConfigManager,
            "load_yaml_config",
            side_effect=[agent_config_mock, state_model_mock],
        ):
            agent = Agent("workflow_agent")
            with patch.object(Agent, "execute", return_value=BaseResponseModel()):
                updates = []
                async for update in agent.execute_workflow():
                    updates.append(update)
                assert updates[-1]["COMPLETED"] is True
