# Architecture - Kagura v4.0

> **Universal AI Memory Platform - System Design**

This document describes the architecture of Kagura v4.0.

---

## 🏗️ High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Platforms (MCP Clients)               │
│        Claude Desktop • ChatGPT • Gemini • Cursor           │
│                 Cline • Custom Agents                       │
└────────────────────────┬────────────────────────────────────┘
                         │
                    MCP Protocol
                         │
┌────────────────────────▼────────────────────────────────────┐
│                  Kagura MCP Server                          │
│            (src/kagura/mcp/server.py)                       │
│                                                             │
│  Tools:                                                     │
│  • memory_store, memory_recall, memory_search               │
│  • memory_list, memory_feedback, memory_delete              │
│  • web_search, youtube_transcript, file_ops, etc.           │
└────────────────────────┬────────────────────────────────────┘
                         │
              Internal Python API
                         │
┌────────────────────────▼────────────────────────────────────┐
│                  Memory Manager                             │
│           (src/kagura/core/memory/manager.py)               │
│                                                             │
│  ┌─────────────┬────────────────┬─────────────────┐       │
│  │  Working    │   Context      │   Persistent    │       │
│  │  Memory     │   Memory       │   Memory        │       │
│  │ (In-Memory) │  (Messages)    │   (SQLite)      │       │
│  └─────────────┴────────────────┴─────────────────┘       │
│                                                             │
│  ┌──────────────────────────────────────────────┐         │
│  │  RAG (Retrieval-Augmented Generation)         │         │
│  │  • Working RAG (ChromaDB)                     │         │
│  │  • Persistent RAG (ChromaDB)                  │         │
│  │  • Semantic search, Vector similarity         │         │
│  └──────────────────────────────────────────────┘         │
│                                                             │
│  🆕 Phase B (Coming):                                      │
│  ┌──────────────────────────────────────────────┐         │
│  │  Graph Memory (NetworkX)                      │         │
│  │  • Relationships between memories             │         │
│  │  • AI-User interaction history                │         │
│  └──────────────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────────┘
                         │
                    Storage Layer
                         │
┌────────────────────────▼────────────────────────────────────┐
│                     Storage                                  │
│                                                             │
│  • SQLite - Persistent key-value memory                     │
│  • ChromaDB - Vector embeddings for semantic search         │
│  • Local files - Graph persistence (Phase B)                │
│                                                             │
│  🔮 Future (v4.1+):                                        │
│  • PostgreSQL + pgvector - Production deployment            │
│  • Redis - Caching & job queue                              │
│  • S3-compatible - Multimodal attachments                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🧩 Component Details

### 1. MCP Server

**Location**: `src/kagura/mcp/server.py`

**Responsibilities**:
- Expose tools via MCP protocol
- Handle stdio communication with MCP clients
- Route tool calls to appropriate handlers

**Tools Categories**:
- **Memory**: 6 tools (store, recall, search, list, feedback, delete)
- **Web**: 2 tools (web_search, brave_search)
- **Files**: 3 tools (read, write, list)
- **YouTube**: 2 tools (transcript, metadata)
- **Multimodal**: 2 tools (vision, audio)
- **Other**: 13 tools (routing, fact-check, etc.)

**Total**: 28 MCP tools

---

### 2. Memory Manager

**Location**: `src/kagura/core/memory/manager.py`

**3-Tier Memory System**:

#### a) Working Memory
- **Type**: In-memory dictionary
- **Lifetime**: Session only
- **Use case**: Temporary variables, conversation context
- **Implementation**: `WorkingMemory` class

#### b) Context Memory
- **Type**: Message history
- **Lifetime**: Session or saved session
- **Use case**: Conversation history for LLM context
- **Implementation**: `ContextMemory` class
- **Features**: Compression, token counting

#### c) Persistent Memory
- **Type**: SQLite database
- **Lifetime**: Permanent
- **Use case**: User preferences, long-term knowledge
- **Implementation**: `PersistentMemory` class

