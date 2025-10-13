"""Tests for authentication exceptions"""

import pytest

from kagura.auth.exceptions import (
    AuthenticationError,
    InvalidCredentialsError,
    NotAuthenticatedError,
    TokenRefreshError,
)


class TestAuthenticationError:
    """Tests for AuthenticationError base exception"""

    def test_authentication_error_basic(self):
        """Test AuthenticationError can be raised"""
        with pytest.raises(AuthenticationError) as exc_info:
            raise AuthenticationError("Test error")

        assert "Test error" in str(exc_info.value)

    def test_authentication_error_inheritance(self):
        """Test AuthenticationError is an Exception"""
        error = AuthenticationError("Test")
        assert isinstance(error, Exception)


class TestNotAuthenticatedError:
    """Tests for NotAuthenticatedError"""

    def test_not_authenticated_error(self):
        """Test NotAuthenticatedError with provider"""
        error = NotAuthenticatedError("google")

        assert error.provider == "google"
        assert "google" in str(error).lower()
        assert "kagura auth login" in str(error).lower()

    def test_not_authenticated_error_inheritance(self):
        """Test NotAuthenticatedError inherits from AuthenticationError"""
        error = NotAuthenticatedError("google")
        assert isinstance(error, AuthenticationError)


class TestInvalidCredentialsError:
    """Tests for InvalidCredentialsError"""

    def test_invalid_credentials_error_default(self):
        """Test InvalidCredentialsError with default message"""
        error = InvalidCredentialsError()

        assert "Invalid or corrupted credentials" in str(error)

    def test_invalid_credentials_error_custom(self):
        """Test InvalidCredentialsError with custom message"""
        error = InvalidCredentialsError("Custom error message")

        assert "Custom error message" in str(error)

    def test_invalid_credentials_error_inheritance(self):
        """Test InvalidCredentialsError inherits from AuthenticationError"""
        error = InvalidCredentialsError()
        assert isinstance(error, AuthenticationError)


class TestTokenRefreshError:
    """Tests for TokenRefreshError"""

    def test_token_refresh_error_no_reason(self):
        """Test TokenRefreshError without reason"""
        error = TokenRefreshError("google")

        assert error.provider == "google"
        assert error.reason is None
        assert "google" in str(error).lower()
        assert "refresh token" in str(error).lower()

    def test_token_refresh_error_with_reason(self):
        """Test TokenRefreshError with reason"""
        error = TokenRefreshError("google", reason="Network timeout")

        assert error.provider == "google"
        assert error.reason == "Network timeout"
        assert "google" in str(error).lower()
        assert "Network timeout" in str(error)

    def test_token_refresh_error_inheritance(self):
        """Test TokenRefreshError inherits from AuthenticationError"""
        error = TokenRefreshError("google")
        assert isinstance(error, AuthenticationError)
