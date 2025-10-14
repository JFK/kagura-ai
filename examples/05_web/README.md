# 05_web - Web Integration

This directory contains examples demonstrating web search and scraping capabilities.

## Overview

Kagura AI provides powerful web integration features:
- **Web Search** - Search the web using Brave Search or DuckDuckGo
- **Web Scraping** - Extract content from websites safely
- **Research Agents** - Build agents that gather and synthesize web information
- **Web Tools** - Integrate web capabilities into any agent

## Web Integration Architecture

```
┌─────────────┐
│ User Query  │
└──────┬──────┘
       │
       ▼
┌──────────────┐     ┌─────────────┐
│ Agent        │────>│ Web Search  │
│ @web.enable  │     │ - Brave     │
└──────┬───────┘     │ - DuckDuckGo│
       │             └─────────────┘
       ▼
┌──────────────┐     ┌─────────────┐
│ Process      │────>│ Web Scraper │
│ Results      │     │ - Extract   │
└──────┬───────┘     │ - Clean     │
       │             └─────────────┘
       ▼
┌──────────────┐
│ Response     │
└──────────────┘
```

## Examples

### 1. web_search.py - Web Search Integration
**Demonstrates:**
- Brave Search API integration
- DuckDuckGo search (no API key)
- Search result processing
- Fact-checking with web search

```python
from kagura import agent, tool

@tool
async def brave_search(query: str, count: int = 5) -> str:
    """Search the web using Brave Search API"""
    # Implementation uses Brave Search API
    pass

@agent(tools=[brave_search])
async def search_assistant(question: str) -> str:
    """
    Answer {{ question }} using web search.

    Use brave_search tool to find current information.
    """
    pass

# Search the web
answer = await search_assistant("What is the latest Python version?")
```

**Key Concepts:**
- Search API integration
- Real-time information retrieval
- Tool-based search
- Best for: Current events, facts

**Use Cases:**
- Question answering
- Fact-checking
- News monitoring
- Competitive research
- Market analysis

**Search Providers:**
- **Brave Search** - Privacy-focused, API required
- **DuckDuckGo** - No API key, rate-limited
- **Google (via SerpAPI)** - Requires API key
- **Bing** - Requires API key

---

### 2. web_scraping.py - Web Content Extraction
**Demonstrates:**
- Scraping web pages safely
- HTML parsing and cleaning
- Rate limiting and robots.txt respect
- Content extraction strategies

```python
from kagura.web import WebScraper

scraper = WebScraper(
    respect_robots_txt=True,
    rate_limit_delay=1.0  # 1 second between requests
)

# Scrape webpage
content = await scraper.scrape("https://example.com")

# Extract specific content
article = await scraper.extract_article("https://blog.example.com/post")
```

**Key Concepts:**
- Ethical scraping (robots.txt, rate limits)
- HTML parsing (BeautifulSoup/lxml)
- Content extraction
- Best for: Structured data extraction

**Use Cases:**
- Article extraction
- Product information
- Price monitoring
- News aggregation
- Data collection

**Best Practices:**
- ✅ Respect robots.txt
- ✅ Rate limiting (1-2s between requests)
- ✅ User-Agent headers
- ✅ Error handling (404, timeouts)
- ❌ Don't overwhelm servers

---

### 3. research_agent.py - Research Assistant
**Demonstrates:**
- Combining search + scraping
- Multi-source information synthesis
- Citation tracking
- Research workflow automation

```python
from kagura import agent, workflow
from kagura.web import search, WebScraper

@workflow
async def research_topic(topic: str) -> dict:
    """
    Research {{ topic }} using web search and scraping.

    Steps:
    1. Search for recent articles
    2. Scrape top results
    3. Analyze and synthesize information
    4. Provide citations
    """
    # Search phase
    search_results = await search(topic, count=10)

    # Scrape phase
    scraper = WebScraper()
    articles = []
    for result in search_results[:5]:
        content = await scraper.scrape(result.url)
        articles.append(content)

    # Analysis phase
    summary = await summarize_agent(articles)

    return {
        "topic": topic,
        "summary": summary,
        "sources": [r.url for r in search_results[:5]]
    }

# Research a topic
report = await research_topic("Latest developments in quantum computing")
```

**Key Concepts:**
- Multi-step research workflow
- Search + scrape + analyze
- Source attribution
- Best for: In-depth research

**Use Cases:**
- Market research
- Competitive analysis
- Technical research
- News summarization
- Literature review

**Workflow:**
1. **Search** - Find relevant sources
2. **Scrape** - Extract content
3. **Analyze** - Synthesize information
4. **Report** - Generate summary with citations

---

## Prerequisites

