# Full-Featured Mode Guide

This guide explains how to use Kagura AI's full-featured mode, which combines multimodal RAG (local file indexing) with web search capabilities for maximum power.

## Overview

Full-featured mode provides:
- **Local Knowledge**: Search through your project files (code, docs, images, PDFs)
- **Web Search**: Access current information from the internet
- **Unified Chat**: Single interface for both local and web data
- **Intelligent Routing**: AI decides when to use local files vs web search

## Quick Start

### One Command Setup

Start full-featured mode with a single command:

```bash
kagura chat --full --dir ./my-project
```

This is equivalent to:

```bash
kagura chat --enable-multimodal --enable-web --dir ./my-project
```

### Example Session

```bash
$ kagura chat --full --dir ./my-app

Initializing multimodal RAG for: ./my-app
✓ Indexed 127 files from ./my-app

🚀 Full-Featured Mode
⚡ Multimodal RAG
   Indexed: ./my-app
🌐 Web Search

Type your message to chat with AI, or use commands:
  /help      - Show help
  /exit      - Exit chat

[You] > How does our authentication system work?

Searching indexed files...
Found 3 relevant documents
💬 Generating response...

[AI]
Based on your codebase (auth.py and auth-diagram.png), your authentication
system uses:

1. **JWT Tokens**:
   - Generated after successful login (auth.py:42)
   - 24-hour expiry configured in config.py
   - RSA-256 signature

2. **Password Hashing**:
   - bcrypt with cost factor 12
   - Implemented in auth.py:authenticate()

3. **Token Validation**:
   - Middleware checks Authorization header
   - Validates signature and expiry
   - Loads user from database

The architecture diagram shows the complete flow from login to protected
resource access.

[You] > What are the current best practices for JWT in 2025?

🌐 Searching the web for: JWT security best practices 2025
✓ Web search completed
💬 Generating response...

[AI]
Current best practices for JWT in 2025:

1. **Short Expiry Times**:
   - Access tokens: 15 minutes (recommended)
   - Your current 24 hours is too long
   - Use refresh tokens for long sessions

2. **Algorithm Security**:
   - ✅ You're using RS256 (good!)
   - Avoid HS256 for production

3. **Token Storage**:
   - Never store in localStorage (XSS vulnerable)
   - Use httpOnly cookies
   - Consider SameSite=Strict

4. **Token Rotation**:
   - Implement refresh token rotation
   - Invalidate old tokens on rotation

5. **Content Minimization**:
   - Only store essential claims
   - Avoid PII in tokens

[Sources: OWASP JWT Cheat Sheet 2025, Auth0 Security Blog]

[You] > Can you update our auth.py to follow these best practices?

Searching indexed files...
💬 Generating response...

[AI]
I'll suggest updates to auth.py based on 2025 best practices:

\`\`\`python
# auth.py - Updated with 2025 best practices

from datetime import timedelta

# NEW: Shorter token expiry
ACCESS_TOKEN_EXPIRY = timedelta(minutes=15)  # Was: 24 hours
REFRESH_TOKEN_EXPIRY = timedelta(days=7)

# NEW: Add refresh token support
def create_tokens(user_id: str) -> dict:
    """Create access and refresh tokens."""
    access_token = create_jwt(
        payload={"sub": user_id, "type": "access"},
        expires_delta=ACCESS_TOKEN_EXPIRY
    )
    refresh_token = create_jwt(
        payload={"sub": user_id, "type": "refresh"},
        expires_delta=REFRESH_TOKEN_EXPIRY
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token
    }

# NEW: Token refresh endpoint
@app.post("/auth/refresh")
async def refresh_access_token(refresh_token: str):
    """Refresh access token using refresh token."""
    payload = verify_jwt(refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(401, "Invalid token type")

    new_access_token = create_jwt(
        payload={"sub": payload["sub"], "type": "access"},
        expires_delta=ACCESS_TOKEN_EXPIRY
    )
    return {"access_token": new_access_token}
\`\`\`

Key changes:
1. Reduced access token to 15 minutes
2. Added refresh token with 7-day expiry
3. New /auth/refresh endpoint for token rotation
4. Type field to distinguish token types

Would you like me to also update the frontend to handle token refresh?
```

