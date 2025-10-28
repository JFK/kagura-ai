# Kagura AI Architecture - v4.0

**Last Updated**: 2025-10-27
**Version**: 4.0 (Phase C Complete)

---

## Overview

Kagura AI v4.0 is a **Universal AI Memory Platform** - MCP-native memory infrastructure for all AI platforms.

**Design Philosophy**: MCP-First, Universal Memory

**Strategic Shift**:
- v3.0: SDK-First (Python integration focus)
- v4.0: MCP-First (Platform-agnostic memory focus)

---

## System Architecture

### High-Level Architecture (v4.0)

```
┌────────────────────────────────────────────────────────────────┐
│                   AI Platforms (MCP Clients)                   │
│       Claude Desktop • ChatGPT • Gemini • Cursor • Cline       │
└──────┬──────────────────────────────────────────────┬──────────┘
       │ stdio (local)              HTTP/SSE (remote) │
       │                                              │
┌──────▼─────────────┐                  ┌────────────▼──────────┐
│  MCP Server        │                  │  MCP over HTTP/SSE    │
│  (stdio)           │                  │  (/mcp endpoint)      │
│  context="local"   │                  │  context="remote"     │
│  All 31 tools ✅   │                  │  24 safe tools ✅     │
└──────┬─────────────┘                  └────────────┬──────────┘
       │                                              │
       │         ┌────────────────────────────────────┘
       │         │   FastAPI Server (port 8080)
       │         │   ┌─────────────────────────────┐
       │         └──►│  /api/v1/*  (REST API)      │
       │             │  /mcp        (MCP HTTP/SSE) │
       │             │  /docs       (OpenAPI)      │
       │             └─────────────┬───────────────┘
       │                           │
       │              Authentication & Authorization
       │                           │
       │         ┌─────────────────▼────────────────┐
       │         │     API Key Manager              │
       │         │     (SHA256, SQLite)             │
       │         └─────────────────┬────────────────┘
       │                           │
       └───────────────────────────┘
                    │
       ┌────────────▼──────────────────────────────┐
       │         Memory Manager                    │
       │   (src/kagura/core/memory/manager.py)     │
       │                                           │
       │  ┌───────────┬────────────┬────────────┐ │
       │  │  Working  │  Context   │ Persistent │ │
       │  │  Memory   │  Memory    │  Memory    │ │
       │  │ (In-Mem)  │ (Messages) │  (SQLite)  │ │
       │  └───────────┴────────────┴────────────┘ │
       │                                           │
       │  ┌───────────────────────────────────┐   │
       │  │  RAG (ChromaDB)                   │   │
       │  │  • Working RAG                    │   │
       │  │  • Persistent RAG                 │   │
       │  │  • Semantic search                │   │
       │  └───────────────────────────────────┘   │
       │                                           │
       │  ┌───────────────────────────────────┐   │
       │  │  Graph Memory (NetworkX)          │   │
       │  │  • Node/Edge management           │   │
       │  │  • Interaction tracking           │   │
       │  │  • Pattern analysis               │   │
       │  └───────────────────────────────────┘   │
       │                                           │
       │  ┌───────────────────────────────────┐   │
       │  │  Export/Import (JSONL)            │   │
       │  │  • MemoryExporter                 │   │
       │  │  • MemoryImporter                 │   │
       │  └───────────────────────────────────┘   │
       └────────────────┬──────────────────────────┘
                        │
       ┌────────────────▼──────────────────────────┐
       │              Storage Layer                │
       │  • SQLite (memory.db, api_keys.db)        │
       │  • ChromaDB (vectors)                     │
       │  • NetworkX JSON (graph.json)             │
       │  • JSONL exports                          │
       └───────────────────────────────────────────┘
```

---

## Phase C: Remote MCP Server Architecture

### Remote Access Architecture

