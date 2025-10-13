"""Tests for AuthConfig"""

from pathlib import Path

from kagura.auth.config import AuthConfig


class TestAuthConfig:
    """Tests for AuthConfig dataclass"""

    def test_default_values(self):
        """Test AuthConfig with default values"""
        config = AuthConfig()

        assert config.provider == "google"
        assert config.client_secrets_path is None
        assert config.credentials_path is None
        assert isinstance(config.scopes, list)
        assert len(config.scopes) == 2
        assert "generative-language" in config.scopes[0]

    def test_custom_provider(self):
        """Test AuthConfig with custom provider"""
        config = AuthConfig(provider="custom_provider")

        assert config.provider == "custom_provider"

    def test_custom_paths(self, tmp_path: Path):
        """Test AuthConfig with custom paths"""
        secrets_path = tmp_path / "secrets.json"
        creds_path = tmp_path / "creds.json"

        config = AuthConfig(
            client_secrets_path=secrets_path,
            credentials_path=creds_path,
        )

        assert config.client_secrets_path == secrets_path
        assert config.credentials_path == creds_path

    def test_custom_scopes(self):
        """Test AuthConfig with custom scopes"""
        custom_scopes = [
            "https://www.googleapis.com/auth/custom",
            "openid",
        ]

        config = AuthConfig(scopes=custom_scopes)

        assert config.scopes == custom_scopes

    def test_path_types(self, tmp_path: Path):
        """Test AuthConfig accepts Path objects"""
        config = AuthConfig(
            client_secrets_path=tmp_path / "secrets.json",
            credentials_path=tmp_path / "creds.json",
        )

        assert isinstance(config.client_secrets_path, Path)
        assert isinstance(config.credentials_path, Path)

    def test_empty_scopes(self):
        """Test AuthConfig with empty scopes"""
        config = AuthConfig(scopes=[])

        assert config.scopes == []

    def test_pydantic_validation(self):
        """Test Pydantic validation works"""
        # Should not raise validation error
        config = AuthConfig(
            provider="google",
            scopes=["scope1", "scope2"],
        )

        assert config.provider == "google"
        assert len(config.scopes) == 2

    def test_config_immutability(self):
        """Test config can be updated (Pydantic allows mutation by default)"""
        config = AuthConfig()
        config.provider = "new_provider"

        assert config.provider == "new_provider"