## Prerequisites

### Installation

Install both multimodal and web dependencies:

```bash
pip install kagura-ai[multimodal,web]
```

Or install all extras at once:

```bash
pip install kagura-ai[all]
```

### API Keys

1. **Gemini API** (for multimodal):
   ```bash
   export GEMINI_API_KEY="your-gemini-key"
   ```

2. **Brave Search** (optional, for better web results):
   ```bash
   export BRAVE_API_KEY="your-brave-key"
   ```

Without Brave key, Kagura falls back to DuckDuckGo (no API key required).

## Use Cases

### 1. Code Analysis + Web Research

Analyze your code with context from latest best practices:

```bash
[You] > Review our database connection pool code and compare with current best practices

# AI will:
# 1. Read your db.py and related files
# 2. Search web for "database connection pool best practices 2025"
# 3. Compare your code with current recommendations
# 4. Suggest improvements
```

### 2. Documentation + API Lookup

Work with your docs and external API documentation:

```bash
[You] > How do I integrate Stripe payments in our checkout flow?

# AI will:
# 1. Find your checkout code
# 2. Search Stripe's latest API docs
# 3. Provide implementation guide
# 4. Reference your existing payment structure
```

### 3. Debugging + Error Research

Debug with your code context and web solutions:

```bash
[You] > Why am I getting "Connection refused" in docker-compose?

# AI will:
# 1. Read your docker-compose.yml
# 2. Check your Dockerfile
# 3. Search web for common docker connection issues
# 4. Diagnose specific to your setup
```

### 4. Project Planning + Market Research

Plan features with local context and market data:

```bash
[You] > What features should we add to compete with [competitor]?

# AI will:
# 1. Analyze your current features (from code/docs)
# 2. Research competitor's features (web search)
# 3. Find industry trends (web search)
# 4. Suggest prioritized feature list
```

## Programmatic Usage

### Full-Featured Agent

Create an agent with both capabilities:

```python
from kagura import agent
from kagura.core.memory import MultimodalRAG
from kagura.web import web_search
from pathlib import Path

async def search_tool(query: str) -> str:
    """Search the web for information."""
    return await web_search(query)

@agent(
    model="gemini/gemini-1.5-flash",
    enable_multimodal_rag=True,
    rag_directory=Path("./project"),
    tools=[search_tool]
)
async def full_featured_assistant(question: str, rag: MultimodalRAG) -> str:
    """Answer questions using both local files and web search.

    Question: {{ question }}

    Use rag.query() to search local files.
    Use search_tool() to search the web.
    """
    pass

# Usage
answer = await full_featured_assistant(
    "Compare our API design with REST best practices 2025"
)
```

### Manual Control

Control when to use each source:

```python
from kagura.core.memory import MultimodalRAG
from kagura.web import web_search
from pathlib import Path

# Initialize RAG
rag = MultimodalRAG(directory=Path("./project"))
await rag.build_index()

async def hybrid_search(query: str) -> dict:
    """Search both local and web."""

    # Search local files
    local_results = rag.query(query, n_results=3)

    # Search web
    web_results = await web_search(query)

    return {
        "local": local_results,
        "web": web_results
    }

# Usage
results = await hybrid_search("authentication implementation")
```

## Configuration

### Command-Line Options

```bash
# Full mode (recommended)
kagura chat --full --dir ./project

# Equivalent long form
kagura chat --enable-multimodal --enable-web --dir ./project

# With model selection
kagura chat --full --dir ./project --model gpt-4o

# With custom session directory
kagura chat --full --dir ./project --session-dir ./my-sessions
```

### Programmatic Configuration

