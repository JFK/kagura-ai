"""
Decorators to convert functions into AI agents
"""

import functools
import inspect
from pathlib import Path
from typing import Any, Awaitable, Callable, Optional, ParamSpec, TypeVar, overload

from .compression import CompressionPolicy
from .llm import LLMConfig, call_llm
from .memory import MemoryManager
from .parser import parse_response
from .prompt import extract_template, render_prompt
from .registry import agent_registry
from .tool_registry import tool_registry
from .workflow_registry import workflow_registry

P = ParamSpec("P")
T = TypeVar("T")


def _convert_tools_to_llm_format(tools: list[Callable]) -> list[dict[str, Any]]:
    """Convert Python tool functions to LiteLLM tools format.

    Args:
        tools: List of tool functions

    Returns:
        List of tool dictionaries in OpenAI tools format
    """
    llm_tools = []
    for tool in tools:
        sig = inspect.signature(tool)

        # Build parameters schema
        properties: dict[str, Any] = {}
        required: list[str] = []

        for param_name, param in sig.parameters.items():
            # Convert Python type annotations to JSON schema types
            param_type = "string"  # default
            if param.annotation != inspect.Parameter.empty:
                if param.annotation in (int, type(1)):
                    param_type = "integer"
                elif param.annotation in (float, type(1.0)):
                    param_type = "number"
                elif param.annotation in (bool, type(True)):
                    param_type = "boolean"
                elif param.annotation in (list, type([])):
                    param_type = "array"
                elif param.annotation in (dict, type({})):
                    param_type = "object"

            properties[param_name] = {
                "type": param_type,
                "description": f"{param_name} parameter",
            }

            # Mark as required if no default value
            if param.default == inspect.Parameter.empty:
                required.append(param_name)

        # Get function description from docstring
        description = tool.__doc__ or tool.__name__
        if description:
            description = description.strip().split("\n")[0]  # First line only

        llm_tools.append(
            {
                "type": "function",
                "function": {
                    "name": tool.__name__,
                    "description": description,
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required,
                    },
                },
            }
        )

    return llm_tools


@overload
def agent(
    fn: Callable[P, Awaitable[T]],
    *,
    config: Optional[LLMConfig] = None,
    model: str = "gpt-5-mini",
    temperature: float = 0.7,
    enable_memory: bool = False,
    persist_dir: Optional[Path] = None,
    max_messages: int = 100,
    tools: Optional[list[Callable]] = None,
    enable_multimodal_rag: bool = False,
    rag_directory: Optional[Path] = None,
    rag_cache_size_mb: int = 100,
    enable_compression: bool = True,
    compression_policy: Optional[CompressionPolicy] = None,
    enable_telemetry: bool = True,
    **kwargs: Any,
) -> Callable[P, Awaitable[T]]: ...


@overload
def agent(
    fn: None = None,
    *,
    config: Optional[LLMConfig] = None,
    model: str = "gpt-5-mini",
    temperature: float = 0.7,
    enable_memory: bool = False,
    persist_dir: Optional[Path] = None,
    max_messages: int = 100,
    tools: Optional[list[Callable]] = None,
    enable_multimodal_rag: bool = False,
    rag_directory: Optional[Path] = None,
    rag_cache_size_mb: int = 100,
    enable_compression: bool = True,
    compression_policy: Optional[CompressionPolicy] = None,
    enable_telemetry: bool = True,
    **kwargs: Any,
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]: ...


