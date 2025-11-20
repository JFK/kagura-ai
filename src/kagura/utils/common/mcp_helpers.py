"""MCP tool helper functions (extracted from deprecated mcp.builtin.common).

Helper functions for MCP tool parameter parsing and validation.
Previously in mcp/builtin/common.py (deprecated v4.3.0, removed v4.4.0).
"""

from __future__ import annotations

import json
from typing import Any


def parse_json_list(
    value: str | list, param_name: str = "parameter"
) -> list:
    """Parse JSON string to list, with error handling.

    Args:
        value: JSON string or list
        param_name: Parameter name for error messages

    Returns:
        Parsed list

    Raises:
        ValueError: If parsing fails
    """
    if isinstance(value, list):
        return value
    
    try:
        result = json.loads(value)
        if not isinstance(result, list):
            raise ValueError(f"{param_name} must be a list")
        return result
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON for {param_name}: {e}")


def parse_json_dict(
    value: str | dict, param_name: str = "parameter"
) -> dict:
    """Parse JSON string to dict."""
    if isinstance(value, dict):
        return value
    
    try:
        result = json.loads(value)
        if not isinstance(result, dict):
            raise ValueError(f"{param_name} must be a dict")
        return result
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON for {param_name}: {e}")


def to_int(
    value: str | int,
    default: int = 0,
    min_val: int | None = None,
    max_val: int | None = None,
    param_name: str = "parameter",
) -> int:
    """Convert to int with validation."""
    if isinstance(value, int):
        result = value
    else:
        try:
            result = int(value)
        except (ValueError, TypeError):
            return default
    
    if min_val is not None and result < min_val:
        result = min_val
    if max_val is not None and result > max_val:
        result = max_val
    
    return result


def to_float_clamped(
    value: str | float,
    min_val: float = 0.0,
    max_val: float = 1.0,
    default: float = 0.5,
    param_name: str = "parameter",
) -> float:
    """Convert to float and clamp to range."""
    if isinstance(value, (int, float)):
        result = float(value)
    else:
        try:
            result = float(value)
        except (ValueError, TypeError):
            return default
    
    return max(min_val, min(max_val, result))


def to_bool(value: str | bool | None, default: bool = False) -> bool:
    """Convert string to bool."""
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes")
    return default


def format_error(message: str, details: dict[str, Any] | None = None) -> str:
    """Format error message as JSON."""
    error_obj = {"status": "error", "error": message}
    if details:
        error_obj["details"] = details
    return json.dumps(error_obj, indent=2)
