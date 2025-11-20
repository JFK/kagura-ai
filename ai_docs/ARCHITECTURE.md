# Kagura AI Architecture - v4.0+

**Last Updated**: 2025-11-09
**Version**: 4.3.0 (Code Quality Release)

---

## Overview

Kagura AI v4.0 is a **Universal AI Memory Platform** - MCP-native memory infrastructure for all AI platforms.

**Design Philosophy**: MCP-First, Universal Memory

**Strategic Shift**:
- v3.0: SDK-First (Python integration focus)
- v4.0: MCP-First (Platform-agnostic memory focus)
- v4.3.0: Code Quality & Organization (Internal refactoring, zero breaking changes)

---

## v4.3.0 Refactoring Outcomes

### Code Quality Release (Issue #612)

**Goal**: Improve codebase maintainability, extensibility, and developer experience without breaking changes.

**Completed Phases** (as of 2025-11-09):

#### Phase 1: Utils Consolidation ✅
- **Problem**: Duplicate utilities in `utils/` and `cli/utils/`
- **Solution**: Consolidated into single `utils/` directory with subdirectories:
  - `utils/cli/` - CLI-specific utilities
  - `utils/memory/` - Memory-related helpers
  - `utils/api/` - API helpers
  - `utils/common/` - Shared utilities
- **Impact**: Eliminated ~15% code duplication

#### Phase 2: MCP Tools Auto-Discovery ✅ (Partial)
- **Problem**: Manual tool registration, difficult to maintain
- **Solution**: Implemented auto-discovery registry pattern
- **Impact**: New tools automatically registered, no manual updates needed
- **Remaining**: Individual tool file splitting (optional enhancement)

#### Phase 3: Core Memory Refactoring ✅
- **Problem**: `coding_memory.py` was 2,116 lines (monolithic)
- **Solution**: Split into focused modules:
  - `core/memory/coding/session_manager.py` - Session lifecycle
  - `core/memory/coding/file_change_tracker.py` - File tracking
  - `core/memory/coding/error_recorder.py` - Error recording
  - `core/memory/coding/decision_recorder.py` - Design decisions
  - `core/memory/coding/interaction_tracker.py` - AI-user interactions
  - `core/memory/coding/github_integration.py` - GitHub Issue/PR
  - `core/memory/coding/search.py` - Session search
  - `core/memory/coding/models.py` - Pydantic models
- **Facade**: `coding_memory.py` maintained as facade (582 lines, 72.5% reduction)
- **Impact**:
  - Improved testability (unit tests per module)
  - Better Single Responsibility adherence
  - Easier to navigate and maintain
  - 100% backward compatibility via facade

#### Phase 4: CLI Commands Reorganization ✅
- **Problem**: Large CLI files (`mcp.py`, `memory_cli.py`, `coding_cli.py`)
- **Solution**: Split into modular command directories:
  - `cli/mcp/` - MCP server commands (serve, stats, tools, doctor)
  - `cli/memory/` - Memory commands (store, search, delete, export)
  - `cli/coding/` - Coding commands (sessions, errors, decisions)
- **Impact**:
  - CLI startup time: 1.2s → <500ms (lazy loading)
  - Clearer command organization
  - Easier to add new commands

#### Phase 5: Continuous Improvements 🔄 (Ongoing)
- **Test Coverage**: Maintained at 90%+ (1,450+ tests passing)
- **Type Coverage**: Working toward 100% (`pyright --strict`)
- **TODO/FIXME Cleanup**: Version-tagged technical debt tracking

#### Phase 6: Documentation Update 🔄 (In Progress)
- **QUICKSTART.md**: New quick reference guide created
- **README.md**: Reduced from 726 → 388 lines (46.5% reduction)
- **CLAUDE.md**: Updated with v4.3.0 structure
- **ARCHITECTURE.md**: This document (updated)
- **CHANGELOG.md**: Comprehensive v4.3.0 entry (pending)

