"""Unified exception system for Kagura AI

This module provides a hierarchical exception system with error codes,
structured error details, and retry strategies.

Error Code Format:
    {CATEGORY}-{NUMBER}

    Categories:
    - AUTH: Authentication/Authorization errors (AUTH-001, AUTH-002, ...)
    - EXEC: Code execution errors (EXEC-001, EXEC-002, ...)
    - LLM: LLM API errors (LLM-001, LLM-002, ...)
    - COMP: Compression/Context errors (COMP-001, COMP-002, ...)
    - ROUTE: Routing errors (ROUTE-001, ROUTE-002, ...)
    - VAL: Validation errors (VAL-001, VAL-002, ...)
    - RES: Resource errors (RES-001, RES-002, ...)
    - SEC: Security errors (SEC-001, SEC-002, ...)
"""

from __future__ import annotations

from typing import Any


class KaguraError(Exception):
    """Base exception for all Kagura AI errors

    Attributes:
        message: Human-readable error message
        code: Error code (e.g., "AUTH-001", "EXEC-002")
        details: Additional context about the error
        recoverable: Whether the error can be recovered from (for retry strategies)
    """

    def __init__(
        self,
        message: str,
        code: str | None = None,
        recoverable: bool = False,
        **details: Any,
    ) -> None:
        """Initialize Kagura error

        Args:
            message: Error message
            code: Error code (e.g., "AUTH-001")
            recoverable: Whether error is recoverable (for retry)
            **details: Additional context (e.g., provider="google", status_code=401)
        """
        super().__init__(message)
        self.message = message
        self.code = code or self._default_code()
        self.details = details
        self.recoverable = recoverable

    def _default_code(self) -> str:
        """Get default error code for this exception class"""
        return "KAGURA-000"

    def __str__(self) -> str:
        """Format error message with code"""
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message

    def __repr__(self) -> str:
        """Detailed representation for debugging"""
        parts = [f"{self.__class__.__name__}"]
        parts.append(f"code={self.code!r}")
        parts.append(f"message={self.message!r}")
        if self.details:
            parts.append(f"details={self.details!r}")
        return f"<{' '.join(parts)}>"


# ============================================
# Authentication & Authorization Errors
# ============================================


class AuthenticationError(KaguraError):
    """Authentication/authorization failures"""

    def _default_code(self) -> str:
        return "AUTH-000"


class NotAuthenticatedError(AuthenticationError):
    """User is not authenticated

    Error Code: AUTH-001
    """

    def __init__(self, provider: str) -> None:
        super().__init__(
            f"Not authenticated with {provider}. "
            f"Please run: kagura auth login --provider {provider}",
            code="AUTH-001",
            recoverable=False,
            provider=provider,
        )
        self.provider = provider


class InvalidCredentialsError(AuthenticationError):
    """Credentials are invalid or corrupted

    Error Code: AUTH-002
    """

    def __init__(self, message: str = "Invalid or corrupted credentials") -> None:
        super().__init__(message, code="AUTH-002", recoverable=False)


class TokenRefreshError(AuthenticationError):
    """Token refresh failed

    Error Code: AUTH-003
    """

    def __init__(self, provider: str, reason: str | None = None) -> None:
        message = f"Failed to refresh token for {provider}"
        if reason:
            message += f": {reason}"
        super().__init__(
            message, code="AUTH-003", recoverable=True, provider=provider, reason=reason
        )
        self.provider = provider
        self.reason = reason


# ============================================
# Code Execution Errors
# ============================================


class ExecutionError(KaguraError):
    """Code execution failures"""

    def _default_code(self) -> str:
        return "EXEC-000"


class SecurityError(ExecutionError):
    """Security violation during execution

    Error Code: EXEC-001
    """

    def __init__(self, message: str, violation_type: str | None = None) -> None:
        super().__init__(
            message,
            code="EXEC-001",
            recoverable=False,
            violation_type=violation_type,
        )
        self.violation_type = violation_type


class UserCancelledError(ExecutionError):
    """User cancelled execution

    Error Code: EXEC-002
    """

    def __init__(self, message: str = "User cancelled execution") -> None:
        super().__init__(message, code="EXEC-002", recoverable=False)


class CodeExecutionError(ExecutionError):
    """Code execution failed

    Error Code: EXEC-003
    """

    def __init__(
        self,
        message: str,
        code_snippet: str | None = None,
        error_traceback: str | None = None,
    ) -> None:
        super().__init__(
            message,
            code="EXEC-003",
            recoverable=False,
            code_snippet=code_snippet,
            error_traceback=error_traceback,
        )


# ============================================
# LLM API Errors
# ============================================


class LLMError(KaguraError):
    """LLM API failures"""

    def _default_code(self) -> str:
        return "LLM-000"


class LLMAPIError(LLMError):
    """LLM API request failed

    Error Code: LLM-001
    """

    def __init__(
        self,
        message: str,
        provider: str | None = None,
        model: str | None = None,
        status_code: int | None = None,
    ) -> None:
        # Determine if recoverable based on status code
        recoverable = status_code in (429, 500, 502, 503, 504) if status_code else True
        super().__init__(
            message,
            code="LLM-001",
            recoverable=recoverable,
            provider=provider,
            model=model,
            status_code=status_code,
        )


class LLMRateLimitError(LLMError):
    """LLM rate limit exceeded

    Error Code: LLM-002
    """

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int | None = None,
        provider: str | None = None,
    ) -> None:
        super().__init__(
            message,
            code="LLM-002",
            recoverable=True,
            retry_after=retry_after,
            provider=provider,
        )
        self.retry_after = retry_after