```python
from kagura.chat import ChatSession
from pathlib import Path

session = ChatSession(
    model="gemini/gemini-1.5-flash",
    enable_multimodal=True,
    rag_directory=Path("./project"),
    enable_web=True,
    session_dir=Path("./.kagura/sessions")
)

await session.run()
```

## How It Works

### Intelligent Routing

The AI decides when to use each source:

```
Question: "How does our auth work?"
→ Uses: Local RAG (reads your code)

Question: "What are JWT best practices?"
→ Uses: Web search (gets current info)

Question: "Update our auth to follow best practices"
→ Uses: Both (reads code + researches practices)
```

### Data Flow

```
User Query
    ↓
┌───────────────────┐
│   Chat Session    │
│   (Memory)        │
└───────────────────┘
    ↓           ↓
┌─────────┐  ┌─────────┐
│   RAG   │  │   Web   │
│ Search  │  │ Search  │
└─────────┘  └─────────┘
    ↓           ↓
┌───────────────────┐
│   Context         │
│   Aggregation     │
└───────────────────┘
    ↓
┌───────────────────┐
│   LLM             │
│   (Gemini/GPT)    │
└───────────────────┘
    ↓
  Response
```

## Best Practices

### 1. Organize Your Project

Structure for better RAG results:

```
project/
├── src/              # Source code
├── docs/             # Documentation
├── diagrams/         # Architecture diagrams
├── specs/            # Requirements, RFCs
└── .kaguraignore     # Exclude build artifacts
```

### 2. Use Descriptive Queries

Good queries get better results:

```
✅ "How does our rate limiting implementation compare to industry standards?"
✅ "What security vulnerabilities exist in our authentication code?"
✅ "Refactor our database layer using 2025 best practices"

❌ "Check this"
❌ "Is this good?"
❌ "Help"
```

### 3. Iterative Refinement

Build on previous context:

```bash
[You] > What payment methods do we support?
[AI] > You support: Credit cards (Stripe), PayPal...

[You] > What other payment methods are popular now?
[AI] > [Searches web for current trends]

[You] > Add Apple Pay to our payment flow
[AI] > [References your code + Apple Pay docs]
```

### 4. Monitor Costs

Full-featured mode uses APIs for both RAG and web:

```python
# Track API usage
stats = await rag.build_index()
print(f"Files processed with Gemini: {stats['multimodal_files']}")

# Use caching to reduce costs
rag = MultimodalRAG(
    directory=Path("./project"),
    enable_cache=True,
    cache_size_mb=500
)
```

### 5. Incremental Updates

Keep RAG index fresh:

```python
# Initial build (run once)
await rag.build_index()

# Incremental updates (run periodically)
await rag.incremental_update()  # Only new/modified files
```

## Performance Optimization

### 1. Choose the Right Model

Different models for different needs:

```bash
# Fast and cheap (recommended)
kagura chat --full --dir . --model gemini/gemini-1.5-flash

# More accurate
kagura chat --full --dir . --model gemini/gemini-1.5-pro

# Code-focused
kagura chat --full --dir . --model gpt-4o
```

### 2. Enable Caching

Cache both RAG and web results:

```python
from kagura.core.memory import MultimodalRAG
from kagura.web.scraper import WebScraper

# RAG caching
rag = MultimodalRAG(
    directory=Path("./project"),
    enable_cache=True,
    cache_size_mb=500
)

# Web scraping with rate limiting
scraper = WebScraper(rate_limit_delay=1.0)
```

### 3. Parallel Processing

Process files in parallel:

```python
await rag.build_index(max_concurrent=5)  # Default: 3
```

### 4. Selective Indexing

Use `.kaguraignore` to exclude unnecessary files:

```
# .kaguraignore
node_modules/
.venv/
*.log
*.tmp
build/
dist/
__pycache__/
.git/
```

## Troubleshooting

### "No local results found"

Check if files are indexed:

