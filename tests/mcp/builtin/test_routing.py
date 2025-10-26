"""Tests for routing MCP tools."""

import pytest

from kagura.mcp.builtin.routing import route_query


class TestRouteQuery:
    """Test route_query MCP tool."""

    @pytest.mark.asyncio
    async def test_route_query_default(self) -> None:
        """Test route_query with default router type."""
        result = await route_query("How to use FastAPI?")

        # Current implementation is placeholder
        assert "llm" in result
        assert "requires agent registration" in result

    @pytest.mark.asyncio
    async def test_route_query_llm_router(self) -> None:
        """Test route_query with LLM router type."""
        result = await route_query("Python tutorial", router_type="llm")

        assert "llm" in result
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_route_query_keyword_router(self) -> None:
        """Test route_query with keyword router type."""
        result = await route_query("Python tutorial", router_type="keyword")

        assert "keyword" in result
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_route_query_semantic_router(self) -> None:
        """Test route_query with semantic router type."""
        result = await route_query("Python tutorial", router_type="semantic")

        assert "semantic" in result
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_route_query_empty_query(self) -> None:
        """Test route_query with empty query."""
        result = await route_query("")

        # Should still return a valid response (placeholder implementation)
        assert isinstance(result, str)
        assert "requires agent registration" in result