def agent(
    fn: Callable[P, Awaitable[T]] | None = None,
    *,
    config: Optional[LLMConfig] = None,
    model: str = "gpt-5-mini",
    temperature: float = 0.7,
    enable_memory: bool = False,
    persist_dir: Optional[Path] = None,
    max_messages: int = 100,
    tools: Optional[list[Callable]] = None,
    enable_multimodal_rag: bool = False,
    rag_directory: Optional[Path] = None,
    rag_cache_size_mb: int = 100,
    enable_compression: bool = True,
    compression_policy: Optional[CompressionPolicy] = None,
    enable_telemetry: bool = True,
    **kwargs: Any,
) -> (
    Callable[P, Awaitable[T]]
    | Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]
):
    """
    Convert a function into an AI agent.

    Args:
        fn: Function to convert
        config: Pre-configured LLMConfig instance (overrides model/temperature)
        model: LLM model to use (ignored if config is provided)
        temperature: Temperature for LLM (ignored if config is provided)
        enable_memory: Enable memory management
        persist_dir: Directory for persistent memory storage
        max_messages: Maximum messages in context memory
        tools: List of tool functions available to the agent
        enable_multimodal_rag: Enable multimodal RAG (requires multimodal extra)
        rag_directory: Directory to index for RAG
            (required if enable_multimodal_rag=True)
        rag_cache_size_mb: Cache size in MB for RAG file loading
        enable_compression: Enable automatic context compression (default: True)
        compression_policy: Compression configuration (default: CompressionPolicy())
        enable_telemetry: Enable automatic telemetry recording (default: True)
        **kwargs: Additional LLM parameters

    Returns:
        Decorated async function

    Example:
        @agent
        async def hello(name: str) -> str:
            '''Say hello to {{ name }}'''
            pass

        result = await hello("World")

        # With memory (compression enabled by default)
        @agent(enable_memory=True)
        async def assistant(query: str, memory: MemoryManager) -> str:
            '''Answer: {{ query }}'''
            memory.add_message("user", query)
            return "response"

        # With custom compression policy
        @agent(
            enable_memory=True,
            compression_policy=CompressionPolicy(
                strategy="smart",
                max_tokens=4000,
                trigger_threshold=0.8
            )
        )
        async def smart_assistant(query: str, memory: MemoryManager) -> str:
            '''Answer: {{ query }}'''
            pass

        # With tools
        @agent(tools=[search_tool, calculator])
        async def research_agent(topic: str) -> str:
            '''Research {{ topic }} using available tools'''
            pass

        # With multimodal RAG
        @agent(enable_multimodal_rag=True, rag_directory=Path("./docs"))
        async def docs_assistant(query: str, rag: MultimodalRAG) -> str:
            '''Answer {{ query }} using documentation.
            Use rag.query() to search relevant content.'''
            pass
    """

    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        # Extract template from docstring
        template_str = extract_template(func)

        # Use provided config or create from parameters
        llm_config = (
            config
            if config is not None
            else LLMConfig(model=model, temperature=temperature)
        )

        # Get function signature to check for special parameters
        sig = inspect.signature(func)
        has_memory_param = "memory" in sig.parameters
        has_rag_param = "rag" in sig.parameters

        # Validate MultimodalRAG configuration
        if enable_multimodal_rag:
            if rag_directory is None:
                raise ValueError(
                    "rag_directory is required when enable_multimodal_rag=True"
                )
            if not has_rag_param:
                raise ValueError(
                    "Function must have 'rag' parameter when enable_multimodal_rag=True"
                )

        # Check if @web.enable is applied and inject web_search tool
        tools_list = list(tools) if tools else []
        if hasattr(func, "_web_enabled") and func._web_enabled:
            # Inject web_search tool from @web.enable decorator
            web_tool = getattr(func, "_web_search_tool", None)
            if web_tool and web_tool not in tools_list:
                tools_list.append(web_tool)

        # Convert tools to LiteLLM format if provided
        llm_tools = None
        if tools_list:
            llm_tools = _convert_tools_to_llm_format(tools_list)

        # Initialize MultimodalRAG once (shared across calls)
        multimodal_rag = None
        if enable_multimodal_rag and has_rag_param:
            try:
                from .memory import MultimodalRAG

                multimodal_rag = MultimodalRAG(
                    directory=rag_directory,  # type: ignore
                    collection_name=f"{func.__name__}_rag",
                    persist_dir=persist_dir,
                    cache_size_mb=rag_cache_size_mb,
                )
            except ImportError as e:
                raise ImportError(
                    "MultimodalRAG requires multimodal extra. "
                    "Install with: pip install kagura-ai[multimodal]"
                ) from e

        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs_inner: P.kwargs) -> T:
            # Make kwargs mutable
            kwargs_inner = dict(kwargs_inner)  # type: ignore

            # Initialize telemetry if enabled
            telemetry_collector = None
            if enable_telemetry:
                from kagura.observability import get_global_telemetry

                telemetry = get_global_telemetry()
                telemetry_collector = telemetry.get_collector()

            # Prepare telemetry kwargs (simple params only, before injection)
            telemetry_kwargs = {}
            if telemetry_collector:
                try:
                    # Only bind user-provided arguments (not special params)
                    user_params = {
                        k: v
                        for k, v in sig.parameters.items()
                        if k not in ("memory", "rag")
                    }
                    user_sig = sig.replace(
                        parameters=[sig.parameters[k] for k in user_params]
                    )
                    filtered_kwargs = {
                        k: v
                        for k, v in kwargs_inner.items()
                        if k not in ("memory", "rag")
                    }
                    bound = user_sig.bind(*args, **filtered_kwargs)
                    telemetry_kwargs = dict(bound.arguments)
                except Exception:
                    # If binding fails, use kwargs_inner without special params
                    telemetry_kwargs = {
                        k: v
                        for k, v in kwargs_inner.items()
                        if k not in ("memory", "rag")
                    }

            # Track execution with telemetry
            if telemetry_collector:
                async with telemetry_collector.track_execution(
                    func.__name__, **telemetry_kwargs
                ):
                    result = await _execute_agent(
                        func,
                        args,
                        kwargs_inner,
                        telemetry_collector,
                        sig,
                        template_str,
                        llm_config,
                        enable_memory,
                        has_memory_param,
                        persist_dir,
                        max_messages,
                        enable_compression,
                        compression_policy,
                        multimodal_rag,
                        has_rag_param,
                        llm_tools,
                        tools_list,
                        kwargs,
                    )
                    return result  # type: ignore
            else:
                # No telemetry
                result = await _execute_agent(
                    func,
                    args,
                    kwargs_inner,
                    None,
                    sig,
                    template_str,
                    llm_config,
                    enable_memory,
                    has_memory_param,
                    persist_dir,
                    max_messages,
                    enable_compression,
                    compression_policy,
                    multimodal_rag,
                    has_rag_param,
                    llm_tools,
                    tools_list,
                    kwargs,
                )
                return result  # type: ignore

        # Mark as agent for MCP discovery
        wrapper._is_agent = True  # type: ignore
        wrapper._agent_config = llm_config  # type: ignore
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


