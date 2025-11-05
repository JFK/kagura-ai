"""Tests for memory tool deprecations."""

from __future__ import annotations

import warnings

import pytest

from kagura.mcp.builtin.memory import memory_search_hybrid


class TestMemorySearchHybridDeprecation:
    """Tests for memory_search_hybrid deprecation."""

    @pytest.mark.asyncio
    async def test_deprecation_warning_emitted(self) -> None:
        """Test that memory_search_hybrid emits DeprecationWarning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # Call the deprecated function
            await memory_search_hybrid(
                user_id="test_user",
                agent_name="test_agent",
                query="test query",
                k="5",
            )

            # Check that a DeprecationWarning was raised
            assert len(w) >= 1
            assert any(issubclass(warning.category, DeprecationWarning) for warning in w)

            # Check the warning message
            deprecation_warnings = [
                warning for warning in w if issubclass(warning.category, DeprecationWarning)
            ]
            assert len(deprecation_warnings) >= 1
            warning_msg = str(deprecation_warnings[0].message)
            assert "memory_search_hybrid" in warning_msg
            assert "deprecated" in warning_msg.lower()
            assert "memory_search()" in warning_msg
            assert "v4.2.0" in warning_msg

    @pytest.mark.asyncio
    async def test_functionality_still_works(self) -> None:
        """Test that deprecated function still works correctly."""
        # Suppress the deprecation warning for this test
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)

            result = await memory_search_hybrid(
                user_id="test_user",
                agent_name="test_agent",
                query="test query",
                k="3",
            )

            # Should return a result (functionality preserved)
            assert isinstance(result, str)
            # Result should be JSON or contain results
            assert len(result) > 0