```
Internet
   │
   ▼
┌──────────────────┐
│  Caddy Proxy     │  Port 443 (HTTPS)
│  + Let's Encrypt │  HTTP/2, HTTP/3
└────────┬─────────┘
         │
    ┌────▼─────┐
    │ Security │
    │ Headers  │
    └────┬─────┘
         │
┌────────▼──────────────────────────────────┐
│       Kagura API Server                   │
│       (FastAPI, port 8080)                │
│                                           │
│  ┌─────────────────────────────────────┐ │
│  │  Authentication Middleware          │ │
│  │  • Extract Bearer token             │ │
│  │  │  Check API key (SHA256 hash)      │ │
│  │  └─► Get user_id from key           │ │
│  └─────────────────────────────────────┘ │
│                                           │
│  ┌─────────────────────────────────────┐ │
│  │  Tool Permissions Filter            │ │
│  │  • context="remote"                 │ │
│  │  • Dangerous tools blocked          │ │
│  │  • Safe tools allowed               │ │
│  └─────────────────────────────────────┘ │
│                                           │
│  ┌─────────────────────────────────────┐ │
│  │  Endpoints                          │ │
│  │  • /mcp (MCP over HTTP/SSE)         │ │
│  │  • /api/v1/memory (REST CRUD)       │ │
│  │  • /api/v1/graph/* (Graph ops)      │ │
│  │  • /api/v1/health (Health check)    │ │
│  └─────────────────────────────────────┘ │
└───────────────────────────────────────────┘
         │
    ┌────▼──────┐
    │ Memory    │
    │ Manager   │
    └───────────┘
```

---

## Directory Structure (v4.0)

```
src/kagura/
├── __init__.py              # Public exports (minimal)
│
├── core/                    # Core logic
│   ├── memory/              # Memory system (Phase A)
│   │   ├── manager.py       # MemoryManager coordinator
│   │   ├── working.py       # Working memory (in-memory)
│   │   ├── persistent.py    # Persistent memory (SQLite)
│   │   ├── context.py       # Context memory (messages)
│   │   ├── rag.py           # RAG with ChromaDB
│   │   └── export.py        # Export/Import (Phase C)
│   │
│   ├── graph/               # Graph memory (Phase B)
│   │   ├── memory.py        # GraphMemory (NetworkX)
│   │   └── analysis.py      # Pattern analysis
│   │
│   ├── registry.py          # Agent registry
│   ├── tool_registry.py     # Tool registry (unified)
│   └── workflow_registry.py # Workflow registry
│
├── api/                     # REST API (Phase A)
│   ├── server.py            # FastAPI app
│   ├── auth.py              # API Key auth (Phase C)
│   ├── dependencies.py      # Dependency injection
│   ├── models.py            # Pydantic models
│   └── routes/              # API routes
│       ├── memory.py        # Memory CRUD
│       ├── graph.py         # Graph operations
│       ├── search.py        # Search & recall
│       ├── system.py        # Health, metrics
│       └── mcp_transport.py # MCP over HTTP/SSE (Phase C)
│
├── mcp/                     # MCP Server (Phase A)
│   ├── server.py            # create_mcp_server()
│   ├── schema.py            # JSON Schema generation
│   ├── permissions.py       # Tool access control (Phase C)
│   ├── config.py            # MCP config management
│   ├── diagnostics.py       # MCP doctor
│   └── builtin/             # Built-in MCP tools
│       ├── memory.py        # Memory tools (6)
│       ├── web.py           # Web search
│       ├── file_ops.py      # File operations
│       ├── youtube.py       # YouTube tools
│       └── ...
│
├── cli/                     # CLI commands
│   ├── main.py              # Main CLI entry
│   ├── mcp.py               # MCP commands
│   ├── api_cli.py           # API key management (Phase C)
│   ├── memory_cli.py        # Memory export/import (Phase C)
│   ├── auth_cli.py          # OAuth2 auth (legacy)
│   ├── init.py              # User setup
│   └── monitor.py           # Telemetry monitoring
│
├── tools/                   # Optional tools
│   ├── web.py               # Brave Search
│   ├── youtube.py           # YouTube integration
│   └── ...
│
└── observability/           # Telemetry & monitoring
    ├── telemetry.py         # Telemetry collector
    └── cost.py              # Cost tracking
```

---

## Component Details