### Key Metrics

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **coding_memory.py** | 2,116 lines | 582 lines (+ 8 modules) | -72.5% |
| **Code Duplication** | ~15% | <5% | -67% |
| **README.md** | 726 lines | 388 lines | -46.5% |
| **CLI Startup Time** | 1.2s | <500ms (target) | -58% |
| **Test Coverage** | 90% | 90%+ (maintained) | Stable |
| **Breaking Changes** | - | 0 | 100% compatible |

### Architecture Impact

**No changes to external APIs**:
- MCP Protocol endpoints unchanged
- REST API routes unchanged
- Python SDK (`@agent` decorator) unchanged
- CLI commands unchanged (internal reorganization only)

**Internal improvements**:
- Better separation of concerns
- Improved testability
- Easier onboarding for contributors
- Reduced cognitive load

---

## v4.4.0 Service Layer Architecture (Issue #714)

### Code Quality & Duplication Elimination

**Problem Solved:** 35-40% code duplication across MCP tools, REST API routes, and CLI commands.

**Solution:** Service Layer Pattern - Extract business logic into reusable services.

### Service Layer Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                   External Clients                            │
│       Claude Code • ChatGPT • Web UI • CLI                   │
└───────┬──────────────────┬────────────────────┬─────────────┘
        │                  │                    │
        │ (MCP stdio)      │ (HTTP/SSE)         │ (CLI)
        ▼                  ▼                    ▼
┌───────────────┐  ┌──────────────┐   ┌─────────────────┐
│  MCP Tools    │  │  API Routes  │   │  CLI Commands   │
│  (thin layer) │  │ (thin layer) │   │  (thin layer)   │
└───────┬───────┘  └──────┬───────┘   └────────┬────────┘
        │                 │                     │
        └─────────────────┼─────────────────────┘
                          │
                ┌─────────▼──────────┐
                │  Service Layer     │  ← NEW (v4.4.0)
                │  (Business Logic)  │
                ├────────────────────┤
                │ • MemoryService    │  Memory CRUD with validation
                │ • CodingService    │  Session management
                │ • HealthService    │  System diagnostics
                │ • AuthService      │  Authentication logic
                └─────────┬──────────┘
                          │
                ┌─────────▼──────────┐
                │   Core Layer       │
                │  (Data Access)     │
                ├────────────────────┤
                │ • MemoryManager    │
                │ • CodingMemory     │
                │ • UnifiedAuth      │  6 patterns → 1
                └────────────────────┘
```

### Services Implemented

#### 1. **MemoryService** (`src/kagura/services/memory_service.py` - 418 lines)

**Responsibilities:**
- Input validation (required fields, ranges, types)
- Metadata construction (tags, importance, timestamps)
- CRUD operations with consistent error handling
- Search with filters (importance, tags, pagination)

**Methods:**
- `store_memory()` - Validated storage
- `recall_memory()` - Key-based retrieval
- `delete_memory()` - Deletion with audit
- `search_memory()` - Hybrid search with filters
- `list_memories()` - Paginated listing

**Usage Example:**
```python
# MCP Tool (thin wrapper)
@tool
async def memory_store(user_id, key, value, tags, importance):
    memory = get_memory_manager(user_id, "global")
    service = MemoryService(memory)
    result = service.store_memory(key, value, tags, importance)
    return f"[OK] {result.message}" if result.success else f"[ERROR] {result.message}"

# API Route (thin wrapper)
@router.post("/memory")
async def create_memory(request: MemoryCreate, memory: MemoryManagerDep):
    service = MemoryService(memory)
    result = service.store_memory(request.key, request.value, request.tags, request.importance)
    if not result.success:
        raise HTTPException(500, result.message)
    return result.to_dict()

# CLI Command (thin wrapper)
@click.command()
def store(key, value, tags, importance):
    memory = get_memory_manager("cli_user", "cli")
    service = MemoryService(memory)
    result = service.store_memory(key, value, tags, importance)
    console.print(f"[green]✓[/green] {result.message}")
