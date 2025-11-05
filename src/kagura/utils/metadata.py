"""Metadata extraction and manipulation utilities.

Standard memory metadata structure and helper functions for consistent
metadata handling across CLI, MCP, and API layers.
"""

from datetime import datetime
from typing import Any, NotRequired, TypedDict

from kagura.utils.json_helpers import encode_chromadb_metadata


class MemoryMetadata(TypedDict):
    """Standard memory metadata fields.

    This TypedDict defines the canonical structure for memory metadata
    across all Kagura AI components.

    Attributes:
        tags: List of tags for categorization
        importance: Importance score (0.0-1.0)
        created_at: Creation timestamp (ISO 8601 format)
        updated_at: Last update timestamp (ISO 8601 format)
        user_metadata: Additional user-defined metadata
    """

    tags: list[str]
    importance: float
    created_at: str | None
    updated_at: str | None
    user_metadata: NotRequired[dict[str, Any]]


# Internal field names (should not be exposed to users)
_INTERNAL_FIELDS = frozenset({"tags", "importance", "created_at", "updated_at"})


def extract_memory_fields(metadata: dict[str, Any]) -> MemoryMetadata:
    """Extract and validate standard memory fields from metadata.

    Separates internal memory fields (tags, importance, timestamps) from
    user-defined metadata, with validation and defaults.

    Args:
        metadata: Raw metadata dictionary (potentially from ChromaDB)

    Returns:
        MemoryMetadata with extracted fields and user metadata separated

    Examples:
        >>> extract_memory_fields({
        ...     "tags": ["python", "ai"],
        ...     "importance": 0.8,
        ...     "created_at": "2025-01-01T12:00:00",
        ...     "custom_field": "value"
        ... })
        {
            'tags': ['python', 'ai'],
            'importance': 0.8,
            'created_at': '2025-01-01T12:00:00',
            'updated_at': None,
            'user_metadata': {'custom_field': 'value'}
        }

        >>> extract_memory_fields({})  # Defaults
        {
            'tags': [],
            'importance': 0.5,
            'created_at': None,
            'updated_at': None,
            'user_metadata': {}
        }
    """
    # Extract internal fields with defaults
    tags = metadata.get("tags", [])
    if not isinstance(tags, list):
        tags = []

    importance = metadata.get("importance", 0.5)
    if not isinstance(importance, (int, float)):
        importance = 0.5
    else:
        # Clamp to [0.0, 1.0]
        importance = max(0.0, min(1.0, float(importance)))

    created_at = metadata.get("created_at")
    if created_at is not None and not isinstance(created_at, str):
        created_at = None

    updated_at = metadata.get("updated_at")
    if updated_at is not None and not isinstance(updated_at, str):
        updated_at = None

    # Extract user metadata (everything except internal fields)
    user_metadata = {
        k: v for k, v in metadata.items() if k not in _INTERNAL_FIELDS
    }

    return MemoryMetadata(
        tags=tags,
        importance=importance,
        created_at=created_at,
        updated_at=updated_at,
        user_metadata=user_metadata,
    )


def merge_metadata(
    base: dict[str, Any], updates: dict[str, Any], *, add_timestamp: bool = True
) -> dict[str, Any]:
    """Merge metadata dicts with proper handling of internal fields.

    Updates base metadata with values from updates dict. Handles list merging
    for tags and optionally adds/updates timestamps.

    Args:
        base: Base metadata dictionary
        updates: Updates to apply (can be partial)
        add_timestamp: If True, add/update "updated_at" timestamp

    Returns:
        Merged metadata dictionary

    Examples:
        >>> base = {
        ...     "tags": ["python"],
        ...     "importance": 0.5,
        ...     "created_at": "2025-01-01T12:00:00",
        ...     "custom": "value1"
        ... }
        >>> updates = {
        ...     "tags": ["python", "ai"],
        ...     "importance": 0.8,
        ...     "custom": "value2"
        ... }
        >>> merge_metadata(base, updates, add_timestamp=False)
        {
            'tags': ['python', 'ai'],
            'importance': 0.8,
            'created_at': '2025-01-01T12:00:00',
            'custom': 'value2'
        }
    """
    merged = base.copy()

    # Update with new values
    for key, value in updates.items():
        merged[key] = value

    # Add timestamp if requested
    if add_timestamp:
        merged["updated_at"] = datetime.now().isoformat()

    return merged


