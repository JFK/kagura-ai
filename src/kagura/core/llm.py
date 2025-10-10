"""LLM integration using LiteLLM"""

import json
from typing import Any, Callable, Optional

import litellm
from pydantic import BaseModel


class LLMConfig(BaseModel):
    """LLM configuration"""

    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    top_p: float = 1.0


async def call_llm(
    prompt: str,
    config: LLMConfig,
    tool_functions: Optional[list[Callable]] = None,
    **kwargs: Any,
) -> str:
    """
    Call LLM with given prompt, handling tool calls if present.

    Args:
        prompt: The prompt to send
        config: LLM configuration
        tool_functions: Optional list of tool functions (Python callables)
        **kwargs: Additional LiteLLM parameters (including 'tools' schema)

    Returns:
        LLM response text
    """
    # Build messages list
    messages: list[dict[str, Any]] = [{"role": "user", "content": prompt}]

    # Create tool name -> function mapping from Python callables
    tool_map: dict[str, Callable] = {}
    if tool_functions:
        tool_map = {tool.__name__: tool for tool in tool_functions}

    # Maximum iterations to prevent infinite loops
    max_iterations = 5
    iterations = 0

    while iterations < max_iterations:
        iterations += 1

        # Call LLM (kwargs may contain 'tools' for OpenAI schema)
        response = await litellm.acompletion(
            model=config.model,
            messages=messages,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            top_p=config.top_p,
            **kwargs,
        )

        message = response.choices[0].message  # type: ignore

        # Check if LLM wants to call tools
        tool_calls = getattr(message, "tool_calls", None)

        if tool_calls:
            # Add assistant message with tool calls to conversation
            messages.append(
                {
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in tool_calls
                    ],
                }
            )

            # Execute each tool call
            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                tool_args_str = tool_call.function.arguments

                # Parse arguments
                try:
                    tool_args = json.loads(tool_args_str)
                except json.JSONDecodeError:
                    tool_args = {}

                # Execute tool
                if tool_name in tool_map:
                    tool_func = tool_map[tool_name]
                    try:
                        # Call tool (handle both sync and async)
                        import inspect

                        if inspect.iscoroutinefunction(tool_func):
                            tool_result = await tool_func(**tool_args)
                        else:
                            tool_result = tool_func(**tool_args)

                        result_content = str(tool_result)
                    except Exception as e:
                        result_content = f"Error executing {tool_name}: {str(e)}"
                else:
                    result_content = f"Tool {tool_name} not found"

                # Add tool result to messages
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "content": result_content,
                    }
                )

            # Continue loop to get final response
            continue

        # No tool calls, return content
        content = message.content
        return content if content else ""

    # Max iterations reached
    return "Error: Maximum tool call iterations reached"
