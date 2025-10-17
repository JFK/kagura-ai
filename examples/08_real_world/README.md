# 08_real_world - Real-World Use Cases

This directory contains production-ready examples demonstrating complete, real-world applications built with Kagura AI.

## Overview

See how all Kagura AI features come together in production-ready applications:
- **Code Review Agent** - Automated PR review system
- **Content Generator** - Multi-format content creation
- **Customer Support Bot** - Intelligent support automation
- **Research Assistant** - Comprehensive research workflows

Each example demonstrates:
- ✅ Complete working application
- ✅ Production best practices
- ✅ Error handling
- ✅ Performance optimization
- ✅ Real-world complexity

## Examples

### 1. code_review_agent.py - Automated Code Review
**Demonstrates:**
- GitHub integration
- Multi-file analysis
- Security scanning
- Automated feedback generation
- Pull request commenting

```python
from kagura.presets import CodeReviewPreset
from kagura import workflow
import asyncio

# Create code reviewer
reviewer = (
    CodeReviewPreset("pr_reviewer")
    .with_model("claude-3-5-sonnet")
    .with_context(
        languages=["python", "javascript", "typescript"],
        focus_areas=["security", "performance", "style"],
        strictness="medium"
    )
    .build()
)

@workflow
async def review_pull_request(pr_number: int) -> dict:
    """
    Complete PR review workflow:
    1. Fetch PR files from GitHub
    2. Analyze each file
    3. Check for security issues
    4. Generate summary
    5. Post review comments
    """
    # Fetch PR
    files = await github.get_pr_files(pr_number)

    # Review files in parallel
    reviews = await asyncio.gather(
        *[reviewer(file.content) for file in files]
    )

    # Combine feedback
    summary = await generate_summary(reviews)

    # Post to GitHub
    await github.post_review_comment(pr_number, summary)

    return {
        "pr": pr_number,
        "files_reviewed": len(files),
        "issues_found": count_issues(reviews),
        "summary": summary
    }

# Review PR #123
result = await review_pull_request(123)
```

**Key Features:**
- Multi-file parallel review
- Security vulnerability detection
- Best practice suggestions
- Performance optimization hints
- Style consistency checks
- Automated PR comments

**Production Considerations:**
- Rate limiting (GitHub API)
- Error handling (network, API)
- Retry logic (transient failures)
- Cost optimization (caching reviews)
- Incremental reviews (only changed lines)

**Use Cases:**
- Automated PR reviews
- Pre-commit checks
- Security audits
- Code quality gates
- Team productivity

**Integration:**
```python
# GitHub Actions workflow
# .github/workflows/code-review.yml
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Review PR
        run: python code_review_agent.py ${{ github.event.pull_request.number }}
```

---

### 2. content_generator.py - Multi-format Content Creation
**Demonstrates:**
- Blog post generation
- Social media adaptation
- SEO optimization
- Multi-format output
- Brand consistency

```python
from kagura.presets import ContentWriterPreset
from kagura import workflow

# Create content writer
writer = (
    ContentWriterPreset("content_creator")
    .with_model("gpt-4o")
    .with_context(
        brand_voice="professional yet approachable",
        target_audience="tech professionals",
        seo_optimization=True
    )
    .build()
)

@workflow
async def create_content_campaign(topic: str, formats: list) -> dict:
    """
    Generate multi-format content:
    1. Research topic
    2. Create long-form content
    3. Adapt to different formats
    4. Optimize for SEO
    5. Generate metadata
    """
    # Research phase
    research = await research_agent(topic)

    # Generate base content
    blog_post = await writer(f"""
        Write a comprehensive blog post about: {topic}

        Research: {research}

        Requirements:
        - 1500-2000 words
        - SEO optimized
        - Include examples
        - Engaging introduction
    """)

    # Adapt to formats in parallel
    adaptations = await asyncio.gather(
        adapt_for_linkedin(blog_post),
        adapt_for_twitter(blog_post),
        create_newsletter(blog_post),
        generate_seo_metadata(blog_post)
    )

    return {
        "topic": topic,
        "blog_post": blog_post,
        "linkedin": adaptations[0],
        "twitter": adaptations[1],
        "newsletter": adaptations[2],
        "seo": adaptations[3]
    }

# Create content campaign
campaign = await create_content_campaign(
    "AI in Healthcare",
    formats=["blog", "linkedin", "twitter", "newsletter"]
)
```

