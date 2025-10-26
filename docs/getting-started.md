# Getting Started with Kagura AI v4.0

> **Universal AI Memory Platform - 5-minute setup**

This guide will help you get started with Kagura v4.0, the universal memory layer for all your AI platforms.

---

## 📋 Prerequisites

- Python 3.11 or higher
- pip or uv package manager
- (Optional) Docker for API server deployment
- (Optional) Claude Desktop for MCP integration

---

## 🚀 Quick Start

### Option 1: Local Installation (Recommended)

```bash
# Install Kagura with all features
pip install kagura-ai[full]

# Or use uv for faster installation
uv pip install kagura-ai[full]
```

### Option 2: Development Setup

```bash
# Clone repository
git clone https://github.com/JFK/kagura-ai.git
cd kagura-ai

# Checkout v4.0 branch
git checkout 364-featv40-phase-a-mcp-first-foundation

# Install dependencies
uv sync --all-extras

# Verify installation
kagura --version
```

---

## 🧪 Verify Installation

### Check MCP Tools

```bash
# List all available MCP tools
kagura mcp tools
```

**Expected output**:
```
Kagura MCP Tools (28)

┏━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━┓
┃ Tool Name              ┃ Category ┃ Description          ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━┩
│ memory_store           │ memory   │ Store information... │
│ memory_recall          │ memory   │ Recall information...│
...
```

### Run Diagnostics

```bash
# Check system health
kagura mcp doctor
```

**Expected output**:
```
Kagura MCP Diagnostics

┏━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━┓
┃ Component      ┃ Status           ┃ Details         ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━┩
│ Memory Manager │ ✅ healthy       │ Persistent: 0...│
│ Storage        │ ✅ healthy       │ 0.0 MB          │
└────────────────┴──────────────────┴─────────────────┘
```

---

## 🔌 Usage Options

Kagura v4.0 provides 3 ways to use the memory platform:

### 1. MCP Integration (Recommended)

Use Kagura with Claude Desktop, Cursor, Cline, or any MCP-compatible client.

```bash
# Configure Claude Desktop automatically
kagura mcp install

# Start MCP server (usually called by Claude Desktop)
kagura mcp serve
```

**See**: [MCP Setup Guide](./mcp-setup.md) for detailed instructions.

---

### 2. REST API

Use the HTTP API for custom integrations.

```bash
# Start API server
uvicorn kagura.api.server:app --host 0.0.0.0 --port 8080

# Or use Docker
docker compose up -d
```

**API Docs**: http://localhost:8080/docs

**Example**:
```bash
# Create memory
curl -X POST http://localhost:8080/api/v1/memory \
  -H "Content-Type: application/json" \
  -d '{
    "key": "my_preference",
    "value": "I prefer Python over JavaScript",
    "scope": "persistent",
    "tags": ["preferences", "programming"],
    "importance": 0.9
  }'

# Recall memory
curl -X POST http://localhost:8080/api/v1/recall \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What programming languages do I like?",
    "k": 5
  }'
```

**See**: [API Reference](./api-reference.md)

---

### 3. Python SDK (v3.0 Compatible)

Use Kagura programmatically in your Python applications.

```python
from kagura.core.memory import MemoryManager

# Initialize memory manager
memory = MemoryManager(
    agent_name="my_app",
    enable_rag=True  # Enable semantic search
)

# Store memory
memory.remember(
    key="user_preference",
    value="Prefers Python",
    metadata={"tags": ["python", "preferences"], "importance": 0.9}
)

# Recall by key
preference = memory.recall("user_preference")
print(preference)  # "Prefers Python"

# Semantic search
results = memory.recall_semantic(
    query="programming languages",
    top_k=5
)
for result in results:
    print(f"- {result['content']} (similarity: {1 - result['distance']:.2f})")
```

---

## 🛠️ Common Tasks

### Store a Memory

**MCP** (via Claude Desktop):
> "Remember that I prefer dark mode for my IDE"

**REST API**:
```bash
curl -X POST http://localhost:8080/api/v1/memory \
  -H "Content-Type: application/json" \
  -d '{
    "key": "ide_preference",
    "value": "Prefers dark mode",
    "scope": "persistent",
    "tags": ["preferences", "ide"]
  }'
```

**Python SDK**:
```python
memory.remember("ide_preference", "Prefers dark mode")
```

---

### Search Memories

**MCP** (via Claude):
> "What do you remember about my IDE preferences?"

**REST API**:
```bash
curl -X POST http://localhost:8080/api/v1/recall \
  -H "Content-Type: application/json" \
  -d '{
    "query": "IDE preferences",
    "k": 5
  }'
```

**Python SDK**:
```python
results = memory.recall_semantic("IDE preferences", top_k=5)
```

---

### Provide Feedback

**MCP**:
> "That memory about dark mode was helpful"

**Python** (via MCP tool):
```python
# This would be called by the AI agent automatically
# when it detects useful memories
```

---

## 🎯 Next Steps

1. **[MCP Setup](./mcp-setup.md)** - Configure Claude Desktop
2. **[API Reference](./api-reference.md)** - Explore REST API
3. **[Architecture](./architecture.md)** - Understand system design
4. **[Examples](../examples/)** - See code examples

---

## 💬 Need Help?

- **Documentation**: https://github.com/JFK/kagura-ai/tree/main/docs
- **Issues**: https://github.com/JFK/kagura-ai/issues
- **Discussions**: https://github.com/JFK/kagura-ai/discussions

---

**Version**: 4.0.0-alpha
**Last updated**: 2025-10-26