---

### 3. RAG (Semantic Search)

**Location**: `src/kagura/core/memory/rag.py`

**Dual RAG System**:

#### Working RAG
- **Collection**: `kagura_{agent_name}_working`
- **Purpose**: Semantic search in temporary memory
- **Storage**: ChromaDB (in-memory or persisted)

#### Persistent RAG
- **Collection**: `kagura_{agent_name}_persistent`
- **Purpose**: Semantic search in long-term memory
- **Storage**: ChromaDB (persisted to disk)

**How it works**:
1. Content → Embedding (OpenAI text-embedding-3-small)
2. Store embedding in ChromaDB
3. Query → Query embedding
4. Cosine similarity search
5. Return top-k results with distance scores

---

### 4. REST API (v4.0 New)

**Location**: `src/kagura/api/server.py`

**Framework**: FastAPI

**Endpoints**:
- `/api/v1/memory` - Memory CRUD
- `/api/v1/search` - Full-text search
- `/api/v1/recall` - Semantic recall
- `/api/v1/health` - Health check
- `/api/v1/metrics` - System metrics

**Dependency Injection**:
```python
# src/kagura/api/dependencies.py
def get_memory_manager() -> MemoryManager:
    # Returns shared MemoryManager instance
    # Enables state persistence across requests
```

---

### 5. Graph Memory (Phase B)

**Location**: `src/kagura/core/graph/memory.py` (Coming in Phase B)

**Node Types**:
- `memory`: Memory nodes
- `user`: User nodes
- `topic`: Topic nodes
- `interaction`: AI-User interaction nodes

**Edge Types**:
- `related_to`: Semantic relationship
- `depends_on`: Dependency relationship
- `learned_from`: Learning path
- `influences`: Influence relationship
- `works_on`: Project/task relationship

**Use Cases**:
- Find related memories (multi-hop traversal)
- Track AI-User interaction history ("Vibe Coding")
- Discover learning paths
- Understand user's knowledge graph

---

## 📊 Data Flow

### Memory Storage Flow

```
1. AI Agent (Claude) calls memory_store via MCP
   ↓
2. MCP Server receives tool call
   ↓
3. Calls MemoryManager.remember() or set_temp()
   ↓
4. If persistent:
   a) Store in SQLite (key-value)
   b) Generate embedding
   c) Store in ChromaDB (vector)
   d) Convert metadata (ChromaDB constraints)
   ↓
5. Return confirmation to AI
```

### Semantic Recall Flow

```
1. AI Agent calls memory_recall via MCP
   ↓
2. MCP Server receives tool call
   ↓
3. Calls MemoryManager.recall_semantic(query, k=5)
   ↓
4. Generate query embedding
   ↓
5. ChromaDB cosine similarity search
   ↓
6. Retrieve top-k results with distances
   ↓
7. Convert distance to similarity (1 - distance/2)
   ↓
8. Return results to AI (JSON)
```

---

## 💾 Storage Details

### SQLite Schema (Persistent Memory)

```sql
CREATE TABLE memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    agent_name TEXT,
    metadata TEXT,  -- JSON string
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(key, agent_name)
);
```

### ChromaDB Collections

**Working Memory RAG**:
```python
{
  "collection_name": "kagura_{agent_name}_working",
  "metadata": {
    "type": "working_memory",
    "key": str,
    "tags": str,  # JSON array string
    "importance": float
  }
}
```

**Persistent Memory RAG**:
```python
{
  "collection_name": "kagura_{agent_name}_persistent",
  "metadata": {
    "type": "persistent_memory",
    "key": str,
    "tags": str,  # JSON array string
    "importance": float,
    "created_at": str,
    "updated_at": str
  }
}
```

**Metadata Constraints**:
- ChromaDB only accepts: `str`, `int`, `float`, `bool`, `None`
- Lists/dicts → JSON strings
- Transparent encoding/decoding in API layer

---

