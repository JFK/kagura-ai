"""Base service class with common utilities."""

from __future__ import annotations

import logging
from abc import ABC
from typing import Any


class BaseService(ABC):
    """Base class for all services.

    Provides common utilities for logging, error handling, and validation.

    Services should inherit from this class and implement business logic
    without directly depending on interface-specific code (MCP, API, CLI).

    Example:
        >>> class MyService(BaseService):
        ...     def __init__(self, data_manager):
        ...         super().__init__()
        ...         self.data = data_manager
        ...
        ...     async def do_something(self, param: str) -> Result:
        ...         self.logger.info(f"Doing something with {param}")
        ...         # Business logic here
        ...         return Result(success=True)
    """

    def __init__(self):
        """Initialize base service with logger."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.debug(f"Initialized {self.__class__.__name__}")

    def validate_required(self, value: Any, field_name: str) -> None:
        """Validate that a required field is not None or empty.

        Args:
            value: Value to validate
            field_name: Name of the field (for error messages)

        Raises:
            ValueError: If value is None or empty string
        """
        if value is None:
            raise ValueError(f"{field_name} is required")

        if isinstance(value, str) and not value.strip():
            raise ValueError(f"{field_name} cannot be empty")

    def validate_range(
        self,
        value: float,
        field_name: str,
        min_val: float | None = None,
        max_val: float | None = None,
    ) -> None:
        """Validate that a numeric value is within range.

        Args:
            value: Value to validate
            field_name: Name of the field (for error messages)
            min_val: Minimum allowed value (inclusive)
            max_val: Maximum allowed value (inclusive)

        Raises:
            ValueError: If value is out of range
        """
        if min_val is not None and value < min_val:
            raise ValueError(f"{field_name} must be >= {min_val}")

        if max_val is not None and value > max_val:
            raise ValueError(f"{field_name} must be <= {max_val}")

    def validate_length(
        self,
        value: str,
        field_name: str,
        min_length: int | None = None,
        max_length: int | None = None,
    ) -> None:
        """Validate string length.

        Args:
            value: String to validate
            field_name: Name of the field (for error messages)
            min_length: Minimum length (inclusive)
            max_length: Maximum length (inclusive)

        Raises:
            ValueError: If length is invalid
        """
        length = len(value)

        if min_length is not None and length < min_length:
            raise ValueError(
                f"{field_name} must be at least {min_length} characters"
            )

        if max_length is not None and length > max_length:
            raise ValueError(
                f"{field_name} must be at most {max_length} characters"
            )

    def build_metadata(self, **kwargs: Any) -> dict[str, Any]:
        """Build metadata dictionary, filtering out None values.

        Args:
            **kwargs: Metadata key-value pairs

        Returns:
            Dictionary with non-None values

        Example:
            >>> service = BaseService()
            >>> service.build_metadata(
            ...     user="alice",
            ...     importance=0.8,
            ...     source=None,  # Filtered out
            ... )
            {'user': 'alice', 'importance': 0.8}
        """
        return {k: v for k, v in kwargs.items() if v is not None}
