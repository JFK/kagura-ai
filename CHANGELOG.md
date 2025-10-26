# Changelog

All notable changes to Kagura AI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

### ⚠️ Breaking Changes

None - v4.0 is developed on separate branch (`364-featv40-phase-a-mcp-first-foundation`)

v3.0 remains stable on `main` branch.

### 🚧 In Progress

#### Phase B (Coming in v4.0.0 stable)
- GraphMemory integration (Issue #345, #365)
- Memory consolidation (short → long-term)
- Export/Import (JSONL format)
- Multimodal database schema

#### Phase C (Coming in v4.1.0)
- Self-hosted API with authentication
- Multimodal MVP (attachments + derived texts)
- Connectors (GitHub, Calendar, Files)
- Consumer App (Flutter)

### 📊 Statistics

**Phase A Metrics**:
- **Files changed**: 30+
- **Lines added**: 5,000+
- **New modules**: 7
- **API endpoints**: 10
- **MCP tools**: 28 (6 memory tools)
- **CLI commands**: 6 (4 new)
- **Documentation pages**: 7

**Git Stats**:
- **Commits**: 6 (Phase A Week 1-4)
- **PR**: #366 (Draft)
- **Issues**: #364 (Phase A), #365 (Phase B)

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
