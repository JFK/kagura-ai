import importlib.resources as pkg_resources
import os
import shutil
import sys
from pathlib import Path
from string import Template
from typing import Any, Dict, List, Optional, Type, Union

import yaml
from pydantic import BaseModel

from .models import Models, convert_typing_to_builtin, map_type
from .utils.logger import get_logger

logger = get_logger(__name__)


class ConfigError(Exception):
    pass


class ConfigInitializer:
    def __init__(self, package_name: str = "kagura"):
        self.package_name = package_name
        self.user_config_dir = Path(os.path.expanduser("~")) / ".config" / package_name

        # Try multiple methods to find the package data
        self.package_config_dir = self._find_package_config_dir()

    def _find_package_config_dir(self) -> Path:
        """Find the package config directory using multiple methods"""
        # Method 1: Try importlib.resources
        try:
            with pkg_resources.path(self.package_name, "agents") as package_root:
                if package_root.exists():
                    logger.debug(
                        f"Found package config using importlib.resources: {package_root}"
                    )
                    return package_root
        except Exception as e:
            logger.debug(f"importlib.resources method failed: {e}")

        # Method 2: Try relative to __file__
        try:
            file_path = Path(__file__).resolve()
            package_root = file_path.parent.parent / "agents"
            if package_root.exists():
                logger.debug(f"Found package config using __file__: {package_root}")
                return package_root
        except Exception as e:
            logger.debug(f"__file__ method failed: {e}")

        # Method 3: Try sys.modules
        try:
            module = sys.modules.get(self.package_name)
            if module:
                package_root = Path(module.__file__).parent / "agents"
                if package_root.exists():
                    logger.debug(
                        f"Found package config using sys.modules: {package_root}"
                    )
                    return package_root
        except Exception as e:
            logger.debug(f"sys.modules method failed: {e}")

        # Method 4: Development environment fallback
        try:
            current_dir = Path.cwd()
            package_root = current_dir / "src" / self.package_name / "agents"
            if package_root.exists():
                logger.debug(
                    f"Found package config in development environment: {package_root}"
                )
                return package_root
        except Exception as e:
            logger.debug(f"Development environment fallback failed: {e}")

        raise FileNotFoundError(
            f"Could not find package configuration directory for {self.package_name}"
        )

    def initialize(self) -> None:
        """Initialize user configuration directory with default settings"""
        try:
            if not self._should_initialize():
                logger.debug(
                    f"Configuration directory {self.user_config_dir} already exists"
                )
                return

            logger.info(
                f"Initializing configuration directory at {self.user_config_dir}"
            )
            self._create_config_dir()
            self._copy_default_config()

        except Exception as e:
            logger.error(f"Failed to initialize configuration: {str(e)}")
            raise

    def _should_initialize(self) -> bool:
        """Check if initialization is needed"""
        if not self.user_config_dir.exists():
            return True

        # Also check if system.yml exists in agents directory
        system_yml = self.user_config_dir / "agents" / "system.yml"
        return not system_yml.exists()

    def _create_config_dir(self) -> None:
        """Create configuration directory structure"""
        self.user_config_dir.mkdir(parents=True, exist_ok=True)
        (self.user_config_dir / "agents").mkdir(exist_ok=True)

    def _copy_default_config(self) -> None:
        """Copy only the system.yml configuration file from the package to the user directory"""
        system_yml_source = self.package_config_dir / "system.yml"
        if not system_yml_source.exists():
            raise FileNotFoundError(
                f"system.yml not found in package configuration directory: {system_yml_source}"
            )

        destination_agents_dir = self.user_config_dir / "agents"
        destination_system_yml = destination_agents_dir / "system.yml"

        logger.debug(
            f"Copying system.yml from {system_yml_source} to {destination_system_yml}"
        )

        try:
            shutil.copy(system_yml_source, destination_system_yml)
            logger.info("system.yml copied successfully")
        except Exception as e:
            logger.error(f"Error copying system.yml: {e}")
            raise

        # Verify system.yml exists after copy
        if not destination_system_yml.exists():
            logger.error(
                f"system.yml not found at {destination_system_yml} after copy operation"
            )
            raise FileNotFoundError("Failed to copy system.yml")


