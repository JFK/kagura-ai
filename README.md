# Kagura AI - Universal AI Memory Platform

<p align="center">
  <img src="https://raw.githubusercontent.com/JFK/kagura-ai/main/docs/assets/kagura-logo.svg" alt="Kagura AI Logo" width="400">
</p>

<p align="center">
  <strong>Own your memory. Bring it to every AI.</strong>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-blue.svg" alt="License"></a>
  <a href="https://pypi.org/project/kagura-ai/"><img src="https://img.shields.io/pypi/pyversions/kagura-ai.svg" alt="Python versions"></a>
  <a href="https://pypi.org/project/kagura-ai/"><img src="https://img.shields.io/pypi/v/kagura-ai.svg" alt="PyPI version"></a>
  <a href="https://pypi.org/project/kagura-ai/"><img src="https://img.shields.io/pypi/dm/kagura-ai.svg" alt="Downloads"></a>
  <a href="https://modelcontextprotocol.io/"><img src="https://img.shields.io/badge/protocol-MCP-blue.svg" alt="MCP"></a>
  <img src="https://img.shields.io/badge/status-stable-green.svg" alt="Status">
</p>

**Kagura** is an open-source **MCP-enabled memory platform** that allows your **context and memories** to be **shared across** Claude, ChatGPT, Gemini, and all your AI agents.

---

## 💡 The Problem

Your AI conversations are **scattered** across platforms.

```
Morning:   ChatGPT helps you plan your day
Afternoon: Claude Desktop writes code with you
Evening:   Gemini analyzes your documents
```

**But they don't remember each other.** Every AI starts from zero.

Switching platforms = **starting over**.

**For developers?** Even worse:
- Your custom agents can't access shared memory
- Building AI workflows means managing scattered state
- No unified SDK to connect everything

---

## ✨ The Solution

**Kagura**: A universal memory layer that **connects all your AIs**.

```
┌──────────────────────────────────┐
│   All Your AI Platforms          │
│   Claude • ChatGPT • Gemini      │
│   Cursor • Cline • Custom Agents │
└────────────┬─────────────────────┘
             │ (MCP Protocol + REST API)
     ┌───────▼────────────────┐
     │   Kagura Memory Hub    │
     │   Your unified memory  │
     └───────┬────────────────┘
             │
    ┌────────▼─────────┐
    │  Your Data       │
    │  (Local/Cloud)   │
    └──────────────────┘
```

Give **every AI** access to:
- ✅ Your knowledge base
- ✅ Conversation history
- ✅ Coding patterns
- ✅ Learning journey

**For developers**:
- 🔌 **REST API**: Query memory from any agent, any language
- 🐍 **Python SDK**: Build AI agents with unified memory access
- 📦 **MCP Tools**: 56 built-in tools (15 Memory + 20 Coding + 6 GitHub + others)
- 🧠 **Neural Memory**: Hebbian learning, activation spreading, adaptive associations
- 🛠️ **Extensible**: Custom connectors, workflows, integrations

**One memory. Every AI. Every developer.**

---

## 🎯 Why Kagura?

### For Individuals
- 🔒 **Privacy-first**: Local storage, self-hosted, or cloud (your choice)
- 🚫 **No vendor lock-in**: Complete data export anytime
- 🧠 **Smart recall**: Hybrid search (BM25 + vector + reranking)
- 📊 **Insights**: Visualize your learning patterns

### For Developers
- 🧠 **Neural Memory Network**: Hebbian learning, activation spreading, GDPR-compliant forgetting
- 💻 **Coding-Specialized Memory**: Track file changes, errors, design decisions with AI summaries
- 🔧 **GitHub CLI Integration**: Safe shell execution with 6 MCP tools
- 🔌 **MCP-native**: Works with Claude Desktop, Cursor, Cline, etc.
- 🌐 **REST API**: Access from any language
- 📦 **Production-ready**: Docker, full test coverage (1,450+ tests, 90%+ coverage)

### For Teams (Coming in v4.2)
- 👥 **Shared knowledge**: Team-wide memory
- 🔐 **Enterprise features**: SSO, BYOK, audit logs
- 📈 **Analytics**: Track team AI usage patterns

---

## 🚀 Quick Start

**Get started in less than 5 minutes!**

### Installation

```bash
pip install kagura-ai[full]
```

### Your First Memory

```bash
# Store a memory
kagura memory store \
  --key "python_pref" \
  --value "I prefer FastAPI for new projects" \
  --tags "preferences"

# Search it
kagura memory search --query "web framework preference"
```

### Connect to Claude Desktop

```bash
# Auto-configure
kagura mcp install

# Restart Claude Desktop, then try:
# "Run memory_stats to show Kagura status"
```

### Connect to Claude Code

