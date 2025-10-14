"""Tests for unified exception system"""

import pytest

from kagura.exceptions import (
    AgentNotRegisteredError,
    AuthenticationError,
    CodeExecutionError,
    CompressionError,
    ContextLimitExceededError,
    ExecutionError,
    InvalidCredentialsError,
    InvalidRouterStrategyError,
    KaguraError,
    LLMAPIError,
    LLMError,
    LLMRateLimitError,
    LLMTimeoutError,
    ModelNotSupportedError,
    NoAgentFoundError,
    NotAuthenticatedError,
    PermissionDeniedError,
    ResourceError,
    RoutingError,
    SchemaValidationError,
    SecurityError,
    TokenCountError,
    TokenRefreshError,
    UserCancelledError,
    ValidationError,
)


class TestKaguraError:
    """Tests for base KaguraError"""

    def test_basic_error(self):
        """Test basic error creation"""
        error = KaguraError("Test error")
        assert str(error) == "[KAGURA-000] Test error"
        assert error.code == "KAGURA-000"
        assert error.message == "Test error"
        assert error.recoverable is False

    def test_error_with_code(self):
        """Test error with custom code"""
        error = KaguraError("Test error", code="TEST-001")
        assert str(error) == "[TEST-001] Test error"
        assert error.code == "TEST-001"

    def test_error_with_details(self):
        """Test error with additional details"""
        error = KaguraError(
            "Test error", code="TEST-001", provider="test", status=500
        )
        assert error.details == {"provider": "test", "status": 500}

    def test_error_recoverable(self):
        """Test recoverable error"""
        error = KaguraError("Test error", recoverable=True)
        assert error.recoverable is True

    def test_error_repr(self):
        """Test error representation"""
        error = KaguraError("Test error", code="TEST-001", foo="bar")
        repr_str = repr(error)
        assert "KaguraError" in repr_str
        assert "TEST-001" in repr_str
        assert "foo" in repr_str


class TestAuthenticationErrors:
    """Tests for authentication errors"""

    def test_not_authenticated_error(self):
        """Test NotAuthenticatedError"""
        error = NotAuthenticatedError("google")
        assert str(error).startswith("[AUTH-001]")
        assert "google" in str(error)
        assert error.code == "AUTH-001"
        assert error.provider == "google"
        assert error.recoverable is False

    def test_invalid_credentials_error(self):
        """Test InvalidCredentialsError"""
        error = InvalidCredentialsError("Custom message")
        assert error.code == "AUTH-002"
        assert "Custom message" in str(error)

    def test_token_refresh_error(self):
        """Test TokenRefreshError"""
        error = TokenRefreshError("google", reason="expired")
        assert error.code == "AUTH-003"
        assert error.provider == "google"
        assert error.reason == "expired"
        assert error.recoverable is True


class TestExecutionErrors:
    """Tests for code execution errors"""

    def test_security_error(self):
        """Test SecurityError"""
        error = SecurityError("Dangerous operation", violation_type="import_blocked")
        assert error.code == "EXEC-001"
        assert error.violation_type == "import_blocked"
        assert error.recoverable is False

    def test_user_cancelled_error(self):
        """Test UserCancelledError"""
        error = UserCancelledError()
        assert error.code == "EXEC-002"
        assert "cancelled" in str(error).lower()

    def test_code_execution_error(self):
        """Test CodeExecutionError"""
        error = CodeExecutionError(
            "Execution failed",
            code_snippet="print('hello')",
            error_traceback="Traceback...",
        )
        assert error.code == "EXEC-003"
        assert error.details["code_snippet"] == "print('hello')"
        assert error.details["error_traceback"] == "Traceback..."


class TestLLMErrors:
    """Tests for LLM API errors"""

    def test_llm_api_error_recoverable(self):
        """Test LLM API error with recoverable status code"""
        error = LLMAPIError(
            "Rate limit", provider="openai", model="gpt-4", status_code=429
        )
        assert error.code == "LLM-001"
        assert error.recoverable is True

    def test_llm_api_error_not_recoverable(self):
        """Test LLM API error with non-recoverable status code"""
        error = LLMAPIError(
            "Invalid request", provider="openai", status_code=400
        )
        assert error.recoverable is False

    def test_llm_rate_limit_error(self):
        """Test LLM rate limit error"""
        error = LLMRateLimitError(retry_after=60, provider="anthropic")
        assert error.code == "LLM-002"
        assert error.retry_after == 60
        assert error.recoverable is True

    def test_llm_timeout_error(self):
        """Test LLM timeout error"""
        error = LLMTimeoutError(timeout=30.0)
        assert error.code == "LLM-003"
        assert error.timeout == 30.0
        assert error.recoverable is True


