"""Tests for memory_stats tool."""

import json

import pytest

from kagura.mcp.builtin.memory import memory_stats


class TestMemoryStats:
    """Test memory_stats tool."""

    @pytest.mark.asyncio
    async def test_memory_stats_basic(self):
        """Test basic memory stats functionality."""
        result = await memory_stats(user_id="test_user", agent_name="test_agent")

        # Should return valid JSON
        data = json.loads(result)

        # Check structure
        assert "total_memories" in data
        assert "breakdown" in data
        assert "analysis" in data
        assert "recommendations" in data
        assert "health_score" in data

        # Check breakdown
        assert "working" in data["breakdown"]
        assert "persistent" in data["breakdown"]

        # Check analysis
        assert "duplicates" in data["analysis"]
        assert "old_90days" in data["analysis"]

    @pytest.mark.asyncio
    async def test_memory_stats_returns_valid_json(self):
        """Test that memory_stats returns valid JSON structure."""
        result = await memory_stats(user_id="json_test_user", agent_name="test")
        data = json.loads(result)

        # Check all required fields exist
        assert isinstance(data["total_memories"], int)
        assert isinstance(data["breakdown"], dict)
        assert isinstance(data["analysis"], dict)
        assert isinstance(data["top_tags"], dict)
        assert isinstance(data["recommendations"], list)
        assert data["health_score"] in ["excellent", "good", "fair", "needs_attention"]

    @pytest.mark.asyncio
    async def test_memory_stats_health_scores(self):
        """Test health score calculation."""
        result = await memory_stats(user_id="new_user", agent_name="test")
        data = json.loads(result)

        # New user should have excellent or good health
        assert data["health_score"] in ["excellent", "good", "fair"]

    @pytest.mark.asyncio
    async def test_memory_stats_recommendations(self):
        """Test recommendations are provided."""
        result = await memory_stats(user_id="test_recs", agent_name="test")
        data = json.loads(result)

        # Should always have recommendations
        assert len(data["recommendations"]) > 0
        assert isinstance(data["recommendations"], list)