```python
indexed_files = rag.get_indexed_files()
print(f"Indexed: {len(indexed_files)} files")

# Rebuild if needed
await rag.build_index(force_rebuild=True)
```

### "Web search failed"

Check API keys:

```bash
echo $BRAVE_API_KEY
echo $GEMINI_API_KEY
```

Fallback is automatic (Brave → DuckDuckGo).

### "Out of memory"

Reduce cache size or concurrent processing:

```python
rag = MultimodalRAG(
    directory=Path("./project"),
    cache_size_mb=100  # Reduce from 500
)

await rag.build_index(max_concurrent=1)  # Process one at a time
```

### "API rate limit exceeded"

For Gemini:

```python
await rag.build_index(max_concurrent=1)  # Slower but within limits
```

For Brave/web:

```python
scraper = WebScraper(rate_limit_delay=2.0)  # Increase delay
```

## Examples

### Example 1: Full Stack Development Assistant

```python
from kagura import agent
from kagura.core.memory import MultimodalRAG
from kagura.web import web_search
from pathlib import Path

async def web_tool(query: str) -> str:
    return await web_search(query)

@agent(
    model="gemini/gemini-1.5-flash",
    enable_multimodal_rag=True,
    rag_directory=Path("./fullstack-app"),
    tools=[web_tool]
)
async def dev_assistant(task: str, rag: MultimodalRAG) -> str:
    """Help with full-stack development tasks.

    Task: {{ task }}

    You have access to:
    - Local codebase (frontend + backend)
    - Architecture diagrams
    - Web search for current best practices
    """
    pass

# Usage
response = await dev_assistant(
    "Add real-time notifications using WebSockets"
)
```

### Example 2: Security Audit

```python
@agent(
    model="gpt-4o",
    enable_multimodal_rag=True,
    rag_directory=Path("./app"),
    tools=[web_tool]
)
async def security_auditor(component: str, rag: MultimodalRAG) -> str:
    """Audit {{ component }} for security vulnerabilities.

    1. Analyze the code
    2. Research current CVEs and vulnerabilities
    3. Check against OWASP Top 10
    4. Provide actionable recommendations
    """
    pass

# Usage
report = await security_auditor("authentication module")
```

### Example 3: Documentation Writer

```python
@agent(
    model="gemini/gemini-1.5-flash",
    enable_multimodal_rag=True,
    rag_directory=Path("./project"),
    tools=[web_tool]
)
async def doc_writer(topic: str, rag: MultimodalRAG) -> str:
    """Write documentation for {{ topic }}.

    1. Read the implementation code
    2. Research documentation best practices
    3. Generate comprehensive docs with examples
    """
    pass

# Usage
docs = await doc_writer("API authentication endpoints")
```

## Cost Estimation

Approximate costs for full-featured mode:

### Gemini API (Multimodal RAG)
- **Flash (1.5)**: $0.25 per 1M input tokens
- **Pro (1.5)**: $1.25 per 1M input tokens

Example: Indexing 1000 files (~50MB text) ≈ $0.10-0.50

### Brave Search API
- **Free tier**: 2000 queries/month
- **Paid**: $5/month for 20,000 queries

### Typical Monthly Cost
- Small project (< 5000 files): < $10/month
- Medium project (5000-20000 files): $10-50/month
- Large project (> 20000 files): $50-200/month

**Optimization tips**:
- Enable caching (reduce repeat processing)
- Use incremental updates (process only changed files)
- Use Flash model (3x cheaper than Pro)
- Cache web search results

## Next Steps

- [Multimodal RAG Guide](./chat-multimodal.md) - Deep dive into local indexing
- [Web Integration Guide](./web-integration.md) - Advanced web search techniques
- [API Reference](../api/full-featured.md) - Complete API documentation

## Resources

- [Gemini API Pricing](https://ai.google.dev/pricing)
- [Brave Search API](https://brave.com/search/api/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Kagura AI Examples](../../examples/)