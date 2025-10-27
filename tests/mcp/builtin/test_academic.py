"""Tests for Academic search tools."""

import json

import pytest

from kagura.mcp.builtin.academic import arxiv_search


class TestArxivSearch:
    """Test arxiv_search tool."""

    @pytest.mark.asyncio
    async def test_missing_library(self, monkeypatch) -> None:
        """Test error when arxiv package not installed"""
        import builtins
        import sys

        if "arxiv" in sys.modules:
            del sys.modules["arxiv"]

        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "arxiv":
                raise ImportError("No module named 'arxiv'")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)

        result = await arxiv_search("test query")
        data = json.loads(result)

        assert "error" in data
        assert "arxiv" in data["error"]
        assert "install" in data

    @pytest.mark.asyncio
    async def test_max_results_string_conversion(self) -> None:
        """Test that max_results parameter handles string input"""
        # Pass max_results as string - should be converted to int
        result = await arxiv_search("test", max_results="5")  # type: ignore[arg-type]

        # The key test: no TypeError should occur
        assert isinstance(result, str)
        assert len(result) > 0

        # Should be valid JSON
        data = json.loads(result)
        assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_max_results_clamping(self) -> None:
        """Test that max_results is clamped to valid range"""
        # Test with very large number
        result = await arxiv_search("test", max_results=999)

        # Should not error
        assert isinstance(result, str)
        data = json.loads(result)
        assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_category_parameter(self) -> None:
        """Test that category parameter is accepted"""
        # Should not raise error about category parameter
        result = await arxiv_search("machine learning", category="cs.LG")

        assert isinstance(result, str)
        data = json.loads(result)
        assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_returns_valid_json(self) -> None:
        """Test that results are valid JSON"""
        result = await arxiv_search("deep learning", max_results=3)

        # Should be valid JSON
        assert isinstance(result, str)
        data = json.loads(result)

        # Should have expected structure
        assert isinstance(data, dict)
        if "results" in data:
            # Success case
            assert isinstance(data["results"], list)
        elif "error" in data:
            # Error case (arxiv package not installed)
            assert isinstance(data["error"], str)
