# 移行ガイド: v3.0 → v4.0

このガイドでは migrate from Kagura AI v3.0 to v4.0.

**対象読者**: v3.0からv4.0にアップグレードする既存ユーザー

---

## 🎯 概要

**v4.0** is a major release focusing on **Universal AI Memory Platform**:
- REST API (FastAPI)
- 34 MCP Tools (vs 15 in v3.0)
- GraphMemory (knowledge graphs)
- Remote MCP Server (HTTP/SSE)
- Production-ready infrastructure

**アップグレード作業**: 約30分
**互換性**: ほとんどのv3.0コードは最小限の変更で動作します

---

## 📋 破壊的変更

### 1. Memory API: `user_id` Now Required

**v3.0**:
```python
from kagura import MemoryManager

memory = MemoryManager()
await memory.store("key", "value")
```

**v4.0**:
```python
from kagura.core.memory import MemoryManager

memory = MemoryManager(user_id="alice")  # ⬅️ Required
await memory.store("key", "value")
```

**Why**: Multi-user support for remote MCP server and cloud deployment.

**Migration**:
- Add `user_id` parameter to all `MemoryManager()` calls
- Use consistent user_id across your application
- For single-user: Use any identifier (e.g., `"default"`, `"me"`)

---

### 2. Embedding Model Change

**v3.0**: `all-MiniLM-L6-v2` (English-only, 384 dimensions)
**v4.0**: `multilingual-e5-large` (100+ languages, 1024 dimensions)

**Impact**:
- ✅ Better accuracy (+40-60% precision)
- ✅ Multilingual support (Japanese, Chinese, etc.)
- ⚠️ **Requires reindexing** existing memories

**Migration**:
```bash
# Export old memories (v3.0)
kagura memory export --output=./backup-v3

# Upgrade to v4.0
pip install --upgrade kagura-ai[full]

# Import memories (will reindex automatically)
kagura memory import --input=./backup-v3
```

**Note**: First search after upgrade may be slower (embedding generation).

---

### 3. MCP Tool Name Changes

| v3.0 Tool | v4.0 Tool | Change |
|-----------|-----------|--------|
| `memory_save` | `memory_store` | Renamed |
| `memory_fetch` | `memory_recall` | Renamed |
| `memory_query` | `memory_search` | Renamed |

**Migration**: Update your MCP configurations if using specific tool names.

---

### 4. Configuration File Location (XDG Compliance)

**v3.0**:
```
~/.kagura/memory.db
~/.kagura/config.json
~/.kagura/chromadb/
```

**v4.0** (Linux/macOS):
```
~/.cache/kagura/           # Temporary/cache
~/.local/share/kagura/     # Persistent data
~/.config/kagura/          # Configuration
```

**v4.0** (Windows):
```
%LOCALAPPDATA%\kagura\cache\
%LOCALAPPDATA%\kagura\data\
%APPDATA%\kagura\
```

**Migration**:
```bash
# Auto-migration on first v4.0 run
kagura config doctor

# Manual migration (if needed)
mv ~/.kagura/memory.db ~/.local/share/kagura/
mv ~/.kagura/config.json ~/.config/kagura/
mv ~/.kagura/chromadb ~/.cache/kagura/
```

**Why**: XDG Base Directory specification for better OS integration.

---

## ✨ 新機能

### 1. GraphMemory (Knowledge Graphs)

**Not available in v3.0**. Now you can:

```python
from kagura.core.memory import MemoryManager

memory = MemoryManager(user_id="alice", enable_graph=True)

# Create relationship
await memory.link(
    src="python_tips",
    dst="fastapi_tutorial",
    rel_type="related_to"
)

# Multi-hop traversal
related = await memory.query_graph(
    seed_ids=["python_tips"],
    hops=2
)
```

**Use cases**:
- Track learning paths
- Find related memories
- Discover connections

---

### 2. Remote MCP Server

**New in v4.0**: Connect ChatGPT, custom agents via HTTP/SSE.

```bash
# Start remote MCP server
kagura api serve --host 0.0.0.0 --port 8000

# Create API key
kagura api create-key --name "chatgpt"

# Configure ChatGPT
URL: https://your-domain.com/mcp
Auth: Bearer <api-key>
```

**See**: [MCP over HTTP Setup](./mcp-http-setup.md)

---

### 3. Memory Export/Import

```bash
# Export (JSONL format)
kagura memory export --output=./backup --user-id=alice

# Import to another instance
kagura memory import --input=./backup --user-id=bob
```

**Format**: Human-readable JSONL + metadata.

---

### 4. Production Docker Setup

**v3.0**: Development only
**v4.0**: Production-ready with Caddy reverse proxy

```bash
# Production deployment
docker compose -f docker-compose.prod.yml up -d
```

