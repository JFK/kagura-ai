"""Core functionality for Kagura AI"""

from typing import Awaitable, Callable, Optional, ParamSpec, TypeVar, overload

from . import workflow as workflow_module
from .cache import LLMCache
from .decorators import agent, tool
from .decorators import workflow as workflow_decorator
from .llm import get_llm_cache, set_llm_cache
from .model_selector import ModelConfig, ModelSelector, TaskType
from .parallel import parallel_gather, parallel_map, parallel_map_unordered
from .registry import AgentRegistry, agent_registry
from .tool_registry import ToolRegistry, tool_registry
from .workflow_registry import WorkflowRegistry, workflow_registry

P = ParamSpec("P")
T = TypeVar("T")


# Create workflow namespace with both basic decorator and advanced patterns
class WorkflowNamespace:
    """Workflow namespace providing basic and advanced workflow patterns.

    Usage:
        @workflow  # Basic workflow
        async def my_workflow(): ...

        @workflow.chain  # Sequential chain
        async def pipeline(): ...

        @workflow.parallel  # Parallel execution
        async def concurrent(): ...

        @workflow.stateful(state_class=MyState)  # Stateful workflow
        async def stateful_flow(state): ...
    """

    def __call__(self, *args, **kwargs):  # type: ignore
        """Basic workflow decorator (backward compatible)."""
        return workflow_decorator(*args, **kwargs)

    # Advanced workflow patterns
    chain = workflow_module.chain
    parallel = workflow_module.parallel
    stateful = workflow_module.stateful
    run_parallel = staticmethod(workflow_module.run_parallel)


# Create singleton workflow namespace
workflow = WorkflowNamespace()

__all__ = [
    "agent",
    "tool",
    "workflow",
    "agent_registry",
    "AgentRegistry",
    "tool_registry",
    "ToolRegistry",
    "workflow_registry",
    "WorkflowRegistry",
    # LLM Cache
    "LLMCache",
    "get_llm_cache",
    "set_llm_cache",
    # Model Selection
    "ModelSelector",
    "ModelConfig",
    "TaskType",
    # Parallel Execution
    "parallel_gather",
    "parallel_map",
    "parallel_map_unordered",
]
