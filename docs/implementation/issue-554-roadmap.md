# Issue #554 Implementation Roadmap
**Cloud-Native Infrastructure Migration (PostgreSQL + Redis + Qdrant)**

**Status**: 🟡 In Progress
**Branch**: `554-featinfra-cloud-native-infrastructure-migration-postgresql-+-redis-+-qdrant`
**Started**: 2025-11-10
**Estimated Completion**: 4 weeks

---

## 📋 Overview

Migrate Kagura AI from local file-based storage to cloud-native infrastructure:
- **GraphMemory**: JSON File → PostgreSQL
- **RAG/Vector**: ChromaDB → Qdrant (optional)
- **Cache**: In-Memory → Redis
- **Persistent**: SQLite → PostgreSQL

---

## 🎯 Goals

1. **Multi-instance deployment**: Support horizontal scaling
2. **Cloud-native**: Use GCP managed services (Cloud SQL, Memorystore)
3. **Backward compatibility**: 100% API compatibility
4. **Gradual migration**: Support both old and new backends during transition

---

## 📅 Implementation Phases

### ✅ Phase 0: Infrastructure Setup (Completed)
**Completed**: 2025-11-10
**Related**: Issue #649

- ✅ GCP Terraform configuration
- ✅ docker-compose.cloud.yml
- ✅ Deployment scripts
- ✅ Documentation

**Deliverables**:
- `terraform/gcp/` - Complete GCP infrastructure
- `docs/deployment/gcp.md` - Deployment guide

---

### 🔄 Phase 1: PostgreSQL Migration (In Progress)
**Duration**: 2 weeks
**Priority**: 🔴 High

#### 1.1 GraphMemory PostgreSQL Backend
**Status**: 📝 Design Complete
**Files**:
- `src/kagura/core/graph/backends/README.md` ✅
- `src/kagura/core/graph/backends/base.py` 🚧
- `src/kagura/core/graph/backends/json_backend.py` 🚧
- `src/kagura/core/graph/backends/postgres_backend.py` 🚧

**Implementation**:
```python
# Option 1: JSONB (Phase 1)
CREATE TABLE graph_memory (
    user_id VARCHAR(255) PRIMARY KEY,
    graph_data JSONB NOT NULL
);

# Option 2: Normalized (Future)
CREATE TABLE graph_nodes (...);
CREATE TABLE graph_edges (...);
```

**Tasks**:
- [ ] Implement `GraphBackend` abstract base class
- [ ] Refactor existing code to `JSONBackend`
- [ ] Implement `PostgresBackend` (JSONB approach)
- [ ] Update `GraphMemory` to use backends
- [ ] Add backend selection via environment variables
- [ ] Write tests (unit + integration)

#### 1.2 Persistent Memory PostgreSQL Backend
**Status**: 📋 Planned
**Files**:
- `src/kagura/core/memory/persistent.py` (refactor)
- `src/kagura/core/memory/backends/postgres_persistent.py`

**Implementation**:
```python
# SQLAlchemy models (already compatible)
# Just need to switch database URL
PERSISTENT_BACKEND=postgres
DATABASE_URL=postgresql://...
```

**Tasks**:
- [ ] Abstract storage layer in `persistent.py`
- [ ] Implement PostgreSQL backend
- [ ] Migration script: SQLite → PostgreSQL
- [ ] Tests

#### 1.3 Migration Tools
**Files**:
- `scripts/migrate-graph-to-postgres.py`
- `scripts/migrate-persistent-to-postgres.py`

**Features**:
- Migrate JSON → PostgreSQL
- Migrate SQLite → PostgreSQL
- Validation & rollback support

#### 1.4 Configuration
**Environment Variables**:
```bash
# Backend selection
GRAPH_BACKEND=postgres
PERSISTENT_BACKEND=postgres
DATABASE_URL=postgresql://user:pass@host:5432/db

# Fallback to legacy
GRAPH_BACKEND=json
PERSISTENT_BACKEND=sqlite
```

---

### 🕐 Phase 2: Redis Integration
**Duration**: 1 week
**Priority**: 🟡 Medium
**Depends On**: Issue #650 (Google OAuth2 Web Integration)

#### 2.1 LLM Cache Redis Backend
**Files**:
- `src/kagura/core/cache.py` (extend)

