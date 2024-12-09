from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from kagura.core.agent import Agent
from kagura.core.config import AgentConfigManager, ConfigInitializer
from kagura.core.models import BaseModel

pytestmark = pytest.mark.asyncio


@pytest.fixture
def project_root():
    return Path(__file__).resolve().parent.parent.parent  # Adjust as necessary


def test_initialize_config_directory(fs, project_root):
    user_config_dir = project_root / ".config" / "kagura"
    agents_config_dir = user_config_dir / "agents"
    user_system_yml = agents_config_dir / "system.yml"
    package_config_dir = project_root / "src" / "kagura" / "agents"
    package_system_yml = package_config_dir / "system.yml"

    assert not package_config_dir.exists()
    assert not package_system_yml.exists()

    fs.create_file(package_system_yml)
    initializer = ConfigInitializer(
        package_config_dir=package_config_dir, user_config_dir=user_config_dir
    )
    initializer.initialize()

    assert user_config_dir.exists()
    assert agents_config_dir.exists()
    assert user_system_yml.exists()


async def test_atomic_agent_configs():
    """Test loading and validating agent configurations"""
    config_manager = AgentConfigManager("test_atomic_agent")

    # システム設定のテスト
    assert config_manager.system_config is not None
    assert "system" in config_manager.system_config
    assert "language" in config_manager.system_config["system"]
    assert config_manager.system_language in ["en", "ja"]

    # システムLLM設定のテスト
    assert config_manager.system_llm is not None
    assert "model" in config_manager.system_llm
    assert isinstance(config_manager.system_llm_model, str)

    # エージェント設定のテスト
    agent_config = config_manager.agent_config
    assert agent_config is not None

    # LLM設定のテスト
    assert "llm" in agent_config
    llm_config = agent_config["llm"]
    assert llm_config["model"] == "openai/gpt-4o-mini"
    assert llm_config["max_tokens"] == 1
    assert llm_config["retry_count"] == 1

    # 説明のテスト
    descriptions = agent_config["description"]
    assert any(
        desc["language"] == "en"
        and desc["text"] == "This agent is to test the atomic agent."
        for desc in descriptions
    )

    # 指示のテスト
    instructions = agent_config["instructions"]
    assert any(
        instr["language"] == "en"
        and "test_atomic_agent instructions" in instr["description"]
        for instr in instructions
    )

    # プロンプトテンプレートのテスト
    prompts = agent_config["prompt"]
    assert any(
        prompt["language"] == "en" and "test_atomic_agent prompt" in prompt["template"]
        for prompt in prompts
    )

    # レスポンスフィールドのテスト
    assert "response_fields" in agent_config
    assert "test_agent_response_fields" in agent_config["response_fields"]

    # カスタムツール設定のテスト
    assert "pre_custom_tool" in agent_config
    assert "post_custom_tool" in agent_config
    assert (
        agent_config["pre_custom_tool"]
        == "kagura.agents.test_atomic_agent.tools.pre_process"
    )
    assert (
        agent_config["post_custom_tool"]
        == "kagura.agents.test_atomic_agent.tools.post_process"
    )

    # 状態モデル設定のテスト
    state_model_config = config_manager.state_model_config
    assert state_model_config is not None

    # カスタムモデルのテスト
    custom_models = state_model_config["custom_models"]
    assert len(custom_models) > 0

    # TestAgentCustomModelの構造検証
    test_agent_model = next(
        model for model in custom_models if model["name"] == "TestAgentCustomModel"
    )
    expected_fields = {
        "string": "str",
        "integer": "int",
        "float": "float",
        "boolean": "bool",
        "list_string": "List[str]",
        "list_integer": "List[int]",
        "list_float": "List[float]",
        "set_string": "Set[str]",
        "frozen_set_int": "FrozenSet[int]",
        "dict_str_int": "Dict[str, int]",
        "dict_str_any": "Dict[str, Any]",
        "optional_string": "Optional[str]",
        "tuple_int_str": "Tuple[int, str]",
    }

    actual_fields = {
        field["name"]: field["type"]
        for field in test_agent_model["fields"]
        if field["name"] in expected_fields
    }
    assert all(
        actual_fields[name] == type_str for name, type_str in expected_fields.items()
    )

    # 状態フィールドのテスト
    state_fields = config_manager.state_fields
    assert len(state_fields) > 0

    # 必須状態フィールドの検証
    required_fields = {
        "test_agent_response_fields": "TestAgentCustomModel",
        "test_agent_user_input": "str",
    }
    actual_state_fields = {
        field["name"]: field["type"]
        for field in state_fields
        if field["name"] in required_fields
    }
    assert all(
        actual_state_fields[name] == type_str
        for name, type_str in required_fields.items()
    )

    # モデル生成のテスト
    state_model = config_manager.state_model
    assert issubclass(state_model, BaseModel)

    # モデルのアノテーションテスト
    model_fields = state_model.model_fields
    assert "test_agent_response_fields" in model_fields
    assert "test_agent_user_input" in model_fields

    # フィールドの型テスト
    test_field = model_fields["test_agent_response_fields"]
    assert test_field.annotation is not None

    # 登録済みカスタムモデルのテスト
    registered_models = config_manager.registered_custom_models
    assert "TestAgentCustomModel" in registered_models
    assert "NestedModel" in registered_models
    assert "ComplexModel" in registered_models

    # テストインスタンス生成
    test_instance = state_model(
        test_agent_user_input="test",
        test_agent_response_fields={
            "string": "test",
            "integer": 42,
            "float": 3.14,
            "boolean": True,
            "list_string": ["test"],
            "list_integer": [1],
            "list_float": [1.0],
            "set_string": {"test"},
            "frozen_set_int": frozenset([1]),
            "dict_str_int": {"test": 1},
            "dict_str_any": {"test": "test"},
            "optional_string": "test",
            "tuple_int_str": (1, "test"),
        },
    )
    assert test_instance is not None

    # 言語設定のテスト
    assert config_manager.instructions is not None
    assert config_manager.prompt_template is not None

    # LLM固有の設定テスト
    assert config_manager.llm_model == "openai/gpt-4o-mini"
    assert config_manager.llm_max_tokens == 1
    assert config_manager.llm_retry_count == 1
    assert config_manager.llm_stream == False

    # ワークフロー関連プロパティのテスト
    assert config_manager.is_workflow == False
    assert len(config_manager.nodes) == 0
    assert len(config_manager.edges) == 0
    assert len(config_manager.state_field_bindings) == 0

    # カスタムツールプロパティのテスト
    assert config_manager.custom_tool is None
    assert (
        config_manager.pre_custom_tool
        == "kagura.agents.test_atomic_agent.tools.pre_process"
    )
    assert (
        config_manager.post_custom_tool
        == "kagura.agents.test_atomic_agent.tools.post_process"
    )

    # レスポンスモデル生成のテスト
    response_model = config_manager.response_model
    assert response_model is not None
    assert "test_agent_response_fields" in response_model.model_fields