def build_full_metadata(
    *,
    tags: list[str] | None = None,
    importance: float | None = None,
    user_metadata: dict[str, Any] | None = None,
    created_at: str | datetime | None = None,
    updated_at: str | datetime | None = None,
) -> dict[str, Any]:
    """Build a complete metadata dictionary with all standard fields.

    Convenience function to construct metadata from individual components.
    Automatically converts datetime objects to ISO format strings.

    Args:
        tags: List of tags (default: [])
        importance: Importance score 0.0-1.0 (default: 0.5)
        user_metadata: User-defined metadata (default: {})
        created_at: Creation timestamp (default: current time)
        updated_at: Update timestamp (default: None)

    Returns:
        Complete metadata dictionary

    Examples:
        >>> build_full_metadata(
        ...     tags=["test"],
        ...     importance=0.9,
        ...     user_metadata={"project": "kagura"}
        ... )
        {
            'tags': ['test'],
            'importance': 0.9,
            'created_at': '2025-11-05T...',
            'updated_at': None,
            'project': 'kagura'
        }
    """
    now = datetime.now()

    # Handle timestamps
    if created_at is None:
        created_at_str = now.isoformat()
    elif isinstance(created_at, datetime):
        created_at_str = created_at.isoformat()
    else:
        created_at_str = created_at

    if updated_at is None:
        updated_at_str = None
    elif isinstance(updated_at, datetime):
        updated_at_str = updated_at.isoformat()
    else:
        updated_at_str = updated_at

    # Build metadata
    metadata: dict[str, Any] = {
        "tags": tags or [],
        "importance": importance if importance is not None else 0.5,
        "created_at": created_at_str,
        "updated_at": updated_at_str,
    }

    # Add user metadata
    if user_metadata:
        metadata.update(user_metadata)

    return metadata


def prepare_for_chromadb(metadata: dict[str, Any]) -> dict[str, Any]:
    """Prepare metadata for ChromaDB storage.

    Combines encode_chromadb_metadata with validation to ensure all
    metadata is ChromaDB-compatible (scalars or JSON strings).

    Args:
        metadata: Metadata dictionary to prepare

    Returns:
        ChromaDB-compatible metadata dictionary

    Examples:
        >>> prepare_for_chromadb({
        ...     "tags": ["python", "ai"],
        ...     "importance": 0.8,
        ...     "config": {"model": "gpt-4"}
        ... })
        {
            'tags': '["python", "ai"]',
            'importance': 0.8,
            'config': '{"model": "gpt-4"}'
        }
    """
    return encode_chromadb_metadata(metadata)


def validate_importance(importance: Any) -> float:
    """Validate and normalize importance score.

    Ensures importance is a float in range [0.0, 1.0].

    Args:
        importance: Value to validate (int, float, or string)

    Returns:
        Validated importance score (clamped to [0.0, 1.0])

    Raises:
        ValueError: If importance cannot be converted to float

    Examples:
        >>> validate_importance(0.5)
        0.5

        >>> validate_importance(1.5)  # Clamped
        1.0

        >>> validate_importance(-0.1)  # Clamped
        0.0

        >>> validate_importance("0.7")
        0.7

        >>> validate_importance("invalid")
        Traceback (most recent call last):
            ...
        ValueError: Importance must be a number (got 'invalid')
    """
    try:
        value = float(importance)
    except (TypeError, ValueError) as e:
        msg = f"Importance must be a number (got {importance!r})"
        raise ValueError(msg) from e

    # Clamp to [0.0, 1.0]
    return max(0.0, min(1.0, value))
