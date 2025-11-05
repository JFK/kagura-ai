"""Tests for API connectivity check utilities."""

from __future__ import annotations

import pytest


class TestApiCheckModule:
    """Basic tests for api_check module."""

    def test_module_imports(self) -> None:
        """Test that module imports successfully."""
        from kagura.utils import api_check

        assert hasattr(api_check, "check_llm_api")
        assert hasattr(api_check, "check_brave_search_api")
        assert hasattr(api_check, "check_api_configuration")

    @pytest.mark.asyncio
    async def test_check_api_configuration_returns_list(self) -> None:
        """Test that check_api_configuration returns expected format."""
        from kagura.utils.api_check import check_api_configuration

        results = await check_api_configuration()

        assert isinstance(results, list)
        assert len(results) >= 4  # At least 4 providers
        for item in results:
            assert isinstance(item, tuple)
            assert len(item) == 3
            provider, status, message = item
            assert isinstance(provider, str)
            assert status in ("ok", "warning", "error", "info")
            assert isinstance(message, str)

    def test_has_correct_exports(self) -> None:
        """Test that all expected functions are exported."""
        from kagura.utils.api_check import (
            check_api_configuration,
            check_brave_search_api,
            check_llm_api,
        )

        # Just verify they exist
        assert callable(check_llm_api)
        assert callable(check_brave_search_api)
        assert callable(check_api_configuration)
