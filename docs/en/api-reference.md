# API Reference - Kagura v4.0

> **REST API & MCP Tools Documentation**

Comprehensive reference for Kagura's REST API and MCP tools.

---

## 📚 Table of Contents

1. [REST API](#rest-api) - HTTP endpoints
2. [MCP over HTTP/SSE](#mcp-over-httpsse) - ChatGPT Connector
3. [MCP Tools](#mcp-tools) - Claude Desktop, stdio
4. [Authentication](#authentication) - API Keys
5. [OpenAPI Specification](#openapi-specification)

---

## 🌐 REST API

**Base URL**: `http://localhost:8000` (default)

**Interactive Docs**: http://localhost:8000/docs

### Authentication

**v4.0.0**: Optional API Key authentication

```bash
# With API key
curl -H "Authorization: Bearer kagura_abc123..." \
     http://localhost:8000/api/v1/memory

# Without (uses default_user)
curl http://localhost:8000/api/v1/memory
```

**Headers**:
- `Authorization: Bearer <api_key>` - Optional API key
- `X-User-ID: <user_id>` - Optional user identifier

---

## Memory Operations

### POST /api/v1/memory

Create or update a memory.

**Request**:
```json
{
  "key": "python_tips",
  "value": "Always use type hints",
  "scope": "persistent",
  "tags": ["python"],
  "importance": 0.8
}
```

**Response** (201 Created):
```json
{
  "key": "python_tips",
  "value": "Always use type hints",
  "scope": "persistent",
  "tags": ["python"],
  "importance": 0.8
}
```

### GET /api/v1/memory/{key}

Retrieve a memory by key.

**Response** (200 OK):
```json
{
  "key": "python_tips",
  "value": "Always use type hints",
  "scope": "persistent"
}
```

### DELETE /api/v1/memory/{key}

Delete a memory.

**Response** (204 No Content)

---

## Search & Recall

### POST /api/v1/recall

Semantic search using RAG.

**Request**:
```json
{
  "query": "Python coding tips",
  "k": 5,
  "scope": "all"
}
```

**Response** (200 OK):
```json
{
  "results": [
    {"key": "python_tips", "value": "...", "score": 0.95}
  ]
}
```

### GET /api/v1/search

Full-text search.

**Query params**:
- `q`: Search query
- `limit`: Max results (default: 10)

---

## Graph Operations

### POST /api/v1/graph/interaction

Record AI-User interaction.

**Request**:
```json
{
  "user_id": "jfk",
  "query": "How do I use async?",
  "response": "...",
  "metadata": {"topic": "python"}
}
```

### GET /api/v1/graph/pattern/{user_id}

Analyze user patterns.

**Response**:
```json
{
  "user_id": "jfk",
  "total_interactions": 150,
  "topics": {"python": 45, "docker": 20},
  "learning_trajectory": [...]
}
```

---

## System Endpoints

### GET /api/v1/health

Health check.

**Response**:
```json
{
  "status": "healthy",
  "services": {
    "database": "healthy",
    "redis": "healthy"
  }
}
```

### GET /api/v1/metrics

System metrics.

**Response**:
```json
{
  "memories_count": 150,
  "graph_nodes": 87,
  "graph_edges": 42,
  "storage_size_mb": 12.5
}
```

---

## 🔌 MCP over HTTP/SSE

**Endpoint**: `/mcp`

**Protocol**: MCP (Model Context Protocol) over HTTP/SSE

**Methods**:
- `GET /mcp` - SSE streaming (server → client)
- `POST /mcp` - JSON-RPC requests (client → server)
- `DELETE /mcp` - Session termination

**Authentication**:
```bash
curl -H "Authorization: Bearer kagura_abc123..." \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' \
     http://localhost:8000/mcp
```

**See**: [MCP over HTTP/SSE Guide](mcp-http-setup.md)

---

## 🛠️ MCP Tools

**Available via**: Claude Desktop, stdio transport, HTTP/SSE

### Remote MCP vs Local MCP

| Feature | Remote MCP (HTTP/SSE) | Local MCP (stdio) |
|---------|----------------------|-------------------|
| **Platforms** | ChatGPT, Claude Chat (future) | Claude Desktop, Claude Code, Cursor |
| **Transport** | HTTP/SSE over network | stdio (stdin/stdout) |
| **File Access** | ❌ No | ✅ Yes |
| **Available Tools** | 49/56 tools | 56/56 tools (all) |
| **Authentication** | API Key required | Local only (no auth) |

### Remote MCP Tools (49/56)

These tools work with **both Remote and Local MCP**:

#### ✅ Available for Remote MCP

**Memory Tools** (13):
- `memory_store`, `memory_recall`, `memory_search`, `memory_list`, `memory_delete`
- `memory_feedback`, `memory_fetch`, `memory_search_ids`, `memory_stats`
- `memory_get_related`, `memory_get_user_pattern`, `memory_record_interaction`

**Web Search** (5):
- `brave_web_search`, `brave_image_search`, `brave_video_search`, `brave_news_search`
- `web_scrape`

**YouTube** (4):
- `get_youtube_transcript`, `get_youtube_metadata`, `youtube_summarize`, `youtube_fact_check`

**Coding** (14):
- `coding_start_session`, `coding_end_session`, `coding_track_file_change`
- `coding_record_error`, `coding_search_errors`, `coding_record_decision`
- `coding_analyze_patterns`, `coding_analyze_file_dependencies`
- `coding_analyze_refactor_impact`, `coding_suggest_refactor_order`
- `coding_get_project_context`, `coding_get_issue_context`
- `coding_link_github_issue`, `coding_generate_pr_description`

**GitHub** (6):
- `github_exec`, `github_issue_list`, `github_issue_view`
- `github_pr_view`, `github_pr_create`, `github_pr_merge`

**Multimodal** (2):
- `multimodal_index`, `multimodal_search`

**Other** (5):
- `arxiv_search`, `fact_check_claim`, `telemetry_stats`, `telemetry_cost`, `route_query`

#### ❌ Local-Only Tools (7)

These tools **only work with Local MCP** (require file system access):

- `file_read` - Read files from disk
- `file_write` - Write files to disk
- `dir_list` - List directory contents
- `shell_exec` - Execute shell commands
- `media_open_image` - Open image in OS app
- `media_open_audio` - Open audio in OS app
- `media_open_video` - Open video in OS app

**Note**: File upload for Remote MCP is planned for v4.1 ([Issue #462](https://github.com/JFK/kagura-ai/issues/462))

---

### Memory Tools

#### memory_store

Store information in memory.

**Parameters**:
- `user_id` (string, required) - User identifier
- `agent_name` (string, required) - Agent name ("global" for cross-thread)
- `key` (string, required) - Memory key
- `value` (string, required) - Value to store
- `scope` (string) - "working" or "persistent" (default: "working")
- `tags` (string) - JSON array of tags (e.g., '["python"]')
- `importance` (number) - 0.0-1.0 (default: 0.5)

**Example**:
```json
{
  "user_id": "jfk",
  "agent_name": "global",
  "key": "pref_language",
  "value": "Python",
  "scope": "persistent",
  "tags": "[\"preferences\"]",
  "importance": 0.8
}
```

#### memory_recall

Search memories semantically.

**Parameters**:
- `user_id` (string, required)
- `agent_name` (string, required)
- `query` (string, required) - Search query
- `k` (number) - Number of results (default: 5)
- `scope` (string) - "working", "persistent", or "all"

#### memory_search

Full-text + semantic search.

**Parameters**:
- `user_id`, `agent_name` (required)
- `query` (string, required)
- `limit` (number) - Max results

#### memory_list

List all memories.

#### memory_delete

Delete a memory with audit logging.

#### memory_feedback

Provide feedback on memory usefulness.

**Parameters**:
- `user_id`, `agent_name` (required)
- `node_id` (string) - Memory to rate
- `label` (string) - "useful", "irrelevant", or "outdated"
- `weight` (number) - -1.0 to 1.0

### Graph Tools

#### memory_record_interaction

Record AI-User interaction.

**Parameters**:
- `user_id` (required)
- `query`, `response` (required)
- `metadata` (object) - Optional metadata

#### memory_get_related

Get related memories via graph.

**Parameters**:
- `user_id`, `agent_name` (required)
- `key` (string) - Starting memory
- `depth` (number) - Traversal depth (default: 2)

#### memory_get_user_pattern

Analyze user's interaction patterns.

### Web/API Tools (Safe for Remote)

- `brave_web_search` - Brave Search integration (replaces deprecated `web_search`)
- `brave_local_search` - Brave Local Search for businesses/places
- `brave_news_search` - Brave News Search
- `brave_image_search` - Brave Image Search
- `brave_video_search` - Brave Video Search
- `web_scrape` - Scrape web pages
- `youtube_summarize` - Summarize YouTube videos
- `get_youtube_transcript` - Get video transcript

### File Tools (Local Only)

⛔ **Blocked remotely** for security:
- `file_read` - Read local files
- `file_write` - Write local files
- `dir_list` - List directory contents
- `shell_exec` - Execute shell commands

**Note**: These tools are only available via local stdio MCP server (`kagura mcp serve`), NOT via HTTP/SSE (`/mcp` endpoint).

---

## 🔐 Authentication

### API Key Management

```bash
# Create API key
kagura api create-key --name "my-key"

# List keys
kagura api list-keys

# Revoke key
kagura api revoke-key --name "my-key"
```

### Using API Keys

**REST API**:
```bash
curl -H "Authorization: Bearer kagura_abc123..." \
     http://localhost:8000/api/v1/memory
```

**MCP over HTTP/SSE**:
```bash
curl -H "Authorization: Bearer kagura_abc123..." \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' \
     http://localhost:8000/mcp
```

**User ID Extraction**:
- API keys are associated with `user_id`
- Authenticated requests automatically use the key's `user_id`
- Fallback to `default_user` if no authentication

---

## 📄 OpenAPI Specification

**Interactive Docs**: http://localhost:8000/docs

**OpenAPI JSON**: http://localhost:8000/openapi.json

**Download**:
```bash
curl http://localhost:8000/openapi.json > openapi.json
```

---

## 🔗 Related Documentation

- [MCP Setup Guide](mcp-setup.md) - Claude Desktop
- [MCP over HTTP/SSE](mcp-http-setup.md) - ChatGPT Connector
- [Self-Hosting Guide](self-hosting.md) - Production deployment
- [Memory Export/Import](memory-export.md) - Backup and migration
- [Architecture](architecture.md) - System design

---

**Last Updated**: 2025-10-27
**Version**: 4.0.0
**API Version**: v1
