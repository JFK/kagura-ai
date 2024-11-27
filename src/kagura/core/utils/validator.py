from pathlib import Path
from typing import Any, Dict, List

import yaml


class AgentValidationError(Exception):
    pass


class KaguraAgentValidator:
    REQUIRED_FILES = ["agent.yml", "README.md"]
    REQUIRED_AGENT_FIELDS = ["description", "instructions", "prompt"]

    @classmethod
    def validate_repository(cls, repo_path: Path) -> None:
        """リポジトリ全体の構造を検証"""
        agents_dir = repo_path / "agents"
        if not agents_dir.is_dir():
            raise AgentValidationError("agents directory not found")

        tests_dir = repo_path / "tests"
        if not tests_dir.is_dir():
            raise AgentValidationError("tests directory not found")

        # エージェントごとの検証
        for agent_dir in agents_dir.iterdir():
            if agent_dir.is_dir():
                cls.validate_agent(agent_dir)
                cls.validate_agent_tests(tests_dir / agent_dir.name)

    @classmethod
    def validate_agent(cls, agent_dir: Path) -> None:
        """個別エージェントの構造と設定を検証"""
        # 必須ファイルの確認
        for file in cls.REQUIRED_FILES:
            if not (agent_dir / file).exists():
                raise AgentValidationError(f"{file} not found in {agent_dir.name}")

        # agent.ymlの検証
        agent_config = cls._load_yaml(agent_dir / "agent.yml")
        cls._validate_agent_config(agent_config, agent_dir.name)

        # state_model.ymlの検証（存在する場合）
        state_model_path = agent_dir / "state_model.yml"
        if state_model_path.exists():
            state_model = cls._load_yaml(state_model_path)
            cls._validate_state_model(state_model, agent_dir.name)

    @classmethod
    def validate_agent_tests(cls, test_dir: Path) -> None:
        """エージェントのテストを検証"""
        if not test_dir.exists():
            raise AgentValidationError(f"Test directory not found for {test_dir.name}")

        test_files = list(test_dir.glob("test_*.py"))
        if not test_files:
            raise AgentValidationError(f"No test files found in {test_dir}")

    @classmethod
    def _load_yaml(cls, path: Path) -> Dict[str, Any]:
        try:
            with open(path) as f:
                return yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise AgentValidationError(f"Invalid YAML in {path}: {e}")

    @classmethod
    def _validate_agent_config(cls, config: Dict[str, Any], agent_name: str) -> None:
        for field in cls.REQUIRED_AGENT_FIELDS:
            if field not in config:
                raise AgentValidationError(
                    f"Missing required field '{field}' in {agent_name}/agent.yml"
                )

        # 言語サポートの検証
        for field in ["description", "instructions", "prompt"]:
            if not cls._has_language_support(config[field]):
                raise AgentValidationError(
                    f"Missing language support in {agent_name}/agent.yml:{field}"
                )

    @classmethod
    def _validate_state_model(cls, model: Dict[str, Any], agent_name: str) -> None:
        if "state_fields" not in model:
            raise AgentValidationError(
                f"Missing state_fields in {agent_name}/state_model.yml"
            )

    @staticmethod
    def _has_language_support(field: List[Dict[str, Any]]) -> bool:
        languages = {item.get("language") for item in field if isinstance(item, dict)}
        return "en" in languages  # 最低限英語サポートを要求
