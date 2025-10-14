# Web Integration Guide

This guide explains how to use Kagura AI's web search and scraping capabilities to access real-time information from the internet.

## Overview

Web integration allows you to:
- Search the web for current information
- Scrape content from websites
- Combine local knowledge (RAG) with web data
- Get up-to-date answers beyond LLM training cutoff

## Prerequisites

### Installation

Install Kagura AI with web support:

```bash
pip install kagura-ai[web]
```

This installs:
- `httpx` - Async HTTP client
- `beautifulsoup4` - HTML parsing
- `lxml` - Fast XML/HTML parser
- `duckduckgo-search` - DuckDuckGo search (optional)

### API Key Setup (Optional)

For Brave Search (recommended for better results):

```bash
export BRAVE_API_KEY="your-brave-api-key"
```

Get a free API key from [Brave Search API](https://brave.com/search/api/) (2000 queries/month free).

**Without API key**: Kagura automatically falls back to DuckDuckGo (no API key required).

## Quick Start

### Basic Usage

Start chat with web search enabled:

```bash
kagura chat --enable-web
```

The AI will automatically search the web when needed:

```bash
$ kagura chat --enable-web

[You] > What are the latest AI news today?

🌐 Searching the web for: latest AI news
✓ Web search completed
💬 Generating response...

[AI]
Here are today's top AI news:

1. **OpenAI releases GPT-5 Preview** - OpenAI announced a preview of
   GPT-5 with improved reasoning capabilities...

2. **Google's Gemini 2.0 launched** - Google released Gemini 2.0 with
   native multimodal support...

3. **AI regulation update** - EU Parliament approved new AI safety
   regulations affecting...

[Sources: TechCrunch, The Verge, MIT Technology Review]
```

## Web Search

### Automatic Search Detection

The AI decides when to search the web:

```python
from kagura import agent

@agent(
    model="gpt-4o-mini",
    enable_web=True  # Enable automatic web search
)
async def research_assistant(question: str) -> str:
    """Answer the user's question.

    Question: {{ question }}

    If you need current information, use web search.
    """
    pass

# The agent will automatically search when needed
response = await research_assistant("What's the weather in Tokyo?")
```

### Manual Web Search

Use the `web_search` function directly:

```python
from kagura.web import web_search

# Search the web
results_text = await web_search("Python async best practices 2025")
print(results_text)
```

Output format:

```
Search results for: Python async best practices 2025

1. Best Practices for Async Python in 2025
   https://realpython.com/async-python-2025
   Comprehensive guide to async/await patterns, asyncio best practices...

2. Asyncio Performance Tips - 2025 Edition
   https://python.org/asyncio-tips
   Learn how to optimize asyncio applications for production...
```

### Search Engines

Kagura supports multiple search engines:

#### 1. Brave Search (Recommended)

Best quality results, requires API key:

```python
from kagura.web.search import BraveSearch

search = BraveSearch(api_key="your-key")
results = await search.search("query", max_results=10)

for result in results:
    print(f"{result.title}: {result.url}")
```

#### 2. DuckDuckGo (Fallback)

No API key required, rate limited:

```python
from kagura.web.search import DuckDuckGoSearch

search = DuckDuckGoSearch()
results = await search.search("query", max_results=10)
```

### Search API

```python
from kagura.web.search import SearchResult

# Search returns list of SearchResult objects
results: list[SearchResult] = await search.search("query")

for result in results:
    print(f"Title: {result.title}")
    print(f"URL: {result.url}")
    print(f"Snippet: {result.snippet}")
    print(f"Source: {result.source}")  # "brave" or "duckduckgo"
    print()
```

## Web Scraping

### Basic Scraping

Fetch and parse webpage content:

```python
from kagura.web.scraper import WebScraper

scraper = WebScraper()

# Fetch HTML
html = await scraper.fetch("https://example.com")

# Extract text content
text = await scraper.fetch_text("https://example.com")
print(text)  # Clean, readable text

# Scrape with CSS selectors
titles = await scraper.scrape(
    "https://news.ycombinator.com",
    selector="span.titleline > a"
)
for title in titles:
    print(title)
```

### robots.txt Compliance

Kagura respects robots.txt by default:

```python
scraper = WebScraper(
    respect_robots_txt=True,  # Default: True
    user_agent="KaguraAI/2.5.0",
    rate_limit_delay=1.0  # Delay between requests (seconds)
)
```

If a site disallows scraping:

```python
try:
    html = await scraper.fetch("https://example.com/private")
except ValueError as e:
    print(f"Blocked by robots.txt: {e}")
```

### Rate Limiting

Automatic rate limiting prevents overwhelming servers:

```python
from kagura.web.scraper import WebScraper

scraper = WebScraper(rate_limit_delay=2.0)  # 2 seconds between requests

# These will be rate-limited automatically
await scraper.fetch("https://example.com/page1")
await scraper.fetch("https://example.com/page2")  # Waits 2 seconds
await scraper.fetch("https://example.com/page3")  # Waits 2 seconds
```

### Advanced Scraping

```python
from kagura.web.scraper import WebScraper

scraper = WebScraper(
    user_agent="MyBot/1.0 (+https://mysite.com/bot)",
    respect_robots_txt=True,
    rate_limit_delay=1.5
)

# Custom timeout
html = await scraper.fetch("https://slow-site.com", timeout=60.0)

# Parse specific elements
articles = await scraper.scrape(
    "https://blog.com",
    selector="article.post"
)
```

## Agent Integration

### Web-Enabled Agent

Create an agent that can search the web:

```python
from kagura import agent
from kagura.web import web_search

async def search_tool(query: str) -> str:
    """Search the web for information."""
    return await web_search(query)

@agent(
    model="gpt-4o-mini",
    tools=[search_tool]
)
async def research_agent(topic: str) -> str:
    """Research {{ topic }} using web search.

    Use search_tool(query) to search the web.
    """
    pass

# The agent will use the tool when needed
report = await research_agent("AI safety regulations 2025")
```

### Custom Web Tools

Create specialized web tools:

```python
from kagura import agent
from kagura.web.scraper import WebScraper

async def fetch_news(topic: str) -> str:
    """Fetch latest news about a topic."""
    scraper = WebScraper()

    # Scrape news site
    headlines = await scraper.scrape(
        f"https://news-site.com/search?q={topic}",
        selector="h2.headline"
    )

    return "\n".join(headlines[:5])

@agent(tools=[fetch_news])
async def news_assistant(query: str) -> str:
    """Answer questions about current news.

    Query: {{ query }}
    """
    pass
```

## Configuration

### Environment Variables

```bash
# Brave Search (optional)
export BRAVE_API_KEY="your-key"

# User agent (optional)
export USER_AGENT="MyBot/1.0"

# Rate limiting (optional)
export WEB_RATE_LIMIT=1.5
```

### Programmatic Configuration

```python
from kagura.web.search import BraveSearch, DuckDuckGoSearch
from kagura.web.scraper import WebScraper
import os

# Configure search
if os.getenv("BRAVE_API_KEY"):
    search = BraveSearch(api_key=os.getenv("BRAVE_API_KEY"))
else:
    search = DuckDuckGoSearch()

# Configure scraper
scraper = WebScraper(
    user_agent=os.getenv("USER_AGENT", "KaguraAI/2.5.0"),
    respect_robots_txt=True,
    rate_limit_delay=float(os.getenv("WEB_RATE_LIMIT", "1.0"))
)
```

## Best Practices

### 1. Respect robots.txt

Always check robots.txt before scraping:

```python
scraper = WebScraper(respect_robots_txt=True)  # Default
```

### 2. Use Appropriate User Agent

Identify your bot:

```python
scraper = WebScraper(
    user_agent="MyBot/1.0 (+https://mysite.com/bot-info)"
)
```

### 3. Rate Limiting

Be a good citizen:

```python
scraper = WebScraper(rate_limit_delay=1.0)  # Minimum 1 second
```

### 4. Handle Errors

```python
from httpx import HTTPError

try:
    content = await scraper.fetch_text(url)
except HTTPError as e:
    print(f"HTTP error: {e}")
except ValueError as e:
    print(f"Blocked by robots.txt: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### 5. Cache Results

Avoid repeated requests:

```python
from functools import lru_cache

@lru_cache(maxsize=100)
async def cached_search(query: str) -> str:
    return await web_search(query)
```

## Troubleshooting

### "ImportError: httpx not installed"

Install web dependencies:

```bash
pip install kagura-ai[web]
```

### "Rate limit exceeded"

Increase delay between requests:

```python
scraper = WebScraper(rate_limit_delay=2.0)
```

Or wait before retrying:

```python
import asyncio

try:
    results = await search.search(query)
except Exception as e:
    print(f"Rate limited, waiting...")
    await asyncio.sleep(60)
    results = await search.search(query)
```

### "robots.txt disallows fetching"

Either:

1. Respect the site's wishes (recommended)
2. Disable robots.txt check (not recommended):

```python
scraper = WebScraper(respect_robots_txt=False)
```

### Connection Timeout

Increase timeout:

```python
html = await scraper.fetch(url, timeout=60.0)  # 60 seconds
```

## Examples

### Example 1: News Aggregator

```python
from kagura import agent
from kagura.web import web_search

@agent(model="gpt-4o-mini")
async def news_bot(topic: str) -> str:
    """Fetch and summarize news about {{ topic }}.

    Use web_search() to find latest news.
    """
    pass

# Usage
summary = await news_bot("AI breakthroughs")
```

### Example 2: Documentation Fetcher

```python
from kagura.web.scraper import WebScraper

async def fetch_api_docs(library: str) -> str:
    """Fetch API documentation for a library."""
    scraper = WebScraper()

    # Fetch official docs
    docs_url = f"https://{library}.readthedocs.io/"
    text = await scraper.fetch_text(docs_url)

    return text[:5000]  # First 5000 chars

# Usage
docs = await fetch_api_docs("httpx")
```

### Example 3: Competitor Analysis

```python
from kagura import agent
from kagura.web import web_search
from kagura.web.scraper import WebScraper

async def analyze_competitor(competitor_url: str) -> dict:
    """Analyze competitor website."""
    scraper = WebScraper()

    # Fetch homepage
    text = await scraper.fetch_text(competitor_url)

    # Extract features
    features = await scraper.scrape(
        competitor_url,
        selector="div.feature h3"
    )

    return {
        "content": text[:2000],
        "features": features
    }

@agent
async def market_analyst(company_name: str) -> str:
    """Analyze {{ company_name }} and competitors."""
    pass
```

## Performance Tips

### 1. Parallel Requests

Use asyncio.gather for parallel fetching:

```python
import asyncio

urls = ["https://site1.com", "https://site2.com", "https://site3.com"]

# Fetch in parallel
results = await asyncio.gather(
    *[scraper.fetch_text(url) for url in urls]
)
```

### 2. Connection Pooling

httpx automatically pools connections:

```python
# Reuse scraper instance
scraper = WebScraper()

for url in urls:
    await scraper.fetch(url)  # Reuses connections
```

### 3. Timeout Management

Set appropriate timeouts:

```python
# Fast timeout for quick checks
await scraper.fetch(url, timeout=5.0)

# Longer timeout for heavy pages
await scraper.fetch(url, timeout=30.0)
```

## Next Steps

- [Multimodal RAG Guide](./chat-multimodal.md) - Add local file indexing
- [Full-Featured Mode](./full-featured-mode.md) - Combine all features
- [API Reference](../api/web-integration.md) - Detailed API documentation

## Resources

- [Brave Search API](https://brave.com/search/api/)
- [httpx Documentation](https://www.python-httpx.org/)
- [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/)
- [robots.txt Specification](https://www.robotstxt.org/)