**Key Features:**
- Multi-format content generation
- SEO optimization
- Brand voice consistency
- Audience targeting
- Research integration
- Metadata generation

**Production Considerations:**
- Content quality checks
- Plagiarism detection
- Fact verification
- Editorial review workflow
- Version control
- Publishing automation

**Use Cases:**
- Content marketing
- Social media management
- Blog automation
- Newsletter creation
- SEO content

**Workflow:**
```
Research → Draft → Adapt → Optimize → Review → Publish
   ↓         ↓       ↓        ↓         ↓        ↓
 Web      GPT-4   Format   SEO      Human   CMS API
Search           Specific  Check    Review
```

---

### 3. customer_support_bot.py - Intelligent Support System
**Demonstrates:**
- Multi-tier support (L1/L2/L3)
- Knowledge base integration
- Escalation handling
- Ticket management
- Analytics tracking

```python
from kagura.presets import TechnicalSupportPreset
from kagura.routing import MemoryAwareRouter
from kagura.core.memory import MemoryManager
from kagura import workflow

# Create support bot
support = (
    TechnicalSupportPreset("support_bot")
    .with_model("gpt-4o-mini")
    .with_knowledge_base(path="./knowledge_base")
    .with_memory(type="persistent", persist_dir="./tickets")
    .with_context(
        product="Kagura AI",
        support_level="L1",
        escalation_threshold="complex_issue"
    )
    .build()
)

# Create memory-aware router
memory = MemoryManager(agent_name="support_router")
router = MemoryAwareRouter(memory=memory, context_window=10)

@workflow
async def handle_support_ticket(
    ticket_id: str,
    user_query: str,
    user_history: dict
) -> dict:
    """
    Complete support workflow:
    1. Classify issue severity
    2. Search knowledge base
    3. Attempt L1 resolution
    4. Escalate if needed
    5. Track interaction
    """
    # Classify issue
    classification = await classify_issue(user_query)

    # Search knowledge base
    kb_results = await search_knowledge_base(
        user_query,
        user_history
    )

    # L1 Resolution attempt
    if classification.severity == "low":
        response = await support(f"""
            Ticket #{ticket_id}
            User: {user_query}

            Knowledge base:
            {kb_results}

            Provide solution or escalate.
        """)

        if "ESCALATE" in response:
            # L2 Escalation
            return await escalate_to_l2(
                ticket_id,
                user_query,
                classification,
                kb_results
            )

    # Track interaction
    await log_support_interaction(
        ticket_id=ticket_id,
        query=user_query,
        response=response,
        resolved=True,
        resolution_time=get_duration()
    )

    return {
        "ticket_id": ticket_id,
        "resolved": True,
        "response": response,
        "classification": classification,
        "next_action": "close_ticket"
    }

# Handle ticket
result = await handle_support_ticket(
    ticket_id="T-12345",
    user_query="My agent is not responding",
    user_history={...}
)
```

**Key Features:**
- Intelligent issue classification
- Knowledge base search
- Multi-tier escalation
- Conversation context
- Ticket tracking
- Analytics/metrics

**Production Considerations:**
- SLA compliance
- Response time optimization
- Customer satisfaction tracking
- Escalation rules
- Load balancing
- 24/7 availability

**Use Cases:**
- Customer support automation
- Technical helpdesk
- FAQ automation
- Ticket routing
- Self-service portals

**Metrics:**
```python
# Track support performance
metrics = {
    "avg_resolution_time": "2.5 minutes",
    "first_contact_resolution": "85%",
    "escalation_rate": "15%",
    "customer_satisfaction": "4.7/5.0",
    "tickets_handled": 1250,
    "cost_per_ticket": "$0.15"
}
```

---

### 4. research_assistant.py - Comprehensive Research System
**Demonstrates:**
- Multi-source research
- Web search integration
- Document analysis
- Citation management
- Report generation