class LLMTimeoutError(LLMError):
    """LLM request timed out

    Error Code: LLM-003
    """

    def __init__(
        self, message: str = "LLM request timed out", timeout: float | None = None
    ) -> None:
        super().__init__(message, code="LLM-003", recoverable=True, timeout=timeout)
        self.timeout = timeout


# ============================================
# Compression & Context Errors
# ============================================


class CompressionError(KaguraError):
    """Compression/context management failures"""

    def _default_code(self) -> str:
        return "COMP-000"


class TokenCountError(CompressionError):
    """Token counting failed

    Error Code: COMP-001
    """

    def __init__(
        self, message: str, model: str | None = None, text_length: int | None = None
    ) -> None:
        super().__init__(
            message,
            code="COMP-001",
            recoverable=False,
            model=model,
            text_length=text_length,
        )


class ModelNotSupportedError(CompressionError):
    """Model not supported for compression

    Error Code: COMP-002
    """

    def __init__(self, model: str, supported_models: list[str] | None = None) -> None:
        message = f"Model '{model}' is not supported"
        if supported_models:
            message += f". Supported models: {', '.join(supported_models[:5])}"
            if len(supported_models) > 5:
                message += f" (and {len(supported_models) - 5} more)"
        super().__init__(
            message,
            code="COMP-002",
            recoverable=False,
            model=model,
            supported_models=supported_models,
        )


class ContextLimitExceededError(CompressionError):
    """Context window limit exceeded

    Error Code: COMP-003
    """

    def __init__(
        self,
        message: str,
        current_tokens: int | None = None,
        max_tokens: int | None = None,
    ) -> None:
        super().__init__(
            message,
            code="COMP-003",
            recoverable=False,
            current_tokens=current_tokens,
            max_tokens=max_tokens,
        )


# ============================================
# Routing Errors
# ============================================


class RoutingError(KaguraError):
    """Agent routing failures"""

    def _default_code(self) -> str:
        return "ROUTE-000"


class NoAgentFoundError(RoutingError):
    """No suitable agent found

    Error Code: ROUTE-001
    """

    def __init__(self, message: str, user_input: str | None = None) -> None:
        super().__init__(
            message, code="ROUTE-001", recoverable=False, user_input=user_input
        )
        self.user_input = user_input


class AgentNotRegisteredError(RoutingError):
    """Agent not registered

    Error Code: ROUTE-002
    """

    def __init__(self, agent_name: str) -> None:
        super().__init__(
            f"Agent '{agent_name}' is not registered",
            code="ROUTE-002",
            recoverable=False,
            agent_name=agent_name,
        )
        self.agent_name = agent_name


class InvalidRouterStrategyError(RoutingError):
    """Invalid routing strategy

    Error Code: ROUTE-003
    """

    def __init__(self, strategy: str, valid_strategies: list[str]) -> None:
        super().__init__(
            f"Invalid strategy '{strategy}'. "
            f"Valid strategies: {', '.join(valid_strategies)}",
            code="ROUTE-003",
            recoverable=False,
            strategy=strategy,
            valid_strategies=valid_strategies,
        )
        self.strategy = strategy
        self.valid_strategies = valid_strategies


# ============================================
# Validation Errors
# ============================================


class ValidationError(KaguraError):
    """Input/output validation failures"""

    def _default_code(self) -> str:
        return "VAL-000"


class SchemaValidationError(ValidationError):
    """Schema validation failed

    Error Code: VAL-001
    """

    def __init__(
        self,
        message: str,
        field: str | None = None,
        expected_type: str | None = None,
        actual_value: Any = None,
    ) -> None:
        super().__init__(
            message,
            code="VAL-001",
            recoverable=False,
            field=field,
            expected_type=expected_type,
            actual_value=str(actual_value) if actual_value is not None else None,
        )


# ============================================
# Resource Errors
# ============================================


class ResourceError(KaguraError):
    """Resource access/management failures"""

    def _default_code(self) -> str:
        return "RES-000"


class FileNotFoundError(ResourceError):
    """File not found

    Error Code: RES-001
    """

    def __init__(self, path: str) -> None:
        super().__init__(
            f"File not found: {path}", code="RES-001", recoverable=False, path=path
        )
        self.path = path


class PermissionDeniedError(ResourceError):
    """Permission denied

    Error Code: RES-002
    """

    def __init__(self, path: str, operation: str | None = None) -> None:
        message = f"Permission denied: {path}"
        if operation:
            message += f" (operation: {operation})"
        super().__init__(
            message, code="RES-002", recoverable=False, path=path, operation=operation
        )


# ============================================
# Legacy Aliases (for backward compatibility)
# ============================================

# Maintain backward compatibility with old exception names
# These can be deprecated in future versions

__all__ = [
    # Base
    "KaguraError",
    # Auth
    "AuthenticationError",
    "NotAuthenticatedError",
    "InvalidCredentialsError",
    "TokenRefreshError",
    # Execution
    "ExecutionError",
    "SecurityError",
    "UserCancelledError",
    "CodeExecutionError",
    # LLM
    "LLMError",
    "LLMAPIError",
    "LLMRateLimitError",
    "LLMTimeoutError",
    # Compression
    "CompressionError",
    "TokenCountError",
    "ModelNotSupportedError",
    "ContextLimitExceededError",
    # Routing
    "RoutingError",
    "NoAgentFoundError",
    "AgentNotRegisteredError",
    "InvalidRouterStrategyError",
    # Validation
    "ValidationError",
    "SchemaValidationError",
    # Resource
    "ResourceError",
    "FileNotFoundError",
    "PermissionDeniedError",
]
