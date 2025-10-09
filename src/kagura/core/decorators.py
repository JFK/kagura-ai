"""
Decorators to convert functions into AI agents
"""
import functools
import inspect
from pathlib import Path
from typing import Any, Awaitable, Callable, Optional, ParamSpec, TypeVar, overload

from .llm import LLMConfig, call_llm
from .memory import MemoryManager
from .parser import parse_response
from .prompt import extract_template, render_prompt
from .registry import agent_registry

P = ParamSpec('P')
T = TypeVar('T')


@overload
def agent(
    fn: Callable[P, Awaitable[T]],
    *,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    enable_memory: bool = False,
    persist_dir: Optional[Path] = None,
    max_messages: int = 100,
    **kwargs: Any
) -> Callable[P, Awaitable[T]]: ...

@overload
def agent(
    fn: None = None,
    *,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    enable_memory: bool = False,
    persist_dir: Optional[Path] = None,
    max_messages: int = 100,
    **kwargs: Any
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]: ...

def agent(
    fn: Callable[P, Awaitable[T]] | None = None,
    *,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    enable_memory: bool = False,
    persist_dir: Optional[Path] = None,
    max_messages: int = 100,
    **kwargs: Any
) -> Callable[P, Awaitable[T]] | Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """
    Convert a function into an AI agent.

    Args:
        fn: Function to convert
        model: LLM model to use
        temperature: Temperature for LLM
        enable_memory: Enable memory management
        persist_dir: Directory for persistent memory storage
        max_messages: Maximum messages in context memory
        **kwargs: Additional LLM parameters

    Returns:
        Decorated async function

    Example:
        @agent
        async def hello(name: str) -> str:
            '''Say hello to {{ name }}'''
            pass

        result = await hello("World")

        # With memory
        @agent(enable_memory=True)
        async def assistant(query: str, memory: MemoryManager) -> str:
            '''Answer: {{ query }}'''
            memory.add_message("user", query)
            return "response"
    """
    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        # Extract template from docstring
        template_str = extract_template(func)

        # Create LLM config
        config = LLMConfig(model=model, temperature=temperature)

        # Get function signature to check for memory parameter
        sig = inspect.signature(func)
        has_memory_param = "memory" in sig.parameters

        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs_inner: P.kwargs) -> T:
            # Create and inject memory if enabled
            if enable_memory and has_memory_param:
                memory = MemoryManager(
                    agent_name=func.__name__,
                    persist_dir=persist_dir,
                    max_messages=max_messages,
                )
                # Inject memory into kwargs before binding
                kwargs_inner = dict(kwargs_inner)  # type: ignore
                kwargs_inner["memory"] = memory  # type: ignore

            # Get function signature and bind arguments
            bound = sig.bind(*args, **kwargs_inner)
            bound.apply_defaults()

            # Render prompt with arguments (excluding memory from template)
            template_args = {
                k: v for k, v in bound.arguments.items() if k != "memory"
            }
            prompt = render_prompt(template_str, **template_args)

            # Call LLM
            response = await call_llm(prompt, config, **kwargs)

            # Parse response based on return type annotation
            return_type = sig.return_annotation
            if return_type != inspect.Signature.empty and return_type is not str:
                return parse_response(response, return_type)  # type: ignore

            return response  # type: ignore

        # Mark as agent for MCP discovery
        wrapper._is_agent = True  # type: ignore
        wrapper._agent_config = config  # type: ignore
        wrapper._agent_template = template_str  # type: ignore
        wrapper._enable_memory = enable_memory  # type: ignore

        # Register in global registry
        agent_name = func.__name__
        try:
            agent_registry.register(agent_name, wrapper)  # type: ignore
        except ValueError:
            # Agent already registered (e.g., in tests), skip
            pass

        return wrapper  # type: ignore

    return decorator if fn is None else decorator(fn)


@overload
def tool(fn: Callable[P, T]) -> Callable[P, T]: ...

@overload
def tool(fn: None = None) -> Callable[[Callable[P, T]], Callable[P, T]]: ...

def tool(fn: Callable[P, T] | None = None) -> Callable[P, T] | Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Convert a function into a tool (non-LLM function).

    Stub implementation.
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        # Stub
        return func

    return decorator if fn is None else decorator(fn)


@overload
def workflow(fn: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]: ...

@overload
def workflow(fn: None = None) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]: ...

def workflow(fn: Callable[P, Awaitable[T]] | None = None) -> Callable[P, Awaitable[T]] | Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """
    Convert a function into a workflow (multi-agent orchestration).

    Stub implementation.
    """
    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        # Stub
        return func

    return decorator if fn is None else decorator(fn)