async def _execute_agent(
    func: Callable,
    args: tuple,
    kwargs_inner: dict,
    telemetry_collector,
    sig: inspect.Signature,
    template_str: str,
    llm_config: LLMConfig,
    enable_memory: bool,
    has_memory_param: bool,
    persist_dir: Optional[Path],
    max_messages: int,
    enable_compression: bool,
    compression_policy: Optional[CompressionPolicy],
    multimodal_rag,
    has_rag_param: bool,
    llm_tools,
    tools_list,
    kwargs: dict,
):
    """Execute agent logic with optional telemetry"""
    # Create and inject memory if enabled
    if enable_memory and has_memory_param:
        memory = MemoryManager(
            agent_name=func.__name__,
            persist_dir=persist_dir,
            max_messages=max_messages,
            enable_compression=enable_compression,
            compression_policy=compression_policy,
            model=llm_config.model,
        )
        kwargs_inner["memory"] = memory  # type: ignore

    # Inject MultimodalRAG if enabled
    if multimodal_rag is not None and has_rag_param:
        kwargs_inner["rag"] = multimodal_rag  # type: ignore

    # Get function signature and bind arguments
    bound = sig.bind(*args, **kwargs_inner)
    bound.apply_defaults()

    # Render prompt with arguments (excluding special params from template)
    exclude_from_template = {"memory", "rag"}
    template_args = {
        k: v for k, v in bound.arguments.items() if k not in exclude_from_template
    }
    prompt = render_prompt(template_str, **template_args)

    # Add JSON format instruction for Pydantic models
    return_type = sig.return_annotation
    if return_type != inspect.Signature.empty:
        from typing import Union, get_args, get_origin

        from pydantic import BaseModel

        # Check if return type is a Pydantic model or list[Pydantic]
        origin = get_origin(return_type)
        actual_type = return_type

        # Handle Optional[Model] -> get the actual model type
        if origin is Union:
            type_args = get_args(return_type)
            # Filter out None type to get actual type
            non_none_args = [arg for arg in type_args if arg is not type(None)]
            if non_none_args:
                actual_type = non_none_args[0]
                origin = get_origin(actual_type)

        # Check if it's a Pydantic model
        is_pydantic = isinstance(actual_type, type) and issubclass(
            actual_type, BaseModel
        )

        # Check if it's list[PydanticModel]
        is_pydantic_list = False
        if origin is list:
            list_args = get_args(actual_type)
            if (
                list_args
                and isinstance(list_args[0], type)
                and issubclass(list_args[0], BaseModel)
            ):
                is_pydantic = True
                is_pydantic_list = True
                actual_type = list_args[0]  # Get the model type

        # If it's a Pydantic model, add JSON instruction
        if is_pydantic:
            from pydantic import BaseModel

            # Type assertion for pyright
            assert isinstance(actual_type, type) and issubclass(actual_type, BaseModel)
            schema = actual_type.model_json_schema()
            # Get required fields and properties for better instruction
            properties = schema.get("properties", {})

            # Build field description
            field_desc = ", ".join(
                f'"{field}" ({props.get("type", "any")})'
                for field, props in properties.items()
            )

            if is_pydantic_list:
                prompt += (
                    f"\n\nIMPORTANT: Return ONLY a JSON array of objects "
                    f"with these fields: {field_desc}. "
                    "Do NOT include the schema definition, explanations, "
                    "or any other text. Just the data array."
                )
            else:
                prompt += (
                    f"\n\nIMPORTANT: Return ONLY a JSON object "
                    f"with these fields: {field_desc}. "
                    "Do NOT include the schema definition, explanations, "
                    "or any other text. Just the data object."
                )

    # Prepare kwargs for LLM call
    llm_kwargs = dict(kwargs)

    # Add OpenAI tools schema to kwargs for litellm.acompletion
    if llm_tools:
        llm_kwargs["tools"] = llm_tools

    # Call LLM with Python tool functions
    response = await call_llm(
        prompt,
        llm_config,
        tool_functions=tools_list if tools_list else None,
        **llm_kwargs,
    )

    # Record LLM call in telemetry
    if telemetry_collector:
        # Import LLMResponse for type checking
        from kagura.core.llm import LLMResponse

        if isinstance(response, LLMResponse):
            from kagura.observability.pricing import calculate_cost

            telemetry_collector.record_llm_call(
                model=response.model,
                prompt_tokens=response.usage.get("prompt_tokens", 0),
                completion_tokens=response.usage.get("completion_tokens", 0),
                duration=response.duration,
                cost=calculate_cost(response.usage, response.model),
            )

    # Parse response based on return type annotation
    return_type = sig.return_annotation
    if return_type != inspect.Signature.empty and return_type is not str:
        # parse_response expects str, so convert if LLMResponse
        response_str = str(response)
        return parse_response(response_str, return_type)  # type: ignore

    return response  # type: ignore