**Current**:
```python
class LLMCache:
    backend: Literal["memory", "redis", "disk"] = "memory"
    # Only "memory" implemented
```

**Implementation**:
```python
class LLMCache:
    def __init__(self, backend="memory", redis_url=None):
        if backend == "redis":
            self.client = redis.Redis.from_url(redis_url)
        else:
            self.cache = {}  # In-memory
```

**Tasks**:
- [ ] Implement Redis backend in `cache.py`
- [ ] Add TTL support
- [ ] Add cache invalidation
- [ ] Tests

#### 2.2 Session Store (Web UI)
**Files**:
- `src/kagura/auth/session.py`

**Related**: Issue #650

**Implementation**:
```python
class SessionManager:
    def __init__(self, redis_url: str):
        self.redis = Redis.from_url(redis_url)

    def create_session(self, user_info: dict) -> str:
        session_id = secrets.token_urlsafe(32)
        self.redis.setex(f\"session:{session_id}\", 7*24*3600, json.dumps(user_info))
        return session_id
```

**Tasks**:
- [ ] Implement Redis session store
- [ ] Integrate with FastAPI auth
- [ ] Tests

---

### 🕑 Phase 3: Qdrant Migration (Optional)
**Duration**: 1 week
**Priority**: 🟢 Low

#### 3.1 RAG Qdrant Backend
**Files**:
- `src/kagura/core/memory/backends/qdrant_rag.py`

**Current**: ChromaDB (local files)
**Target**: Qdrant (Docker container or Qdrant Cloud)

**Implementation**:
```python
class QdrantRAG:
    def __init__(self, qdrant_url: str):
        self.client = QdrantClient(url=qdrant_url)

    def add_documents(self, docs: list[str], embeddings: list[list[float]]):
        self.client.upsert(
            collection_name=\"kagura_memory\",
            points=[
                PointStruct(id=i, vector=emb, payload={\"text\": doc})
                for i, (doc, emb) in enumerate(zip(docs, embeddings))
            ]
        )
```

**Tasks**:
- [ ] Implement `QdrantRAG` class
- [ ] Migration tool: ChromaDB → Qdrant
- [ ] Update `MemoryManager` to support Qdrant
- [ ] Tests
- [ ] Benchmark: ChromaDB vs Qdrant

---

## 🧪 Testing Strategy

### Unit Tests
- Each backend independently
- Mock database connections
- Test error handling

### Integration Tests
- Backend switching (JSON ↔ PostgreSQL)
- Data consistency
- Migration scripts

### Performance Tests
- PostgreSQL vs JSON (graph size: 1k, 10k, 100k nodes)
- Qdrant vs ChromaDB (vector search latency)
- Redis vs In-Memory (cache hit rate)

---

## 📊 Success Metrics

| Metric | Target |
|--------|--------|
| **Backward Compatibility** | 100% (no API changes) |
| **Test Coverage** | 90%+ |
| **Migration Success Rate** | 100% (data integrity) |
| **Performance** | ≤ 10% regression vs JSON/ChromaDB |
| **Type Coverage** | 100% (pyright --strict) |

---

## 📝 Documentation Updates

- [ ] `docs/deployment/gcp.md` - PostgreSQL setup
- [ ] `docs/configuration/backends.md` - Backend selection guide
- [ ] `docs/migration/sql-migration.md` - Migration guide
- [ ] `README.md` - Update architecture diagram
- [ ] `CHANGELOG.md` - Add v4.2.0 entry

---

## 🚧 Current Status (2025-11-10)

### Completed
- ✅ Issue #649: GCP deployment infrastructure
- ✅ GraphMemory backend architecture design
- ✅ PostgreSQL table schema design

### In Progress
- 🚧 GraphMemory backend implementation

### Next Session
1. Implement `GraphBackend` abstract base class
2. Refactor to `JSONBackend`
3. Implement `PostgresBackend` (JSONB)
4. Tests

---

## 🔗 Related Issues

- #649 - Cloud Deployment Setup (✅ Completed)
- #650 - Google OAuth2 Web Integration (depends on Redis)
- #651 - Web Admin Dashboard
- #554 - This issue (PostgreSQL + Redis + Qdrant)

---

**Last Updated**: 2025-11-10
**Next Review**: 2025-11-17
**Assignee**: @JFK
