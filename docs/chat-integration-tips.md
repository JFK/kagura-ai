# Chat Integration Tips & Best Practices

> **Maximize Kagura AI with ChatGPT, Claude Chat, and other AI platforms**

This guide helps you get the most out of Kagura AI when integrated with chat-based AI platforms using Remote MCP (Model Context Protocol).

---

## 📋 Overview

### What is Kagura AI?

Kagura AI is a **universal memory platform** that allows your conversations and knowledge to be **shared across** Claude, ChatGPT, Gemini, and all your AI agents.

**Key Features**:
- 🧠 **Universal Memory**: Store and recall information across all AI platforms
- 🔍 **Smart Search**: Semantic search with vector embeddings + BM25
- 📊 **Knowledge Graph**: Track relationships between memories
- 🌐 **Web Integration**: Search web, YouTube, arXiv directly
- 🎨 **Multimodal**: Index and search images, PDFs, audio
- 💻 **Coding Support**: Track file changes, errors, design decisions

### Remote MCP vs Local MCP

| Feature | Remote MCP | Local MCP |
|---------|------------|-----------|
| **Platforms** | ChatGPT, Claude Chat, Gemini | Claude Desktop, Claude Code, Cursor |
| **Transport** | HTTP/SSE | stdio |
| **File Access** | ❌ No | ✅ Yes |
| **Memory Tools** | ✅ All (49/56) | ✅ All (56/56) |
| **Security** | API Key required | Local only |

**This guide focuses on Remote MCP** (ChatGPT, Claude Chat, etc.)

---

## ⚡ Quick Start

### Step 1: Start Kagura Remote MCP Server

```bash
# Install Kagura
pip install kagura-ai[full]

# Start remote MCP server
docker compose -f docker-compose.prod.yml up -d

# Or local dev mode
uvicorn kagura.api.server:app --host 0.0.0.0 --port 8080
```

### Step 2: Configure Your AI Platform

**ChatGPT** (via MCP over HTTP/SSE):
1. Open ChatGPT Settings → Tools
2. Add MCP Server: `https://your-domain.com/mcp`
3. Add API Key (optional, recommended for production)

**Claude Chat** (future support):
- Anthropic announced MCP support for Claude Chat in 2026

See: [MCP over HTTP/SSE Setup Guide](./mcp-http-setup.md)

### Step 3: Try It Out!

Try these prompts in your AI chat:

```
"Hello! Can you run memory_stats to show me Kagura's status?"

"Remember that my favorite programming language is Python"

"Search the web for Python 3.13 release notes"

"What do you remember about my preferences?"
```

---

## 🧰 Remote MCP Tools (49/56)

### ✅ Available Tools

#### Memory Tools (13 tools)

| Tool | Description | Example Usage |
|------|-------------|---------------|
| `memory_store` | Save information | "Remember X" |
| `memory_recall` | Retrieve by key | "What did I say about Y?" |
| `memory_search` | Semantic search | "Find memories about Z" |
| `memory_list` | List all memories | "What do you remember?" |
| `memory_delete` | Forget information | "Forget about X" |
| `memory_feedback` | Mark useful/outdated | Automatic |
| `memory_fetch` | Get specific memory | Internal use |
| `memory_search_ids` | Search with IDs only | Low-token search |
| `memory_stats` | Get memory statistics | "Show memory stats" |
| `memory_get_related` | Get related memories | Graph traversal |
| `memory_get_user_pattern` | Analyze user patterns | "What are my interests?" |
| `memory_record_interaction` | Track interactions | Automatic |

#### Web Search Tools (5 tools)

| Tool | Description |
|------|-------------|
| `brave_web_search` | General web search |
| `brave_image_search` | Image search |
| `brave_video_search` | Video search |
| `brave_news_search` | News search |
| `web_scrape` | Scrape web pages |

**Note**: Requires `BRAVE_API_KEY` environment variable

#### Academic Search (1 tool)

| Tool | Description |
|------|-------------|
| `arxiv_search` | Search academic papers on arXiv |