@overload
def tool(fn: Callable[P, T]) -> Callable[P, T]: ...


@overload
def tool(fn: None = None) -> Callable[[Callable[P, T]], Callable[P, T]]: ...


def tool(
    fn: Callable[P, T] | None = None, *, name: Optional[str] = None
) -> Callable[P, T] | Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Convert a function into a tool (non-LLM function).

    Tools are regular Python functions that can be called by agents.
    They are registered in the tool registry and can be exposed via MCP.

    Args:
        fn: Function to convert
        name: Optional tool name (defaults to function name)

    Returns:
        Decorated function with type validation

    Example:
        @tool
        def calculate_tax(amount: float, rate: float = 0.1) -> float:
            '''Calculate tax amount'''
            return amount * rate

        # Call directly
        result = calculate_tax(100.0, 0.15)  # 15.0

        # Or use in agent via MCP
        @agent
        async def shopping_assistant(query: str) -> str:
            '''
            Help with shopping. Available tools:
            - calculate_tax(amount, rate): Calculate tax

            Query: {{ query }}
            '''
            pass
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        # Get function signature for validation
        sig = inspect.signature(func)
        tool_name = name or func.__name__

        # Check if function is async
        is_async = inspect.iscoroutinefunction(func)

        if is_async:
            # Async wrapper
            @functools.wraps(func)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                # Bind arguments to signature for validation
                try:
                    bound = sig.bind(*args, **kwargs)
                    bound.apply_defaults()
                except TypeError as e:
                    raise TypeError(
                        f"Tool '{tool_name}' called with invalid arguments: {e}"
                    ) from e

                # Execute the tool function
                result = await func(*bound.args, **bound.kwargs)  # type: ignore

                # Validate return type if annotated
                return_type = sig.return_annotation
                if return_type != inspect.Signature.empty:
                    # TODO: Add Pydantic validation for return type
                    pass

                return result  # type: ignore

            wrapper = async_wrapper  # type: ignore
        else:
            # Sync wrapper
            @functools.wraps(func)
            def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                # Bind arguments to signature for validation
                try:
                    bound = sig.bind(*args, **kwargs)
                    bound.apply_defaults()
                except TypeError as e:
                    raise TypeError(
                        f"Tool '{tool_name}' called with invalid arguments: {e}"
                    ) from e

                # Execute the tool function
                result = func(*bound.args, **bound.kwargs)

                # Validate return type if annotated
                return_type = sig.return_annotation
                if return_type != inspect.Signature.empty:
                    # TODO: Add Pydantic validation for return type
                    pass

                return result  # type: ignore

            wrapper = sync_wrapper  # type: ignore

        # Mark as tool for MCP discovery
        wrapper._is_tool = True  # type: ignore
        wrapper._tool_name = tool_name  # type: ignore
        wrapper._tool_signature = sig  # type: ignore
        wrapper._tool_docstring = func.__doc__ or ""  # type: ignore

        # Register in global tool registry
        try:
            tool_registry.register(tool_name, wrapper)  # type: ignore
        except ValueError:
            # Tool already registered (e.g., in tests), skip
            pass

        return wrapper  # type: ignore

    return decorator if fn is None else decorator(fn)