```bash
# Install Kagura AI with web support
pip install kagura-ai[web]

# This includes:
# - httpx (HTTP client)
# - beautifulsoup4 (HTML parsing)
# - lxml (XML/HTML parser)

# For Brave Search (optional)
export BRAVE_API_KEY="your-api-key"
# Get key at: https://brave.com/search/api/

# For DuckDuckGo (no API key needed)
# Already included in [web] extras
```

## Running Examples

```bash
# Set API keys (if using Brave Search)
export BRAVE_API_KEY="your-key"

# Run examples
python web_search.py
python web_scraping.py
python research_agent.py
```

## Web Search Providers Comparison

| Provider | API Key | Cost | Rate Limits | Quality |
|----------|---------|------|-------------|---------|
| **Brave Search** | ✅ Required | Freemium | 2K/month free | ⭐⭐⭐⭐⭐ |
| **DuckDuckGo** | ❌ Not needed | Free | Limited | ⭐⭐⭐ |
| **Google (SerpAPI)** | ✅ Required | Paid | 100/month free | ⭐⭐⭐⭐⭐ |
| **Bing** | ✅ Required | Freemium | 1K/month free | ⭐⭐⭐⭐ |

## Common Patterns

### Pattern 1: Simple Web Search Agent
```python
from kagura import agent
from kagura.web import web, web_search

@web.enable  # Automatically adds web_search tool
@agent
async def web_assistant(question: str) -> str:
    """
    Answer {{ question }} using web search.

    Search the web for current information and synthesize an answer.
    """
    pass

# Use web search automatically
answer = await web_assistant("Who won the latest Nobel Prize?")
```

### Pattern 2: Web Scraping with Error Handling
```python
from kagura.web import WebScraper

scraper = WebScraper(
    timeout=10.0,
    max_retries=3,
    respect_robots_txt=True
)

try:
    content = await scraper.scrape(url)
except TimeoutError:
    print(f"Timeout scraping {url}")
except PermissionError:
    print(f"Robots.txt disallows scraping {url}")
except Exception as e:
    print(f"Error: {e}")
```

### Pattern 3: Multi-Source Research
```python
from kagura import workflow
from kagura.web import search, WebScraper

@workflow
async def compare_sources(query: str) -> dict:
    """Research topic across multiple sources"""
    # Search multiple providers
    brave_results = await search(query, provider="brave", count=5)
    ddg_results = await search(query, provider="duckduckgo", count=5)

    # Combine and deduplicate
    all_urls = set([r.url for r in brave_results + ddg_results])

    # Scrape top 5
    scraper = WebScraper()
    contents = []
    for url in list(all_urls)[:5]:
        try:
            content = await scraper.scrape(url)
            contents.append({"url": url, "content": content})
        except Exception:
            continue

    return {
        "query": query,
        "sources": contents,
        "total": len(contents)
    }
```

### Pattern 4: Fact-Checking Agent
```python
from kagura import agent
from kagura.web import web, web_search

@web.enable
@agent
async def fact_checker(claim: str) -> dict:
    """
    Fact-check this claim: {{ claim }}

    Use web_search to find reliable sources.

    Return:
    - verdict: TRUE, FALSE, PARTIALLY_TRUE, or UNVERIFIED
    - explanation: Brief reasoning
    - sources: List of URLs
    """
    pass

# Check a claim
result = await fact_checker("Python was created in 1991")
# → {"verdict": "TRUE", "explanation": "...", "sources": [...]}
```

## Best Practices

### 1. Respect Website Policies

✅ **Good:**
```python
from kagura.web import WebScraper

scraper = WebScraper(
    respect_robots_txt=True,      # Honor robots.txt
    rate_limit_delay=2.0,          # 2s between requests
    user_agent="MyBot/1.0 (+URL)"  # Identify yourself
)
```

❌ **Bad:**
```python
scraper = WebScraper(
    respect_robots_txt=False,  # Ignore robots.txt
    rate_limit_delay=0.1       # Too fast!
)
```

### 2. Handle Errors Gracefully

```python
# ✅ Good: Comprehensive error handling
try:
    content = await scraper.scrape(url)
except TimeoutError:
    # Handle timeout
    content = None
except PermissionError:
    # Robots.txt disallows
    content = None
except Exception as e:
    # Log error
    logger.error(f"Scraping failed: {e}")
    content = None

# ❌ Bad: No error handling
content = await scraper.scrape(url)  # May crash
```

### 3. Cache Search Results

```python
# ✅ Good: Cache to avoid redundant searches
from functools import lru_cache

@lru_cache(maxsize=100)
async def cached_search(query: str):
    return await search(query, count=10)

# ❌ Bad: Repeated identical searches
results1 = await search("Python")
results2 = await search("Python")  # Duplicate!
```

### 4. Filter and Validate Sources

```python
# ✅ Good: Filter by domain/quality
TRUSTED_DOMAINS = ["wikipedia.org", "github.com", "python.org"]

results = await search(query)
filtered = [
    r for r in results
    if any(domain in r.url for domain in TRUSTED_DOMAINS)
]

# ❌ Bad: Use all results indiscriminately
results = await search(query)  # May include spam/low-quality
```