### 1. MCP Server (`src/kagura/mcp/`)

**Two Transport Modes** (Phase C):

**stdio Transport** (local):
- **Entry**: `kagura mcp serve`
- **Context**: `local` (all tools)
- **Tools**: 31 tools (including file ops, shell exec)
- **Clients**: Claude Desktop, Cursor, Cline
- **Security**: Full trust (local execution)

**HTTP/SSE Transport** (remote):
- **Entry**: `/mcp` endpoint (FastAPI)
- **Context**: `remote` (safe tools only)
- **Tools**: 24 safe tools (no file ops, no shell exec)
- **Clients**: ChatGPT Connector, web browsers
- **Security**: Tool filtering, API key auth

**Tool Filtering** (`permissions.py`):
```python
TOOL_PERMISSIONS = {
    "memory_store": {"remote": True},   # Safe
    "web_search": {"remote": True},     # Safe
    "file_read": {"remote": False},     # Dangerous!
    "shell_exec": {"remote": False},    # Dangerous!
}
```

---

### 2. Memory Manager (`src/kagura/core/memory/`)

**Multi-User Architecture** (Phase C - Issue #382):
```python
MemoryManager(user_id="jfk", agent_name="global")
```

**4-Tier Memory System**:

1. **Working Memory** (`working.py`)
   - In-memory dict
   - Session-scoped
   - Fast access

2. **Context Memory** (`context.py`)
   - Conversation messages
   - In-memory
   - Automatic summarization

3. **Persistent Memory** (`persistent.py`)
   - SQLite database
   - Survives restart
   - User-scoped (`user_id` column)

4. **RAG** (`rag.py`)
   - ChromaDB vector search
   - Semantic similarity
   - User-scoped collections

**Export/Import** (`export.py` - Phase C):
- JSONL format
- Complete data portability
- Roundtrip validation

---

### 3. Graph Memory (`src/kagura/core/graph/`)

**Implementation**: NetworkX-based directed graph

**Data Model**:
```python
# Nodes
{
    "id": "mem_001",
    "type": "memory",  # user, topic, memory, interaction
    "data": {...}
}

# Edges
{
    "src": "mem_001",
    "dst": "mem_002",
    "type": "related_to",  # depends_on, learned_from, etc.
    "weight": 0.8
}
```

**Operations**:
- `add_node()`, `add_edge()`
- `query_graph()` - Multi-hop traversal
- `record_interaction()` - AI-User interaction tracking
- `analyze_user_pattern()` - Pattern analysis

**Storage**: JSON file (`~/.kagura/graph.json`)

---

### 4. REST API (`src/kagura/api/`)

**Framework**: FastAPI

**Architecture**:
```
FastAPI App (server.py)
├── CORS Middleware (all origins for MCP)
├── Routers
│   ├── /api/v1/memory   (memory.py)
│   ├── /api/v1/graph    (graph.py)
│   ├── /api/v1/search   (search.py)
│   └── /api/v1/system   (system.py)
├── ASGI Mount
│   └── /mcp             (mcp_transport.py)
└── Exception Handlers
```

**Authentication** (Phase C):
- **File**: `auth.py`
- **Class**: `APIKeyManager`
- **Method**: Bearer token
- **Storage**: SQLite (`~/.kagura/api_keys.db`)
- **Hashing**: SHA256
- **Extraction**: `user_id` from validated key

**Dependency Injection** (`dependencies.py`):
```python
def get_memory_manager(user_id: str) -> MemoryManager:
    # Per-user MemoryManager instances
    # Cached for request lifecycle
```

---

### 5. MCP Transport (`src/kagura/api/routes/mcp_transport.py`)

**Implementation**: MCP SDK's `StreamableHTTPServerTransport`

**Protocol Support**:
- GET `/mcp` - SSE streaming (server → client messages)
- POST `/mcp` - JSON-RPC requests (client → server)
- DELETE `/mcp` - Session termination

**Session Management**:
- Auto-generated session IDs
- Background task runs MCP server
- Transport connects server to HTTP layer

**Authentication Flow**:
```
1. Extract Authorization header
2. Validate API key (APIKeyManager.verify_key())
3. Get user_id from key
4. Pass user_id to downstream operations
5. Fallback to "default_user" if no auth
```

---

## Data Flow

### Memory Store Flow (Remote)

```
1. ChatGPT
   └─► POST /mcp
       {"jsonrpc":"2.0","method":"tools/call",
        "params":{"name":"kagura_tool_memory_store",...}}

2. mcp_asgi_app() (mcp_transport.py)
   ├─► Authentication (extract user_id from API key)
   ├─► Tool filtering (is memory_store allowed remotely? YES)
   └─► StreamableHTTPServerTransport.handle_request()

3. MCP Server (context="remote")
   ├─► handle_list_tools() - filtered to 24 safe tools
   └─► handle_call_tool("kagura_tool_memory_store", args)

4. memory_store() (src/kagura/mcp/builtin/memory.py)
   └─► MemoryManager.store(user_id, key, value, scope, ...)

5. Memory Manager
   ├─► persistent.store() if scope="persistent"
   ├─► working.set() if scope="working"
   └─► RAG indexing (both scopes)

6. Storage
   ├─► SQLite write (persistent)
   ├─► ChromaDB vector index (RAG)
   └─► In-memory dict (working)

7. Response
   └─► JSON-RPC response → ChatGPT
```

### Memory Recall Flow

```
1. MCP Client
   └─► memory_recall(user_id, query, k=5)

2. Memory Manager
   └─► RAG.search(query, k=5)

3. ChromaDB
   ├─► Embed query (text-embedding-3-small)
   ├─► Vector similarity search
   └─► Return top-k with scores

4. Format results
   └─► [{"key": "...", "value": "...", "score": 0.95}, ...]
```

---

## Security Architecture (Phase C)

### 1. API Key Authentication

**Storage** (`~/.kagura/api_keys.db`):
```sql
CREATE TABLE api_keys (
    id INTEGER PRIMARY KEY,
    key_hash TEXT UNIQUE,        -- SHA256(api_key)
    key_prefix TEXT,             -- First 16 chars (display)
    name TEXT,                   -- Friendly name
    user_id TEXT,                -- Associated user
    created_at TIMESTAMP,
    last_used_at TIMESTAMP,      -- Audit trail
    revoked_at TIMESTAMP,
    expires_at TIMESTAMP
);
```

**Workflow**:
```
1. Create: kagura api create-key --name "my-key"
   └─► Generate: kagura_<32_random_bytes>
   └─► Hash: SHA256(key)
   └─► Store: hash + metadata

2. Validate: verify_api_key(api_key)
   └─► Hash: SHA256(api_key)
   └─► Query: api_keys.db
   └─► Check: expiration, revocation
   └─► Return: user_id or None

3. Use: Authorization: Bearer kagura_...
   └─► Authenticated as user_id
```

### 2. Tool Access Control

**Permission System** (`src/kagura/mcp/permissions.py`):

```python
def is_tool_allowed(tool_name: str, context: Literal["local", "remote"]) -> bool:
    if context == "local":
        return True  # All tools allowed locally

    # Remote: check permissions
    return TOOL_PERMISSIONS.get(tool_name, {}).get("remote", False)
```

**Classification**:
- **Safe** (remote=True): memory_*, web_*, youtube_*, telemetry_*
- **Dangerous** (remote=False): file_*, shell_exec, media_open_*

**Enforcement**:
```
create_mcp_server(context="remote")
└─► handle_list_tools()
    ├─► Get all tools (31)
    ├─► Filter: get_allowed_tools(tools, "remote")
    └─► Return: 24 safe tools
```

---

## Export/Import System (Phase C Week 3)

### JSONL Format

**Files**:
```
backup/
├── memories.jsonl      # Memory records
├── graph.jsonl         # Graph nodes & edges
└── metadata.json       # Export metadata
```

**Memory Record**:
```jsonl
{"type":"memory","scope":"persistent","key":"pref","value":"Python","user_id":"jfk","agent_name":"global","tags":["config"],"importance":0.8,"created_at":"2025-10-26T12:00:00Z","exported_at":"2025-10-27T10:00:00Z"}
```

**Graph Record**:
```jsonl
{"type":"node","id":"mem_001","node_type":"memory","data":{"key":"pref"},"exported_at":"..."}
{"type":"edge","src":"mem_001","dst":"mem_002","rel_type":"related_to","weight":0.8,"exported_at":"..."}
```

**Implementation**:
- **Exporter**: `MemoryExporter.export_all(output_dir)`
- **Importer**: `MemoryImporter.import_all(input_dir)`
- **CLI**: `kagura memory export/import`

---

## Production Deployment (Phase C Week 4)

### Docker Stack (`docker-compose.prod.yml`)

```yaml
services:
  caddy:          # Reverse proxy + HTTPS
  api:            # Kagura API (FastAPI)
  postgres:       # Database + pgvector
  redis:          # Caching (future)

volumes:
  postgres_data:  # Database persistence
  redis_data:     # Redis persistence
  kagura_data:    # Exports, uploads
  caddy_data:     # SSL certificates
```

**Network Flow**:
```
Internet → Caddy:443 (HTTPS) → API:8080 (HTTP) → PostgreSQL:5432
```

**Health Checks**:
- PostgreSQL: `pg_isready`
- Redis: `redis-cli ping`
- API: `curl /api/v1/health`

---

## Design Principles (v4.0)

### 1. MCP-First
全機能をMCPツールとして公開。プラットフォーム横断が第一目標。

### 2. Universal Memory
`user_id` による完全なマルチユーザーサポート。データ分離。

### 3. Security by Default
Remote contextでは危険なツールを自動フィルタ。Fail-safe設計。

### 4. Data Portability
JSONL形式による完全なExport/Import。ベンダーロックイン無し。

### 5. Zero-Trust Remote Access
API Key認証必須。全操作は`user_id`でスコープ化。

---

## Technology Stack

### Core
- **Python**: 3.11+
- **Framework**: FastAPI (REST), MCP SDK (protocol)
- **Database**: SQLite (dev), PostgreSQL (prod)
- **Vector DB**: ChromaDB
- **Graph**: NetworkX

### Transport
- **Local**: stdio (MCP SDK)
- **Remote**: HTTP/SSE (StreamableHTTPServerTransport)

### Deployment
- **Container**: Docker + Docker Compose
- **Reverse Proxy**: Caddy (auto HTTPS)
- **Storage**: Volumes (postgres_data, caddy_data, etc.)

### Development
- **Type Check**: pyright (strict mode)
- **Lint**: ruff
- **Test**: pytest + pytest-asyncio
- **Package**: uv

---

## Performance Characteristics

**Target** (Issue #378 Success Criteria):
- API response: < 200ms (p95)
- Memory recall: < 100ms (p95)
- API startup: < 5 seconds

**Optimization Points**:
- SQLite indexed queries
- ChromaDB vector caching
- Memory manager instance caching
- API key hash lookup (indexed)

---

## Future Roadmap

### Phase D (Q2 2026): Multimodal MVP
- Image, audio, video indexing
- Multimodal RAG
- Attachment support

### Phase E (Q3 2026): Consumer App
- Flutter mobile/desktop app
- Graph visualization
- Insights dashboard

### Phase F (Q4 2026): Cloud SaaS
- Multi-tenant architecture
- Row-level security
- SSO, BYOK
- Team collaboration

---

## 🔗 Related Documents

- [V4.0_STRATEGIC_PIVOT.md](./V4.0_STRATEGIC_PIVOT.md) - Strategic direction
- [V4.0_IMPLEMENTATION_ROADMAP.md](./V4.0_IMPLEMENTATION_ROADMAP.md) - Implementation plan
- [CODING_STANDARDS.md](./CODING_STANDARDS.md) - Coding guidelines
- [MEMORY_STRATEGY.md](./MEMORY_STRATEGY.md) - Memory system design

---

**Last Updated**: 2025-10-27
**Version**: 4.0 (Phase C Complete)
**Status**: Production-Ready
