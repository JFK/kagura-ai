"""Tests for environment variable management."""

import warnings

from kagura.config.env import (
    check_required_env_vars,
    get_anthropic_api_key,
    get_anthropic_default_model,
    get_brave_search_api_key,
    get_default_model,
    get_default_temperature,
    get_google_ai_default_model,
    get_google_api_key,
    get_openai_api_key,
    get_openai_default_model,
    list_env_vars,
)


class TestOpenAIAPIKey:
    """Tests for get_openai_api_key()"""

    def test_get_with_env_var(self, monkeypatch):
        """Test getting OpenAI API key from environment"""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test123")
        assert get_openai_api_key() == "sk-test123"

    def test_get_without_env_var(self, monkeypatch):
        """Test getting OpenAI API key when not set"""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        assert get_openai_api_key() is None


class TestAnthropicAPIKey:
    """Tests for get_anthropic_api_key()"""

    def test_get_with_env_var(self, monkeypatch):
        """Test getting Anthropic API key from environment"""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test123")
        assert get_anthropic_api_key() == "sk-ant-test123"

    def test_get_without_env_var(self, monkeypatch):
        """Test getting Anthropic API key when not set"""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        assert get_anthropic_api_key() is None


class TestGoogleAPIKey:
    """Tests for get_google_api_key()"""

    def test_get_with_env_var(self, monkeypatch):
        """Test getting Google API key from environment"""
        monkeypatch.setenv("GOOGLE_API_KEY", "google-test123")
        assert get_google_api_key() == "google-test123"

    def test_get_without_env_var(self, monkeypatch):
        """Test getting Google API key when not set"""
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        assert get_google_api_key() is None


class TestBraveSearchAPIKey:
    """Tests for get_brave_search_api_key()"""

    def test_get_with_env_var(self, monkeypatch):
        """Test getting Brave Search API key"""
        monkeypatch.setenv("BRAVE_SEARCH_API_KEY", "brave-test123")
        assert get_brave_search_api_key() == "brave-test123"

    def test_get_without_env_var(self, monkeypatch):
        """Test getting Brave Search API key when not set"""
        monkeypatch.delenv("BRAVE_SEARCH_API_KEY", raising=False)
        assert get_brave_search_api_key() is None


class TestDefaultModel:
    """Tests for get_default_model()"""

    def test_get_with_env_var(self, monkeypatch):
        """Test getting default model from environment"""
        monkeypatch.setenv("DEFAULT_MODEL", "gpt-4o")
        assert get_default_model() == "gpt-4o"

    def test_get_default_value(self, monkeypatch):
        """Test default value when not set"""
        monkeypatch.delenv("DEFAULT_MODEL", raising=False)
        assert get_default_model() == "gpt-4o-mini"


class TestGoogleAIDefaultModel:
    """Tests for get_google_ai_default_model()"""

    def test_get_with_env_var(self, monkeypatch):
        """Test getting Google AI default model from environment"""
        monkeypatch.setenv("GOOGLE_AI_DEFAULT_MODEL", "gemini/gemini-2.5-flash")
        assert get_google_ai_default_model() == "gemini/gemini-2.5-flash"

    def test_get_default_value(self, monkeypatch):
        """Test default value when not set"""
        monkeypatch.delenv("GOOGLE_AI_DEFAULT_MODEL", raising=False)
        assert get_google_ai_default_model() == "gemini/gemini-2.0-flash-exp"


class TestOpenAIDefaultModel:
    """Tests for get_openai_default_model()"""

    def test_get_with_env_var(self, monkeypatch):
        """Test getting OpenAI default model from environment"""
        monkeypatch.setenv("OPENAI_DEFAULT_MODEL", "gpt-5")
        assert get_openai_default_model() == "gpt-5"

    def test_get_default_value(self, monkeypatch):
        """Test default value when not set"""
        monkeypatch.delenv("OPENAI_DEFAULT_MODEL", raising=False)
        assert get_openai_default_model() == "gpt-5-mini"


class TestAnthropicDefaultModel:
    """Tests for get_anthropic_default_model()"""

    def test_get_with_env_var(self, monkeypatch):
        """Test getting Anthropic default model from environment"""
        monkeypatch.setenv("ANTHROPIC_DEFAULT_MODEL", "claude-haiku-4-5")
        assert get_anthropic_default_model() == "claude-haiku-4-5"

    def test_get_default_value(self, monkeypatch):
        """Test default value when not set"""
        monkeypatch.delenv("ANTHROPIC_DEFAULT_MODEL", raising=False)
        assert get_anthropic_default_model() == "claude-sonnet-4-5"


