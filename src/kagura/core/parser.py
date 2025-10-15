"""Type-based response parser for LLM outputs"""

import json
import re
from typing import Any, TypeVar, Union, get_args, get_origin

from pydantic import BaseModel, ValidationError

T = TypeVar("T")


def extract_json(text: str) -> str:
    """
    Extract JSON from LLM response.

    Tries multiple strategies:
    1. Find JSON in markdown code blocks
    2. Find JSON objects/arrays in text using bracket counting
    3. Return original text if no JSON found

    Args:
        text: LLM response text

    Returns:
        Extracted JSON string or original text
    """
    # Strategy 1: Extract from markdown code blocks
    json_block_pattern = r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```"
    matches = re.findall(json_block_pattern, text, re.DOTALL)
    if matches:
        return matches[0]

    # Strategy 2: Find JSON using bracket counting for proper nesting
    # Try to find JSON array first (handles nested objects)
    def find_balanced_json(text: str, start_char: str, end_char: str) -> list[str]:
        """Find balanced JSON structures"""
        results = []
        i = 0
        while i < len(text):
            if text[i] == start_char:
                count = 1
                j = i + 1
                while j < len(text) and count > 0:
                    if text[j] == start_char:
                        count += 1
                    elif text[j] == end_char:
                        count -= 1
                    j += 1
                if count == 0:
                    results.append(text[i:j])
                i = j
            else:
                i += 1
        return results

    # Find both arrays and objects
    arrays = find_balanced_json(text, "[", "]")
    objects = find_balanced_json(text, "{", "}")

    # Return the longest one (outermost structure)
    all_json = arrays + objects
    if all_json:
        return max(all_json, key=len)

    # Strategy 3: Return original text
    return text.strip()


def parse_basic_type(text: str, target_type: type) -> Any:
    """
    Parse basic Python types from text.

    Args:
        text: Text to parse
        target_type: Target type (int, float, bool, str)

    Returns:
        Parsed value

    Raises:
        ValueError: If parsing fails
    """
    text = text.strip()

    if target_type is str:
        return text

    if target_type is int:
        # Extract first number from text
        numbers = re.findall(r"-?\d+", text)
        if numbers:
            return int(numbers[0])
        raise ValueError(f"No integer found in: {text}")

    if target_type is float:
        # Extract first float from text
        numbers = re.findall(r"-?\d+\.?\d*", text)
        if numbers:
            return float(numbers[0])
        raise ValueError(f"No float found in: {text}")

    if target_type is bool:
        lower_text = text.lower()
        if any(word in lower_text for word in ["true", "yes", "1"]):
            return True
        if any(word in lower_text for word in ["false", "no", "0"]):
            return False
        raise ValueError(f"No boolean found in: {text}")

    raise ValueError(f"Unsupported basic type: {target_type}")


def parse_response(response: str, target_type: type[T]) -> T:
    """
    Parse LLM response based on target type.

    Supports:
    - Basic types: str, int, float, bool
    - Pydantic models
    - List types: list[str], list[int], etc.
    - Optional types

    Args:
        response: LLM response text
        target_type: Target return type class

    Returns:
        Parsed value of target type

    Raises:
        ValueError: If parsing fails

    Example:
        >>> parse_response("42", int)
        42
        >>> parse_response('{"name": "test"}', dict)
        {'name': 'test'}
    """
    # Handle str directly (no parsing needed)
    if target_type is str:
        return response  # type: ignore

    # Handle basic types
    if target_type in (int, float, bool):
        return parse_basic_type(response, target_type)  # type: ignore

    # Handle Optional types (Union[T, None])
    origin = get_origin(target_type)
    if origin is Union:
        args = get_args(target_type)
        # Check if it's Optional (Union with None)
        if type(None) in args:
            # Get the non-None type
            actual_type = next(arg for arg in args if arg is not type(None))
            try:
                return parse_response(response, actual_type)  # type: ignore
            except (ValueError, ValidationError):
                return None  # type: ignore

    # Handle list types
    if origin is list:
        args = get_args(target_type)
        item_type = args[0] if args else str

        # Extract JSON
        json_text = extract_json(response)

        try:
            # Try parsing as JSON array
            data = json.loads(json_text)
            if isinstance(data, list):
                # Parse each item
                if item_type in (str, int, float, bool):
                    return [item_type(item) for item in data]  # type: ignore
                elif isinstance(item_type, type) and issubclass(item_type, BaseModel):
                    return [item_type.model_validate(item) for item in data]  # type: ignore
                return data  # type: ignore
        except (json.JSONDecodeError, ValidationError, TypeError):
            pass

        # Fallback: split by common delimiters (only for basic types)
        if item_type in (str, int, float, bool):
            items = re.split(r"[,\n]", response)
            cleaned_items = [item.strip() for item in items if item.strip()]
            try:
                return [item_type(item) for item in cleaned_items]  # type: ignore
            except (ValueError, TypeError):
                pass

        # If we can't parse, raise error
        raise ValueError(f"Failed to parse list[{item_type}] from response")

    # Handle Pydantic models
    if isinstance(target_type, type) and issubclass(target_type, BaseModel):
        json_text = extract_json(response)

        try:
            # Try parsing as JSON
            data = json.loads(json_text)
            return target_type.model_validate(data)  # type: ignore
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON from response: {e}")
        except ValidationError as e:
            raise ValueError(f"Failed to validate Pydantic model: {e}")

    # Fallback: return as string
    raise ValueError(f"Unsupported type for parsing: {target_type}")
