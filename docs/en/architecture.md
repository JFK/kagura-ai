# Architecture - Kagura v4.0

> **Universal AI Memory Platform - System Design**

This document describes the architecture of Kagura v4.0 after Phase C completion.

---

## 🏗️ High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                  AI Platforms (MCP Clients)                     │
│      Claude Desktop • ChatGPT • Gemini • Cursor • Cline         │
└──────┬────────────────────────────────────────────────┬─────────┘
       │ stdio (local)                    HTTP/SSE (remote)│
       │                                                   │
┌──────▼─────────────┐                    ┌──────────────▼────────┐
│  MCP Server        │                    │  MCP over HTTP/SSE    │
│  (Local)           │                    │  (/mcp endpoint)      │
│                    │                    │                       │
│  All 31 tools ✅   │                    │  24 safe tools only   │
│  File ops ✅       │                    │  File ops ❌          │
│  Shell exec ✅     │                    │  Shell exec ❌        │
└──────┬─────────────┘                    └──────────────┬────────┘
       │                                                   │
       │              Internal Python API                  │
       └───────────────────────┬───────────────────────────┘
                               │
          ┌────────────────────▼─────────────────────┐
          │         Memory Manager                   │
          │   (src/kagura/core/memory/manager.py)    │
          │                                          │
          │  ┌───────────────┬───────────────────┐  │
          │  │   Context     │    Persistent     │  │
          │  │   Memory      │    Memory         │  │
          │  │ (Messages)    │   (SQLite)        │  │
          │  └───────────────┴───────────────────┘  │
          │                                          │
          │  ┌────────────────────────────────────┐ │
          │  │  RAG (ChromaDB)                    │ │
          │  │  • Semantic search                 │ │
          │  │  • Document indexing               │ │
          │  └────────────────────────────────────┘ │
          │                                          │
          │  ┌────────────────────────────────────┐ │
          │  │  Graph Memory (NetworkX)           │ │
          │  │  • Relationships                   │ │
          │  │  • Interaction history             │ │
          │  │  • User patterns                   │ │
          │  └────────────────────────────────────┘ │
          └────────────────┬─────────────────────────┘
                           │
                  ┌────────▼────────┐
                  │    Storage      │
                  │  • SQLite       │
                  │  • ChromaDB     │
                  │  • Pickle files │
                  └─────────────────┘