class TestDefaultTemperature:
    """Tests for get_default_temperature()"""

    def test_get_with_env_var(self, monkeypatch):
        """Test getting default temperature from environment"""
        monkeypatch.setenv("DEFAULT_TEMPERATURE", "0.5")
        assert get_default_temperature() == 0.5

    def test_get_default_value(self, monkeypatch):
        """Test default value when not set"""
        monkeypatch.delenv("DEFAULT_TEMPERATURE", raising=False)
        assert get_default_temperature() == 0.7

    def test_get_with_invalid_value_shows_warning(self, monkeypatch):
        """Test that invalid value shows warning and returns default"""
        monkeypatch.setenv("DEFAULT_TEMPERATURE", "invalid")

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = get_default_temperature()

            # Should return default
            assert result == 0.7

            # Should show warning
            assert len(w) == 1
            assert issubclass(w[0].category, UserWarning)
            assert "Invalid DEFAULT_TEMPERATURE" in str(w[0].message)


class TestListEnvVars:
    """Tests for list_env_vars()"""

    def test_list_all_vars(self, monkeypatch):
        """Test listing all environment variables"""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.setenv("BRAVE_SEARCH_API_KEY", "brave-test")
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

        result = list_env_vars()

        # API keys should be masked
        assert result["OPENAI_API_KEY"] == "***"
        assert result["BRAVE_SEARCH_API_KEY"] == "***"
        assert result["ANTHROPIC_API_KEY"] is None
        assert result["GOOGLE_API_KEY"] is None

        # Non-sensitive values should be shown
        assert result["DEFAULT_MODEL"] is not None
        assert "gpt-4o-mini" in result["DEFAULT_MODEL"]
        assert result["OPENAI_DEFAULT_MODEL"] is not None
        assert "gpt-5-mini" in result["OPENAI_DEFAULT_MODEL"]
        assert result["ANTHROPIC_DEFAULT_MODEL"] is not None
        assert "claude-sonnet-4-5" in result["ANTHROPIC_DEFAULT_MODEL"]
        assert result["GOOGLE_AI_DEFAULT_MODEL"] is not None
        assert "gemini-2.0-flash-exp" in result["GOOGLE_AI_DEFAULT_MODEL"]
        assert result["DEFAULT_TEMPERATURE"] is not None
        assert "0.7" in result["DEFAULT_TEMPERATURE"]

    def test_list_with_no_vars_set(self, monkeypatch):
        """Test listing when no API keys are set"""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.delenv("BRAVE_SEARCH_API_KEY", raising=False)

        result = list_env_vars()

        assert result["OPENAI_API_KEY"] is None
        assert result["ANTHROPIC_API_KEY"] is None
        assert result["GOOGLE_API_KEY"] is None
        assert result["BRAVE_SEARCH_API_KEY"] is None


class TestCheckRequiredEnvVars:
    """Tests for check_required_env_vars()"""

    def test_no_missing_with_openai(self, monkeypatch):
        """Test no missing vars when OpenAI key is set"""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

        missing = check_required_env_vars()
        assert missing == []

    def test_no_missing_with_anthropic(self, monkeypatch):
        """Test no missing vars when Anthropic key is set"""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

        missing = check_required_env_vars()
        assert missing == []

    def test_no_missing_with_google(self, monkeypatch):
        """Test no missing vars when Google key is set"""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.setenv("GOOGLE_API_KEY", "google-test")

        missing = check_required_env_vars()
        assert missing == []

    def test_missing_all_llm_keys(self, monkeypatch):
        """Test missing vars when no LLM keys are set"""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

        missing = check_required_env_vars()
        assert len(missing) == 1
        assert "At least one of" in missing[0]
        assert "OPENAI_API_KEY" in missing[0]
        assert "ANTHROPIC_API_KEY" in missing[0]
        assert "GOOGLE_API_KEY" in missing[0]

    def test_no_missing_with_multiple_keys(self, monkeypatch):
        """Test no missing vars when multiple keys are set"""
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
        monkeypatch.setenv("GOOGLE_API_KEY", "google-test")

        missing = check_required_env_vars()
        assert missing == []