## 🔄 Request Flow (REST API)

```
1. HTTP Request
   ↓
2. FastAPI route (e.g., routes/memory.py)
   ↓
3. Dependency injection: get_memory_manager()
   ↓
4. Business logic (CRUD operations)
   ↓
5. Encode metadata (lists → JSON strings)
   ↓
6. Call MemoryManager methods
   ↓
7. Decode metadata (JSON strings → lists)
   ↓
8. Return HTTP Response (Pydantic model)
```

---

## 🚀 Deployment Options

### Local Development

```bash
# Option 1: Direct Python
uvicorn kagura.api.server:app --reload

# Option 2: Docker Compose
docker compose up -d
```

**Services**:
- API server (port 8080)
- PostgreSQL + pgvector (Phase A: optional)
- Redis (Phase A: optional)

### Self-Hosted (v4.1.0+)

```yaml
# docker-compose.prod.yml
services:
  postgres:
    image: pgvector/pgvector:pg16
  redis:
    image: redis:7-alpine
  api:
    build: .
    environment:
      DATABASE_URL: postgres://...
  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
```

### Cloud (v4.2.0+)

- Managed SaaS
- Multi-tenant architecture
- Row-Level Security (RLS)
- BYOK (Bring Your Own Key)

---

## 🔐 Security Architecture

### v4.0.0a0(Current)

- **Authentication**: None (localhost only)
- **Authorization**: None
- **Encryption**: None (local deployment)

### v4.1.0 (Planned)

- **Authentication**: API Key
- **Authorization**: Per-key permissions
- **Encryption**: TLS in transit

### v4.2.0 (Planned)

- **Authentication**: OAuth2 + JWT
- **Authorization**: RBAC (Role-Based Access Control)
- **Encryption**: At rest + in transit, BYOK

---

## 📈 Scalability

### Current (v4.0)

- **Memory capacity**: Limited by disk space
- **Concurrent users**: Single user (localhost)
- **Performance**: ChromaDB scales to ~1M vectors

### Future (v4.1+)

- **Memory capacity**: Unlimited (cloud storage)
- **Concurrent users**: Multi-tenant
- **Performance**: pgvector + Redis caching

**Benchmarks** (v4.0, local):
- Recall@5 accuracy: 0.89
- p95 latency: 82ms
- Storage: 45MB for 10K memories

---

## 🔗 Integration Points

### MCP Clients

- **Claude Desktop**: Native MCP support
- **Cursor**: MCP support (coming)
- **Cline**: VS Code extension with MCP
- **Custom agents**: Use MCP SDK

### External Services (Phase C)

**Connectors** (v4.1.0+):
- GitHub: Repository indexing
- Google Calendar: Event indexing
- Local Files: Directory watching

---

## 🆕 Phase Roadmap

### Phase A (Current - v4.0.0a0
- ✅ FastAPI REST API
- ✅ MCP Tools v1.0 (6 memory tools)
- ✅ MCP CLI Management
- ✅ MemoryManager integration
- ✅ Docker Compose setup

### Phase B (v4.0.0)
- 🔄 GraphMemory (NetworkX)
- 🔄 Consolidation (short → long-term)
- 🔄 Export/Import (JSONL)
- 🔄 Multimodal DB schema

### Phase C (v4.1.0)
- 🔮 Self-hosted API
- 🔮 Multimodal MVP
- 🔮 Connectors
- 🔮 Consumer App

---

## 🔗 Related

- [Getting Started](./getting-started.md) - Setup guide
- [MCP Setup](./mcp-setup.md) - Claude Desktop integration
- [API Reference](./api-reference.md) - REST API docs
- [V4.0 Strategic Pivot](../ai_docs/V4.0_STRATEGIC_PIVOT.md) - Strategy
- [V4.0 Roadmap](../ai_docs/V4.0_IMPLEMENTATION_ROADMAP.md) - Detailed plan

---

**Version**: 4.0.0a
**Last updated**: 2025-10-26
