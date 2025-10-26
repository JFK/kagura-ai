# API Reference - Kagura v4.0

> **REST API & MCP Tools Documentation**

This document provides comprehensive reference for Kagura's APIs.

---

## 📚 Table of Contents

1. [REST API](#rest-api)
   - [Memory Operations](#memory-operations)
   - [Search & Recall](#search--recall)
   - [System](#system)
2. [MCP Tools](#mcp-tools)
   - [Memory Tools](#memory-tools)

---

## 🌐 REST API

**Base URL**: `http://localhost:8080` (default)

**OpenAPI Spec**: [docs/api/reference.yaml](../docs/api/reference.yaml)

**Interactive Docs**: http://localhost:8080/docs

### Authentication

- **v4.0.0a0*: No authentication (localhost only)
- **v4.1.0+**: API Key authentication
- **v4.2.0+**: OAuth2 + JWT

---

## Memory Operations

### POST /api/v1/memory

Create a new memory.

**Request**:
```json
{
  "key": "python_tips",
  "value": "Always use type hints for better code quality",
  "scope": "persistent",
  "tags": ["python", "best-practices"],
  "importance": 0.9,
  "metadata": {"project": "kagura"}
}
```

**Response** (201 Created):
```json
{
  "key": "python_tips",
  "value": "Always use type hints for better code quality",
  "scope": "persistent",
  "tags": ["python", "best-practices"],
  "importance": 0.9,
  "metadata": {"project": "kagura"},
  "created_at": "2025-10-26T10:00:00Z",
  "updated_at": "2025-10-26T10:00:00Z"
}
```

**Parameters**:
- `key` (string, required): Unique memory key
- `value` (string, required): Memory content
- `scope` (string): "working" or "persistent" (default: "working")
- `tags` (array): Tags for categorization
- `importance` (number): 0.0-1.0 (default: 0.5)
- `metadata` (object): Additional metadata

**Errors**:
- `409 Conflict`: Memory key already exists

---

### GET /api/v1/memory/{key}

Get memory by key.

**Request**:
```bash
GET /api/v1/memory/python_tips?scope=persistent
```

**Response** (200 OK):
```json
{
  "key": "python_tips",
  "value": "Always use type hints for better code quality",
  "scope": "persistent",
  "tags": ["python", "best-practices"],
  "importance": 0.9,
  "metadata": {"project": "kagura"},
  "created_at": "2025-10-26T10:00:00Z",
  "updated_at": "2025-10-26T10:00:00Z"
}
```

**Query Parameters**:
- `scope` (optional): "working" or "persistent" (searches both if not specified)

**Errors**:
- `404 Not Found`: Memory not found

---

### PUT /api/v1/memory/{key}

Update memory.

**Request**:
```json
{
  "value": "Always use type hints and docstrings",
  "importance": 1.0
}
```

**Response** (200 OK):
```json
{
  "key": "python_tips",
  "value": "Always use type hints and docstrings",
  "scope": "persistent",
  "tags": ["python", "best-practices"],
  "importance": 1.0,
  "metadata": {"project": "kagura"},
  "created_at": "2025-10-26T10:00:00Z",
  "updated_at": "2025-10-26T10:05:00Z"
}
```

**Parameters**: All optional
- `value` (string): Updated content
- `tags` (array): Updated tags
- `importance` (number): Updated importance
- `metadata` (object): Updated metadata

---

### DELETE /api/v1/memory/{key}

Delete memory.

**Request**:
```bash
DELETE /api/v1/memory/python_tips?scope=persistent
```

**Response** (204 No Content)

**Query Parameters**:
- `scope` (optional): "working" or "persistent"

**Errors**:
- `404 Not Found`: Memory not found

---

### GET /api/v1/memory

List memories with pagination.

**Request**:
```bash
GET /api/v1/memory?scope=persistent&page=1&page_size=20
```

**Response** (200 OK):
```json
{
  "memories": [
    {
      "key": "python_tips",
      "value": "Always use type hints",
      "scope": "persistent",
      "tags": ["python"],
      "importance": 0.9,
      "metadata": {},
      "created_at": "2025-10-26T10:00:00Z",
      "updated_at": "2025-10-26T10:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

**Query Parameters**:
- `scope` (optional): Filter by scope
- `page` (integer): Page number (1-indexed, default: 1)
- `page_size` (integer): Items per page (1-100, default: 20)

---

## Search & Recall

### POST /api/v1/search

Full-text search across memories.

**Request**:
```json
{
  "query": "python type hints",
  "scope": "all",
  "limit": 10,
  "filter_tags": ["python"]
}
```

**Response** (200 OK):
```json
{
  "results": [
    {
      "key": "python_tips",
      "value": "Always use type hints",
      "scope": "persistent",
      "tags": ["python", "best-practices"],
      "score": 1.0,
      "metadata": {}
    }
  ],
  "total": 1,
  "query": "python type hints"
}
```

**Parameters**:
- `query` (string, required): Search query
- `scope` (string): "working", "persistent", or "all" (default: "all")
- `limit` (integer): Max results (1-100, default: 10)
- `filter_tags` (array): Filter by tags (AND logic)

---

### POST /api/v1/recall

Semantic recall using vector similarity.

**Request**:
```json
{
  "query": "How should I write Python code?",
  "k": 5,
  "scope": "all",
  "include_graph": false
}
```

**Response** (200 OK):
```json
{
  "results": [
    {
      "key": "python_tips",
      "value": "python_tips: Always use type hints",
      "scope": "persistent",
      "similarity": 0.85,
      "tags": ["python", "best-practices"],
      "metadata": {}
    }
  ],
  "query": "How should I write Python code?",
  "k": 5
}
```

**Parameters**:
- `query` (string, required): Semantic query
- `k` (integer): Number of results (1-50, default: 5)
- `scope` (string): "working", "persistent", or "all" (default: "all")
- `include_graph` (boolean): Include graph-related memories (v4.0.0+, default: false)

**Note**: Requires ChromaDB (RAG) to be enabled.

---

## System

### GET /api/v1/health

Health check.

**Response** (200 OK):
```json
{
  "status": "healthy",
  "timestamp": "2025-10-26T10:00:00Z",
  "services": {
    "api": "healthy",
    "database": "healthy",
    "vector_db": "healthy"
  }
}
```

**Status values**:
- `healthy`: All systems operational
- `degraded`: Some services have issues
- `unhealthy`: Critical services down

---

### GET /api/v1/metrics

System metrics.

**Response** (200 OK):
```json
{
  "memory_count": 150,
  "storage_size_mb": 45.2,
  "cache_hit_rate": null,
  "api_requests_total": null,
  "uptime_seconds": 3600.5
}
```

---

## 🔌 MCP Tools

MCP (Model Context Protocol) tools for AI agents.

**Access**: Via MCP-compatible clients (Claude Desktop, Cursor, Cline, etc.)

---

## Memory Tools

### memory_store

Store information in memory.

**Parameters**:
```python
{
  "agent_name": "global",           # Agent identifier
  "key": "user_language",            # Memory key
  "value": "Japanese",               # Content to store
  "scope": "working",                # "working" or "persistent"
  "tags": '["preferences"]',         # JSON array string
  "importance": 0.8,                 # 0.0-1.0
  "metadata": '{"source": "user"}'   # JSON object string
}
```

**Returns**:
```
Stored 'user_language' in working memory for global
```

**Usage by AI**:
> User: "Remember that I prefer Python over JavaScript"
>
> Claude: *Uses memory_store(agent_name="global", key="language_preference", value="Prefers Python over JavaScript", scope="persistent", tags='["preferences", "programming"]', importance=0.9)*

---

### memory_recall

Recall memory by key.

**Parameters**:
```python
{
  "agent_name": "global",  # Must match the one used in memory_store
  "key": "user_language",  # Memory key
  "scope": "working"       # "working" or "persistent"
}
```

**Returns**:
```
Japanese
```

**Usage by AI**:
> User: "What language do I prefer?"
>
> Claude: *Uses memory_recall(agent_name="global", key="language_preference")*
> Claude: "You prefer Python over JavaScript."

---

### memory_search

Semantic search using RAG.

**Parameters**:
```python
{
  "agent_name": "global",  # Agent identifier
  "query": "programming",  # Search query
  "k": 5,                  # Number of results
  "scope": "all"           # "working", "persistent", or "all"
}
```

**Returns** (JSON):
```json
[
  {
    "content": "language_preference: Prefers Python",
    "source": "rag",
    "scope": "persistent",
    "distance": 0.15,
    "metadata": {...}
  }
]
```

**Usage by AI**:
> User: "What do you know about my programming preferences?"
>
> Claude: *Uses memory_search(agent_name="global", query="programming preferences", k=5)*

---

### memory_list

List all memories.

**Parameters**:
```python
{
  "agent_name": "global",     # Agent identifier
  "scope": "persistent",      # "working" or "persistent"
  "limit": 50                 # Max results
}
```

**Returns** (JSON):
```json
{
  "agent_name": "global",
  "scope": "persistent",
  "count": 2,
  "memories": [
    {
      "key": "user_language",
      "value": "Japanese",
      "scope": "persistent",
      "created_at": "2025-10-26T10:00:00Z",
      "metadata": {...}
    }
  ]
}
```

---

### memory_feedback

Provide feedback on memory usefulness.

**Parameters**:
```python
{
  "agent_name": "global",
  "key": "user_language",
  "label": "useful",          # "useful", "irrelevant", or "outdated"
  "weight": 0.2,              # Feedback strength (0.0-1.0)
  "scope": "persistent"
}
```

**Returns** (JSON):
```json
{
  "status": "success",
  "key": "user_language",
  "label": "useful",
  "weight": 0.2,
  "importance": {
    "previous": 0.8,
    "current": 0.82,
    "delta": 0.02
  }
}
```

**Usage by AI**:
> Claude automatically provides feedback when a memory helps answer a question.
>
> If memory was helpful: *memory_feedback(label="useful")*
> If memory is outdated: *memory_feedback(label="outdated")*

**Importance Scoring**:
- `useful`: importance + (weight × 0.1)
- `irrelevant` / `outdated`: importance - (weight × 0.1)
- Range: Clamped to [0.0, 1.0]

---

### memory_delete

Delete memory permanently.

**Parameters**:
```python
{
  "agent_name": "global",
  "key": "old_preference",
  "scope": "persistent"
}
```

**Returns** (JSON):
```json
{
  "status": "deleted",
  "key": "old_preference",
  "scope": "persistent",
  "agent_name": "global",
  "message": "Memory 'old_preference' deleted from persistent memory",
  "audit": "Deletion logged"
}
```

**Usage by AI**:
> User: "Forget about my old JavaScript preference"
>
> Claude: *Uses memory_delete(agent_name="global", key="old_js_preference")*
> Claude: "I've forgotten about your JavaScript preference."

**Note**:
- Deletion is permanent
- Deletes from both key-value storage and RAG
- GDPR-compliant (complete deletion)
- Audit logging (TODO: Phase B)

---

## 🧠 Memory Scopes

### working (In-Memory)

- **Lifetime**: Session only
- **Storage**: RAM
- **Use case**: Temporary context, conversation state
- **Survives**: No (cleared on restart)

**Example**:
```json
{
  "key": "current_task",
  "value": "Writing documentation",
  "scope": "working"
}
```

### persistent (On-Disk)

- **Lifetime**: Permanent
- **Storage**: SQLite + ChromaDB
- **Use case**: User preferences, long-term knowledge
- **Survives**: Yes (saved to disk)

**Example**:
```json
{
  "key": "user_name",
  "value": "John",
  "scope": "persistent"
}
```

---

## 🎯 Best Practices

### 1. Use Appropriate Scope

```python
# Temporary context (this conversation)
scope="working"

# Long-term knowledge (user preferences)
scope="persistent"
```

### 2. Tag Your Memories

```python
{
  "tags": ["python", "best-practices", "coding"],
  "importance": 0.9
}
```

Tags enable:
- Better search filtering
- Categorization
- Future graph relationships

### 3. Set Importance Wisely

```python
{
  "importance": 1.0  # Critical user preference
  "importance": 0.5  # Neutral information
  "importance": 0.1  # Low priority, may prune later
}
```

---

## 🔗 Related

- [Getting Started](./getting-started.md) - Setup guide
- [MCP Setup](./mcp-setup.md) - Claude Desktop integration
- [Architecture](./architecture.md) - System design
- [OpenAPI Spec](../docs/api/reference.yaml) - Full API specification

---

**Version**: 4.0.0a
**Last updated**: 2025-10-26
