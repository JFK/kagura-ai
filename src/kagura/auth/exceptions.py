"""Custom exceptions for authentication module"""


class AuthenticationError(Exception):
    """Base exception for authentication errors"""

    pass


class NotAuthenticatedError(AuthenticationError):
    """Raised when user is not authenticated"""

    def __init__(self, provider: str):
        self.provider = provider
        super().__init__(
            f"Not authenticated with {provider}. "
            f"Please run: kagura auth login --provider {provider}"
        )


class InvalidCredentialsError(AuthenticationError):
    """Raised when credentials are invalid or corrupted"""

    def __init__(self, message: str = "Invalid or corrupted credentials"):
        super().__init__(message)


class TokenRefreshError(AuthenticationError):
    """Raised when token refresh fails"""

    def __init__(self, provider: str, reason: str | None = None):
        self.provider = provider
        self.reason = reason
        message = f"Failed to refresh token for {provider}"
        if reason:
            message += f": {reason}"
        super().__init__(message)