```bash
# Add MCP server
claude mcp add --transport stdio kagura -- kagura mcp serve

# Verify
claude mcp list
```

### Full Guide

**📖 [Complete Quick Start Guide →](QUICKSTART.md)**

Everything you need:
- Installation (pip, docker, source)
- First memory operation (5 min tutorial)
- MCP setup for Claude Desktop/Code
- Coding session basics
- Common commands cheat sheet
- Troubleshooting

---

## ✅ v4.0 Status - Stable Release

**Current**: v4.0.9 (stable) - Universal AI Memory Platform

**Core Features** (Complete):
- ✅ **REST API** with OpenAPI docs
- ✅ **56 MCP Tools** with full management CLI
- ✅ **Neural Memory Network** (Hebbian learning, activation spreading)
- ✅ **Coding Memory** (20 MCP tools for developer workflows)
- ✅ **GitHub Integration** (6 MCP tools for safe shell operations)
- ✅ **Remote MCP Server** (HTTP/SSE for ChatGPT)
- ✅ **Memory Accuracy** (+40-60% precision via hybrid search)
- ✅ **Export/Import** (JSONL format, complete data portability)

**Test Coverage**: 1,450+ tests passing | 90%+ coverage

**What's Next**:
- 🎯 **v4.3.0** (November 2025): Code quality release (refactoring, optimization)
- 🔜 **v4.4.0** (Q1 2026): Smart Forgetting, Auto-recall, PostgreSQL
- 🔜 **v5.0.0** (Q2-Q4 2026): Cloud SaaS, Enterprise features

**See**: [Full Roadmap →](ai_docs/V4.0_IMPLEMENTATION_ROADMAP.md)

---

## 🧩 Core Features

### Universal Memory API
- **Store/Recall**: Semantic search with ChromaDB embeddings (E5 multilingual)
- **Hybrid Search**: BM25 + vector fusion + cross-encoder reranking
- **Graph Memory**: NetworkX-based knowledge graph with multi-hop traversal
- **Data Portability**: Export/import in JSONL format

### Coding-Specialized Memory
- **Session Tracking**: Start/end sessions with AI-generated summaries
- **File Change Tracking**: AST-based dependency analysis
- **Error Recording**: Track errors and solutions, searchable history
- **Design Decisions**: Document architectural choices
- **GitHub Integration**: Auto-post summaries to Issues/PRs

### Neural Memory Network
- **Hebbian Learning**: Adaptive memory associations
- **Activation Spreading**: 1-3 hop graph propagation
- **Trust Modulation**: Poisoning defense
- **GDPR-Compliant**: Automatic forgetting mechanisms

### MCP Tools (56 total)
- **Memory**: 15 tools (store, recall, search, delete, stats, etc.)
- **Coding**: 20 tools (sessions, file tracking, errors, decisions, GitHub)
- **GitHub**: 6 tools (issue view, PR operations, safe shell execution)
- **Search**: 5 tools (Brave Search, academic, fact-check)
- **Media**: 4 YouTube tools + multimodal RAG
- **Utilities**: Cache, routing, observability, meta-agent

### REST API & SDK
- **FastAPI** with OpenAPI documentation
- **Python SDK** with `@agent` decorator (v3.0)
- **API Key Authentication** with bearer tokens
- **Multi-language Support** via HTTP

---

## 🏗️ Architecture

### Storage
- **Vector**: ChromaDB (local) or pgvector (cloud)
- **Graph**: NetworkX for relationships
- **Metadata**: SQLite (local) or PostgreSQL (production)

### Access
- **MCP Protocol**: Claude Desktop, Claude Code, Cursor, Cline
- **REST API**: Any language, any agent
- **Python SDK**: `@agent` decorator for rapid development

### Deployment
- **Local**: Docker Compose (dev)
- **Self-hosted**: Production Docker + Caddy (HTTPS)
- **GCP**: Terraform + Cloud SQL + Memorystore ([terraform/gcp/](terraform/gcp/))
  - e2-medium VM (2 vCPU, 4GB) - ~$57/month
  - PostgreSQL + Redis + Qdrant (Docker)
  - OpenAI embeddings recommended (RAM efficient)
- **Cloud SaaS**: Managed service (coming in v5.0)

**Data Location** (XDG-compliant):
```
~/.cache/kagura/          # Cache (ChromaDB, logs)
~/.local/share/kagura/    # Persistent data (memory.db, sessions)
~/.config/kagura/         # Configuration
```

---

## 🗺️ Roadmap

### ✅ v4.0.9 (Current - Stable)
- MCP-native with 56 tools
- Neural Memory Network
- Coding-specialized memory
- Hybrid search (+40-60% precision)
- Remote MCP (HTTP/SSE)
- Production Docker + API

### 🎯 v4.3.0 (November 2025) - Code Quality Release
**Focus**: Internal refactoring, performance optimization, developer experience