class ConfigBase:
    def __init__(self, base_dir: Optional[Path] = None):
        self.default_base_dir = base_dir or Path(__file__).parent.parent
        self.user_base_dir = Path(os.path.expanduser("~")) / ".config" / "kagura"
        self._config_cache: Dict[str, Dict[str, Any]] = {}

    def load_yaml_config(self, relative_path: str) -> Dict[str, Any]:
        cache_key = relative_path
        if cache_key in self._config_cache:
            return self._config_cache[cache_key]

        file_path = self.user_base_dir / relative_path
        if not file_path.exists():
            file_path = self.default_base_dir / relative_path
            if not file_path.exists():
                raise FileNotFoundError(f"Configuration file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            config = self.load_yaml(content)
            self._config_cache[cache_key] = config
            return config

    def load_yaml(self, content: str) -> Dict[str, Any]:
        try:
            content = Template(content).safe_substitute(os.environ)
            config = yaml.safe_load(content)
            return config or {}
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML: {str(e)}")
        except Exception as e:
            raise Exception(f"Error loading configuration: {str(e)}")

    @property
    def agent_readme(self) -> str:
        # Try language-specific README first
        readme_path = (
            self.default_base_dir / "agents" / "agent_generator" / "tools" / "README.md"
        )
        if readme_path.exists():
            return readme_path.read_text(encoding="utf-8")

        # Fall back to default English README
        readme_path = self.default_base_dir / "agents" / "README.md"
        return readme_path.read_text(encoding="utf-8")
        if not readme_path.exists():
            raise FileNotFoundError(f"README file not found at {readme_path}")

    @property
    def system_config(self) -> Dict[str, Any]:
        if not hasattr(self, "_system_config"):
            self._system_config = self.load_yaml_config("agents/system.yml")
        return self._system_config

    @property
    def system_instructions(self) -> List[Dict[str, Any]]:
        if not hasattr(self, "_system_instructions"):
            for instruction in self.system_config.get("prompt", {}).get(
                "instructions", []
            ):
                if (
                    isinstance(instruction, dict)
                    and instruction.get("language") == self.system_language
                ):
                    self._system_instructions = instruction.get(
                        "description", ""
                    ).strip()
                    break
                else:
                    default_instruction = instruction.get("description", "").strip()
            if not self._system_instructions:
                self._system_instructions = default_instruction
        return self._system_instructions

    @property
    def system_language(self) -> str:
        return self.system_config.get("system", {}).get("language", "en")

    @property
    def system_memory(self) -> Dict[str, Any]:
        return self.system_config.get("memory", {})

    @property
    def system_memory_message_history(self) -> Dict[str, Any]:
        return self.system_memory.get("message_history", {})

    @property
    def system_memory_history_uuid(self) -> str:
        return self.system_memory.get("history_uuid", "kagura_personal_chat")

    @property
    def system_memory_backend(self) -> Dict[str, Any]:
        return self.system_memory.get("backend", {})

    @property
    def system_llm(self) -> Dict[str, Any]:
        return self.system_config.get("llm", {})

    @property
    def system_backends(self) -> List[str]:
        return self.system_config.get("backends", [])

    def get_system_backend(self, backend_name: str) -> Dict[str, Any]:
        for backend in self.system_backends:
            if backend.get("name") == backend_name:
                return backend

    @property
    def system_llm_model(self) -> str:
        if "model" not in self.system_llm:
            raise ValueError("Missing LLM model in system configuration")
        return self.system_llm.get("model", "")


class AgentConfigManager(ConfigBase):

    def __init__(
        self,
        agent_name: str,
        base_dir: Optional[Path] = None,
    ):
        super().__init__(base_dir)
        self.agent_name = agent_name
        self._models = Models(language=self.system_language)
        self._initialize_state_model()

    def _initialize_state_model(self) -> None:
        if not self.skip_state_model:
            self._check_custom_models_dependencies()
            self._registered_custom_models: Dict = self._models.create_custom_models(
                self.custom_models
            )
            self._state_model: BaseModel = self._models.generate_state_model(
                self.state_fields, self._registered_custom_models
            )

    def _check_custom_models_dependencies(self):
        agent_custom_models = {}
        self._validate_state_fields()

        agent_configs = self._load_agent_configs()
        self._process_custom_models(agent_configs, agent_custom_models)
        self._finalize_state_fields(agent_configs, agent_custom_models)

    def _validate_state_fields(self):
        """Validate that agent names and state field names are provided together."""
        agent_names = []
        agent_state_field_names = []

        for field in self.state_fields:
            if agent_name := field.get("agent_name"):
                agent_names.append(agent_name)
                if state_field_name := field.get("state_field_name", ""):
                    agent_state_field_names.append(state_field_name)

                if len(agent_names) != len(agent_state_field_names):
                    raise ValueError(
                        "Agent name and state field name should be provided together"
                    )

    def _load_agent_configs(self):
        """Load configurations for all agents."""
        agent_configs = {}

        for field in self.state_fields:
            agent_name = field.get("agent_name")
            if agent_name and agent_name not in agent_configs:
                relative_path = f"agents/{agent_name}/state_model.yml"
                agent_configs[agent_name] = self.load_yaml_config(relative_path)

        return agent_configs

    def _process_custom_models(self, agent_configs, agent_custom_models):
        """Extract custom model information from agent configurations."""
        for agent_name, config in agent_configs.items():
            if custom_models := config.get("custom_models"):
                agent_custom_models[agent_name] = {
                    model["name"]: model for model in custom_models
                }

    def _finalize_state_fields(self, agent_configs, agent_custom_models):
        """Match and append custom models to the state fields."""
        all_state_fields = []
        all_custom_models = []
        for field in self.state_fields:
            agent_name = field.get("agent_name")
            state_field_name = field.get("state_field_name")

            if not agent_name or not state_field_name:
                all_state_fields.append(field)
                continue

            config = agent_configs.get(agent_name, {})
            processing_state_fields = config.get("state_fields", [])

            for state_field in processing_state_fields:
                if state_field.get("name") == state_field_name:
                    custom_model_type = state_field.get("type")
                    agent_custom_models_dict = agent_custom_models.get(agent_name)
                    if new_custom_model := map_type(
                        custom_model_type, agent_custom_models_dict
                    ):
                        custom_model = convert_typing_to_builtin(new_custom_model)
                        if isinstance(new_custom_model, dict):
                            all_custom_models.append(new_custom_model)
                        else:
                            for c in custom_model:
                                all_custom_models.append(c)

                    else:
                        custom_model = agent_custom_models.get(agent_name).get(
                            custom_model_type
                        )
                        if custom_model:
                            all_custom_models.append(custom_model)
                    all_state_fields.append(state_field)

        if all_custom_models:
            combined_custom_models = self.custom_models + all_custom_models
            self._custom_models = combined_custom_models
            self._state_fields = all_state_fields

    @property
    def models(self) -> Models:
        return self._models

    @property
    def state_model_config(self) -> Dict[str, Any]:
        if not hasattr(self, "_state_model_config"):
            relative_path = f"agents/{self.agent_name}/state_model.yml"
            self._state_model_config = self.load_yaml_config(relative_path)
        return self._state_model_config

    @property
    def agent_config(self) -> Dict[str, Any]:
        if not hasattr(self, "_agent_config"):
            relative_path = f"agents/{self.agent_name}/agent.yml"
            self._agent_config = self.load_yaml_config(relative_path)
        return self._agent_config

    @property
    def state_model(self) -> BaseModel:
        if not hasattr(self, "_state_model"):
            self._initialize_state_model()
        return self._state_model

    @property
    def registered_custom_models(self) -> Dict[str, Type[Any]]:
        if not hasattr(self, "_registered_custom_models"):
            self._initialize_state_model()
        return self._registered_custom_models

    @property
    def response_model(self) -> Union[Type[BaseModel], None]:
        if not self.response_fields:
            return None
        return self._models.generate_response_fields_model(
            self.state_fields,
            self.response_fields,
            registered_custom_models=self.registered_custom_models,
        )

    @property
    def description(self) -> str:
        if hasattr(self, "_description"):
            desc_entry = self.state_model_config.get("description", [])
            if (
                isinstance(desc_entry, dict)
                and desc_entry.get("language") == self.system_language
            ):
                self._description = desc_entry.get("text", "")
            else:
                self._description = self.state_model_config.get("description", "")
        return self._description

    @property
    def state_fields(self) -> List[Dict[str, Any]]:
        if not hasattr(self, "_state_fields"):
            self._state_fields = self.state_model_config.get("state_fields", [])
        return self._state_fields

    @property
    def custom_models(self) -> List[Dict[str, Any]]:
        if not hasattr(self, "_custom_models"):
            self._custom_models = self.state_model_config.get("custom_models", [])
        return self._custom_models

    @property
    def agent_llm_config(self) -> Dict[str, Any]:
        if not hasattr(self, "_agent_llm_config"):
            self._agent_llm_config = self.agent_config.get("llm", {})
        return self._agent_llm_config

    @property
    def llm_stream(self) -> bool:
        return self.agent_llm_config.get("stream", False)

    @property
    def skip_llm_invoke(self) -> bool:
        if self.is_workflow:
            self._skip_llm_invoke = True
        elif not hasattr(self, "_skip_llm_invoke"):
            self._skip_llm_invoke = self.agent_config.get("skip_llm_invoke", False)
        if (
            not self.prompt_template
        ):  # Override skip_llm_invoke if prompt is not available
            self._skip_llm_invoke = True

        return self._skip_llm_invoke

    @property
    def llm_model(self) -> Union[str, None]:
        if not hasattr(self, "_llm_model"):
            llm_model = self.agent_llm_config.get("model", None)
            self._llm_model = llm_model if llm_model else self.system_llm_model
        return self._llm_model

    @property
    def skip_state_model(self) -> bool:
        if self.is_workflow:
            return True
        return self.agent_config.get("skip_state_model", False)

    @property
    def llm_max_tokens(self) -> int:
        llm_max_tokens = self.agent_llm_config.get("max_tokens", None)
        return (
            llm_max_tokens
            if llm_max_tokens is not None
            else self.system_llm.get("max_tokens", 4096)
        )

    @property
    def llm_retry_count(self) -> int:
        llm_retry_count = self.agent_llm_config.get("retry_count", None)
        return (
            llm_retry_count
            if llm_retry_count is not None
            else self.system_llm.get("retry_count", 3)
        )

    @property
    def response_fields(self) -> List[str]:
        return self.agent_config.get("response_fields", [])

    @property
    def instructions(self) -> List[Dict[str, Any]]:
        if not hasattr(self, "_instructions"):
            for instruction in self.agent_config.get("instructions", []):
                if (
                    isinstance(instruction, dict)
                    and instruction.get("language") == self.system_language
                ):
                    self._instructions = instruction.get("description", "").strip()
                    break
            else:
                self._instructions = self.system_instructions
        return self._instructions

    @property
    def prompt_template(self) -> List[Dict[str, Any]]:
        if not hasattr(self, "_prompt_template"):
            default_prompt = ""
            self._prompt_template = []
            prompt = self.agent_config.get("prompt", [])
            for prompt_entry in prompt:
                if (
                    isinstance(prompt_entry, dict)
                    and prompt_entry.get("language") == self.system_language
                ):
                    self._prompt_template = prompt_entry.get("template", "").strip()
                if (
                    isinstance(prompt_entry, dict)
                    and prompt_entry.get("language") == "en"
                ):
                    default_prompt = prompt_entry.get("template", "").strip()
            if not self._prompt_template and default_prompt:
                self._prompt_template = default_prompt

        return self._prompt_template

    @property
    def custom_tool(self) -> Union[str, None]:
        if not hasattr(self, "_custom_tool"):
            self._custom_tool = self.agent_config.get("custom_tool", None)
        return self._custom_tool

    @property
    def pre_custom_tool(self) -> Union[str, None]:
        if not hasattr(self, "_pre_custom_tool"):
            self._pre_custom_tool = self.agent_config.get("pre_custom_tool", None)
        return self._pre_custom_tool

    @property
    def post_custom_tool(self) -> Union[str, None]:
        if not hasattr(self, "_post_custom_tool"):
            self._post_custom_tool = self.agent_config.get("post_custom_tool", None)
        return self._post_custom_tool

    @post_custom_tool.setter
    def post_custom_tool(self, value: str):
        self._post_custom_tool = value

    @property
    def is_workflow(self) -> bool:
        return len(self.nodes) > 0 and len(self.edges) > 0

    @property
    def edges(self) -> List[Dict[str, str]]:
        return self.agent_config.get("edges", [])

    @property
    def state_field_bindings(self) -> List[Dict[str, str]]:
        return self.agent_config.get("state_field_bindings", [])

    @property
    def nodes(self) -> List[str]:
        return self.agent_config.get("nodes", [])

    @property
    def entry_point(self) -> str:
        return self.agent_config.get("entry_point")

    @property
    def workflow_state_model(self) -> Optional[BaseModel]:
        """Generate a combined state model from all nodes in the workflow"""
        if not self.is_workflow:
            return None

        if not hasattr(self, "_workflow_state_model"):
            all_state_fields = []
            all_custom_models = []
            node_configs = {}
            node_custom_models = {}

            # First pass: Collect all configs and validate
            for node_name in self.nodes:
                try:
                    node_config = self.load_yaml_config(
                        f"agents/{node_name}/state_model.yml"
                    )
                    node_configs[node_name] = node_config

                    # Process custom models for this node
                    if custom_models := node_config.get("custom_models", []):
                        node_custom_models[node_name] = {
                            model["name"]: model for model in custom_models
                        }

                except Exception as e:
                    raise ConfigError(
                        f"Error loading state model for node {node_name}: {str(e)}"
                    )

            # Second pass: Process state fields and their dependencies
            for node_name, node_config in node_configs.items():
                if state_fields := node_config.get("state_fields", []):
                    for field in state_fields:
                        # Handle fields that reference other agents
                        if referenced_agent := field.get("agent_name"):
                            if referenced_agent not in node_configs:
                                raise ConfigError(
                                    f"Referenced agent {referenced_agent} not found in workflow"
                                )

                            referenced_config = node_configs[referenced_agent]
                            referenced_fields = referenced_config.get(
                                "state_fields", []
                            )

                            state_field_name = field.get("state_field_name")
                            if not state_field_name:
                                raise ConfigError(
                                    f"state_field_name must be provided when referencing agent {referenced_agent}"
                                )

                            # Find the referenced field
                            referenced_field = next(
                                (
                                    f
                                    for f in referenced_fields
                                    if f.get("name") == state_field_name
                                ),
                                None,
                            )
                            if not referenced_field:
                                raise ConfigError(
                                    f"Referenced field {state_field_name} not found in agent {referenced_agent}"
                                )

                            # Check if the field uses a custom model
                            field_type = referenced_field.get("type")
                            if custom_model := node_custom_models.get(
                                referenced_agent, {}
                            ).get(field_type):
                                if not any(
                                    m["name"] == custom_model["name"]
                                    for m in all_custom_models
                                ):
                                    all_custom_models.append(custom_model)

                            if not any(
                                f.get("name") == state_field_name
                                for f in all_state_fields
                            ):
                                all_state_fields.append(referenced_field)

                        else:
                            # Handle regular fields
                            field_type = field.get("type")
                            if custom_model := node_custom_models.get(
                                node_name, {}
                            ).get(field_type):
                                if not any(
                                    m["name"] == custom_model["name"]
                                    for m in all_custom_models
                                ):
                                    all_custom_models.append(custom_model)

                            if not any(
                                f.get("name") == field.get("name")
                                for f in all_state_fields
                            ):
                                all_state_fields.append(field)

            # Create combined state model
            try:
                registered_custom_models = self._models.create_custom_models(
                    all_custom_models
                )
                self._workflow_state_model = self._models.generate_state_model(
                    all_state_fields, registered_custom_models
                )
            except Exception as e:
                raise ConfigError(f"Error generating workflow state model: {str(e)}")

        return self._workflow_state_model

    @property
    def conditional_edges(self) -> List[Dict[str, Any]]:
        return self.agent_config.get("conditional_edges", [])
