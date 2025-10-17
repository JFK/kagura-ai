"""Tests for web decorators."""

import pytest

from kagura.core.decorators import agent
from kagura.web import web
from kagura.web.decorators import enable, web_search


class TestWebSearchTool:
    """Tests for web_search tool function."""

    @pytest.mark.asyncio
    async def test_web_search_basic(self):
        """Test basic web_search functionality."""
        # Mock the search function
        from unittest.mock import AsyncMock, patch

        mock_results = [
            type(
                "SearchResult",
                (),
                {
                    "title": "Python Tutorial",
                    "url": "https://example.com",
                    "snippet": "Learn Python",
                    "source": "test",
                },
            )()
        ]

        with patch("kagura.web.decorators.search", new=AsyncMock(return_value=mock_results)):
            result = await web_search("Python programming")

            assert "Python Tutorial" in result
            assert "https://example.com" in result
            assert "Learn Python" in result

    @pytest.mark.asyncio
    async def test_web_search_no_results(self):
        """Test web_search with no results."""
        from unittest.mock import AsyncMock, patch

        with patch("kagura.web.decorators.search", new=AsyncMock(return_value=[])):
            result = await web_search("nonexistent query")

            assert "No results found" in result
            assert "nonexistent query" in result

    @pytest.mark.asyncio
    async def test_web_search_max_results(self):
        """Test web_search with max_results parameter."""
        from unittest.mock import AsyncMock, patch

        mock_search = AsyncMock(return_value=[])

        with patch("kagura.web.decorators.search", new=mock_search):
            await web_search("test", max_results=5)

            # Verify search was called with max_results
            mock_search.assert_called_once_with("test", 5)


class TestWebEnableDecorator:
    """Tests for @web.enable decorator."""

    def test_enable_decorator_metadata(self):
        """Test that @web.enable sets correct metadata."""

        @web.enable()
        async def test_agent(topic: str) -> str:
            """Test agent"""
            pass

        assert hasattr(test_agent, "_web_enabled")
        assert test_agent._web_enabled is True
        assert hasattr(test_agent, "_web_search_tool")
        assert test_agent._web_search_tool == web_search

    def test_enable_decorator_with_engine(self):
        """Test @web.enable with search_engine parameter."""

        @web.enable(search_engine="brave")
        async def test_agent(topic: str) -> str:
            """Test agent"""
            pass

        assert test_agent._web_enabled is True
        assert test_agent._web_search_engine == "brave"

    @pytest.mark.asyncio
    async def test_enable_decorator_passthrough(self):
        """Test that @web.enable doesn't break function execution."""

        @web.enable()
        async def test_func(x: int) -> int:
            """Test function"""
            return x * 2

        result = await test_func(5)
        assert result == 10


class TestWebAgentIntegration:
    """Integration tests for @agent + @web.enable."""

    def test_web_enabled_agent_has_tool(self):
        """Test that @agent detects @web.enable and injects web_search tool."""

        @agent(model="gpt-5-mini")
        @web.enable()
        async def research_agent(topic: str) -> str:
            """Research {{ topic }} using web search."""
            pass

        # Check that the agent has web enabled
        assert hasattr(research_agent, "_web_enabled")
        assert research_agent._web_enabled is True

    def test_agent_without_web_enable(self):
        """Test that agents without @web.enable don't have web metadata."""

        @agent(model="gpt-5-mini")
        async def normal_agent(topic: str) -> str:
            """Normal agent without web"""
            pass

        assert not hasattr(normal_agent, "_web_enabled")

    def test_web_enable_must_be_inner(self):
        """Test decorator order: @agent should be outer, @web.enable inner."""

        # Correct order: @agent on top, @web.enable below
        @agent(model="gpt-5-mini")
        @web.enable()
        async def correct_agent(topic: str) -> str:
            """Research {{ topic }}"""
            pass

        assert hasattr(correct_agent, "_is_agent")
        assert hasattr(correct_agent, "_web_enabled")


class TestWebEnableStandalone:
    """Tests for @web.enable used standalone."""

    def test_enable_alias(self):
        """Test that 'enable' is accessible."""
        assert enable is not None
        assert callable(enable)

    @pytest.mark.asyncio
    async def test_enable_without_agent(self):
        """Test @web.enable can be used without @agent."""

        @enable()
        async def standalone_func(query: str) -> str:
            """Standalone function with web.enable"""
            return f"Processed: {query}"

        result = await standalone_func("test")
        assert result == "Processed: test"
        assert hasattr(standalone_func, "_web_enabled")
