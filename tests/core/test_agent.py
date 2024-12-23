# tests/core/test_agent.py

from unittest.mock import patch
from typing import Dict, Any

import pytest

from kagura.core.agent import Agent
from kagura.core.config import AgentConfigManager
from kagura.core.models import BaseResponseModel
from kagura.core.prompts import BasePrompt
from kagura.core.utils.llm import LLM

pytestmark = pytest.mark.asyncio


class TestAgent:
    @pytest.fixture
    def agent_config_mock(self) -> Dict[str, Any]:
        """Mock agent configuration"""
        return {
            "llm": {"model": "openai/gpt-4-mini", "max_tokens": 1024},
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
    def state_model_mock(self) -> Dict[str, Any]:
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
    def system_config_mock(self) -> Dict[str, Any]:
        """Mock system configuration"""
        return {
            "system": {"language": "en"},
            "llm": {"model": "openai/gpt-4", "retry_count": 3},
            "backends": [],
        }

    @pytest.fixture
    def mock_yaml_config(self, agent_config_mock, state_model_mock, system_config_mock):
        def load_yaml_config_side_effect(path: str):
            if "system.yml" in path:
                return system_config_mock
            elif "agent.yml" in path:
                return agent_config_mock
            elif "state_model.yml" in path:
                return state_model_mock
            raise FileNotFoundError(f"Mock file not found: {path}")

        return load_yaml_config_side_effect

    @pytest.fixture
    def agent_instance(self, mock_yaml_config):
        with patch.object(
            AgentConfigManager, "load_yaml_config", side_effect=mock_yaml_config
        ):
            agent = Agent("test_agent", state={"QUERY": "Test input text."})
            yield agent

    async def test_agent_initialization(self, agent_instance):
        """Test agent initialization"""
        assert agent_instance.agent_name == "test_agent"
        assert agent_instance.state.QUERY == "Test input text."
        assert agent_instance.state.SUCCESS is True
        assert agent_instance.llm is not None
        assert isinstance(agent_instance.prompt, BasePrompt)

    async def test_validate_agent_missing_file(self, system_config_mock):
        """Test agent validation with missing agent.yml"""

        def raise_not_found_except_system(path: str):
            if "system.yml" in path:
                return system_config_mock
            raise FileNotFoundError(f"Mock file not found: {path}")

    async def test_initialize_state_with_string(self, mock_yaml_config):
        """Test state initialization with string input"""
        with patch.object(
            AgentConfigManager, "load_yaml_config", side_effect=mock_yaml_config
        ):
            agent = Agent("test_agent", state="Test input")
            assert agent.state.QUERY == "Test input"

    async def test_initialize_state_with_dict(self, mock_yaml_config):
        """Test state initialization with dictionary"""
        with patch.object(
            AgentConfigManager, "load_yaml_config", side_effect=mock_yaml_config
        ):
            agent = Agent(
                "test_agent", state={"QUERY": "Test input", "SUMMARY": "Test summary"}
            )
            assert agent.state.QUERY == "Test input"
            assert agent.state.SUMMARY == "Test summary"

    async def test_initialize_state_with_base_model(self, mock_yaml_config):
        """Test state initialization with BaseModel"""
        initial_state = BaseResponseModel(QUERY="Test input")
        with patch.object(
            AgentConfigManager, "load_yaml_config", side_effect=mock_yaml_config
        ):
            agent = Agent("test_agent", state=initial_state)
            assert agent.state.QUERY == "Test input"

    async def test_agent_llm_invoke(self, agent_instance):
        """Test LLM invocation"""
        llm_response = '{"SUMMARY": "This is a summary."}'

        with patch.object(LLM, "ainvoke", return_value=llm_response):
            new_state = await agent_instance.llm_ainvoke(agent_instance.state)
            assert new_state.SUMMARY == "This is a summary."
            assert new_state.SUCCESS is True

    async def test_agent_execute(self, agent_instance):
        """Test agent execution"""
        llm_response = '{"SUMMARY": "This is a summary."}'

        with patch.object(LLM, "ainvoke", return_value=llm_response):
            result = await agent_instance.execute()
            assert isinstance(result, BaseResponseModel)
            assert result.SUMMARY == "This is a summary."
            assert result.SUCCESS is True

    async def test_agent_execute_with_error(self, agent_instance):
        """Test agent execution with LLM error"""
        with patch.object(LLM, "ainvoke", side_effect=Exception("LLM error")):
            result = await agent_instance.execute()
            assert result.SUCCESS is False
            assert "LLM error" in result.ERROR_MESSAGE

    async def test_agent_skip_llm_invoke(self, mock_yaml_config, agent_config_mock):
        """Test agent execution when skip_llm_invoke is True"""
        agent_config_mock["skip_llm_invoke"] = True

        with patch.object(
            AgentConfigManager, "load_yaml_config", side_effect=mock_yaml_config
        ):
            agent = Agent("test_agent", state={"QUERY": "Test input text."})
            result = await agent.execute()
            assert result.QUERY == "Test input text."
            assert result.SUCCESS is True

    async def test_workflow_execution_with_state_bindings(
        self, mock_yaml_config, agent_config_mock, state_model_mock
    ):
        """Test workflow execution with state field bindings"""
        workflow_config = {
            "nodes": ["node1", "node2"],
            "edges": [{"from": "node1", "to": "node2"}],
            "entry_point": "node1",
            "state_field_bindings": [{"from": "node1.SUMMARY", "to": "node2.QUERY"}],
        }
        # ワークフロー設定の修正
        base_agent_config = {
            **agent_config_mock,
            **workflow_config,
            "skip_state_model": False,  # 明示的にFalseに設定
            "response_fields": [],  # ワークフローではresponse_fieldsは不要
        }

        node_config = {
            "state_fields": state_model_mock["state_fields"],
            "skip_state_model": False,
        }

        def modified_yaml_config(path: str):
            if path == "agents/system.yml":
                return {"system": {"language": "en"}, "llm": {"model": "test"}}
            elif path == "agents/workflow_agent/agent.yml":
                return base_agent_config
            elif path == "agents/workflow_agent/state_model.yml":
                return state_model_mock
            elif "node1/agent.yml" in path or "node2/agent.yml" in path:
                return node_config
            elif "node1/state_model.yml" in path or "node2/state_model.yml" in path:
                return state_model_mock
            raise FileNotFoundError(f"Mock file not found: {path}")

        with patch.object(
            AgentConfigManager, "load_yaml_config", side_effect=modified_yaml_config
        ):
            # 初期化時のstateを設定
            initial_state = {"QUERY": "Initial input", "SUMMARY": None}
            agent = Agent("workflow_agent", state=initial_state)
            mock_state = BaseResponseModel(SUMMARY="Node1 output")

            with patch.object(Agent, "execute", return_value=mock_state):
                async for update in agent.execute_workflow(agent.state):
                    if "COMPLETED" in update:
                        assert update["COMPLETED"] is True

    async def test_llm_retry_on_error(self, mock_yaml_config):
        """Test LLM retry behavior on error"""
        error_count = 0

        async def llm_with_retry(*args, **kwargs):
            nonlocal error_count
            error_count += 1
            if error_count < 3:  # Fail twice, succeed on third try
                raise Exception("LLM temporary error")
            return '{"SUMMARY": "Success after retry"}'

        with patch.object(
            AgentConfigManager, "load_yaml_config", side_effect=mock_yaml_config
        ):
            agent = Agent("test_agent", state={"QUERY": "Test input"})
            with patch.object(LLM, "ainvoke", side_effect=llm_with_retry):
                result = await agent.llm_ainvoke(agent.state)
                assert result.SUCCESS is True
                assert result.SUMMARY == "Success after retry"
                assert error_count == 3  # Verify retry count

    async def test_agent_with_custom_tools(self, mock_yaml_config, agent_config_mock):
        """Test agent with custom pre and post tools"""
        agent_config_mock.update(
            {
                "pre_custom_tool": "pre_tool_function",
                "post_custom_tool": "post_tool_function",
            }
        )

        async def mock_pre_tool(state):
            state.QUERY = "Modified by pre-tool"
            return state

        async def mock_post_tool(state):
            state.SUMMARY = "Modified by post-tool"
            return state

        with patch.object(
            AgentConfigManager, "load_yaml_config", side_effect=mock_yaml_config
        ):
            with patch("kagura.core.agent.import_function") as mock_import:
                mock_import.side_effect = [mock_pre_tool, mock_post_tool]
                agent = Agent("test_agent", state={"QUERY": "Original input"})

                llm_response = '{"SUMMARY": "LLM output"}'
                with patch.object(LLM, "ainvoke", return_value=llm_response):
                    result = await agent.execute()
                    assert result.QUERY == "Modified by pre-tool"
                    assert result.SUMMARY == "Modified by post-tool"
                    assert result.SUCCESS is True