- ✅ **Phase 1-5 Complete**: Utils consolidation, MCP reorganization, CLI optimization
- **File Size Reduction**: Major modules reduced by 50-75% (e.g., `coding_memory.py` 2,116 → 582 lines)
- **Code Quality**: <5% duplication, 100% type coverage, 90%+ test coverage
- **Performance**: CLI startup < 500ms (from 1.2s)
- **Backward Compatibility**: 100% maintained, zero breaking changes

**Tracking**: [Issue #612](https://github.com/JFK/kagura-ai/issues/612)

### 🔜 v4.4.0 (Q1 2026) - Smart Memory
- **Smart Forgetting**: Auto-maintenance with RecallScorer
- **Auto-recall Intelligence**: "Unspoken Understanding"
- **PostgreSQL Backend**: Cloud-ready GraphMemory
- **Connectors**: GitHub, Google Workspace

### 🔜 v5.0.0 (Q2-Q4 2026) - Cloud & Enterprise
- **Cloud SaaS**: Managed service
- **Memory Curator**: AI-driven memory management
- **Enterprise**: SSO, BYOK, audit logs
- **Advanced Tools**: Cost tracking, advanced analytics

**See**: [V4.0_IMPLEMENTATION_ROADMAP.md](ai_docs/V4.0_IMPLEMENTATION_ROADMAP.md)

---

## 🔌 Integrations

### Supported AI Platforms

| Platform | Status | Integration |
|----------|--------|-------------|
| **Claude Desktop** | ✅ Stable | MCP v1.0 (56 tools) |
| **Claude Code** | ✅ Stable | MCP stdio transport |
| **Cursor** | ✅ Stable | MCP protocol support |
| **Cline** | ✅ Stable | VS Code extension (MCP) |
| **ChatGPT** | 🔄 Preview | Remote MCP (HTTP/SSE) |
| **Custom Agents** | ✅ Stable | REST API + Python SDK |

### Access Methods

| Method | Language | Use Case |
|--------|----------|----------|
| **MCP Protocol** | Any (JSON-RPC) | AI platform integration |
| **REST API** | Any | Custom agents, any language |
| **Python SDK** | Python | `@agent` decorator for rapid dev |
| **Direct DB** | Any | Advanced: ChromaDB/PostgreSQL access |

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Ways to contribute**:
- 🐛 Report bugs → [GitHub Issues](https://github.com/JFK/kagura-ai/issues)
- 💡 Suggest features → [Discussions](https://github.com/JFK/kagura-ai/discussions)
- 📝 Improve documentation
- 🔧 Submit pull requests
- 🌐 Translate (Japanese ↔ English)

---

## 🌟 Comparison

### vs. Mem0
- ✅ **Kagura**: Local-first, complete OSS, developer-focused
- ❌ **Mem0**: SaaS-first, limited self-hosting

### vs. Anthropic MCP Memory Server
- ✅ **Kagura**: Multi-platform, 56 tools, advanced features (RAG, Graph, Neural)
- ❌ **Anthropic**: Claude-only, 5 basic tools

### vs. Rewind AI
- ✅ **Kagura**: AI interaction memory, cross-platform, free & open source
- ❌ **Rewind**: Screen recording, Mac/iPhone only, $19/month

**See**: [V4.0_COMPETITIVE_ANALYSIS.md](ai_docs/V4.0_COMPETITIVE_ANALYSIS.md)

---

## 📄 License

[Apache License 2.0](LICENSE)

You can:
- ✅ Use commercially
- ✅ Modify
- ✅ Distribute
- ✅ Sublicense
- ✅ Private use

---

## 🌸 About the Name

**Kagura (神楽)** is traditional Japanese performing art that embodies **harmony** and **creativity** - principles at the heart of this project.

Just as Kagura connects humans with the divine, Kagura AI connects you with all your AIs through a **unified memory**.

---

## 🙏 Acknowledgments

**Built with**:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern API framework
- [ChromaDB](https://www.trychroma.com/) - Vector database
- [NetworkX](https://networkx.org/) - Graph library
- [Pydantic](https://pydantic-docs.helpmanual.io/) - Data validation
- [LiteLLM](https://litellm.ai/) - Unified LLM API

**Inspired by**:
- [Model Context Protocol](https://modelcontextprotocol.io/) - Anthropic
- [Mem0](https://mem0.ai/) - Universal memory layer
- [Rewind AI](https://www.rewind.ai/) - Personal memory search

---

**Built with ❤️ for developers who want to own their AI memory**

[GitHub](https://github.com/JFK/kagura-ai) • [PyPI](https://pypi.org/project/kagura-ai/) • [Quick Start →](QUICKSTART.md)

---

*v4.3.0 - Code Quality Release*
*Last updated: 2025-11-09*