```python
from kagura.presets import ResearchPreset
from kagura.web import search, WebScraper
from kagura.core.memory import MultimodalRAG
from kagura import workflow
import asyncio

# Create research assistant
researcher = (
    ResearchPreset("researcher")
    .with_model("gpt-4o")
    .with_web_search(provider="brave")
    .with_memory(type="persistent", persist_dir="./research")
    .build()
)

# RAG for document analysis
rag = MultimodalRAG(
    directory=Path("./research_docs"),
    collection_name="research_kb"
)

@workflow
async def comprehensive_research(
    topic: str,
    depth: str = "comprehensive"
) -> dict:
    """
    Complete research workflow:
    1. Web search for sources
    2. Scrape and analyze content
    3. Cross-reference information
    4. Generate insights
    5. Create report with citations
    """
    # Phase 1: Search
    search_results = await search(
        topic,
        count=20,
        provider="brave"
    )

    # Phase 2: Content extraction (parallel)
    scraper = WebScraper(
        respect_robots_txt=True,
        rate_limit_delay=2.0
    )

    scraping_tasks = [
        scraper.scrape(result.url)
        for result in search_results[:10]
    ]

    contents = await asyncio.gather(
        *scraping_tasks,
        return_exceptions=True
    )

    # Filter successful scrapes
    valid_contents = [
        c for c in contents
        if not isinstance(c, Exception)
    ]

    # Phase 3: Analysis
    analyses = await asyncio.gather(
        analyze_content(valid_contents),
        identify_key_points(valid_contents),
        extract_statistics(valid_contents),
        find_expert_opinions(valid_contents)
    )

    # Phase 4: Synthesis
    report = await researcher(f"""
        Research topic: {topic}

        Sources analyzed: {len(valid_contents)}

        Content analysis: {analyses[0]}
        Key points: {analyses[1]}
        Statistics: {analyses[2]}
        Expert opinions: {analyses[3]}

        Generate comprehensive research report with:
        - Executive summary
        - Key findings (5-7 points)
        - Detailed analysis
        - Statistics and data
        - Expert perspectives
        - Conclusions
        - Recommendations
        - Citations (APA format)
    """)

    # Phase 5: Citation tracking
    citations = format_citations(
        search_results[:10],
        style="APA"
    )

    return {
        "topic": topic,
        "report": report,
        "sources_count": len(valid_contents),
        "citations": citations,
        "confidence": calculate_confidence(analyses),
        "keywords": extract_keywords(report)
    }

# Conduct research
report = await comprehensive_research(
    "Impact of AI on software development",
    depth="comprehensive"
)
```

**Key Features:**
- Multi-source aggregation
- Content extraction
- Cross-referencing
- Citation management
- Report generation
- Quality scoring

**Production Considerations:**
- Source verification
- Fact-checking
- Bias detection
- Citation accuracy
- Report formatting
- Export options (PDF, DOCX, MD)

**Use Cases:**
- Market research
- Competitive analysis
- Academic research
- Due diligence
- Trend analysis
- Literature reviews

**Output Example:**
```markdown
# Research Report: Impact of AI on Software Development

## Executive Summary
AI is fundamentally transforming software development...

## Key Findings
1. 67% of developers now use AI coding assistants
2. Code review time reduced by 40%
3. Bug detection accuracy improved by 30%
...

## Citations
1. Smith, J. (2024). AI in Development. Tech Review.
2. Johnson, A. (2024). Code Assistants Study. ACM.
...
```

---

## Common Production Patterns

### Pattern 1: Error Handling & Retry
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def resilient_agent_call(query: str) -> str:
    """Agent call with automatic retry"""
    try:
        return await agent(query)
    except Exception as e:
        logger.error(f"Agent call failed: {e}")
        raise
```

### Pattern 2: Rate Limiting
```python
from asyncio import Semaphore

# Limit concurrent agent calls
semaphore = Semaphore(5)  # Max 5 concurrent

async def rate_limited_call(query: str):
    async with semaphore:
        return await agent(query)

# Process batch with rate limiting
results = await asyncio.gather(
    *[rate_limited_call(q) for q in queries]
)
```

### Pattern 3: Cost Tracking
```python
from kagura.observability import EventStore

