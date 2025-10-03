import json
import traceback
from pathlib import Path
from typing import Any, AsyncGenerator, Callable, Dict, List, Tuple, Union, Generator

from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel

from .config import AgentConfigManager, ConfigBase
from .models import (
    AGENT,
    ModelRegistry,
    convert_model_to_input_schema,
    BaseResponseModel,
)
from .prompts import BasePrompt
from .utils.import_function import import_function
from .utils.llm import LLM
from .utils.logger import get_logger

logger = get_logger(__name__)


class AgentError(Exception):
    pass


class Agent(AgentConfigManager):
    def __init__(
        self,
        agent_name: str,
        state: Union[BaseModel, Dict[str, Any], str, None] = None,
    ):
        super().__init__(agent_name)
        self.agent_name = agent_name
        self._validte_agent()
        self._initialize_state(state)

    def _validte_agent(self) -> None:
        # Prepare the agent directory path
        agent_dir_path = f"agents/{self.agent_name}"

        # Test that the workflow is existing
        message = f"""
        Workflow {agent_dir_path}/agent.yml in not found.
        Please create the agent.yml
        """
        assert self.agent_config, message

        if self.response_fields:
            fields = set(self.response_fields)
            all_state_fields = set(self.state_model.model_fields.keys())
            assert fields.issubset(
                all_state_fields
            ), f"Fields {fields - all_state_fields} are not present in state model"

    def _initialize_state(self, state: Union[BaseModel, Dict[str, Any], str, None]):
        if self.is_workflow:
            if isinstance(state, Dict):
                self._state = self.workflow_state_model(**state)
            elif state is not None and isinstance(state, BaseModel):
                self._state = self.workflow_state_model(**state.model_dump())
            elif state is None:
                raise AgentError("State is required for workflow")
            return

        if state is not None and isinstance(state, str):
            self._state = BaseResponseModel.model_validate({"QUERY": state})
        elif state is not None and isinstance(state, dict):
            self._state = self.state_model(**state)
        elif state is not None and isinstance(state, BaseModel):
            update_state_fields = {}
            state_fields_names = {field["name"] for field in self.state_fields}
            for key, value in state.model_dump().items():
                if key in state_fields_names:
                    update_state_fields[key] = value
            self._state = self.state_model(**update_state_fields)

    def _import_pre_custom_tool(self) -> Union[Callable, None]:
        return (
            import_function(self.pre_custom_tool, self.agent_name)
            if self.pre_custom_tool
            else None
        )

    def _import_post_custom_tool(self) -> Union[Callable, None]:
        if self.custom_tool:
            self.post_custom_tool = self._custom_tool
        return (
            import_function(self.post_custom_tool, self.agent_name)
            if self.post_custom_tool
            else None
        )

    def _get_conditional_edges(
        self,
    ) -> Generator[Tuple[str, Callable[..., Any], Dict[str, Any]], None, None]:
        if conditional_edges := self.conditional_edges:
            for edges in conditional_edges:
                for node_name, cond_info in edges.items():
                    condition_function_path = cond_info["condition_function"]
                    condition_function = import_function(
                        condition_function_path, self.agent_name
                    )
                    conditions = cond_info["conditions"]
                    yield node_name, condition_function, conditions

    @classmethod
    def list_agents(cls) -> List[Dict[str, Any]]:
        """List all available agents in user and package directories"""
        agents = []
        config = ConfigBase()

        user_agents_dir = config.user_base_dir / "agents"
        if user_agents_dir.exists():
            agents.extend(cls._scan_agents_directory(user_agents_dir))

        default_agents_dir = config.default_base_dir / "agents"
        if default_agents_dir.exists():
            agents.extend(cls._scan_agents_directory(default_agents_dir))

        return agents

    @classmethod
    def _scan_agents_directory(cls, directory: Path) -> List[Dict[str, Any]]:
        """Scan directory for valid agents"""
        agents = []
        for agent_dir in directory.iterdir():
            if not agent_dir.is_dir():
                continue

            agent_yml = agent_dir / "agent.yml"
            if not agent_yml.exists():
                continue

            try:
                agent = cls.assigner(agent_dir.name)
                agents_config_dict = {
                    "name": agent.agent_name,
                    "description": agent.description,
                    "type": (
                        str(agent.agent_type)
                        if hasattr(agent, "agent_type")
                        else "unknown"
                    ),
                    "response_schema": {},
                    "input_schema": {},
                    "path": str(agent_dir),
                }
                if not agent.skip_state_model:
                    input_fields = agent.input_fields
                    response_fields = agent.response_fields
                    agents_config_dict.update(
                        {
                            "response_schema": convert_model_to_input_schema(
                                agent.state_model.model_fields, response_fields
                            ),
                            "input_schema": convert_model_to_input_schema(
                                agent.state_model.model_fields, input_fields
                            ),
                        }
                    )
                if agent.is_workflow:
                    agents_config_dict["workflow"] = {
                        "entry_point": agent.entry_point,
                        "nodes": agent.nodes,
                        "edges": agent.edges,
                        "state_field_bindings": agent.state_field_bindings,
                        "conditional_edges": agent.conditional_edges,
                    }
                agents.append(agents_config_dict)
            except Exception as e:
                logger.warning(f"Failed to load agent {agent_dir.name}: {e}")

        return agents

    @classmethod
    def assigner(
        cls,
        agent_name: str,
        state: Union[BaseModel, Dict[str, Any], None] = None,
    ):
        return cls(agent_name, state)

    @property
    def state(self) -> BaseResponseModel:
        if not isinstance(self._state, BaseResponseModel):
            self._state = BaseResponseModel(**self._state.model_dump())
        return self._state

    @property
    def llm(self) -> LLM:
        if self.llm_model and not self.skip_llm_invoke:
            self._llm = LLM(self.llm_model)
        else:
            self._llm = LLM(self.system_llm_model)
        return self._llm

    @property
    def prompt(self) -> BasePrompt:
        self._prompt = BasePrompt(
            prompt=self.prompt_template,
            response_model=self.response_model,
        )
        return self._prompt

    @property
    def prompt_text(self) -> str:
        return self.prompt.prepare_prompt(**self.state.model_dump())

    def prepare_query(self, query: str, instructions: str = "") -> Dict[str, Any]:
        return {
            "instructions": self.instructions if instructions != "" else instructions,
            "prompt": query,
        }

    def response(self) -> Dict[str, Any]:
        return {field: getattr(self.state, field, "") for field in self.response_fields}

    def json(self) -> str:
        return json.dumps(self.response(), indent=4, ensure_ascii=False)

    def _get_type_name(self, field_type: type) -> str:
        """Retrieve the name of the custom type from the field type"""
        type_str = str(field_type)  # type annotation as string

        # when __future__.annotations is enabled
        if hasattr(field_type, "__origin__"):  # if __future__.annotations is enabled
            if field_type.__origin__ == list:
                elem_type = field_type.__args__[0]  # get the actual type
                return (
                    elem_type.__name__
                    if hasattr(elem_type, "__name__")
                    else str(elem_type)
                )  # Get the class name directly

        return field_type.__name__ if hasattr(field_type, "__name__") else type_str

    async def llm_ainvoke(self, state: Union[BaseModel, None] = None) -> BaseModel:
        if state is None:
            return BaseResponseModel(ERROR_MESSAGE="State is None", SUCCESS=False)

        for attempt in range(self.llm_retry_count):
            try:
                response_text = await self.llm.ainvoke(
                    self.prompt_text, self.instructions
                )
                response_model = self.prompt.parse_response(response_text)
                response_data = response_model.model_dump()
                model_registry = ModelRegistry()
                converted_data = self.models.convert_model_data(
                    response_data, model_registry
                )
                return state.model_copy(update=converted_data)

            except Exception as e:
                if attempt == self.llm_retry_count - 1:
                    base_state = BaseResponseModel(**state.model_dump())
                    base_state.ERROR_MESSAGE = str(e)
                    base_state.SUCCESS = False
                    return base_state
                continue
        return BaseResponseModel(ERROR_MESSAGE="No attempts succeeded", SUCCESS=False)

    async def _apply_state_bindings(
        self, state: BaseModel, bindings: List[Dict[str, str]], node_name: str
    ) -> BaseModel:  # Return updated state
        state_dict = state.model_dump()

        for binding in bindings:
            from_parts = binding["from"].split(".")
            to_parts = binding["to"].split(".")

            if from_parts[0] != node_name:
                continue

            # Get source value
            if len(from_parts) == 2:
                source = getattr(state, from_parts[1], None)
            elif len(from_parts) == 3:
                custom_model = getattr(state, from_parts[1], None)
                if custom_model is not None:
                    source = getattr(custom_model, from_parts[2], None)

            if source is None:
                continue

            # Update state dictionary
            if len(to_parts) == 2:
                state_dict[to_parts[1]] = source
            elif len(to_parts) == 3:
                if to_parts[1] in state_dict:
                    custom_model = getattr(state, to_parts[1], None)
                    if isinstance(custom_model, BaseModel):
                        model_dict = custom_model.model_dump()
                        model_dict[to_parts[2]] = source
                        state_dict[to_parts[1]] = type(custom_model)(**model_dict)
                        break

        return type(state)(**state_dict)

    def _construct_workflow(self, state: BaseModel) -> CompiledStateGraph:
        """Construct workflow graph from configuration"""
        if not self.is_workflow:
            raise AgentError("Workflow configuration not found")

        graph = StateGraph(type(state))
        graph.set_entry_point(self.entry_point)

        for node_name in self.nodes:

            async def node_function(
                current_state: BaseModel,
                node_name=node_name,
            ) -> Dict[str, Any]:
                try:
                    agent = Agent.assigner(node_name, current_state)
                    agent_state = await agent.execute()
                    if isinstance(agent_state, BaseModel):
                        update_state = await self._apply_state_bindings(
                            agent_state, self.state_field_bindings, node_name
                        )
                        return {**update_state.model_dump(), AGENT: agent}
                    else:
                        raise AgentError(
                            f"Error executing node {node_name}: {agent_state}"
                        )
                except Exception as e:
                    raise AgentError(f"Error executing node {node_name}: {str(e)}")

            graph.add_node(node_name, node_function)

        async def final_node_function(state: BaseModel) -> Dict[str, Any]:
            return {**state.model_dump(), "COMPLETED": True}

        graph.add_node("END", final_node_function)

        # Add regular edges
        for edge in self.edges:
            graph.add_edge(edge["from"], edge["to"])

        # last self.edges is the final edge
        graph.add_edge(self.edges[-1]["to"], "END")

        # Add conditional edges
        for node_name, condition_function, conditions in self._get_conditional_edges():
            update_conditions = {}
            for cond_key, cond_val in conditions.items():
                update_conditions[cond_key] = cond_val

            graph.add_conditional_edges(
                node_name, condition_function, update_conditions
            )

        return graph.compile()

    def _store_input_fields(self):
        """Store input_fields values in INPUT_QUERY"""
        input_data = {}
        for field in self.input_fields:
            if hasattr(self._state, field):
                input_data[field] = getattr(self._state, field)
        setattr(self._state, "INPUT_QUERY", input_data)

    async def execute_workflow(
        self, state: BaseModel
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute workflow if agent is configured as workflow"""
        if not self.is_workflow:
            raise AgentError("Not a workflow configuration")

        workflow = self._construct_workflow(state)

        async for state_update in workflow.astream(state.model_dump()):
            yield state_update

    async def execute(
        self,
        state: Union[BaseModel, Dict, str, None] = None,
        stream: bool = False,
    ) -> Union[
        BaseModel, str, AsyncGenerator[str, None], AsyncGenerator[Dict[str, Any], None]
    ]:
        # If workflow, use workflow execution
        if self.is_workflow:
            return self.execute_workflow(self._state)

        self._initialize_state(state)

        # Store input_fields data
        self._store_input_fields()

        stream = True if self.llm_stream else stream

        try:
            if pre_custom_tool := self._import_pre_custom_tool():
                self._state = await pre_custom_tool(self._state)

            if not self.skip_llm_invoke:
                if stream and not self.response_fields:
                    return self.llm.astream(self.prompt_text, self.instructions)

                if self.response_fields:
                    if stream:
                        raise AgentError("Stream is not supported with response fields")

                    self._state = await self.llm_ainvoke(self._state)

                else:

                    async def llm_response() -> str:
                        response = await self.llm.ainvoke(
                            self.prompt_text, self.instructions
                        )
                        return response

                    response = await llm_response()
                    return response

            if post_custom_tool := self._import_post_custom_tool():
                self._state = await post_custom_tool(self._state)

            # Convert response fields to text
            if self.response_fields:
                if isinstance(self._state, BaseModel):
                    setattr(self._state, "TEXT_OUTPUT", str(self._state))

            return self._state

        except AgentError as e:
            state = BaseResponseModel()
            state.ERROR_MESSAGE = str(e)
            state.SUCCESS = False
            return state

        except Exception as e:
            state = BaseResponseModel()
            state.ERROR_MESSAGE = f"{str(e)}\n{traceback.format_exc()}"
            state.SUCCESS = False
            return state
