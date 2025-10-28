"""Tests for config doctor API testing functionality (Issue #446)."""

import pytest

from kagura.cli.config_cli import (
    _test_anthropic_api,
    _test_google_api,
    _test_openai_api,
)


class TestAPIConnectionTests:
    """Test API connection testing functions."""

    @pytest.mark.asyncio
    async def test_openai_invalid_key_error_message(self):
        """Test that invalid OpenAI key returns helpful error."""
        success, message = await _test_openai_api("invalid_key_123")

        assert not success
        assert "Invalid API key" in message or "authentication" in message.lower()

    @pytest.mark.asyncio
    async def test_anthropic_invalid_key_error_message(self):
        """Test that invalid Anthropic key returns helpful error."""
        success, message = await _test_anthropic_api("invalid_key_123")

        assert not success
        assert "Invalid API key" in message or "authentication" in message.lower()

    @pytest.mark.asyncio
    async def test_google_uses_correct_model_prefix(self):
        """Test that Google AI test uses gemini/ prefix (not Vertex AI)."""
        # This test verifies the fix for Issue #446
        # With invalid key, should get auth error (not Vertex credentials error)
        success, message = await _test_google_api("invalid_key_123")

        assert not success
        # Should NOT be Vertex AI error about credentials
        assert "DefaultCredentialsError" not in message
        assert "Vertex" not in message
        # Should be authentication error
        assert (
            "Invalid API key" in message
            or "authentication" in message.lower()
            or "API key not valid" in message
        )
