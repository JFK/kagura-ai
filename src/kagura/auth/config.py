"""Authentication configuration"""

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class AuthConfig(BaseModel):
    """Configuration for OAuth2 authentication

    Args:
        provider: OAuth2 provider name (e.g., "google")
        client_secrets_path: Path to client_secrets.json file
        credentials_path: Path to encrypted credentials file
        scopes: List of OAuth2 scopes to request

    Example:
        >>> config = AuthConfig(
        ...     provider="google",
        ...     scopes=["https://www.googleapis.com/auth/generative-language"]
        ... )
    """

    provider: str = Field(default="google", description="OAuth2 provider name")
    client_secrets_path: Path | None = Field(
        default=None, description="Path to client_secrets.json"
    )
    credentials_path: Path | None = Field(
        default=None, description="Path to encrypted credentials"
    )
    scopes: list[str] = Field(
        default_factory=lambda: [
            "https://www.googleapis.com/auth/generative-language",
            "openid",
        ],
        description="OAuth2 scopes to request",
    )

    model_config = ConfigDict(
        # Allow arbitrary types like Path
        arbitrary_types_allowed=True
    )
