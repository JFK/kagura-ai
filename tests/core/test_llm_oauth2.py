"""Tests for LLMConfig OAuth2 integration"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from kagura.core.llm import LLMConfig


class TestLLMConfigOAuth2:
    """Tests for OAuth2 authentication in LLMConfig"""

    def test_default_api_key_auth(self):
        """Test default authentication type is API key"""
        config = LLMConfig()
        assert config.auth_type == "api_key"
        assert config.oauth_provider is None

    def test_api_key_auth_returns_none(self):
        """Test API key auth returns None (LiteLLM uses env vars)"""
        config = LLMConfig(auth_type="api_key")
        api_key = config.get_api_key()
        assert api_key is None

    def test_oauth2_without_provider_raises_error(self):
        """Test OAuth2 without provider raises ValueError"""
        config = LLMConfig(auth_type="oauth2")

        with pytest.raises(ValueError) as exc_info:
            config.get_api_key()

        assert "oauth_provider must be specified" in str(exc_info.value)

    def test_oauth2_with_google_provider(self, tmp_path: Path, monkeypatch):
        """Test OAuth2 with Google provider gets token"""
        monkeypatch.setenv("HOME", str(tmp_path))

        # Mock OAuth2Manager (patch where it's used in llm.py)
        with patch("kagura.auth.OAuth2Manager") as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.get_token.return_value = "mock_oauth2_token_12345"
            mock_manager_class.return_value = mock_manager

            config = LLMConfig(
                auth_type="oauth2",
                oauth_provider="google",
                model="gemini/gemini-1.5-flash",
            )

            token = config.get_api_key()

            assert token == "mock_oauth2_token_12345"
            mock_manager_class.assert_called_once_with(provider="google")
            mock_manager.get_token.assert_called_once()

    def test_oauth2_config_creation(self):
        """Test creating LLMConfig with OAuth2 settings"""
        config = LLMConfig(
            model="gemini/gemini-1.5-flash",
            auth_type="oauth2",
            oauth_provider="google",
            temperature=0.5,
        )

        assert config.model == "gemini/gemini-1.5-flash"
        assert config.auth_type == "oauth2"
        assert config.oauth_provider == "google"
        assert config.temperature == 0.5

    def test_oauth2_not_authenticated_error(self, tmp_path: Path, monkeypatch):
        """Test OAuth2 raises error when not authenticated"""
        monkeypatch.setenv("HOME", str(tmp_path))

        from kagura.auth.exceptions import NotAuthenticatedError

        with patch("kagura.auth.OAuth2Manager") as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.get_token.side_effect = NotAuthenticatedError("google")
            mock_manager_class.return_value = mock_manager

            config = LLMConfig(auth_type="oauth2", oauth_provider="google")

            with pytest.raises(NotAuthenticatedError):
                config.get_api_key()


class TestLLMConfigOAuth2Integration:
    """Integration tests for OAuth2 in LLM calls"""

    def test_gemini_with_oauth2_config(self):
        """Test Gemini model configuration with OAuth2"""
        config = LLMConfig(
            model="gemini/gemini-1.5-flash",
            auth_type="oauth2",
            oauth_provider="google",
            temperature=0.7,
            max_tokens=1000,
        )

        assert config.model == "gemini/gemini-1.5-flash"
        assert config.auth_type == "oauth2"
        assert config.oauth_provider == "google"
        assert config.temperature == 0.7
        assert config.max_tokens == 1000

    def test_openai_with_api_key_config(self):
        """Test OpenAI model configuration with API key (default)"""
        config = LLMConfig(model="gpt-5-mini", temperature=0.5)

        assert config.model == "gpt-5-mini"
        assert config.auth_type == "api_key"
        assert config.oauth_provider is None
        assert config.temperature == 0.5


@pytest.mark.asyncio
async def test_call_llm_with_oauth2_mock(tmp_path: Path, monkeypatch):
    """Test call_llm uses OAuth2 token when configured"""
    monkeypatch.setenv("HOME", str(tmp_path))

    from kagura.core.llm import call_llm

    # Mock OAuth2Manager to return a token
    with patch("kagura.auth.OAuth2Manager") as mock_manager_class:
        mock_manager = MagicMock()
        mock_manager.get_token.return_value = "mock_oauth2_token"
        mock_manager_class.return_value = mock_manager

        # Mock Gemini SDK (since gemini/* uses Gemini direct backend now)
        with patch("google.generativeai.GenerativeModel") as mock_model_class:
            # Mock Gemini response
            mock_model = MagicMock()
            mock_response = MagicMock()
            mock_response.text = "Hello from Gemini!"

            from unittest.mock import AsyncMock

            mock_model.generate_content_async = AsyncMock(return_value=mock_response)
            mock_model_class.return_value = mock_model

            # Mock genai.configure
            with patch("google.generativeai.configure"):
                config = LLMConfig(
                    model="gemini/gemini-1.5-flash",
                    auth_type="oauth2",
                    oauth_provider="google",
                )

                result = await call_llm("Test prompt", config)

                assert "Hello from Gemini!" in str(result)
                # Verify OAuth2Manager was called
                mock_manager_class.assert_called_once_with(provider="google")
                mock_manager.get_token.assert_called_once()
