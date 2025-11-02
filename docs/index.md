---
title: Kagura AI - Universal AI Memory Platform
description: Own your memory. Bring it to every AI. MCP-native memory for Claude, ChatGPT, Gemini, and all your AI platforms.
keywords:
  - Universal Memory
  - AI Memory
  - MCP Protocol
  - ChatGPT Connector
  - Claude Desktop
  - Self-hosted AI
  - Memory Platform
author: Fumikazu Kiyota
robots: index, follow
og_title: Kagura AI - Universal AI Memory Platform
og_type: website
og_url: https://www.kagura-ai.com
og_description: Own your memory. Bring it to every AI. MCP-native universal memory for all your AI platforms.
og_image: assets/kagura-logo.svg
twitter_card: summary_large_image
twitter_site: "@kagura_ai"
twitter_creator: "@JFK"
---

# Kagura AI

![Kagura AI Logo](assets/kagura-logo.svg)

**Universal AI Memory Platform**

> Own your memory. Bring it to every AI.

MCP-native memory infrastructure that connects Claude Desktop, ChatGPT, Gemini, and all your AI platforms with shared context and memory.

---

## What is Kagura AI v4.0?

A universal memory layer that makes every AI remember your preferences, context, and history across all platforms.

```
Morning: ChatGPT helps you plan your day
         ↓ (remembers your preferences)

Afternoon: Claude Desktop writes code with you
           ↓ (knows your coding style)

Evening: Gemini analyzes your documents
         ↓ (recalls your project context)
```

**One memory. Every AI.**

---

## Why Kagura AI?

### For Individuals

- 🔒 **Privacy-first**: Local storage or self-hosted
- 🚫 **No vendor lock-in**: Complete data export anytime
- 🧠 **Smart recall**: Vector search + Knowledge graph
- 🌐 **Universal**: Works with Claude, ChatGPT, Gemini, Cursor, Cline

### For Developers

- 💻 **MCP-native**: 31 tools via Model Context Protocol
- 🔌 **Easy integration**: `kagura mcp install` for Claude Desktop
- 🛠️ **REST API**: FastAPI server with OpenAPI
- 📦 **Production-ready**: Docker, authentication, monitoring

### For Teams (Coming Soon)

- 👥 **Shared knowledge**: Team-wide memory
- 🔐 **Enterprise features**: SSO, BYOK, audit logs
- 📈 **Analytics**: Track team AI usage patterns

---

## Core Features

### 1. Universal Memory

Store once, access from any AI:

```python
# Via MCP tool (works in Claude Desktop, ChatGPT, etc.)
memory_store(
    user_id="jfk",
    agent_name="global",
    key="coding_style",
    value="Always use type hints in Python",
    scope="persistent",
    tags='["python", "best-practices"]'
)
```

### 2. MCP Integration

**Claude Desktop** (local, all 31 tools):
```bash
kagura mcp install  # Auto-configure
# All tools available: memory, files, web, shell, etc.
```

**ChatGPT Connector** (remote, 24 safe tools):
```bash
docker compose up -d
# Connect ChatGPT to http://localhost:8000/mcp
# Safe tools only (no file ops, no shell)
```

### 3. Knowledge Graph

Track relationships and patterns:
- AI-User interaction history
- Memory relationships
- Learning patterns analysis
- Topic clustering

### 4. Complete Data Portability

```bash
# Export everything
kagura memory export --output ./backup

# Import anywhere
kagura memory import --input ./backup
```

---

## Quick Start

### Option 1: Claude Desktop User

```bash
pip install kagura-ai[full]
kagura mcp install
# Restart Claude Desktop - Done!
```

[Claude Desktop Setup →](mcp-setup.md)

### Option 2: ChatGPT User

```bash
docker compose up -d
# Configure ChatGPT Connector: http://localhost:8000/mcp
```

[ChatGPT Connector Setup →](mcp-http-setup.md)

### Option 3: Self-Hosted Production

```bash
git clone https://github.com/JFK/kagura-ai.git
cd kagura-ai
cp .env.example .env  # Configure DOMAIN, POSTGRES_PASSWORD
docker compose -f docker-compose.prod.yml up -d
```

[Self-Hosting Guide →](self-hosting.md)

---

## Available Tools (MCP)

**Memory** (6 tools):
- memory_store, memory_recall, memory_search
- memory_list, memory_delete, memory_feedback

**Graph** (3 tools):
- memory_record_interaction
- memory_get_related
- memory_get_user_pattern

**Web/API** (10+ tools):
- web_search, web_scrape
- youtube_summarize, get_youtube_transcript
- brave_web_search, fact_check_claim

**File Operations** (local only):
- file_read, file_write, dir_list

**System**:
- shell_exec (local only)
- telemetry_stats, telemetry_cost

---

## Documentation

- [Getting Started](getting-started.md) - 10-minute setup
- [API Reference](api-reference.md) - REST API + MCP tools
- [Architecture](architecture.md) - System design
- [Self-Hosting](self-hosting.md) - Production deployment
- [Memory Export/Import](memory-export.md) - Backup guide

---

## Community

- [GitHub](https://github.com/JFK/kagura-ai) - Source code & issues
- [PyPI](https://pypi.org/project/kagura-ai/) - Package downloads
- [Examples](https://github.com/JFK/kagura-ai/tree/main/examples) - Usage examples

---

## Status: v4.0.0 (Phase C Complete)

**Recently Completed**:
- ✅ Phase A: MCP-First Foundation
- ✅ Phase B: Graph Memory
- ✅ Phase C: Remote MCP Server + Export/Import

**Features**:
- ✅ 31 MCP tools
- ✅ REST API (FastAPI)
- ✅ MCP over HTTP/SSE (ChatGPT Connector)
- ✅ API Key authentication
- ✅ Memory export/import (JSONL)
- ✅ Production Docker setup

**Coming Next**: v4.0.0 stable release

---

**Built with ❤️ for universal AI memory**