async def test_atomic_agent_state_binding():
    """Test state binding and validation"""
    config_manager = AgentConfigManager("test_atomic_agent")

    # Test state initialization with dict
    test_state = {
        "test_agent_user_input": "test input",
        "test_agent_response_fields": {
            "string": "test",
            "integer": 42,
            "float": 3.14,
            "boolean": True,
            "list_string": ["a", "b", "c"],
            "list_integer": [1, 2, 3],
            "list_float": [1.1, 2.2, 3.3],
            "set_string": {"x", "y", "z"},
            "frozen_set_int": frozenset([1, 2, 3]),
            "dict_str_int": {"a": 1, "b": 2},
            "dict_str_any": {"a": "test", "b": 42},
            "optional_string": "optional",
            "tuple_int_str": (1, "test"),
        },
    }

    state_model = config_manager.state_model(**test_state)
    assert state_model is not None
    assert state_model.test_agent_user_input == "test input"
    assert state_model.test_agent_response_fields.integer == 42

    # Test invalid state
    invalid_state = {
        "test_agent_user_input": "test input",
        "test_agent_response_fields": {
            "string": "test",
            "integer": "not an integer",  # Invalid type
        },
    }

    with pytest.raises(Exception):
        config_manager.state_model(**invalid_state)


@pytest.mark.asyncio
async def test_orchestrator_configuration():
    """Test the orchestrator agent configuration loading"""
    agent = Agent.assigner("test_workflow_agent")

    # Test basic configuration
    assert agent.is_workflow == True
    assert agent.entry_point == "content_fetcher"
    assert agent.skip_state_model == True  # Orchestrator should skip state model

    # Test nodes configuration
    assert len(agent.nodes) == 3
    assert "content_fetcher" in agent.nodes
    assert "text_converter" in agent.nodes
    assert "summarizer" in agent.nodes

    # Test edges configuration
    assert len(agent.edges) == 2
    edge1, edge2 = agent.edges
    assert edge1["from"] == "content_fetcher"
    assert edge1["to"] == "text_converter"
    assert edge2["from"] == "text_converter"
    assert edge2["to"] == "summarizer"

    # Test state field bindings
    assert len(agent.state_field_bindings) == 2
    binding1, binding2 = agent.state_field_bindings
    assert binding1["from"] == "content_fetcher.content"
    assert binding1["to"] == "text_converter.content"
    assert binding2["from"] == "text_converter.converted_content"
    assert binding2["to"] == "summarizer.content.text"

    # Test conditional edges
    assert "text_converter" in agent.conditional_edges
    converter_conditions = agent.conditional_edges["text_converter"]["conditions"]
    assert converter_conditions["success"] == "summarizer"
    assert converter_conditions["retry"] == "text_converter"
    assert converter_conditions["failure"] == "error_handler"