#### YouTube Tools (4 tools)

| Tool | Description | Example |
|------|-------------|---------|
| `get_youtube_transcript` | Get video transcript | "Transcribe this video" |
| `get_youtube_metadata` | Get video info | "Get video details" |
| `youtube_summarize` | Summarize video | "Summarize this YouTube video" |
| `youtube_fact_check` | Verify claims | "Fact-check this video's claims" |

#### Multimodal Tools (2 tools)

| Tool | Description | Note |
|------|-------------|------|
| `multimodal_index` | Index images/PDFs/audio | Requires Gemini API |
| `multimodal_search` | Search indexed content | Requires Gemini API |

**Note**: File upload via Remote MCP coming in v4.1 ([Issue #462](https://github.com/JFK/kagura-ai/issues/462))

#### Coding Tools (14 tools)

| Tool | Description |
|------|-------------|
| `coding_start_session` | Start coding session |
| `coding_end_session` | End session + AI summary |
| `coding_track_file_change` | Track file modifications |
| `coding_record_error` | Log errors with stack traces |
| `coding_search_errors` | Find similar past errors |
| `coding_record_decision` | Document design decisions |
| `coding_analyze_patterns` | Analyze coding preferences |
| `coding_analyze_file_dependencies` | AST-based dependency analysis |
| `coding_analyze_refactor_impact` | Refactoring impact assessment |
| `coding_suggest_refactor_order` | Safe refactoring order |
| `coding_get_project_context` | Get project overview |
| `coding_get_issue_context` | Get GitHub issue details |
| `coding_link_github_issue` | Link session to issue |
| `coding_generate_pr_description` | AI-powered PR description |

#### GitHub Tools (6 tools)

| Tool | Description |
|------|-------------|
| `github_exec` | Safe GitHub CLI execution |
| `github_issue_list` | List issues |
| `github_issue_view` | View issue details |
| `github_pr_view` | View PR details |
| `github_pr_create` | Create PR |
| `github_pr_merge` | Merge PR |

**Note**: Requires `gh` CLI installed and authenticated

#### Telemetry Tools (2 tools)

| Tool | Description |
|------|-------------|
| `telemetry_stats` | Get usage statistics |
| `telemetry_cost` | Get cost summary |

#### Other Tools (2 tools)

| Tool | Description |
|------|-------------|
| `fact_check_claim` | Verify claims using web search |
| `route_query` | Route to appropriate agent (placeholder) |

---

### ❌ Local-Only Tools (7 tools)

These tools **only work with Local MCP** (Claude Desktop, Claude Code, Cursor):

| Tool | Why Local-Only? | Alternative |
|------|-----------------|-------------|
| `file_read` | Direct file system access | Copy/paste content |
| `file_write` | Direct file system access | Copy/paste output |
| `dir_list` | Direct file system access | Manually list files |
| `shell_exec` | Shell command execution | Use `github_exec` for GitHub CLI |
| `media_open_image` | Opens OS application | Not applicable |
| `media_open_audio` | Opens OS application | Not applicable |
| `media_open_video` | Opens OS application | Not applicable |

**Future**: File upload via Remote MCP is planned for v4.1 ([Issue #462](https://github.com/JFK/kagura-ai/issues/462))

---

## 💡 Recommended Workflows

### Pattern 1: Small Data (Keep in Context) 🔵

**When to use**: Small amounts of information needed only in current conversation

**How**:
```
User: "Python 3.13 was released on October 7, 2024"
AI: [Keeps in conversation context, no storage]
```

**Pros**: Fast, no overhead
**Cons**: Lost after conversation ends

---

### Pattern 2: Important Data (Persistent Memory) ⭐ RECOMMENDED

**When to use**: Information you want to remember long-term

**How**:
```
User: "Remember that I prefer FastAPI over Django for backend projects.
       This is important and should be persistent."

AI: [Uses memory_store with scope="persistent"]
```

**Later**:
```
User: "What backend framework should I use for my new project?"
AI: [Uses memory_recall/search to retrieve preference]
```

**Pros**:
- Survives across conversations
- Works across all AI platforms
- Searchable semantically

**Cons**: Requires explicit instruction to remember

**Best Practice**:
- Use keywords like "remember", "save", "persist"
- Be explicit: "This is important"
- Add context: "for backend projects"

---

### Pattern 3: Large Data (Multimodal RAG) 🚀

**When to use**: Large documents, images, multiple files

**How** (requires Gemini API):
```
User: "Index all images in ./photos directory"
AI: [Uses multimodal_index]

User: "Find photos with dogs"
AI: [Uses multimodal_search]
```

**Pros**:
- Handles large datasets
- Semantic image search
- Multi-language support

**Cons**:
- Requires Gemini API key
- File upload not yet available via Remote MCP (coming v4.1)

**Current Workaround**: Use Local MCP (Claude Desktop) for file indexing

---

## 📝 Example Prompts (Copy & Paste)

### Memory Operations

**Store**:
```
"Remember that my project deadline is December 31, 2025. This is important."

"Save this information: I work as a Python developer at Acme Corp"

"Remember my coding style preferences: always use type hints and docstrings"
```

**Search**:
```
"What do you remember about my project deadline?"

"Find all memories related to my coding preferences"

"What do you know about me?"

"Show me all memories tagged with 'python'"
```

**Delete**:
```
"Forget about my old JavaScript preference"

"Delete the memory about my previous job"
```

**Statistics**:
```
"How many memories do you have about me?"

"Show me memory statistics"

"What are my most common topics?"
```

---

### Web Search

**Latest News**:
```
"What's the latest version of Python? Search the web."

"Find recent news about FastAPI framework"

"Search for Python 3.13 release notes"
```

**Comparison**:
```
"Compare FastAPI vs Django. Search the web for pros and cons."

"Find benchmarks comparing PostgreSQL and MySQL"
```

**Images**:
```
"Search for images of 'neural network architecture diagrams'"

"Find screenshots of VSCode themes"
```

---

### YouTube

**Summarize**:
```
"Summarize this YouTube video: https://www.youtube.com/watch?v=xxxxx"

"Give me key points from this tutorial video: [URL]"
```

**Fact-Check**:
```
"Fact-check the claims made in this video: [URL]"

"Verify if the statistics mentioned in [URL] are accurate"
```

**Transcript**:
```
"Get the transcript for this video: [URL]"

"Extract the code examples from this tutorial: [URL]"
```

---

### Coding

**Start Session**:
```
"Start a coding session for implementing user authentication"

"Begin tracking my work on Issue #123"
```

**Track Changes**:
```
"I just modified auth.py to add OAuth2 support"

"Record that I fixed the database connection bug"
```

**Record Errors**:
```
"Log this error: [paste stack trace]"

"Record this TypeScript error with screenshot"
```

**Search Past Errors**:
```
"Have I seen this 'Connection refused' error before?"

"Find similar database migration errors from past sessions"
```

**End Session**:
```
"End coding session and generate a summary"

"Finish session and create PR description"
```

---

### GitHub

**List Issues**:
```
"List open issues in JFK/kagura-ai repository"

"Show me issues labeled 'bug' and 'priority:high'"
```

**View Details**:
```
"Get details for issue #463"

"Show me PR #472"
```

**Safe Execution**:
```
"Run: gh issue list --repo JFK/kagura-ai --state open"

"Execute: gh pr view 472"
```

---

## 🌍 Cross-Platform Memory

### user_id Management

**Best Practice**: Always specify `user_id` for personal memories

```python
# ✅ Good
memory_store(
    user_id="user_jfk",
    key="python_preference",
    value="Prefer FastAPI over Django"
)

# ❌ Bad (uses default user)
memory_store(
    key="python_preference",
    value="Prefer FastAPI over Django"
)
```

**Prompt Example**:
```
"Remember this for user_id='john_doe': I prefer dark mode"
```

---

### agent_name Scoping

Control memory scope with `agent_name`:

**Global Memory** (shared across all conversations):
```python
memory_store(
    agent_name="global",
    key="coding_style",
    value="Always use type hints"
)
```

**Thread-Specific Memory** (this conversation only):
```python
memory_store(
    agent_name="thread_abc123",
    key="temp_data",
    value="..."
)
```

**Prompt Example**:
```
"Remember this globally: I prefer Python over JavaScript"

"Remember this just for this conversation: current project is 'kagura-ai'"
```

---

### Memory Scope

**Working Memory** (temporary, session-only):
```python
memory_store(scope="working", ...)
```

**Persistent Memory** (saved to disk, survives restart):
```python
memory_store(scope="persistent", ...)
```

**Prompt Example**:
```
"Remember this permanently: my email is john@example.com"

"Save this temporarily: current task is 'write documentation'"
```

---

## ❓ Frequently Asked Questions (FAQ)

### Q: Why can't I attach files?

**A**: Remote MCP (ChatGPT, Claude Chat) currently doesn't support file uploads.

**Workarounds**:
1. Copy/paste file content directly into chat
2. Use Local MCP (Claude Desktop, Claude Code) for file operations
3. Wait for v4.1 Multimodal Upload API ([Issue #462](https://github.com/JFK/kagura-ai/issues/462))

---

### Q: My memories disappear after the conversation ends. Why?

**A**: You're likely using `scope="working"` (default for temporary data).

**Solution**: Explicitly ask to persist:
```
"Remember this PERMANENTLY: [your data]"
```

Or specify in prompt:
```
"Store this with scope='persistent': [your data]"
```

---

### Q: How do I share memories across different AI platforms?

**A**: Use `user_id` consistently:

1. **ChatGPT**:
   ```
   "Store this for user_id='john': I prefer Python"
   ```

2. **Claude Chat** (same user_id):
   ```
   "What programming languages does user_id='john' prefer?"
   ```

Both AIs will access the same Kagura memory!

---

### Q: Search results are inaccurate. How to improve?

**A**: Tips for better search:

1. **Use semantic search** (not exact keywords):
   ```
   ✅ "Find memories about backend development"
   ❌ "Find 'FastAPI Django comparison'"
   ```

2. **Add tags when storing**:
   ```
   "Remember this with tags=['python', 'backend', 'framework']:
    I prefer FastAPI"
   ```

3. **Use hybrid search** (BM25 + vector):
   ```
   "Search memories for 'FastAPI' using hybrid search"
   ```

4. **Provide feedback**:
   ```
   "Mark memory [key] as useful"
   "This memory is outdated"
   ```

---

### Q: How much does it cost?

**A**: Kagura AI is open-source and free to self-host.

**Costs**:
- **Self-hosting**: Free (uses local ChromaDB)
- **Cloud hosting**: Your server costs (AWS, DigitalOcean, etc.)
- **AI APIs**:
  - OpenAI/Anthropic/Google APIs for embedding (optional)
  - Brave Search API (optional, free tier available)
  - Gemini API for multimodal (optional)

**Cost Tracking**:
```
"Show me telemetry cost summary"
```

---

### Q: Is my data private?

**A**: Yes! Kagura is **privacy-first**:

- ✅ **Self-hosted**: You own your data
- ✅ **Local storage**: SQLite + ChromaDB on your machine
- ✅ **No vendor lock-in**: Export anytime (JSONL format)
- ✅ **Open source**: Audit the code yourself

**Export your data**:
```bash
kagura memory export --output=./backup --format=jsonl
```

---

## 🔧 Troubleshooting

### Memory not found

**Symptom**: "I don't have any memories about X"

**Causes**:
1. Wrong `user_id`
2. Wrong `agent_name`
3. Memory was stored as `scope="working"` and session ended

**Debug**:
```
"List all memories"
"Show memory statistics"
"Search for memories without filters"
```

---

### Search returns nothing

**Symptom**: `memory_search` returns empty results

**Solutions**:
1. **Check if memory exists**:
   ```
   "List all memories"
   ```

2. **Try different search query**:
   ```
   ✅ "Find memories about coding"
   ❌ "Find memory with exact key 'python_coding_style_2024'"
   ```

3. **Use `memory_recall` for exact key**:
   ```
   "Recall memory with key='python_preference'"
   ```

---

### High API costs

**Symptom**: Embedding API costs are high

**Solutions**:
1. **Use local embeddings** (sentence-transformers):
   ```bash
   # No API costs, runs locally
   pip install kagura-ai[ai]
   ```

2. **Reduce search frequency**:
   - Use `memory_recall` (exact key) instead of `memory_search`
   - Use `memory_search_ids` (low-token mode)

3. **Monitor costs**:
   ```
   "Show telemetry cost summary"
   ```

---

### Remote MCP connection fails

**Symptom**: AI can't connect to Kagura

**Debug**:
1. **Check server is running**:
   ```bash
   curl http://localhost:8080/api/v1/health
   ```

2. **Check API key** (if using authentication):
   ```bash
   curl -H "Authorization: Bearer YOUR_KEY" \
        http://localhost:8080/api/v1/health
   ```

3. **Check logs**:
   ```bash
   docker compose logs -f api
   ```

See: [Troubleshooting Guide](./troubleshooting.md)

---

## 🚀 Advanced Tips

### 1. GraphMemory for Knowledge Discovery

**Link related memories**:
```
"Link my Python preference memory with FastAPI tutorial memory"

"Connect all memories about 'backend development' into a knowledge graph"
```

**Discover relationships**:
```
"What memories are related to my Python preference?"

"Find all concepts connected to 'FastAPI' within 2 hops"
```

---

### 2. Pattern Analysis

**Analyze your interactions**:
```
"Analyze my coding patterns from past sessions"

"What are my most common topics?"

"Show me my interaction statistics"
```

**Get insights**:
```
"What programming languages do I use most?"

"What time of day am I most productive?"
```

---

### 3. Session Summaries

**Track coding sessions**:
```
"Start coding session for Issue #123"

[... work on code ...]

"End session and generate AI summary with cost tracking"
```

**Generate PR descriptions**:
```
"Generate PR description from current coding session"
```

---

### 4. Fact-Checking Workflow

**Verify claims**:
```
"Fact-check this claim: Python 3.13 is 40% faster than 3.12"

"Verify the statistics in this YouTube video: [URL]"
```

**Cross-reference sources**:
```
"Search arXiv for papers about neural network optimization"

"Compare the claim with recent news articles"
```

---

## 🔗 Related Documentation

- **Setup Guides**:
  - [MCP over HTTP/SSE (ChatGPT)](./mcp-http-setup.md)
  - [Claude Desktop Setup](./mcp-setup.md)
  - [Claude Code Setup](./mcp-claude-code-setup.md)

- **Platform-Specific Workflows**:
  - [ChatGPT Workflow Examples](./examples/chatgpt-workflow.md)
  - [Claude Workflow Examples](./examples/claude-workflow.md)

- **Technical References**:
  - [REST API Reference](./api-reference.md)
  - [Self-Hosting Guide](./self-hosting.md)
  - [Architecture Overview](./architecture.md)

- **Advanced Topics**:
  - [Memory Export/Import](./memory-export.md)
  - [Troubleshooting Guide](./troubleshooting.md)

---

## 📚 Additional Resources

### Official Links
- [GitHub Repository](https://github.com/JFK/kagura-ai)
- [PyPI Package](https://pypi.org/project/kagura-ai/)
- [Model Context Protocol](https://modelcontextprotocol.io/)

### Community
- [GitHub Issues](https://github.com/JFK/kagura-ai/issues) - Bug reports & feature requests
- [GitHub Discussions](https://github.com/JFK/kagura-ai/discussions) - Q&A & community

---

**Version**: 4.0.0
**Last updated**: 2025-11-02
