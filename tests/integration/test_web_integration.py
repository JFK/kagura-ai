"""Integration tests for web integration"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock


@pytest.mark.asyncio
async def test_web_search_brave():
    """Test Brave Search integration"""
    from kagura.web.search import BraveSearch, SearchResult

    # Mock API response
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "web": {
                "results": [
                    {
                        "title": "Test Result",
                        "url": "https://example.com",
                        "description": "Test description"
                    }
                ]
            }
        }
        mock_response.raise_for_status = MagicMock()

        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )

        search = BraveSearch(api_key="test_key")
        results = await search.search("test query")

        assert isinstance(results, list)
        assert len(results) > 0
        assert isinstance(results[0], SearchResult)
        assert results[0].title == "Test Result"


@pytest.mark.asyncio
async def test_web_search_duckduckgo():
    """Test DuckDuckGo Search integration"""
    from kagura.web.search import DuckDuckGoSearch, SearchResult

    # Mock duckduckgo_search
    with patch('duckduckgo_search.DDGS') as mock_ddgs:
        # Mock context manager
        mock_instance = MagicMock()
        mock_instance.text.return_value = [
            {
                "title": "Test Result",
                "href": "https://example.com",
                "body": "Test description"
            }
        ]
        mock_ddgs.return_value.__enter__.return_value = mock_instance
        mock_ddgs.return_value.__exit__.return_value = None

        search = DuckDuckGoSearch()
        results = await search.search("test query")

        assert isinstance(results, list)
        assert len(results) > 0
        assert isinstance(results[0], SearchResult)


@pytest.mark.asyncio
async def test_web_search_function():
    """Test web_search convenience function"""
    from kagura.web import web_search
    from kagura.web.search import SearchResult

    with patch('kagura.web.search.BraveSearch.search', new_callable=AsyncMock) as mock_search:
        mock_search.return_value = [
            SearchResult(title="Result", url="https://example.com", snippet="Desc", source="brave")
        ]

        result = await web_search("test query")

        assert isinstance(result, str)
        assert "Result" in result or "example.com" in result


@pytest.mark.asyncio
async def test_web_scraper_fetch():
    """Test WebScraper fetch functionality"""
    from kagura.web.scraper import WebScraper

    with patch('httpx.AsyncClient') as mock_client:
        mock_response = MagicMock()
        mock_response.text = "<html><body>Test content</body></html>"
        mock_response.raise_for_status = MagicMock()

        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )

        scraper = WebScraper(respect_robots_txt=False)
        html = await scraper.fetch("https://example.com")

        assert "Test content" in html


@pytest.mark.asyncio
async def test_web_scraper_fetch_text():
    """Test WebScraper fetch_text with HTML parsing"""
    from kagura.web.scraper import WebScraper

    with patch('httpx.AsyncClient') as mock_client:
        mock_response = MagicMock()
        mock_response.text = "<html><body><p>Test paragraph</p></body></html>"
        mock_response.raise_for_status = MagicMock()

        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )

        scraper = WebScraper(respect_robots_txt=False)
        text = await scraper.fetch_text("https://example.com")

        assert "Test paragraph" in text


@pytest.mark.asyncio
async def test_web_scraper_rate_limiting():
    """Test WebScraper rate limiting"""
    from kagura.web.scraper import RateLimiter
    import time

    limiter = RateLimiter(min_delay=0.1)

    start = time.time()
    await limiter.wait("example.com")
    await limiter.wait("example.com")
    elapsed = time.time() - start

    # Second call should wait at least min_delay
    assert elapsed >= 0.1


@pytest.mark.asyncio
async def test_chat_session_web_initialization():
    """Test ChatSession initialization with web enabled"""
    from kagura.chat import ChatSession

    session = ChatSession(
        model="gpt-4o-mini",
        enable_web=True
    )

    assert session.enable_web is True


@pytest.mark.asyncio
async def test_agent_with_web_search_tool():
    """Test @agent with web search tool"""
    from kagura import agent

    async def mock_search(query: str) -> str:
        """Mock web search tool"""
        return f"Search results for: {query}"

    @agent(
        model="gpt-4o-mini",
        tools=[mock_search]
    )
    async def research_agent(topic: str) -> str:
        """Research {{ topic }} using web search"""
        pass

    # Mock LLM to call the tool
    with patch('litellm.acompletion', new_callable=AsyncMock) as mock_llm:
        # First call: LLM wants to use tool
        mock_message1 = MagicMock(
            content=None,
            tool_calls=[
                MagicMock(
                    id="call_1",
                    function=MagicMock(
                        name="mock_search",
                        arguments='{"query": "AI trends"}'
                    )
                )
            ]
        )
        # Second call: LLM returns final response
        mock_message2 = MagicMock(
            content="Based on search: AI trends are growing",
            tool_calls=None
        )

        mock_llm.side_effect = [
            MagicMock(choices=[MagicMock(message=mock_message1)]),
            MagicMock(choices=[MagicMock(message=mock_message2)])
        ]

        result = await research_agent("AI trends")
        assert "AI trends" in result or "search" in result.lower()