class TestCompressionErrors:
    """Tests for compression errors"""

    def test_token_count_error(self):
        """Test TokenCountError"""
        error = TokenCountError("Failed to count", model="gpt-4", text_length=1000)
        assert error.code == "COMP-001"
        assert error.details["model"] == "gpt-4"
        assert error.details["text_length"] == 1000

    def test_model_not_supported_error(self):
        """Test ModelNotSupportedError"""
        error = ModelNotSupportedError("unknown-model", supported_models=["gpt-4", "gpt-3.5"])
        assert error.code == "COMP-002"
        assert "unknown-model" in str(error)
        assert "gpt-4" in str(error)

    def test_model_not_supported_error_many_models(self):
        """Test ModelNotSupportedError with many supported models"""
        models = [f"model-{i}" for i in range(10)]
        error = ModelNotSupportedError("unknown", supported_models=models)
        assert "and 5 more" in str(error)

    def test_context_limit_exceeded_error(self):
        """Test ContextLimitExceededError"""
        error = ContextLimitExceededError(
            "Limit exceeded", current_tokens=5000, max_tokens=4096
        )
        assert error.code == "COMP-003"
        assert error.details["current_tokens"] == 5000
        assert error.details["max_tokens"] == 4096


class TestRoutingErrors:
    """Tests for routing errors"""

    def test_no_agent_found_error(self):
        """Test NoAgentFoundError"""
        error = NoAgentFoundError("No match", user_input="translate hello")
        assert error.code == "ROUTE-001"
        assert error.user_input == "translate hello"

    def test_agent_not_registered_error(self):
        """Test AgentNotRegisteredError"""
        error = AgentNotRegisteredError("translator")
        assert error.code == "ROUTE-002"
        assert error.agent_name == "translator"
        assert "translator" in str(error)

    def test_invalid_router_strategy_error(self):
        """Test InvalidRouterStrategyError"""
        error = InvalidRouterStrategyError("bad", ["keyword", "llm", "semantic"])
        assert error.code == "ROUTE-003"
        assert error.strategy == "bad"
        assert "keyword, llm, semantic" in str(error)


class TestValidationErrors:
    """Tests for validation errors"""

    def test_schema_validation_error(self):
        """Test SchemaValidationError"""
        error = SchemaValidationError(
            "Invalid type",
            field="age",
            expected_type="int",
            actual_value="not a number",
        )
        assert error.code == "VAL-001"
        assert error.details["field"] == "age"
        assert error.details["expected_type"] == "int"
        assert error.details["actual_value"] == "not a number"


class TestResourceErrors:
    """Tests for resource errors"""

    def test_permission_denied_error(self):
        """Test PermissionDeniedError"""
        error = PermissionDeniedError("/path/to/file", operation="write")
        assert error.code == "RES-002"
        assert "/path/to/file" in str(error)
        assert "write" in str(error)


class TestErrorHierarchy:
    """Tests for exception hierarchy"""

    def test_auth_hierarchy(self):
        """Test authentication error hierarchy"""
        assert issubclass(NotAuthenticatedError, AuthenticationError)
        assert issubclass(AuthenticationError, KaguraError)
        assert issubclass(NotAuthenticatedError, Exception)

    def test_execution_hierarchy(self):
        """Test execution error hierarchy"""
        assert issubclass(SecurityError, ExecutionError)
        assert issubclass(ExecutionError, KaguraError)

    def test_llm_hierarchy(self):
        """Test LLM error hierarchy"""
        assert issubclass(LLMAPIError, LLMError)
        assert issubclass(LLMRateLimitError, LLMError)
        assert issubclass(LLMError, KaguraError)

    def test_compression_hierarchy(self):
        """Test compression error hierarchy"""
        assert issubclass(TokenCountError, CompressionError)
        assert issubclass(CompressionError, KaguraError)

    def test_routing_hierarchy(self):
        """Test routing error hierarchy"""
        assert issubclass(NoAgentFoundError, RoutingError)
        assert issubclass(RoutingError, KaguraError)

    def test_validation_hierarchy(self):
        """Test validation error hierarchy"""
        assert issubclass(SchemaValidationError, ValidationError)
        assert issubclass(ValidationError, KaguraError)

    def test_resource_hierarchy(self):
        """Test resource error hierarchy"""
        assert issubclass(PermissionDeniedError, ResourceError)
        assert issubclass(ResourceError, KaguraError)


class TestErrorCatchability:
    """Tests for catching errors at different levels"""

    def test_catch_specific_error(self):
        """Test catching specific error"""
        with pytest.raises(NotAuthenticatedError) as exc_info:
            raise NotAuthenticatedError("google")
        assert exc_info.value.code == "AUTH-001"

    def test_catch_category_error(self):
        """Test catching category-level error"""
        with pytest.raises(AuthenticationError):
            raise NotAuthenticatedError("google")

    def test_catch_base_error(self):
        """Test catching base KaguraError"""
        with pytest.raises(KaguraError):
            raise NotAuthenticatedError("google")

    def test_catch_exception(self):
        """Test catching as Exception"""
        with pytest.raises(Exception):
            raise NotAuthenticatedError("google")
