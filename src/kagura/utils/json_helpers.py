"""JSON encoding/decoding utilities for ChromaDB compatibility.

ChromaDB stores metadata as key-value pairs but only supports string values for complex types.
These utilities handle conversion between Python objects (lists, dicts) and JSON strings.
"""

import json
from typing import Any


def encode_chromadb_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    """Convert lists and dicts to JSON strings for ChromaDB storage.

    ChromaDB metadata only supports scalar values (str, int, float, bool).
    This function converts complex types (list, dict) to JSON strings for storage.

    Args:
        metadata: Metadata dictionary with mixed types

    Returns:
        Metadata dictionary with lists/dicts encoded as JSON strings

    Examples:
        >>> encode_chromadb_metadata({"tags": ["python", "ai"], "count": 5})
        {'tags': '["python", "ai"]', 'count': 5}

        >>> encode_chromadb_metadata({"config": {"model": "gpt-4"}, "active": True})
        {'config': '{"model": "gpt-4"}', 'active': True}
    """
    encoded = {}
    for key, value in metadata.items():
        if isinstance(value, (list, dict)):
            # Convert lists and dicts to JSON strings
            encoded[key] = json.dumps(value, ensure_ascii=False)
        else:
            # Keep scalars as-is
            encoded[key] = value
    return encoded


def decode_chromadb_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    """Decode JSON strings in metadata back to Python objects.

    Inverse of encode_chromadb_metadata(). Attempts to parse strings that look
    like JSON (starting with '[' or '{') back into lists/dicts.

    Args:
        metadata: Metadata dictionary with potential JSON strings

    Returns:
        Metadata dictionary with JSON strings decoded back to lists/dicts

    Examples:
        >>> decode_chromadb_metadata({'tags': '["python", "ai"]', 'count': 5})
        {'tags': ['python', 'ai'], 'count': 5}

        >>> decode_chromadb_metadata({'config': '{"model": "gpt-4"}', 'active': True})
        {'config': {'model': 'gpt-4'}, 'active': True}

        >>> decode_chromadb_metadata({'malformed': '[invalid', 'name': 'test'})
        {'malformed': '[invalid', 'name': 'test'}  # Failed decode preserved
    """
    decoded = {}
    for key, value in metadata.items():
        if isinstance(value, str) and (value.startswith("[") or value.startswith("{")):
            # Attempt to decode JSON strings
            try:
                decoded[key] = json.loads(value)
            except json.JSONDecodeError:
                # If decode fails, keep original string
                decoded[key] = value
        else:
            # Keep non-JSON-like values as-is
            decoded[key] = value
    return decoded


def safe_json_loads(
    value: str | Any,
    default: Any = None,
    *,
    expected_type: type | None = None,
) -> Any:
    """Parse JSON with error recovery and optional type validation.

    This is a robust JSON parser that handles common edge cases:
    - Non-string inputs (returned as-is)
    - Invalid JSON (returns default value)
    - Type mismatches (returns default if expected_type doesn't match)

    Args:
        value: Value to parse (if string, attempt JSON decode)
        default: Value to return if parsing fails or type mismatch
        expected_type: Optional type to validate against (e.g., list, dict)

    Returns:
        Parsed value, or default if parsing fails or type doesn't match

    Examples:
        >>> safe_json_loads('["a", "b"]')
        ['a', 'b']

        >>> safe_json_loads('invalid', default=[])
        []

        >>> safe_json_loads('["a"]', expected_type=dict, default={})
        {}  # Type mismatch, returns default

        >>> safe_json_loads(['already', 'a', 'list'])
        ['already', 'a', 'list']  # Non-string returned as-is

        >>> safe_json_loads('null')
        None

        >>> safe_json_loads('null', default='fallback')
        'fallback'  # None is falsy, default used
    """
    # If not a string, return as-is or default
    if not isinstance(value, str):
        return value if value is not None else default

    # Attempt JSON parsing
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return default

    # If parsed is None (JSON null), use default
    if parsed is None:
        return default

    # Type validation if requested
    if expected_type is not None and not isinstance(parsed, expected_type):
        return default

    return parsed
