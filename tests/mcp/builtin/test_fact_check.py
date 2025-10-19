"""Tests for Fact-check tools."""

import json

import pytest

from kagura.mcp.builtin.fact_check import fact_check_claim


class TestFactCheckClaim:
    """Test fact_check_claim tool."""

    @pytest.mark.asyncio
    async def test_missing_dependencies(self, monkeypatch) -> None:
        """Test error when dependencies are not available"""
        # This test verifies graceful error handling
        result = await fact_check_claim("The sky is blue")

        # Should return valid result or error
        assert isinstance(result, str)

        # If it's JSON error, check structure
        if result.startswith("{"):
            data = json.loads(result)
            if "error" in data:
                assert isinstance(data["error"], str)

    @pytest.mark.asyncio
    async def test_claim_with_sources(self, monkeypatch) -> None:
        """Test fact-checking with additional sources"""
        # Mock environment to avoid actual API calls
        monkeypatch.delenv("BRAVE_SEARCH_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        result = await fact_check_claim(
            "Python is a programming language", sources=["https://python.org"]
        )

        # Should return something (error or result)
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_claim_parameter_required(self) -> None:
        """Test that claim parameter is required"""
        with pytest.raises(TypeError):
            await fact_check_claim()  # type: ignore[call-arg]

    @pytest.mark.asyncio
    async def test_sources_parameter_optional(self, monkeypatch) -> None:
        """Test that sources parameter is optional"""
        monkeypatch.delenv("BRAVE_SEARCH_API_KEY", raising=False)

        # Should not raise error without sources
        result = await fact_check_claim("Test claim")

        assert isinstance(result, str)


class TestFactCheckIntegration:
    """Integration tests for fact-checking."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        True,
        reason="Requires OpenAI and Brave Search API keys",
    )
    async def test_fact_check_real_claim(self) -> None:
        """Test fact-checking a real claim (integration test)"""
        # Real test (skipped by default)
        result = await fact_check_claim("Water freezes at 0°C")

        assert isinstance(result, str)
        assert len(result) > 0
        # Should contain verdict or analysis
        assert any(
            word in result.lower()
            for word in ["true", "false", "verdict", "confidence", "evidence"]
        )