```

---

## 🆕 Phase C Architecture (Remote MCP Server)

### Remote Access Flow

```
ChatGPT                         Your Server
┌─────────┐                     ┌──────────────┐
│ ChatGPT │  HTTPS/SSE          │    Caddy     │
│Connector├────────────────────►│ (Port 443)   │
└─────────┘                     └──────┬───────┘
                                       │
                               ┌───────▼───────┐
                               │  Kagura API   │
                               │  (Port 8000)  │
                               │               │
                               │  /mcp         │◄─ HTTP/SSE
                               │  /api/v1/*    │◄─ REST
                               └───────┬───────┘
                                       │
                              ┌────────▼────────┐
                              │ Memory Manager  │
                              │  + Graph        │
                              └────────┬────────┘
                                       │
                              ┌────────▼────────┐
                              │ PostgreSQL      │
                              │ + pgvector      │
                              └─────────────────┘
```

### Security Layers

```
1. API Key Authentication
   ├─ SHA256 hashed storage
   ├─ Optional expiration
   └─ Audit trail (last_used_at)

2. Tool Access Control
   ├─ Local context: All 31 tools ✅
   ├─ Remote context: 24 safe tools only
   └─ Dangerous tools filtered:
      • file_read, file_write
      • shell_exec
      • media_open_*

3. Network Security
   ├─ Caddy reverse proxy
   ├─ Automatic HTTPS (Let's Encrypt)
   ├─ CORS configuration
   └─ Security headers (HSTS, XSS)
```

---

## 📦 Component Details

### 1. MCP Server (src/kagura/mcp/)

**stdio Transport** (local):
- **File**: `src/kagura/cli/mcp.py`
- **Command**: `kagura mcp serve`
- **Context**: `local` (all tools available)
- **Clients**: Claude Desktop, Cursor, Cline

**HTTP/SSE Transport** (remote):
- **File**: `src/kagura/api/routes/mcp_transport.py`
- **Endpoint**: `/mcp`
- **Context**: `remote` (safe tools only)
- **Clients**: ChatGPT Connector, web browsers

**Tool Permissions**:
- **File**: `src/kagura/mcp/permissions.py`
- **Logic**: `is_tool_allowed(tool_name, context)`
- **Default**: Deny unknown tools (fail-safe)

---

### 2. Memory Manager (src/kagura/core/memory/)

**Components**:
- `manager.py` - Main coordinator
- `persistent.py` - SQLite-based persistent storage
- `rag.py` - ChromaDB vector search
- `export.py` - JSONL export/import

**Storage**:
- **Persistent**: All memory is persistent (survives restarts, SQLite storage)
- **RAG**: Indexed in ChromaDB for semantic search

---

### 3. Graph Memory (src/kagura/core/graph/)

**Implementation**: NetworkX-based

**Node Types**:
- `user` - User profiles
- `topic` - Discussion topics
- `memory` - Memory references
- `interaction` - AI-User interactions

**Edge Types**:
- `related_to` - Related memories
- `depends_on` - Dependencies
- `learned_from` - Learning relationships
- `works_on` - User activities

**Storage**: Pickle files (`~/.local/share/kagura/graph.pkl`)

---

### 4. REST API (src/kagura/api/)

**Framework**: FastAPI

**Endpoints**:
- `/api/v1/memory` - Memory CRUD
- `/api/v1/recall` - Semantic search
- `/api/v1/search` - Full-text search
- `/api/v1/graph/*` - Graph operations
- `/api/v1/health` - Health check
- `/api/v1/metrics` - System metrics
- `/mcp` - MCP over HTTP/SSE ⭐ NEW

**Authentication**:
- **File**: `src/kagura/api/auth.py`
- **Method**: Bearer token (API keys)
- **Storage**: SQLite (`~/.local/share/kagura/api_keys.db`)
- **Hashing**: SHA256

---

## 🔄 Data Flow

### Memory Store Flow

```
1. MCP Client (Claude/ChatGPT)
   └─► MCP Tool Call: memory_store(...)

2. MCP Server (stdio or HTTP/SSE)
   └─► Route to tool_registry

3. Built-in Tool (src/kagura/mcp/builtin/memory.py)
   └─► Call MemoryManager.store()

4. Memory Manager
   ├─► Persistent memory (SQLite)
   └─► RAG indexing (ChromaDB)

5. Storage
   ├─► SQLite (persistent)
   └─► ChromaDB (vectors)
```

### Memory Recall Flow

```
1. MCP Tool Call: memory_recall(query="Python tips", k=5)

2. Memory Manager
   └─► Query RAG (vector similarity)

3. RAG Search
   ├─► Embed query (text-embedding-3-small)
   ├─► Search ChromaDB collections
   └─► Return top-k results

4. Return to client
   └─► Formatted results with scores
```

---

## 🔐 Security Architecture

### Authentication Flow

```
1. Client Request
   └─► Authorization: Bearer kagura_abc123...

2. API Gateway (/mcp or /api/v1/*)
   └─► Extract Bearer token

3. API Key Manager (src/kagura/api/auth.py)
   ├─► Hash provided key (SHA256)
   ├─► Query api_keys.db
   ├─► Check expiration & revocation
   └─► Extract user_id

4. Request Processing
   └─► Use authenticated user_id for memory operations
```

### Tool Filtering (Remote Context)

```
1. create_mcp_server(context="remote")

2. handle_list_tools()
   ├─► Get all registered tools (31 total)
   ├─► Filter by TOOL_PERMISSIONS
   └─► Return safe tools only (24)

3. Client sees:
   ✅ memory_* tools
   ✅ web_* tools
   ❌ file_* tools (blocked)
   ❌ shell_exec (blocked)
```

---

## 💾 Data Model

### Memory Record

```python
{
    "key": str,                  # Unique identifier
    "value": Any,                # Stored data (JSON serializable)
    "user_id": str,              # Owner (v4.0+)
    "agent_name": str,           # Agent scope
    "tags": List[str],           # Categorization
    "importance": float,         # 0.0-1.0
    "created_at": datetime,
    "updated_at": datetime,
    "metadata": Dict[str, Any]   # Additional metadata
}
```

### Graph Node

```python
{
    "id": str,                   # Node identifier
    "type": str,                 # Node type (user, topic, memory, interaction)
    "data": Dict[str, Any],      # Node attributes
}
```

### Graph Edge

```python
{
    "src": str,                  # Source node ID
    "dst": str,                  # Destination node ID
    "type": str,                 # Relationship type
    "weight": float,             # 0.0-1.0
}
```

---

## 📊 Deployment Architecture

### Local Development

```
Developer Machine
├── SQLite (~/.local/share/kagura/memory.db)
├── ChromaDB (~/.local/share/kagura/chromadb/)
├── Graph pickle (~/.local/share/kagura/graph.pkl)
└── API Keys (~/.local/share/kagura/api_keys.db)
```

### Production Deployment

```
Docker Stack (docker-compose.prod.yml)

┌─────────────────────────────────────────┐
│            Caddy (Port 443)             │
│     Automatic HTTPS, Reverse Proxy      │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│       Kagura API (Port 8000)            │
│    FastAPI + MCP over HTTP/SSE          │
└──────┬──────────────────────┬───────────┘
       │                      │
┌──────▼──────────┐   ┌──────▼──────────┐
│   PostgreSQL    │   │     Redis       │
│   + pgvector    │   │   (Caching)     │
└─────────────────┘   └─────────────────┘

Volumes:
├── postgres_data  - Database persistence
├── redis_data     - Redis persistence
├── kagura_data    - Memory exports, etc.
└── caddy_data     - SSL certificates
```

---

## 🔄 Export/Import System

### Export Format (JSONL)

```
backup/
├── memories.jsonl      # All memory records
├── graph.jsonl         # Graph nodes & edges
└── metadata.json       # Export metadata
```

**Example record**:
```jsonl
{"type":"memory","key":"python_tips","value":"Use type hints","user_id":"jfk","agent_name":"global","tags":["python"],"importance":0.8,"exported_at":"2025-10-27T10:00:00Z"}
```

---

## 📐 Design Principles

### 1. MCP-First

All functionality exposed via MCP tools first, then REST API.

### 2. Multi-User from Day 1

All operations scoped by `user_id` (Phase C foundation).

### 3. Security by Default

Remote access auto-filtered for safety.

### 4. Data Portability

Complete export/import in human-readable JSONL.

### 5. Fail-Safe

Unknown tools denied by default in remote context.

---

## 🔗 Related Documentation

- [Getting Started](getting-started.md)
- [MCP Setup Guide](mcp-setup.md)
- [MCP over HTTP/SSE](mcp-http-setup.md)
- [Self-Hosting Guide](self-hosting.md)
- [API Reference](api-reference.md)

---

**Last Updated**: 2025-10-27
**Version**: 4.0.0
**Phase**: C Complete