### 5. Rate Limit Aggressively

```python
# ✅ Good: Conservative rate limiting
import asyncio

async def scrape_multiple(urls):
    results = []
    for url in urls:
        result = await scraper.scrape(url)
        results.append(result)
        await asyncio.sleep(2.0)  # 2s delay
    return results

# ❌ Bad: Parallel without limits
results = await asyncio.gather(*[scraper.scrape(url) for url in urls])
```

## Advanced Features

### Custom Search Implementation
```python
from kagura import tool
import httpx

@tool
async def custom_search(query: str, api_key: str) -> list:
    """Custom search API integration"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.example.com/search",
            params={"q": query, "key": api_key}
        )
        return response.json()

@agent(tools=[custom_search])
async def search_agent(query: str) -> str:
    """Search using custom API: {{ query }}"""
    pass
```

### Content Extraction Strategies
```python
from kagura.web import WebScraper
from bs4 import BeautifulSoup

scraper = WebScraper()
html = await scraper.scrape(url)

# Extract article content
soup = BeautifulSoup(html, 'html.parser')

# Strategy 1: By tag
article = soup.find('article')

# Strategy 2: By class
content = soup.find('div', class_='content')

# Strategy 3: By selector
main_text = soup.select('.main-content p')

# Clean and combine
text = ' '.join([p.get_text() for p in main_text])
```

### Parallel Scraping with Limits
```python
import asyncio
from asyncio import Semaphore

async def scrape_with_limit(urls, max_concurrent=3):
    """Scrape multiple URLs with concurrency limit"""
    semaphore = Semaphore(max_concurrent)
    scraper = WebScraper()

    async def scrape_one(url):
        async with semaphore:
            return await scraper.scrape(url)

    results = await asyncio.gather(
        *[scrape_one(url) for url in urls],
        return_exceptions=True
    )
    return results
```

### Intelligent Source Selection
```python
@agent
async def source_selector(query: str, results: list) -> list:
    """
    Select the most relevant sources for: {{ query }}

    Results: {{ results }}

    Return top 5 most relevant URLs.
    """
    pass

# Filter search results intelligently
search_results = await search(query, count=20)
top_sources = await source_selector(query, search_results)
```

## Troubleshooting

### Issue: Search returns no results
**Solution:** Check API key and rate limits:
```python
import os

api_key = os.getenv("BRAVE_API_KEY")
if not api_key:
    print("Set BRAVE_API_KEY environment variable")

# Check rate limit
results = await search(query, count=5)  # Start with small count
```

### Issue: Scraping fails with 403/bot detection
**Solution:** Set proper User-Agent and rate limit:
```python
scraper = WebScraper(
    user_agent="Mozilla/5.0 (compatible; MyBot/1.0)",
    rate_limit_delay=3.0,  # Slower requests
    respect_robots_txt=True
)
```

### Issue: Timeout errors
**Solution:** Increase timeout and add retries:
```python
scraper = WebScraper(
    timeout=30.0,      # 30 seconds
    max_retries=3,     # Retry 3 times
    retry_delay=2.0    # 2s between retries
)
```

### Issue: HTML parsing errors
**Solution:** Use robust parsing with error handling:
```python
from bs4 import BeautifulSoup

try:
    soup = BeautifulSoup(html, 'lxml')  # Use lxml parser
except Exception:
    soup = BeautifulSoup(html, 'html.parser')  # Fallback
```

### Issue: Memory issues with large pages
**Solution:** Stream and process incrementally:
```python
# Instead of loading entire page
content = await scraper.scrape(url, stream=True)

# Process in chunks
for chunk in content.iter_chunks(chunk_size=1024):
    process_chunk(chunk)
```

## Legal and Ethical Considerations

### Do's ✅
- Respect robots.txt files
- Rate limit requests (1-2s minimum)
- Identify your bot (User-Agent)
- Honor terms of service
- Cache to minimize requests
- Handle errors gracefully

### Don'ts ❌
- Overwhelm servers with requests
- Ignore robots.txt
- Scrape personal data without consent
- Violate copyright
- Use scraped data commercially without permission
- Bypass anti-scraping measures

## Next Steps

After mastering web integration, explore:
- [06_advanced](../06_advanced/) - Advanced workflows
- [08_real_world](../08_real_world/) - Production web agents
- [02_memory](../02_memory/) - Cache web results in memory

## Documentation

- [API Reference - Web](../../docs/en/api/web.md)
- [Web Scraping Guide](../../docs/en/guides/web_scraping.md)
- [Search Integration Guide](../../docs/en/guides/search.md)

---

**Start with `web_search.py` to understand search integration, then progress to scraping and research agents!**