async def cost_aware_agent(query: str) -> dict:
    """Track cost per request"""
    start = time.time()
    result = await agent(query)
    duration = time.time() - start

    # Track metrics
    store = EventStore()
    cost = estimate_cost(query, result)

    await store.record_execution(
        agent_name="my_agent",
        duration=duration,
        cost=cost,
        status="success"
    )

    return {"result": result, "cost": cost}
```

### Pattern 4: Graceful Degradation
```python
async def robust_agent(query: str) -> str:
    """Fallback to simpler model on failure"""
    try:
        # Try primary model
        return await gpt4_agent(query)
    except Exception as e:
        logger.warning(f"GPT-4 failed, falling back: {e}")
        try:
            # Fallback to cheaper model
            return await gpt_mini_agent(query)
        except Exception:
            # Ultimate fallback
            return "Unable to process request. Please try again."
```

### Pattern 5: Monitoring & Alerts
```python
from kagura.observability import EventStore

async def monitored_workflow(input_data):
    """Workflow with monitoring and alerts"""
    store = EventStore()

    try:
        result = await workflow(input_data)

        # Check performance
        stats = store.get_stats(agent_name="workflow")
        if stats["avg_duration"] > 10.0:
            await send_alert("Workflow is slow")

        if stats["error_rate"] > 0.1:
            await send_alert("High error rate")

        return result
    except Exception as e:
        await send_alert(f"Workflow failed: {e}")
        raise
```

## Performance Optimization

### 1. Caching Strategy
```python
from kagura import LLMCache

# Multi-tier cache
cache = LLMCache(
    max_size_mb=500,
    ttl_seconds=3600
)

# Cache static content aggressively
# Don't cache dynamic/time-sensitive data
```

### 2. Parallel Processing
```python
# Process independent tasks in parallel
results = await asyncio.gather(
    task1(),
    task2(),
    task3()
)
# 3× faster than sequential
```

### 3. Batch Operations
```python
# Batch API calls
async def batch_process(items, batch_size=10):
    for i in range(0, len(items), batch_size):
        batch = items[i:i+batch_size]
        await process_batch(batch)
        await asyncio.sleep(1)  # Rate limiting
```

## Production Checklist

Before deploying to production:

### ✅ Functionality
- [ ] All features tested
- [ ] Edge cases handled
- [ ] Error handling implemented
- [ ] Logging configured
- [ ] Monitoring enabled

### ✅ Performance
- [ ] Caching configured
- [ ] Rate limiting implemented
- [ ] Parallel processing optimized
- [ ] Memory usage acceptable
- [ ] Response times < 5s

### ✅ Reliability
- [ ] Retry logic implemented
- [ ] Graceful degradation
- [ ] Timeout handling
- [ ] Circuit breakers
- [ ] Health checks

### ✅ Security
- [ ] Input validation
- [ ] Output sanitization
- [ ] API keys secured
- [ ] Rate limiting
- [ ] Access control

### ✅ Cost
- [ ] Token usage optimized
- [ ] Caching maximized
- [ ] Model selection appropriate
- [ ] Budget alerts configured
- [ ] Cost per request < $0.10

### ✅ Monitoring
- [ ] Metrics collected
- [ ] Alerts configured
- [ ] Dashboard setup
- [ ] Logging centralized
- [ ] Error tracking

## Deployment

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV OPENAI_API_KEY=""
CMD ["python", "customer_support_bot.py"]
```

### Environment Variables
```bash
# .env
OPENAI_API_KEY=sk-...
BRAVE_SEARCH_API_KEY=...
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
LOG_LEVEL=INFO
ENVIRONMENT=production
```

### Monitoring Setup
```python
# monitoring.py
from kagura.observability import EventStore, Dashboard

# Setup monitoring
store = EventStore()
dashboard = Dashboard(store)

# Export metrics
metrics = dashboard.export_metrics()
await send_to_prometheus(metrics)
```

## Next Steps

After mastering real-world examples:
- Deploy your first production agent
- Set up monitoring and alerts
- Optimize costs and performance
- Scale horizontally
- Implement CI/CD

## Documentation

- [Production Deployment Guide](../../docs/en/guides/production.md)
- [Monitoring Guide](../../docs/en/guides/monitoring.md)
- [Cost Optimization](../../docs/en/guides/cost_optimization.md)

---

**These real-world examples show you how to build production-ready AI applications with Kagura AI!**