```

#### 2. **CodingService** (`src/kagura/services/coding_service.py` - 158 lines)

**Responsibilities:**
- Coding session lifecycle management
- File change tracking
- Error recording
- Decision logging

**Methods:**
- `start_session()` - Initialize session
- `end_session()` - Generate summary
- `track_file_change()` - Track modifications

#### 3. **HealthService** (`src/kagura/services/health_service.py` - 108 lines)

**Responsibilities:**
- System diagnostics
- Component health checks
- Status aggregation

**Methods:**
- `check_memory_system()` - MemoryManager health
- `check_coding_system()` - CodingMemory health
- `run_diagnostics()` - Full system check

#### 4. **UnifiedAuthManager** (`src/kagura/auth/unified_auth.py` - 337 lines)

**Consolidates 6 authentication patterns:**
1. API Key (Bearer tokens) - Highest priority
2. OAuth2 (Google, etc.) - Fallback
3. Session (cookies/tokens) - Fallback
4. Anonymous (development) - Lowest priority

**Authentication Flow:**
```
Request
  │
  ├─> Has Bearer token?
  │   ├─> Is kagura_* API key? → Verify → Return user_id
  │   └─> Is OAuth2 token? → Verify → Return user_id
  │
  ├─> Has session token? → Verify → Return user_id
  │
  └─> Allow anonymous? → Return "default_user" | Error
```

### Code Reduction Achieved

**MCP Tools (`mcp/tools/memory/storage.py`):**
- Before: 274 lines
- After: 231 lines
- **Reduction: 43 lines (15.7%)**

**Benefits:**
- Removed duplicate metadata construction (18 lines)
- Removed duplicate ChromaDB conversion (9 lines)
- Removed duplicate error handling (16 lines)

**API Routes (demonstration):**
- Integration overhead: +10 lines initially
- Future integrations: Net reduction as overhead amortizes

**Total Code Added:**
- Service Layer: 807 lines (shared across all interfaces)
- Tests: 491 lines (25 tests, 100% passing)
- Documentation: 881 lines

### Testing Strategy

**Service Layer Tests:**
- Mock MemoryManager for isolation
- Test business logic independently
- Verify validation rules
- Check error handling

**Integration Tests:**
- Test MCP tool → Service → Core
- Test API route → Service → Core
- Test CLI command → Service → Core
- Verify consistent behavior across interfaces

### Benefits Achieved

1. **Single Source of Truth:** Business logic in one place
2. **Consistent Behavior:** Same validation/logic across MCP/API/CLI
3. **Easier Testing:** Mock services, not infrastructure
4. **Reduced Duplication:** 15-57% reduction demonstrated
5. **Better Maintainability:** Bug fixes apply to all interfaces

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
       │   (v4.4.0: All memory is persistent)      │
       │                                           │
       │  ┌───────────────────────────────────┐   │
       │  │  Persistent Memory (SQLite)       │   │
       │  │  • All memory persisted           │   │
       │  │  • user_id scoped                 │   │
       │  └───────────────────────────────────┘   │
       │                                           │
       │  ┌───────────────────────────────────┐   │
       │  │  RAG (ChromaDB)                   │   │
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
       │  XDG-Compliant Directories (v4.0+)        │
       │                                           │
       │  Cache (~/.cache/kagura/):                │
       │    • ChromaDB vectors                     │
       │    • MCP logs                             │
       │                                           │
       │  Data (~/.local/share/kagura/):           │
       │    • SQLite (memory.db, api_keys.db)      │
       │    • NetworkX JSON (graph.json)           │
       │    • Sessions, telemetry                  │
       │                                           │
       │  Config (~/.config/kagura/):              │
       │    • config.json, mcp-config.yaml         │
       │    • Custom agents, commands              │
       └───────────────────────────────────────────┘
```

### Directory Structure (XDG-Compliant, v4.0+)

**Linux/macOS**:
```
~/.cache/kagura/          # Cache (deletable)
├── chromadb/             # Vector embeddings
└── logs/                 # MCP server logs

~/.local/share/kagura/    # Persistent data
├── memory.db             # SQLite memory storage
├── api_keys.db           # API key database
├── telemetry.db          # Observability data
├── graph.json            # NetworkX graph
├── sessions/             # Chat sessions
└── api/{user_id}/        # Per-user API data

~/.config/kagura/         # User-editable config
├── config.json           # Main configuration
├── mcp-config.yaml       # MCP settings
├── remote-config.json    # Remote connection
├── agents/               # Custom agents
└── commands/             # Custom commands
```

