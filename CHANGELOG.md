# Changelog

All notable changes to Kagura AI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### ✨ Added

- **MCP over HTTP/SSE**: New `/mcp` endpoint for ChatGPT Connectors (#378, Phase C Task 1)
  - GET `/mcp` - SSE streaming (server → client messages)
  - POST `/mcp` - JSON-RPC requests (client → server messages)
  - DELETE `/mcp` - Session termination
  - Uses MCP SDK's `StreamableHTTPServerTransport` for protocol handling
  - Auto-registers all built-in MCP tools (memory, graph, etc.)
  - Background task manages MCP server lifecycle
  - Documentation: `docs/mcp-http-setup.md`

- **API Key Authentication**: Secure authentication for remote access (#378, Phase C Task 2)
  - `APIKeyManager` for key generation, validation, and management
  - SQLite-based storage with SHA256 hashing
  - CLI commands: `kagura api create-key`, `list-keys`, `revoke-key`, `delete-key`
  - `/mcp` endpoint authentication via `Authorization: Bearer <key>` header
  - Support for key expiration and audit trails
  - Optional authentication (falls back to `default_user`)
  - User ID extraction from validated API keys

- **Tool Access Control**: Security filtering for remote MCP access (#378, Phase C Task 3)
  - Permission system in `src/kagura/mcp/permissions.py`
  - Local vs. remote context distinction
  - Dangerous tools (file ops, shell exec, local apps) blocked remotely
  - Safe tools (memory, web, API) allowed remotely
  - Automatic filtering in `create_mcp_server(context="remote")`
  - Fail-safe: unknown tools denied by default
  - Comprehensive test coverage (28 tests)

- **MCP Remote Connection CLI**: Commands for remote configuration (#378, Phase C Task 4)
  - `kagura mcp connect` - Configure remote API connection
  - `kagura mcp test-remote` - Test remote connectivity and authentication
  - `kagura mcp serve --remote` - Remote mode placeholder (future)
  - Config storage in `~/.kagura/remote-config.json`
  - Connection diagnostics with health checks
  - 7 new CLI tests

### 🔄 Changed

- **GraphMemory**: Made `ai_platform` parameter optional in `record_interaction` (#381)
  - New signature: `record_interaction(user_id, query, response, metadata)`
  - `ai_platform` moved to metadata (optional)
  - MCP tool: `ai_platform` parameter now optional with default=""
  - REST API: `InteractionCreate.ai_platform` is now `str | None`
  - Backward compatible: `analyze_user_pattern` supports both old and new formats
  - Rationale: Aligns with v4.0 Universal Memory principle ("Own your memory, bring it to every AI")

---

## [4.0.0] - 2025-10-26

### 🎯 Universal Memory Foundation (Issue #382)

**Major Change**: Added `user_id` to all memory operations for true multi-user support.

**Rationale**: Phase C (Remote MCP Server) requires multi-user support. Memory must be scoped by user to enable remote deployment with proper data isolation.

### ⚠️ BREAKING CHANGES

#### MCP Tools API Changes

All memory MCP tools now require `user_id` as the **first parameter**:

**Before v4.0.0**:
```python
memory_store(agent_name="my_agent", key="lang", value="ja")
memory_recall(agent_name="my_agent", key="lang")
```

**After v4.0.0**:
```python
memory_store(user_id="user_jfk", agent_name="my_agent", key="lang", value="ja")
memory_recall(user_id="user_jfk", agent_name="my_agent", key="lang")
```

**Affected Tools** (#382):
- `memory_store(user_id, agent_name, ...)`
- `memory_recall(user_id, agent_name, ...)`
- `memory_search(user_id, agent_name, ...)`
- `memory_list(user_id, agent_name, ...)`
- `memory_feedback(user_id, agent_name, ...)`
- `memory_delete(user_id, agent_name, ...)`
- `memory_get_related(user_id, agent_name, ...)`

#### Python API Changes

`MemoryManager` now requires `user_id`:

**Before v4.0.0**:
```python
manager = MemoryManager(agent_name="test")
```

**After v4.0.0**:
```python
manager = MemoryManager(user_id="user_jfk", agent_name="test")
```

#### REST API Changes

**New**: `X-User-ID` header support

```bash
# With explicit user_id
curl -H "X-User-ID: user_jfk" -X POST .../api/v1/memory

# Without header (uses "default_user")
curl -X POST .../api/v1/memory
```

### ✨ Added

- **Universal Memory**: `user_id` parameter added to all memory operations (#382)
- **Database**: `user_id` column with auto-migration for existing data (#382)
- **REST API**: `X-User-ID` header support with `default_user` fallback (#382)
- **Multi-User**: Per-user MemoryManager instances with isolated storage (#382)
- **Documentation**: Migration guide for v4.0.0 (#382)

### 🔄 Changed

- **MemoryManager**: `user_id` is now required (first positional parameter) (#382)
- **PersistentMemory**: All methods accept `user_id` parameter (#382)
- **MemoryRAG**: User-scoped vector collections (#382)
- **Cache Key Format**: `{user_id}:{agent_name}:rag={bool}` (#382)

### 🗑️ Removed

- **Personal Tools**: Removed v3.0 legacy personal assistant tools (#373)
  - Deleted: `news.py`, `weather.py`, `recipes.py`, `events.py`, `personal_assistant.py`
  - Deleted: `examples/09_personal_tools/` directory
  - Deleted: `tests/agents/test_personal_tools.py` (39 tests)
  - Rationale: v4.0 is MCP-first. Personal tools don't align with Universal Memory Platform strategy

- **SDK Examples**: Removed v3.0 SDK integration examples (#374)
  - Deleted: `examples/08_sdk_integration/` directory (FastAPI, Streamlit, data pipeline, email automation)
  - Updated: `examples/README.md` - Removed section 08 and SDK references
  - Rationale: v4.0 focuses on MCP tools and REST API, not Python SDK integration patterns

### 🐛 Fixed

- **GraphMemory**: Fixed `memory_get_related` type conversion error when `depth` parameter is sent as string by MCP clients (#379)
- **GraphMemory**: Topic extraction now working - `record_interaction` creates topic nodes and edges from metadata (#379)

### ✨ Improved

- **MCP Tools**: Enhanced docstrings with 🔍 USE WHEN, 💡 EXAMPLE, and 📊 RETURNS sections for better LLM understanding (#379, #382)
- **GraphMemory**: `record_interaction` now automatically creates topic nodes when `"topic"` is in metadata (#379)
- **GraphMemory**: User→Topic edges created for pattern analysis (#379)

### 🧪 Tests

- Updated 100+ tests for `user_id` support (#382)
- Added `X-User-ID` header tests for REST API (#382)
- Added user isolation tests (multi-user memory separation) (#382)
- Added `test_get_related_with_string_depth` - MCP protocol compatibility test (#379)
- Added `test_record_interaction_with_topic` - Topic extraction validation (#379)

---

## [4.0.0a0] - 2025-10-26

### 🎯 Strategic Pivot

**From**: Python-First AI Agent SDK (v3.0)
**To**: Universal AI Memory & Context Platform (v4.0)

**Vision**: Make Kagura the de facto standard for AI Memory Management across all platforms via MCP.

**See**: [V4.0 Strategic Pivot](./ai_docs/V4.0_STRATEGIC_PIVOT.md)

### ✨ Added

#### REST API (Phase A)
- FastAPI-based REST API server (`src/kagura/api/`)
  - Memory CRUD endpoints (`POST/GET/PUT/DELETE /api/v1/memory`)
  - Search endpoint (`POST /api/v1/search`)
  - Semantic recall endpoint (`POST /api/v1/recall`)
  - Health check (`GET /api/v1/health`)
  - System metrics (`GET /api/v1/metrics`)
- Pydantic request/response models
- OpenAPI 3.1 specification (`docs/api/reference.yaml`)
- Dependency injection for MemoryManager
- ChromaDB metadata encoding/decoding for list/dict values

#### MCP Tools v1.0 (Phase A)
- `memory_feedback` - Provide quality feedback (Hebbian-like learning)
- `memory_delete` - Delete with audit logging (GDPR-compliant)
- Updated `memory_store` - Support for tags/importance/metadata (v4.0 format)
- Existing tools: `memory_recall`, `memory_search`, `memory_list` (28 tools total)

#### MCP Tool Management (Phase A, Issue #331)
- `kagura mcp tools` - List all MCP tools (28 tools, categorized)
- `kagura mcp doctor` - Comprehensive diagnostics
  - API Server health check
  - Memory Manager status
  - Claude Desktop configuration check
  - Storage usage monitoring
- `kagura mcp install` - Auto-configure Claude Desktop
- `kagura mcp uninstall` - Remove Claude Desktop configuration
- MCP config management (`src/kagura/mcp/config.py`)
- MCP diagnostics (`src/kagura/mcp/diagnostics.py`)

#### GraphMemory Integration (Phase B, Issue #345)
- **GraphMemory Core** (`src/kagura/core/graph/memory.py`)
  - NetworkX-based knowledge graph for relationships
  - Node types: memory, user, topic, interaction
  - Edge types: related_to, depends_on, learned_from, influences, works_on
  - Multi-hop graph traversal with relationship filtering
  - User pattern analysis methods:
    - `get_user_topics()` - Get topics associated with a user
    - `get_user_interactions()` - Get user interaction history
    - `analyze_user_pattern()` - Analyze patterns (topics, platforms, frequency)
  - Graph persistence (pickle format)
  - Auto-load on initialization

- **MCP Tools for Graph** (3 new tools)
  - `memory_get_related(node_id, depth, rel_type)` - Get related nodes via graph traversal
  - `memory_record_interaction(user_id, ai_platform, query, response, metadata)` - Record AI-User interactions
  - `memory_get_user_pattern(user_id)` - Analyze user interaction patterns

- **REST API for Graph** (3 new endpoints)
  - `POST /api/v1/graph/interactions` - Record AI-User interaction
  - `GET /api/v1/graph/{node_id}/related` - Get related nodes (supports depth, rel_type filtering)
  - `GET /api/v1/graph/users/{user_id}/pattern` - Analyze user patterns
  - Pydantic models for type-safe requests/responses
  - OpenAPI documentation support

- **MemoryManager Integration**
  - `enable_graph=True` by default (auto-enables GraphMemory)
  - Auto-detects NetworkX availability (graceful degradation)
  - Graph persistence path: `{persist_dir}/graph.pkl`
  - Integrated with existing 3-tier memory system

- **Dependencies**
  - Added `networkx>=3.0` to `ai` extras (~1.5MB)

#### Docker & Infrastructure
- Docker Compose setup (PostgreSQL + pgvector, Redis, API server)
- Dockerfile for API server
- `.dockerignore` for efficient builds
- Makefile targets (`build_docs`, `serve_docs`, etc.)

#### Documentation
- Getting Started guide (`docs/getting-started.md`)
- MCP Setup guide (`docs/mcp-setup.md`)
- API Reference (`docs/api-reference.md`)
- Architecture documentation (`docs/architecture.md`)
- Redocly API documentation workflow (`.github/workflows/api-docs.yml`)
- V4.0 strategy documents (5 files in `ai_docs/`)

### 🔧 Changed

- **README.md**: Updated to v4.0 positioning
  - "Universal AI Memory Platform" messaging
  - MCP-first approach
  - Roadmap updated (v4.0 → v4.2)
- **pyproject.toml**:
  - Version: 3.0.8 → 4.0.0a0
  - Description: Memory platform focus
  - Keywords: memory, mcp, context, knowledge-graph
  - Dependencies: Added FastAPI, uvicorn, psycopg2, redis, networkx
- **core/registry.py**: Export `tool_registry` from `tool_registry.py`

### 📝 Documentation

- `ai_docs/V4.0_STRATEGIC_PIVOT.md` - Strategic direction & multimodal plan
- `ai_docs/V4.0_IMPLEMENTATION_ROADMAP.md` - Detailed 8-12 month roadmap
- `ai_docs/V4.0_COMPETITIVE_ANALYSIS.md` - Market analysis (vs Mem0, Rewind AI, etc.)
- `ai_docs/V4.0_README_DRAFT.md` - New README draft
- `ai_docs/V4.0_GITHUB_ISSUE_TEMPLATE.md` - Issue templates

### 🐛 Fixed

- ChromaDB metadata constraints for list/dict values
  - Automatic JSON encoding on store
  - Automatic JSON decoding on retrieve
  - Transparent to API users

- **web_search MCP tool** - JSON serialization error (Issue #345)
  - Fixed `SearchResult` dataclass serialization
  - Added `asdict()` conversion before JSON serialization
  - Added `ensure_ascii=False` for proper Japanese character support
  - Added comprehensive unit tests (5 tests) to prevent regression

### ⚠️ Breaking Changes

None - v4.0 is developed on separate branch (`364-featv40-phase-a-mcp-first-foundation`)

v3.0 remains stable on `main` branch.

### 🧪 Tests

**GraphMemory & MCP Tools** (Issue #345):
- GraphMemory unit tests: 40 tests (100% coverage)
  - Node/edge operations, graph queries, persistence
  - User pattern analysis, interaction recording
- MCP Tools integration tests: 27 tests
  - memory graph tools: 9 tests
  - web_search: 5 tests (dataclass serialization validation)
  - file_ops: 17 tests (file I/O, permissions, encoding)
  - routing: 5 tests (placeholder validation)
- **Total**: 76 tests added, all passing
- Type-safe (pyright strict), lint-clean (ruff)

### 🚧 In Progress

#### Phase B (Remaining for v4.0.0 stable)
- Memory consolidation (short → long-term)
- Export/Import (JSONL format)
- Multimodal database schema

#### Phase C (Coming in v4.1.0)
- Self-hosted API with authentication
- Multimodal MVP (attachments + derived texts)
- Connectors (GitHub, Calendar, Files)
- Consumer App (Flutter)
- Remote MCP Server support (Issue #368)

### 📊 Statistics

**Phase A + B Metrics**:
- **Files changed**: 45+ (Phase A: 30, Phase B: 15)
- **Lines added**: 7,331+ (Phase A: 5,000, Phase B: 2,331)
- **New modules**: 8 (Phase A: 7, Phase B: 1 graph module)
- **API endpoints**: 13 (Phase A: 10, Phase B: 3 graph endpoints)
- **MCP tools**: 31 (Phase A: 28, Phase B: +3 graph tools)
- **CLI commands**: 6 (4 new)
- **Documentation pages**: 7
- **Tests**: 76+ GraphMemory/MCP tests

**Git Stats**:
- **Commits**: 11 (Phase A: 6, Phase B: 5)
- **PRs**: #366 (Phase A, merged), #367 (Phase B, merged)
- **Issues**: #364 (Phase A), #345 (Phase B, closed), #368 (Remote MCP Server)

---

## [3.0.8] - 2025-10-23

### Fixed
- Memory telemetry type error (Issue #360, #361)

### Improved
- MCP tool descriptions for better LLM decision making

---

## Earlier Versions

See git history for v3.0.0 - v3.0.7 changes.

---

**For complete details, see**:
- [V4.0 Implementation Roadmap](./ai_docs/V4.0_IMPLEMENTATION_ROADMAP.md)
- [GitHub Releases](https://github.com/JFK/kagura-ai/releases)
- [Pull Requests](https://github.com/JFK/kagura-ai/pulls)
