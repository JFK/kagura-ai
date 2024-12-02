import json
from typing import Any, AsyncGenerator, Callable, Dict, List, Tuple, Union

from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel

from .config import AgentConfigManager
from .models import AGENT, ModelRegistry
from .prompts import BasePrompt
from .utils.import_function import import_function
from .utils.llm import LLM


class AgentError(Exception):
    pass


class Agent(AgentConfigManager):
    _state: BaseModel

    def __init__(
        self,
        agent_name: str,
        state: Union[BaseModel, Dict[str, Any]] = None,
    ):
        super().__init__(agent_name)
        self.agent_name = agent_name
        self._state = None
        self._llm = None
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

    def _initialize_state(self, state: Union[BaseModel, Dict[str, Any]] = None) -> None:
        if self.is_workflow:
            self._state = state
            return

        if state is not None and isinstance(state, str):

            class StateModel(BaseModel):
                QUERY: str = ""

            self._state = StateModel.model_validate({"QUERY": state})

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
            else self.post_custom_tool
        )

    def _get_conditional_edges(self) -> Tuple[str, Callable, Dict[str, Any]]:
        if conditional_edges := self.conditional_edges:
            for node_name, cond_info in conditional_edges.items():
                condition_function_path = cond_info["condition_function"]
                condition_function = import_function(
                    condition_function_path, self.agent_name
                )
                conditions = cond_info["conditions"]
                yield node_name, condition_function, conditions

    @classmethod
    def assigner(
        cls,
        agent_name: str,
        state: Union[BaseModel, Dict[str, Any]] = None,
    ):
        return cls(agent_name, state)

    @property
    def state(self) -> BaseModel:
        return self._state

    @property
    def llm(self) -> Union[LLM, None]:
        if self._llm is None:
            self._llm = LLM(self.llm_model) if not self.skip_llm_invoke else None
        return self._llm

    @property
    def prompt(self) -> BasePrompt:
        if not hasattr(self, "_prompt"):
            self._prompt = BasePrompt(
                prompt=self.prompt_template,
                response_model=self.response_model,
            )
        return self._prompt

    @property
    def prompt_text(self) -> str:
        return self.prompt.prepare_prompt(**self.state.model_dump())

    def prepare_query(self, query: str, instructions: str = None) -> Dict[str, Any]:
        return {
            "instructions": self.instructions if instructions is None else instructions,
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

    def _convert_value(self, value: any, field_type: type) -> any:
        """Convert the value of a field to the appropriate type"""

        # when the field type is a list of custom types
        if hasattr(field_type, "__origin__") and field_type.__origin__ == list:
            if isinstance(value, list):
                elem_type = field_type.__args__[0]
                type_name = self._get_type_name(elem_type)

                if type_name in self.custom_types:
                    model_class = self.custom_types[type_name]
                    return [
                        (
                            self._convert_to_model(item, model_class)
                            if isinstance(item, dict)
                            else item
                        )
                        for item in value
                    ]
            return value

        type_name = self._get_type_name(field_type)  # get the name of the custom type
        if type_name in self.custom_types and isinstance(value, dict):
            return self._convert_to_model(value, self.custom_types[type_name])

        return value

    async def llm_ainvoke(self, state: BaseModel = None) -> BaseModel:

        if state is None:
            state = self._state

        for attempt in range(self.llm_retry_count):

            try:
                response_text = await self.llm.ainvoke(
                    self.prompt_text, self.instructions
                )
                response_model = self.prompt.parse_response(response_text)
                response_data = response_model.model_dump()
                converted_data = self.models.convert_model_data(
                    response_data, ModelRegistry
                )
                return state.model_copy(update=converted_data)

            except Exception as e:
                if attempt == self.llm_retry_count - 1:
                    state.ERROR_MESSAGE = str(e)
                    state.SUCCESS = False
                    raise AgentError(
                        f"Error after {self.llm_retry_count} attempts: {str(e)}"
                    )
                continue

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
                    update_state = await self._apply_state_bindings(
                        agent_state, self.state_field_bindings, node_name
                    )
                    return {**update_state.model_dump(), AGENT: agent}
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

    async def execute_workflow(
        self, state: Union[BaseModel, str, Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute workflow if agent is configured as workflow"""
        if not self.is_workflow:
            raise AgentError("Not a workflow configuration")

        if isinstance(state, Dict):
            state = self.workflow_state_model(**state)

        elif state is not None and isinstance(state, BaseModel):
            state = self.workflow_state_model(**state.model_dump())

        elif state is None:
            state = self.workflow_state_model()

        workflow = self._construct_workflow(state)

        async for state_update in workflow.astream(state.model_dump()):
            yield state_update

    async def execute(
        self,
        state: Union[BaseModel, Dict, str] = None,
        stream: bool = False,
    ) -> Union[BaseModel, str, AsyncGenerator[str, None]]:

        # If workflow, use workflow execution
        if self.is_workflow:
            return self.execute_workflow(self._state)

        self._initialize_state(state)

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

                    self._state = await self.llm_ainvoke()

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

            self._state = self.models.check_state_error(self._state)
            return self._state

        except AgentError as e:
            self._state.ERROR_MESSAGE = str(e)
            self._state.SUCCESS = False
            return self._state

        except Exception as e:
            import traceback

            self._state.ERROR_MESSAGE = f"{str(e)}\n{traceback.format_exc()}"
            self._state.SUCCESS = False
            return self._state
