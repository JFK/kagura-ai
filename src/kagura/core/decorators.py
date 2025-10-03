"""
Decorators to convert functions into AI agents
"""
from typing import TypeVar, Callable, ParamSpec, Awaitable, overload, Any
import functools
import inspect
from .llm import LLMConfig, call_llm
from .prompt import extract_template, render_prompt
from .parser import parse_response

P = ParamSpec('P')
T = TypeVar('T')


@overload
def agent(
    fn: Callable[P, Awaitable[T]],
    *,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    **kwargs: Any
) -> Callable[P, Awaitable[T]]: ...

@overload
def agent(
    fn: None = None,
    *,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    **kwargs: Any
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]: ...

def agent(
    fn: Callable[P, Awaitable[T]] | None = None,
    *,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    **kwargs: Any
) -> Callable[P, Awaitable[T]] | Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """
    Convert a function into an AI agent.

    Args:
        fn: Function to convert
        model: LLM model to use
        temperature: Temperature for LLM
        **kwargs: Additional LLM parameters

    Returns:
        Decorated async function

    Example:
        @agent
        async def hello(name: str) -> str:
            '''Say hello to {{ name }}'''
            pass

        result = await hello("World")
    """
    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        # Extract template from docstring
        template_str = extract_template(func)

        # Create LLM config
        config = LLMConfig(model=model, temperature=temperature)

        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs_inner: P.kwargs) -> T:
            # Get function signature
            sig = inspect.signature(func)
            bound = sig.bind(*args, **kwargs_inner)
            bound.apply_defaults()

            # Render prompt with arguments
            prompt = render_prompt(template_str, **bound.arguments)

            # Call LLM
            response = await call_llm(prompt, config, **kwargs)

            # Parse response based on return type annotation
            return_type = sig.return_annotation
            if return_type != inspect.Signature.empty and return_type != str:
                return parse_response(response, return_type)  # type: ignore

            return response  # type: ignore

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