**Includes**:
- PostgreSQL + pgvector
- Redis caching
- Caddy (HTTPS)
- API key authentication

---

## 🔧 ステップバイステップ移行

### Step 1: Backup v3.0 Data

```bash
# Export memories (v3.0)
kagura memory export --output=./backup-v3-$(date +%Y%m%d)

# Backup config
cp ~/.kagura/config.json ./backup-v3-config.json
```

### Step 2: Upgrade Package

```bash
# Upgrade via pip
pip install --upgrade kagura-ai[full]

# Verify version
kagura --version  # Should show v4.0.0
```

### Step 3: Update Code

**Update imports**:
```python
# v3.0
from kagura import MemoryManager

# v4.0
from kagura.core.memory import MemoryManager  # ⬅️ Changed
```

**Add user_id**:
```python
# v3.0
memory = MemoryManager()

# v4.0
memory = MemoryManager(user_id="your-user-id")  # ⬅️ Required
```

### Step 4: Run Configuration Doctor

```bash
# Auto-detect and fix issues
kagura config doctor

# Check MCP setup
kagura mcp doctor
```

### Step 5: Reindex Memories (if needed)

```bash
# Import backup (auto-reindex with new embeddings)
kagura memory import --input=./backup-v3-$(date +%Y%m%d)
```

### Step 6: Test

```python
from kagura.core.memory import MemoryManager

async def test_migration():
    memory = MemoryManager(user_id="test")

    # Test store
    await memory.store("test_key", "test_value")

    # Test recall
    results = await memory.recall("test_value", top_k=1)
    assert len(results) > 0

    print("✅ Migration successful!")

# Run test
import asyncio
asyncio.run(test_migration())
```

---

## 🆕 推奨アップデート

### 1. Enable GraphMemory

```python
memory = MemoryManager(
    user_id="alice",
    enable_graph=True  # ⬅️ Enable knowledge graph
)
```

### 2. Use New Hybrid Search

```python
# v4.0: Hybrid search (BM25 + vector)
results = await memory.recall_hybrid(
    query="Python tips",
    top_k=5,
    semantic_weight=0.5,  # Balance semantic vs lexical
    lexical_weight=0.5
)
```

### 3. Configure Remote MCP (Optional)

```bash
# For multi-platform access
kagura api create-key --name "production"
kagura api serve --host 0.0.0.0
```

---

## 🐛 トラブルシューティング

### Issue: "user_id is required"

**Error**:
```
TypeError: __init__() missing 1 required positional argument: 'user_id'
```

**Solution**:
```python
# Add user_id parameter
memory = MemoryManager(user_id="your-user-id")
```

---

### Issue: "Cannot find memories from v3.0"

**Cause**: Embedding model change requires reindexing.

**Solution**:
```bash
# Export from v3.0 backup
kagura memory import --input=./backup-v3
```

---

### Issue: "ModuleNotFoundError: No module named 'kagura.core'"

**Cause**: v3.0 imports are outdated.

**Solution**:
```python
# Update imports
from kagura.core.memory import MemoryManager  # v4.0
```

---

### Issue: "Config file not found"

**Cause**: XDG directory migration.

**Solution**:
```bash
# Auto-migrate
kagura config doctor

# Or manually move files
mkdir -p ~/.config/kagura ~/.local/share/kagura ~/.cache/kagura
mv ~/.kagura/config.json ~/.config/kagura/
mv ~/.kagura/memory.db ~/.local/share/kagura/
```

---

## 📚 追加リソース

- [v4.0 Release Notes](../CHANGELOG.md)
- [v4.0 Implementation Roadmap](../ai_docs/V4.0_IMPLEMENTATION_ROADMAP.md)
- [MCP Setup Guide](./mcp-setup.md)
- [Self-Hosting Guide](./self-hosting.md)
- [API Reference](./api-reference.md)

---

## 💬 ヘルプが必要ですか?

- 📖 **Documentation**: https://docs.kagura.ai
- 💬 **Discussions**: https://github.com/JFK/kagura-ai/discussions
- 🐛 **Bug Reports**: https://github.com/JFK/kagura-ai/issues
- 📧 **Email**: support@kagura.ai

---

## ✅ 移行チェックリスト

- [ ] Backup v3.0 data (`kagura memory export`)
- [ ] Upgrade package (`pip install --upgrade kagura-ai[full]`)
- [ ] Update imports (`from kagura.core.memory import MemoryManager`)
- [ ] Add `user_id` parameter to `MemoryManager()`
- [ ] Run `kagura config doctor`
- [ ] Import backup (`kagura memory import`)
- [ ] Test basic operations (store/recall)
- [ ] Update MCP configuration (if applicable)
- [ ] Review new features (GraphMemory, Remote MCP)
- [ ] Update documentation/README in your project

---

**Welcome to Kagura AI v4.0! 🎉**
