"""Tests for unified error handling."""

from __future__ import annotations

import json

import pytest

from kagura.utils.errors import (
    AuthenticationError,
    ConfigurationError,
    DependencyError,
    KaguraError,
    MemoryNotFoundError,
    SessionError,
    ValidationError,
)


class TestKaguraError:
    """Tests for KaguraError base class."""

    def test_basic_error_creation(self) -> None:
        """Test creating a basic error."""
        error = KaguraError("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.details == {}
        assert error.help_text is None

    def test_error_with_details(self) -> None:
        """Test error with details dict."""
        error = KaguraError("Test error", details={"key": "value"})
        assert error.details == {"key": "value"}

    def test_error_with_help_text(self) -> None:
        """Test error with help text."""
        error = KaguraError("Test error", help_text="Try this solution")
        assert error.help_text == "Try this solution"

    def test_error_with_code(self) -> None:
        """Test error with error code."""
        error = KaguraError("Test error", error_code="TEST_001")
        assert error.error_code == "TEST_001"

    def test_to_mcp_response(self) -> None:
        """Test MCP response formatting."""
        error = KaguraError(
            "Test error",
            details={"key": "value"},
            help_text="Help text",
            error_code="TEST_001",
        )
        response = error.to_mcp_response()
        data = json.loads(response)

        assert data["status"] == "error"
        assert data["error"] == "Test error"
        assert data["code"] == "TEST_001"
        assert data["details"] == {"key": "value"}
        assert data["help"] == "Help text"

    def test_to_cli_message(self) -> None:
        """Test CLI message formatting."""
        error = KaguraError(
            "Test error",
            details={"key": "value"},
            help_text="Help text",
        )
        message = error.to_cli_message()

        assert "❌ Error: Test error" in message
        assert "Details:" in message
        assert "key: value" in message
        assert "💡 Help: Help text" in message

    def test_to_http_exception(self) -> None:
        """Test HTTP exception formatting."""
        error = KaguraError(
            "Test error",
            details={"key": "value"},
            help_text="Help text",
            error_code="TEST_001",
        )
        exc_detail = error.to_http_exception()

        assert exc_detail["error"] == "Test error"
        assert exc_detail["code"] == "TEST_001"
        assert exc_detail["details"] == {"key": "value"}
        assert exc_detail["help"] == "Help text"


class TestMemoryNotFoundError:
    """Tests for MemoryNotFoundError."""

    def test_memory_not_found_message(self) -> None:
        """Test error message format."""
        error = MemoryNotFoundError("user_prefs", scope="persistent")
        assert "user_prefs" in error.message
        assert "persistent" in error.message

    def test_memory_not_found_details(self) -> None:
        """Test error details."""
        error = MemoryNotFoundError("user_prefs", scope="working")
        assert error.details["key"] == "user_prefs"
        assert error.details["scope"] == "working"

    def test_memory_not_found_has_help_text(self) -> None:
        """Test default help text."""
        error = MemoryNotFoundError("user_prefs")
        assert error.help_text is not None
        assert "memory_list" in error.help_text or "Check" in error.help_text

    def test_memory_not_found_error_code(self) -> None:
        """Test error code."""
        error = MemoryNotFoundError("user_prefs")
        assert error.error_code == "MEMORY_NOT_FOUND"


class TestValidationError:
    """Tests for ValidationError."""

    def test_validation_error_message(self) -> None:
        """Test error message format."""
        error = ValidationError("count", "must be positive")
        assert "count" in error.message
        assert "must be positive" in error.message

    def test_validation_error_with_expected_received(self) -> None:
        """Test validation error with expected and received values."""
        error = ValidationError(
            "count",
            "invalid type",
            expected="int",
            received="abc",
        )
        assert error.details["expected"] == "int"
        assert error.details["received"] == "abc"

    def test_validation_error_code(self) -> None:
        """Test error code."""
        error = ValidationError("param", "invalid")
        assert error.error_code == "VALIDATION_ERROR"


class TestAuthenticationError:
    """Tests for AuthenticationError."""

    def test_auth_error_default_message(self) -> None:
        """Test default authentication error."""
        error = AuthenticationError()
        assert error.message == "Authentication failed"

    def test_auth_error_with_service(self) -> None:
        """Test authentication error with service name."""
        error = AuthenticationError("API key required", service="Brave Search")
        assert error.details["service"] == "Brave Search"

    def test_auth_error_has_help_text(self) -> None:
        """Test default help text."""
        error = AuthenticationError()
        assert "API key" in error.help_text or "credentials" in error.help_text

    def test_auth_error_code(self) -> None:
        """Test error code."""
        error = AuthenticationError()
        assert error.error_code == "AUTH_ERROR"


class TestSessionError:
    """Tests for SessionError."""

    def test_session_error_basic(self) -> None:
        """Test basic session error."""
        error = SessionError("Session already active")
        assert "Session already active" in error.message

    def test_session_error_with_id(self) -> None:
        """Test session error with session ID."""
        error = SessionError("Session not found", session_id="sess_123")
        assert error.details["session_id"] == "sess_123"

    def test_session_error_code(self) -> None:
        """Test error code."""
        error = SessionError("Test")
        assert error.error_code == "SESSION_ERROR"


class TestDependencyError:
    """Tests for DependencyError."""

    def test_dependency_error_message(self) -> None:
        """Test dependency error message."""
        error = DependencyError("chromadb", "pip install chromadb")
        assert "chromadb" in error.message

    def test_dependency_error_with_feature(self) -> None:
        """Test dependency error with feature name."""
        error = DependencyError("chromadb", "pip install chromadb", feature="RAG search")
        assert "RAG search" in error.message

    def test_dependency_error_help_text(self) -> None:
        """Test installation command in help text."""
        error = DependencyError("chromadb", "pip install chromadb")
        assert "pip install chromadb" in error.help_text

    def test_dependency_error_code(self) -> None:
        """Test error code."""
        error = DependencyError("pkg", "pip install pkg")
        assert error.error_code == "DEPENDENCY_ERROR"


class TestConfigurationError:
    """Tests for ConfigurationError."""

    def test_config_error_basic(self) -> None:
        """Test basic configuration error."""
        error = ConfigurationError("Invalid config")
        assert "Invalid config" in error.message

    def test_config_error_with_key(self) -> None:
        """Test configuration error with config key."""
        error = ConfigurationError("Missing key", config_key="API_URL")
        assert error.details["config_key"] == "API_URL"

    def test_config_error_has_help_text(self) -> None:
        """Test default help text."""
        error = ConfigurationError("Test")
        assert "config doctor" in error.help_text or "diagnostics" in error.help_text

    def test_config_error_code(self) -> None:
        """Test error code."""
        error = ConfigurationError("Test")
        assert error.error_code == "CONFIG_ERROR"


class TestErrorFormatting:
    """Tests for error formatting across different contexts."""

    def test_mcp_response_is_valid_json(self) -> None:
        """Test that MCP response is valid JSON."""
        error = MemoryNotFoundError("test_key")
        response = error.to_mcp_response()
        data = json.loads(response)  # Should not raise
        assert isinstance(data, dict)

    def test_cli_message_is_string(self) -> None:
        """Test that CLI message is a string."""
        error = ValidationError("param", "invalid")
        message = error.to_cli_message()
        assert isinstance(message, str)
        assert len(message) > 0

    def test_http_exception_is_dict(self) -> None:
        """Test that HTTP exception detail is a dict."""
        error = AuthenticationError("Auth failed")
        exc_detail = error.to_http_exception()
        assert isinstance(exc_detail, dict)
        assert "error" in exc_detail
        assert "code" in exc_detail
