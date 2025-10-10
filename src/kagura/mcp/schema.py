"""
JSON Schema generation for MCP tool integration

Converts Python type hints to JSON Schema format required by MCP.
"""

import inspect
from typing import Any, Callable, get_args, get_origin

from pydantic import BaseModel


def python_type_to_json_schema(py_type: type) -> dict[str, Any]:
    """Convert Python type to JSON Schema

    Args:
        py_type: Python type annotation

    Returns:
        JSON Schema dict

    Example:
        >>> python_type_to_json_schema(str)
        {'type': 'string'}
        >>> python_type_to_json_schema(int)
        {'type': 'integer'}
    """
    # Handle None / NoneType
    if py_type is type(None):
        return {"type": "null"}

    # Handle basic types
    if py_type is str:
        return {"type": "string"}
    if py_type is int:
        return {"type": "integer"}
    if py_type is float:
        return {"type": "number"}
    if py_type is bool:
        return {"type": "boolean"}

    # Handle Pydantic BaseModel
    if isinstance(py_type, type) and issubclass(py_type, BaseModel):
        return py_type.model_json_schema()

    # Handle generic types (List, Dict, Optional, Union)
    origin = get_origin(py_type)
    args = get_args(py_type)

    # Optional[X] -> Union[X, None]
    if origin is type(None) or (
        origin is not None
        and hasattr(origin, "__name__")
        and origin.__name__ == "UnionType"
    ):  # type: ignore
        # Union type - check if it's Optional (X | None)
        if len(args) == 2 and type(None) in args:
            # Optional[X] case
            non_none_type = args[0] if args[1] is type(None) else args[1]
            schema = python_type_to_json_schema(non_none_type)
            # Make it nullable
            if isinstance(schema.get("type"), str):
                schema["type"] = [schema["type"], "null"]
            return schema
        # General Union - use anyOf
        return {"anyOf": [python_type_to_json_schema(arg) for arg in args]}

    # List[X]
    if origin is list:
        if args:
            items_schema = python_type_to_json_schema(args[0])
            return {"type": "array", "items": items_schema}
        return {"type": "array"}

    # Dict[K, V]
    if origin is dict:
        if len(args) == 2:
            # Assuming keys are strings for JSON compatibility
            value_schema = python_type_to_json_schema(args[1])
            return {"type": "object", "additionalProperties": value_schema}
        return {"type": "object"}

    # Fallback: treat as string
    return {"type": "string", "description": f"Type: {py_type}"}


def generate_json_schema(func: Callable[..., Any]) -> dict[str, Any]:
    """Generate JSON Schema from function signature

    Args:
        func: Function to generate schema for

    Returns:
        JSON Schema dict with 'type', 'properties', and 'required'

    Example:
        >>> def my_func(name: str, age: int = 18) -> str:
        ...     pass
        >>> schema = generate_json_schema(my_func)
        >>> schema['properties']['name']
        {'type': 'string'}
        >>> schema['required']
        ['name']
    """
    sig = inspect.signature(func)

    properties: dict[str, Any] = {}
    required: list[str] = []

    for param_name, param in sig.parameters.items():
        # Skip *args, **kwargs
        if param.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            continue

        # Get type annotation
        param_type = param.annotation
        if param_type == inspect.Parameter.empty:
            # No type hint - default to string
            param_schema = {"type": "string"}
        else:
            param_schema = python_type_to_json_schema(param_type)

        # Add description from docstring if available
        if func.__doc__:
            # Simple docstring parsing for parameter descriptions
            # Format: "param_name: description"
            for line in func.__doc__.split("\n"):
                stripped = line.strip()
                if stripped.startswith(f"{param_name}:"):
                    desc = stripped.split(":", 1)[1].strip()
                    param_schema["description"] = desc
                    break

        properties[param_name] = param_schema

        # Check if parameter is required (no default value)
        if param.default == inspect.Parameter.empty:
            required.append(param_name)

    schema = {
        "type": "object",
        "properties": properties,
    }

    if required:
        schema["required"] = required

    return schema


__all__ = ["generate_json_schema", "python_type_to_json_schema"]
