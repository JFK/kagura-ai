"""Working memory for temporary data during agent execution."""

from datetime import datetime
from typing import Any


class WorkingMemory:
    """Temporary memory during agent execution.

    Data stored here is cleared when the agent execution completes.
    """

    def __init__(self) -> None:
        """Initialize working memory."""
        self._data: dict[str, Any] = {}
        self._access_log: dict[str, datetime] = {}

    def set(self, key: str, value: Any) -> None:
        """Store temporary data.

        Args:
            key: Key to store data under
            value: Value to store
        """
        self._data[key] = value
        self._access_log[key] = datetime.now()

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve temporary data.

        Args:
            key: Key to retrieve
            default: Default value if key not found

        Returns:
            Stored value or default
        """
        self._access_log[key] = datetime.now()
        return self._data.get(key, default)

    def has(self, key: str) -> bool:
        """Check if key exists.

        Args:
            key: Key to check

        Returns:
            True if key exists
        """
        return key in self._data

    def delete(self, key: str) -> None:
        """Delete a key.

        Args:
            key: Key to delete
        """
        if key in self._data:
            del self._data[key]
        if key in self._access_log:
            del self._access_log[key]

    def clear(self) -> None:
        """Clear all temporary data."""
        self._data.clear()
        self._access_log.clear()

    def keys(self) -> list[str]:
        """Get all keys.

        Returns:
            List of keys
        """
        return list(self._data.keys())

    def to_dict(self) -> dict[str, Any]:
        """Export for persistence.

        Returns:
            Dictionary with data and access log
        """
        return {
            "data": self._data.copy(),
            "access_log": {k: v.isoformat() for k, v in self._access_log.items()},
        }

    def __len__(self) -> int:
        """Get number of stored items."""
        return len(self._data)

    def __repr__(self) -> str:
        """String representation."""
        return f"WorkingMemory(items={len(self._data)})"