**Environment Variable Override**:
```bash
export KAGURA_CACHE_DIR=/custom/cache  # Override cache location
export KAGURA_DATA_DIR=/custom/data    # Override data location
export KAGURA_CONFIG_DIR=/custom/cfg   # Override config location
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
│   │   ├── persistent.py    # Persistent memory (SQLite) - All memory is persistent (v4.4.0)
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

**MCP Middleware** (`middleware.py`) 🆕 v4.1.1:
- **Auto-logging**: All tool calls logged to memory (opt-out available)
- **Non-blocking**: Fire-and-forget via `asyncio.create_task()`
- **Recursion prevention**: Excludes all `memory_*` tools (15+ tools)
- **Privacy**: `KAGURA_DISABLE_AUTO_LOGGING=true` to disable
- **Storage**: `agent_name="mcp_history"`, persistent, importance=0.3
- **Integration**: `server.py:304-319` in `handle_call_tool()`

**Related Tool**: `memory_get_tool_history` - Query logged tool calls

---

### 2. Memory Manager (`src/kagura/core/memory/`)

**Multi-User Architecture** (Phase C - Issue #382):
```python
MemoryManager(user_id="jfk", agent_name="global")
```

**3-Tier Memory System** (v4.4.0):

**Breaking Change**: Working Memory removed. All memory is now persistent.

1. **Context Memory** (`context.py`)
   - Conversation messages
   - In-memory
   - Automatic summarization

2. **Persistent Memory** (`persistent.py`)
   - SQLite database
   - All memory persisted by default
   - Survives restart
   - User-scoped (`user_id` column)

3. **RAG** (`rag.py`)
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

**Storage**: JSON file (`~/.local/share/kagura/graph.json`)

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
- **Storage**: SQLite (`~/.local/share/kagura/api_keys.db`)
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
   ├─► persistent.store() - All memory is persistent (v4.4.0)
   └─► RAG indexing

6. Storage
   ├─► SQLite write (persistent)
   └─► ChromaDB vector index (RAG)

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

**Storage** (`~/.local/share/kagura/api_keys.db`):
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
{"type":"memory","key":"pref","value":"Python","user_id":"jfk","agent_name":"global","tags":["config"],"importance":0.8,"created_at":"2025-10-26T12:00:00Z","exported_at":"2025-10-27T10:00:00Z"}
```

**Note (v4.4.0)**: `scope` field removed. All memory is persistent.

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

## v4.1.1 Architecture Updates 🆕

### MCP Middleware Layer

**Location**: `src/kagura/mcp/middleware.py`

**Auto-Logging System**:
- All MCP tool calls automatically logged to memory
- Fire-and-forget via `asyncio.create_task()` (non-blocking)
- Recursion prevention: 15+ `memory_*` tools excluded
- Privacy: `KAGURA_DISABLE_AUTO_LOGGING=true` opt-out
- Storage: `mcp_history` agent, persistent, importance=0.3

**Integration**: `server.py:304-319` after tool execution

### Enhanced Memory Stats

**New Capabilities** (Issue #411):
- Access tracking: `access_count`, `last_accessed_at`
- Unused detection: `unused_30days`, `unused_90days`
- Storage calculation: `storage_mb` (SQLite + ChromaDB)

### CLI Performance

**Achievement** (Issue #548):
- 83% faster startup: 13.9s → 2.3s
- Lightweight config pattern for CLI
- Performance regression tests added

### Performance Benchmarks

| Metric | v4.0.11 | v4.1.1 | Change |
|--------|---------|--------|--------|
| CLI Startup | 13.9s | 2.3s | 83% ↓ |
| Memory Recall | <100ms | <100ms | - |
| Memory Stats | ~50ms | <100ms | - |
| Middleware | N/A | <5ms | New |

---

**Last Updated**: 2025-11-06
**Version**: 4.1.1 (Performance & Context Awareness)
**Status**: Production-Ready
