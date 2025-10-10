"""
Advanced Workflow Decorators - Chain, Parallel, Stateful

This module provides advanced workflow patterns for multi-agent orchestration:
- @workflow.chain: Sequential execution pipeline
- @workflow.parallel: Parallel execution with asyncio.gather
- @workflow.stateful: Pydantic-based state management (LangGraph-like)
"""

from __future__ import annotations

import asyncio
import functools
import inspect
from typing import Any, Awaitable, Callable, ParamSpec, TypeVar

from pydantic import BaseModel

P = ParamSpec("P")
T = TypeVar("T")
State = TypeVar("State", bound=BaseModel)


class WorkflowChain:
    """Chain decorator for sequential workflow execution.

    Example:
        @workflow.chain
        async def research_pipeline(topic: str) -> str:
            '''Research pipeline for {{ topic }}'''
            keywords = await extract_keywords(topic)
            results = await search_web(keywords)
            summary = await summarize(results)
            return summary
    """

    def __call__(self, fn: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        """Decorate a function as a chain workflow.

        Args:
            fn: Async function to decorate

        Returns:
            Decorated async function
        """
        sig = inspect.signature(fn)

        @functools.wraps(fn)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # Bind arguments
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            # Execute the workflow function (sequential execution)
            result = await fn(*bound.args, **bound.kwargs)

            return result  # type: ignore

        # Mark as chain workflow
        wrapper._is_workflow_chain = True  # type: ignore
        wrapper._workflow_name = fn.__name__  # type: ignore
        wrapper._workflow_signature = sig  # type: ignore
        wrapper._workflow_docstring = fn.__doc__ or ""  # type: ignore

        return wrapper  # type: ignore


class WorkflowParallel:
    """Parallel decorator for concurrent workflow execution.

    Example:
        @workflow.parallel
        async def multi_model_comparison(prompt: str) -> dict[str, str]:
            '''Compare models for {{ prompt }}'''
            gpt4_task = gpt4_agent(prompt)
            claude_task = claude_agent(prompt)

            # Results are automatically gathered in parallel
            results = await asyncio.gather(gpt4_task, claude_task)

            return {
                "gpt4": results[0],
                "claude": results[1]
            }
    """

    def __call__(self, fn: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        """Decorate a function as a parallel workflow.

        Args:
            fn: Async function to decorate

        Returns:
            Decorated async function with parallel execution support
        """
        sig = inspect.signature(fn)

        @functools.wraps(fn)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # Bind arguments
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            # Execute the workflow function
            # The function itself should use asyncio.gather for parallel execution
            result = await fn(*bound.args, **bound.kwargs)

            return result  # type: ignore

        # Mark as parallel workflow
        wrapper._is_workflow_parallel = True  # type: ignore
        wrapper._workflow_name = fn.__name__  # type: ignore
        wrapper._workflow_signature = sig  # type: ignore
        wrapper._workflow_docstring = fn.__doc__ or ""  # type: ignore

        return wrapper  # type: ignore


class WorkflowStateful:
    """Stateful decorator for Pydantic-based state management.

    This provides LangGraph-like stateful workflows where state is a Pydantic model
    that gets passed through and modified by the workflow.

    Example:
        from pydantic import BaseModel

        class ResearchState(BaseModel):
            topic: str
            keywords: list[str] = []
            search_results: list[str] = []
            summary: str = ""

        @workflow.stateful(state_class=ResearchState)
        async def research_flow(state: ResearchState) -> ResearchState:
            '''Research workflow with state management'''
            # Extract keywords
            state.keywords = await extract_keywords(state.topic)

            # Search
            state.search_results = await search(state.keywords)

            # Summarize
            state.summary = await summarize(state.search_results)

            return state
    """

    def __init__(self, state_class: type[State]) -> None:
        """Initialize stateful workflow decorator.

        Args:
            state_class: Pydantic BaseModel class for state management
        """
        if not issubclass(state_class, BaseModel):
            raise TypeError(
                f"state_class must be a Pydantic BaseModel, got {state_class}"
            )
        self.state_class = state_class

    def __call__(
        self, fn: Callable[[State], Awaitable[State]]
    ) -> Callable[[State], Awaitable[State]]:
        """Decorate a function as a stateful workflow.

        Args:
            fn: Async function that takes and returns state

        Returns:
            Decorated async function with state validation
        """
        sig = inspect.signature(fn)
        state_class = self.state_class

        @functools.wraps(fn)
        async def wrapper(state: State) -> State:
            # Validate input state
            if not isinstance(state, state_class):
                raise TypeError(
                    f"Expected state of type {state_class.__name__}, "
                    f"got {type(state).__name__}"
                )

            # Execute the workflow function
            result_state = await fn(state)

            # Validate output state
            if not isinstance(result_state, state_class):
                raise TypeError(
                    f"Workflow must return {state_class.__name__}, "
                    f"got {type(result_state).__name__}"
                )

            return result_state

        # Mark as stateful workflow
        wrapper._is_workflow_stateful = True  # type: ignore
        wrapper._workflow_name = fn.__name__  # type: ignore
        wrapper._workflow_signature = sig  # type: ignore
        wrapper._workflow_docstring = fn.__doc__ or ""  # type: ignore
        wrapper._workflow_state_class = state_class  # type: ignore

        return wrapper  # type: ignore


# Create singleton instances for decorator usage
chain = WorkflowChain()
parallel = WorkflowParallel()
stateful = WorkflowStateful


# Helper function for parallel execution (optional utility)
async def run_parallel(**tasks: Awaitable[Any]) -> dict[str, Any]:
    """Execute multiple async tasks in parallel and return results as dict.

    This is a convenience function for @workflow.parallel decorated functions.

    Args:
        **tasks: Named awaitable tasks to execute in parallel

    Returns:
        Dictionary mapping task names to their results

    Example:
        @workflow.parallel
        async def compare_models(prompt: str) -> dict[str, str]:
            results = await run_parallel(
                gpt4=gpt4_agent(prompt),
                claude=claude_agent(prompt),
                gemini=gemini_agent(prompt)
            )
            return results
    """
    task_names = list(tasks.keys())
    task_awaitables = list(tasks.values())

    # Execute all tasks in parallel
    results = await asyncio.gather(*task_awaitables)

    # Return as dictionary
    return dict(zip(task_names, results))
