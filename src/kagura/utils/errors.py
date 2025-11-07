"""Unified error handling for all Kagura layers (CLI, MCP, API).

Provides KaguraError base class that can format errors appropriately
for different contexts: CLI (Rich console), MCP (JSON), API (HTTPException).
"""

from __future__ import annotations

import json
from typing import Any


class KaguraError(Exception):
    """Base error class with multi-context formatting.

    All Kagura errors should inherit from this class to enable
    consistent error handling across CLI, MCP, and API layers.

    Attributes:
        message: Human-readable error message
        details: Optional error details dict
        help_text: Optional help text for resolution
        error_code: Optional error code for categorization
    """

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        help_text: str | None = None,
        error_code: str | None = None,
    ):
        """Initialize KaguraError.

        Args:
            message: Human-readable error message
            details: Optional error details
            help_text: Optional help text
            error_code: Optional error code
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.help_text = help_text
        self.error_code = error_code

    def to_mcp_response(self) -> str:
        """Format error for MCP tools (JSON string).

        Returns:
            JSON string with status=error

        Example:
            >>> error = MemoryNotFoundError("Key not found")
            >>> error.to_mcp_response()
            '{"status": "error", "error": "Key not found", ...}'
        """
        response: dict[str, Any] = {
            "status": "error",
            "error": self.message,
        }

        if self.error_code:
            response["code"] = self.error_code

        if self.details:
            response["details"] = self.details

        if self.help_text:
            response["help"] = self.help_text

        return json.dumps(response, ensure_ascii=False, indent=2)

    def to_cli_message(self) -> str:
        """Format error for CLI (plain text with Rich markup).

        Returns:
            Formatted string for Rich console

        Example:
            >>> error = MemoryNotFoundError("Key not found", help_text="Check key name")
            >>> print(error.to_cli_message())
            ❌ Error: Key not found

            💡 Help: Check key name
        """
        lines = [f"❌ Error: {self.message}"]

        if self.details:
            lines.append("\nDetails:")
            for key, value in self.details.items():
                lines.append(f"  • {key}: {value}")

        if self.help_text:
            lines.append(f"\n💡 Help: {self.help_text}")

        return "\n".join(lines)

    def to_http_exception(self) -> dict[str, Any]:
        """Format error for FastAPI HTTPException.

        Returns:
            Dict suitable for HTTPException detail parameter

        Example:
            >>> error = MemoryNotFoundError("Key not found")
            >>> raise HTTPException(status_code=404, detail=error.to_http_exception())
        """
        return {
            "error": self.message,
            "code": self.error_code or "INTERNAL_ERROR",
            "details": self.details,
            "help": self.help_text,
        }


class MemoryNotFoundError(KaguraError):
    """Memory key not found in storage."""

    def __init__(
        self,
        key: str,
        scope: str = "persistent",
        help_text: str | None = None,
    ):
        """Initialize MemoryNotFoundError.

        Args:
            key: Memory key that was not found
            scope: Memory scope (working/persistent)
            help_text: Optional help text
        """
        super().__init__(
            message=f"Memory '{key}' not found in {scope} memory",
            details={"key": key, "scope": scope},
            help_text=help_text
            or "Check the key name or use memory_list() to see all keys",
            error_code="MEMORY_NOT_FOUND",
        )


class ValidationError(KaguraError):
    """Parameter validation failed."""

    def __init__(
        self,
        param_name: str,
        message: str,
        expected: str | None = None,
        received: Any = None,
    ):
        """Initialize ValidationError.

        Args:
            param_name: Parameter name that failed validation
            message: Validation error message
            expected: Expected value/type
            received: Actual value received
        """
        details = {"parameter": param_name}
        if expected:
            details["expected"] = expected
        if received is not None:
            details["received"] = str(received)

        super().__init__(
            message=f"Validation error for '{param_name}': {message}",
            details=details,
            error_code="VALIDATION_ERROR",
        )


class AuthenticationError(KaguraError):
    """Authentication or authorization failed."""

    def __init__(
        self,
        message: str = "Authentication failed",
        service: str | None = None,
        help_text: str | None = None,
    ):
        """Initialize AuthenticationError.

        Args:
            message: Error message
            service: Service name (e.g., "Brave Search", "GitHub")
            help_text: Optional help text
        """
        details = {}
        if service:
            details["service"] = service

        super().__init__(
            message=message,
            details=details,
            help_text=help_text or "Check your API key or authentication credentials",
            error_code="AUTH_ERROR",
        )


class SessionError(KaguraError):
    """Coding session error (already active, not found, etc.)."""

    def __init__(
        self,
        message: str,
        session_id: str | None = None,
        help_text: str | None = None,
    ):
        """Initialize SessionError.

        Args:
            message: Error message
            session_id: Optional session ID
            help_text: Optional help text
        """
        details = {}
        if session_id:
            details["session_id"] = session_id

        super().__init__(
            message=message,
            details=details,
            help_text=help_text,
            error_code="SESSION_ERROR",
        )


class DependencyError(KaguraError):
    """Required dependency not available."""

    def __init__(
        self,
        package: str,
        install_cmd: str,
        feature: str | None = None,
    ):
        """Initialize DependencyError.

        Args:
            package: Package name that's missing
            install_cmd: Installation command
            feature: Feature that requires this dependency
        """
        message = f"Missing dependency: {package}"
        if feature:
            message += f" (required for {feature})"

        super().__init__(
            message=message,
            details={"package": package},
            help_text=f"Install with: {install_cmd}",
            error_code="DEPENDENCY_ERROR",
        )


class ConfigurationError(KaguraError):
    """Configuration is invalid or missing."""

    def __init__(
        self,
        message: str,
        config_key: str | None = None,
        help_text: str | None = None,
    ):
        """Initialize ConfigurationError.

        Args:
            message: Error message
            config_key: Configuration key that's problematic
            help_text: Optional help text
        """
        details = {}
        if config_key:
            details["config_key"] = config_key

        super().__init__(
            message=message,
            details=details,
            help_text=help_text or "Run 'kagura config doctor' for diagnostics",
            error_code="CONFIG_ERROR",
        )