@overload
def workflow(fn: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]: ...


@overload
def workflow(
    fn: None = None,
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]: ...


def workflow(
    fn: Callable[P, Awaitable[T]] | None = None, *, name: Optional[str] = None
) -> (
    Callable[P, Awaitable[T]]
    | Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]
):
    """
    Convert a function into a workflow (multi-agent orchestration).

    Workflows coordinate multiple agents and tools to accomplish complex tasks.
    Unlike @agent, workflows execute the actual function body which orchestrates
    the agent calls.

    Args:
        fn: Function to convert
        name: Optional workflow name (defaults to function name)

    Returns:
        Decorated async function

    Example:
        @workflow
        async def research_workflow(topic: str) -> dict:
            '''Research a topic using multiple agents'''
            # Search for information
            search_results = await search_agent(topic)

            # Summarize findings
            summary = await summarize_agent(search_results)

            # Generate report
            report = await report_agent(summary)

            return {"topic": topic, "report": report}

        result = await research_workflow("AI safety")
    """

    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        # Get function signature
        sig = inspect.signature(func)
        workflow_name = name or func.__name__

        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            # Bind arguments to signature
            bound = sig.bind(*args, **kwargs)
            bound.apply_defaults()

            # Execute the workflow function
            result = await func(*bound.args, **bound.kwargs)

            return result  # type: ignore

        # Mark as workflow for MCP discovery
        wrapper._is_workflow = True  # type: ignore
        wrapper._workflow_name = workflow_name  # type: ignore
        wrapper._workflow_signature = sig  # type: ignore
        wrapper._workflow_docstring = func.__doc__ or ""  # type: ignore

        # Register in global workflow registry
        try:
            workflow_registry.register(workflow_name, wrapper)  # type: ignore
        except ValueError:
            # Workflow already registered (e.g., in tests), skip
            pass

        return wrapper  # type: ignore

    return decorator if fn is None else decorator(fn)
