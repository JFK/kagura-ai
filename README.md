# Kagura AI - Universal AI Memory Platform

> **Own your memory. Bring it to every AI.**

[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python versions](https://img.shields.io/pypi/pyversions/kagura-ai.svg)](https://pypi.org/project/kagura-ai/)
[![PyPI version](https://img.shields.io/pypi/v/kagura-ai.svg)](https://pypi.org/project/kagura-ai/)
[![Protocol: MCP](https://img.shields.io/badge/protocol-MCP-blue.svg)](https://modelcontextprotocol.io/)
[![Status](https://img.shields.io/badge/status-v4.0--alpha-orange.svg)]()

**Kagura** は、あなたの**コンテキストと記憶**を、Claude/ChatGPT/Gemini/各種AIエージェントから**横断参照**できるようにする、オープンソースの **MCP対応メモリ基盤**です。

---

## 💡 The Problem

Your AI conversations are **scattered** across platforms.

```
Morning: ChatGPT helps you plan your day
Afternoon: Claude Desktop writes code with you
Evening: Gemini analyzes your documents
```

**But they don't remember each other.** Every AI starts from zero.

Switching platforms = **starting over**.

---

## ✨ The Solution

**Kagura**: A universal memory layer that **connects all your AIs**.

```
┌──────────────────────────────────┐
│   All Your AI Platforms          │
│   Claude • ChatGPT • Gemini      │
│   Cursor • Cline • Custom Agents │
└────────────┬─────────────────────┘
             │ (MCP Protocol)
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
- ✅ Coding patterns（"Vibe Coding"）
- ✅ Learning journey

**One memory. Every AI.**

---

## 🎯 Why Kagura?

### For Individuals
- 🔒 **Privacy-first**: Local storage, self-hosted, or cloud（your choice）
- 🚫 **No vendor lock-in**: Complete data export anytime
- 🧠 **Smart recall**: Vector search + Knowledge graph
- 📊 **Insights**: Visualize your learning patterns

### For Developers
- 💻 **"Vibe Coding" memory**: Track coding patterns, GitHub integration
- 🔌 **MCP-native**: Works with Claude Desktop, Cursor, Cline, etc.
- 🛠️ **Extensible**: Custom connectors via Python SDK
- 📦 **Production-ready**: Docker, API, full test coverage

### For Teams（Coming in v4.2）
- 👥 **Shared knowledge**: Team-wide memory
- 🔐 **Enterprise features**: SSO, BYOK, audit logs
- 📈 **Analytics**: Track team AI usage patterns

---

## 🚧 v4.0 Status - Phase A (In Progress)

**Current**: Implementing MCP-First Foundation

**What's Working**:
- ✅ v3.0 SDK & Chat（previous release）
- 🔄 v4.0 REST API skeleton（Phase A）
- 🔄 Docker Compose setup（Phase A）
- 🔄 MCP Tools v1.0（Phase A）

**Coming in Phase A** (4 weeks):
- FastAPI-based REST API
- 5 Core MCP Tools (store/recall/search/feedback/delete)
- MCP Tool Management (`kagura mcp doctor`, `kagura mcp install`)
- Production Docker setup
- v4.0.0-alpha release

**See**: [Phase A Issue #364](https://github.com/JFK/kagura-ai/issues/364)

---

## 🚀 Quick Start

### Option 1: v3.0 SDK（Current Stable）

```bash
pip install kagura-ai[full]

# Use the @agent decorator
from kagura import agent

@agent
async def translator(text: str) -> str:
    '''Translate to Japanese: {{ text }}'''

result = await translator("Hello World")
```

### Option 2: v4.0 Docker（Alpha - In Development）

```bash
# Clone repository
git clone https://github.com/JFK/kagura-ai.git
cd kagura-ai

# Checkout v4.0 branch
git checkout 364-featv40-phase-a-mcp-first-foundation

# Start services
docker compose up -d

# Verify
curl http://localhost:8080/api/v1/health
```

**API Docs**: http://localhost:8080/docs

### Option 3: MCP with Claude Desktop（Coming in Phase A Week 3）

```bash
# Install Kagura
pip install kagura-ai[full]

# Auto-configure Claude Desktop（Coming soon）
kagura mcp install

# Start MCP server
kagura mcp serve
```

---

## 🧩 Key Features（v4.0 Roadmap）

### 1. **Universal Memory API**（Phase A）

```python
from kagura import MemoryManager

memory = MemoryManager()

# Store
await memory.store(
    key="python_best_practices",
    value="Always use type hints for function signatures",
    scope="persistent",
    tags=["python", "coding"]
)

# Recall（semantic search）
results = await memory.recall(
    query="How should I write Python functions?",
    k=5
)
```

**MCP Tools**:
- `memory_store` - Store memories
- `memory_recall` - Semantic recall
- `memory_search` - Full-text + semantic
- `memory_feedback` - Improve quality
- `memory_delete` - Complete deletion

---

### 2. **Knowledge Graph**（Phase B - Issue #345）

Track **relationships** between memories:

```python
# Link memories
await memory.link(
    src="python_best_practices",
    dst="fastapi_tutorial",
    rel_type="related_to",
    weight=0.8
)

# Multi-hop traversal
related = await memory.query_graph(
    seed_ids=["python_best_practices"],
    hops=2
)
```

**Use cases**:
- Find related memories
- Discover learning paths
- Track dependencies

---

### 3. **Data Portability**（Phase B）

```bash
# Export everything
kagura memory export --output=./backup --format=jsonl

# Import to another instance
kagura memory import --input=./backup
```

**Format**: JSONL + attachments（human-readable, no lock-in）

---

### 4. **Vibe Coding History**（Phase B - Issue #345）

Track your **AI-assisted coding journey**:

```python
# Record interaction
await memory.record_interaction(
    ai_platform="claude",
    query="How to implement OAuth2 in FastAPI?",
    response="...",
    meta={"project": "kagura-api", "session_id": "..."}
)
```

---

## 🏗️ Architecture

### Storage
- **Vector**: ChromaDB（local）or pgvector（self-hosted/cloud）
- **Graph**: NetworkX（relationships）- Phase B
- **Metadata**: SQLite（local）or PostgreSQL（production）

### API
- **REST**: FastAPI with OpenAPI - Phase A ✅
- **MCP**: Model Context Protocol server - Phase A ✅
- **SDK**: Python（v3.0 available, v4.0 refactoring）

### Deployment
- **Local**: Docker Compose - Phase A ✅
- **Self-hosted**: Your own server（Phase C）
- **Cloud**: Managed SaaS（Phase E）

---

## 📦 Installation

### Stable (v3.0)

```bash
pip install kagura-ai[full]
```

### Development (v4.0-alpha)

```bash
# Clone & checkout v4.0 branch
git clone https://github.com/JFK/kagura-ai.git
cd kagura-ai
git checkout 364-featv40-phase-a-mcp-first-foundation

# Install dependencies
uv sync --all-extras

# Run API server（after Phase A completion）
uvicorn kagura.api.server:app --reload
```

---

## 🗺️ Roadmap

### ✅ v3.0（Released）
- Python SDK with `@agent` decorator
- Chat interface（MCP testing）
- 15+ built-in MCP tools

### 🔄 v4.0.0-alpha（Phase A - Week 1-4）
- **REST API**（FastAPI + OpenAPI）✅ In Progress
- **5 Core MCP Tools**（store/recall/search/feedback/delete）
- **MCP Tool Management**（doctor, install）
- **Docker Compose**（Postgres + Redis）✅ In Progress
- **Documentation**

### 🔄 v4.0.0（Phase B - Week 5-12）
- **Knowledge Graph**（NetworkX）- Issue #345
- **Consolidation**（Short → Long-term）
- **Export/Import**（JSONL format）
- **Multimodal DB prep**
- **v4.0.0 stable release**

### 🔮 v4.1.0（Phase C - Q2 2026）
- **Self-hosted API** with authentication
- **Multimodal MVP**（Attachments + derived texts）
- **Connectors**（GitHub, Calendar, Files）
- **Consumer App**（iOS/Android/Desktop）

### 🔮 v4.2.0+（Phase E - Q3-Q4 2026）
- **Cloud SaaS**（managed service）
- **Full Multimodal**（Cross-modal search）
- **Enterprise features**（SSO, BYOK, audit logs）
- **Neural Memory**（Issue #348 research）

**See**: [V4.0_IMPLEMENTATION_ROADMAP.md](./ai_docs/V4.0_IMPLEMENTATION_ROADMAP.md)

---

## 🔌 Integrations

### Supported AI Platforms（via MCP）

| Platform | Status | Notes |
|----------|--------|-------|
| **Claude Desktop** | ✅ v3.0 | MCP v1.0 support（v4.0: Phase A Week 3） |
| **Cline** | ✅ v3.0 | VS Code extension |
| **Cursor** | 🔄 v4.0+ | MCP support coming |
| **ChatGPT Desktop** | 🔄 2026 | OpenAI announced MCP adoption |
| **Gemini** | 🔄 2026 | Google confirmed MCP support |
| **Custom Agents** | ✅ | Use MCP SDK |

**Legend**: ✅ Supported | 🔄 Planned

---

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Active Development**:
- Phase A（v4.0.0-alpha）: [Issue #364](https://github.com/JFK/kagura-ai/issues/364)
- Phase B（GraphMemory）: [Issue #365](https://github.com/JFK/kagura-ai/issues/365)
- Neural Memory Research: [Issue #348](https://github.com/JFK/kagura-ai/issues/348)

**Ways to contribute**:
- 🐛 Report bugs
- 💡 Suggest features
- 📝 Improve documentation
- 🔧 Submit pull requests
- 🌐 Translate（especially Japanese ↔ English）

---

## 🌟 Comparison

### vs. Mem0
- ✅ **Kagura**: Local-first, complete OSS, Vibe Coding focus
- ❌ **Mem0**: SaaS-first, limited self-hosting

### vs. Anthropic MCP Memory Server
- ✅ **Kagura**: Multi-platform, advanced features（RAG, Graph, Consolidation）
- ❌ **Anthropic**: Claude-only, basic functionality

### vs. Rewind AI
- ✅ **Kagura**: AI interaction memory, cross-platform, MCP-native
- ❌ **Rewind**: Screen recording, Mac/iPhone only, $19/month

**See**: [V4.0_COMPETITIVE_ANALYSIS.md](./ai_docs/V4.0_COMPETITIVE_ANALYSIS.md)

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

**Inspired by**:
- [Model Context Protocol](https://modelcontextprotocol.io/) - Anthropic
- [Mem0](https://mem0.ai/) - Universal memory layer
- [Rewind AI](https://www.rewind.ai/) - Personal memory search

---

**Built with ❤️ for developers who want to own their AI memory**

[GitHub](https://github.com/JFK/kagura-ai) • [PyPI](https://pypi.org/project/kagura-ai/)

---

*v4.0.0-alpha - Phase A in progress*
*Last updated: 2025-10-26*
