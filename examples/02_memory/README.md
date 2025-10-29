# 02_memory - Memory Management

This directory contains examples demonstrating Kagura AI's memory management system (RFC-018).

## Overview

Kagura AI provides a **4-tier memory architecture** (v4.0):
1. **WorkingMemory** - Short-term conversational context (Tier 1)
2. **ContextMemory** - Medium-term session memory with limits (Tier 2)
3. **PersistentMemory** - Long-term storage across sessions (Tier 3)
4. **MemoryRAG** - Semantic search with vector embeddings (Tier 4)

**Bonus**: **GraphMemory** - Relationship tracking between memories (v4.0 Phase B)

### v4.0+ Features

- **User-scoped Memory**: All memories are user-specific (via `user_id`)
- **Temperature-based Hierarchy**: Hot/Warm/Cool/Cold tiers for optimization ([see design](../../src/kagura/core/memory/README.md))
- **Export/Import**: JSONL format for backup & migration (v4.0 Phase C)
- **Knowledge Graph**: Relationship tracking with NetworkX (v4.0 Phase B)

For detailed architecture and Temperature-based hierarchy design, see: `src/kagura/core/memory/README.md`

## Memory System Architecture

```
┌─────────────────┐
│ WorkingMemory   │ ← Immediate conversation (last N messages)
└────────┬────────┘
         │
┌────────▼────────┐
│ ContextMemory   │ ← Session context (with compression)
└────────┬────────┘
         │
┌────────▼────────┐
│PersistentMemory │ ← Long-term storage (SQLite)
└────────┬────────┘
         │
┌────────▼────────┐
│  MemoryRAG      │ ← Semantic search (ChromaDB)
└─────────────────┘
```

## Examples

### 1. working_memory.py - Short-term Context
**Demonstrates:**
- Using WorkingMemory for immediate context
- Maintaining conversation history
- Automatic message rotation

```python
from kagura import agent
from kagura.core.memory import MemoryManager, WorkingMemory

memory = MemoryManager(backend=WorkingMemory())

@agent(enable_memory=True)
async def assistant(query: str, memory_manager: MemoryManager) -> str:
    """Answer {{ query }} using conversation context."""
    pass
```

**Key Concepts:**
- In-memory conversation buffer
- No persistence (lost on restart)
- Fast access, no storage overhead
- Best for: Single-session chatbots

**Use Cases:**
- Quick conversations
- Temporary context tracking
- Development/testing

---

### 2. session_memory.py - Context Memory with Limits
**Demonstrates:**
- ContextMemory with max message limits
- Automatic message trimming
- Session-based isolation

```python
from kagura.core.memory import MemoryManager, ContextMemory

memory = MemoryManager(
    backend=ContextMemory(max_messages=50),
    agent_name="chatbot"
)

@agent(enable_memory=True)
async def chatbot(message: str, memory_manager: MemoryManager) -> str:
    """Respond to: {{ message }}"""
    pass
```

**Key Concepts:**
- Configurable message limits
- Automatic compression (RFC-024)
- Session isolation by agent name
- Best for: Multi-turn conversations

**Use Cases:**
- Customer support bots
- Interactive tutorials
- Conversational interfaces

---

### 3. persistent_memory.py - Long-term Storage
**Demonstrates:**
- Persisting memory across sessions
- SQLite-based storage
- Memory recall and search

```python
from pathlib import Path
from kagura.core.memory import MemoryManager, PersistentMemory

memory = MemoryManager(
    backend=PersistentMemory(
        db_path=Path("./memory.db"),
        agent_name="assistant"
    )
)

@agent(enable_memory=True)
async def assistant(query: str, memory_manager: MemoryManager) -> str:
    """Answer {{ query }} using past conversations."""
    pass
```

**Key Concepts:**
- Persistent storage in SQLite
- Survives restarts
- Timestamped messages
- Best for: Long-term assistants

**Use Cases:**
- Personal assistants
- Project tracking
- Knowledge accumulation
- User preference learning

---

### 4. rag_memory.py - Semantic Search (RAG)
**Demonstrates:**
- MemoryRAG with vector embeddings
- Semantic similarity search
- ChromaDB integration
- Relevance-based recall

```python
from kagura.core.memory import MemoryRAG

rag = MemoryRAG(
    collection_name="knowledge_base",
    agent_name="researcher"
)

# Store information
await rag.store("Python was created by Guido van Rossum in 1991")

# Semantic search
results = await rag.recall_semantic(
    "Who created Python?",
    k=5  # Top 5 results
)
```

**Key Concepts:**
- Vector embeddings for semantic search
- ChromaDB backend
- Relevance scoring
- Best for: Knowledge retrieval

**Use Cases:**
- Document Q&A
- Knowledge bases
- Research assistants
- FAQ systems

---

## Prerequisites

```bash
# Install Kagura AI
pip install kagura-ai

# For RAG examples (optional)
pip install chromadb

# Or install all memory features
pip install kagura-ai[memory]
```

## Running Examples

```bash
# Run any example
python working_memory.py
python session_memory.py
python persistent_memory.py

# RAG example (requires chromadb)
python rag_memory.py
```

## Memory Selection Guide

| Feature | WorkingMemory | ContextMemory | PersistentMemory | MemoryRAG |
|---------|--------------|---------------|------------------|-----------|
| **Speed** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **Persistence** | ❌ No | ❌ No | ✅ Yes | ✅ Yes |
| **Semantic Search** | ❌ No | ❌ No | ❌ No | ✅ Yes |
| **Max Storage** | Limited | Configurable | Unlimited | Unlimited |
| **Best For** | Prototyping | Sessions | Long-term | Knowledge |
| **Dependencies** | None | None | None | ChromaDB |

## Common Patterns

### Pattern 1: Conversational Agent with Memory
```python
from kagura import agent
from kagura.core.memory import MemoryManager

memory = MemoryManager(agent_name="chatbot")

@agent(enable_memory=True)
async def chatbot(message: str, memory_manager: MemoryManager) -> str:
    """
    You are a helpful chatbot. Remember our conversation.

    User: {{ message }}
    """
    # Memory is automatically managed
    pass

# Conversation
await chatbot("My name is Alice", memory_manager=memory)
await chatbot("What's my name?", memory_manager=memory)  # Remembers "Alice"
```

### Pattern 2: Persistent Knowledge Base
```python
from pathlib import Path
from kagura.core.memory import MemoryManager, PersistentMemory

memory = MemoryManager(
    backend=PersistentMemory(
        db_path=Path("./knowledge.db"),
        agent_name="knowledge_agent"
    )
)

# Store facts
await memory.store("user_preference", "Alice prefers dark mode")
await memory.store("project_info", "Project deadline: Dec 31")

# Recall later (even after restart)
prefs = await memory.recall("user_preference")
```

### Pattern 3: Semantic Search with RAG
```python
from kagura.core.memory import MemoryRAG

rag = MemoryRAG(collection_name="docs", agent_name="assistant")

# Index documents
docs = [
    "Kagura AI is a Python-first AI agent framework",
    "It uses Jinja2 templates for prompts",
    "Supports OpenAI, Anthropic, and Google models"
]

for doc in docs:
    await rag.store(doc)

# Search semantically
results = await rag.recall_semantic("What templates does Kagura use?", k=3)
# Returns: "It uses Jinja2 templates for prompts"
```

### Pattern 4: Hybrid Memory (All 3 Tiers)
```python
from kagura import agent
from kagura.core.memory import MemoryManager

@agent(
    enable_memory=True,
    persist_dir=Path("./memory"),
    max_messages=100  # ContextMemory limit
)
async def smart_assistant(query: str, memory: MemoryManager) -> str:
    """
    You are a smart assistant with:
    - Short-term: Recent conversation (WorkingMemory)
    - Mid-term: Session context (ContextMemory, max 100 msgs)
    - Long-term: Knowledge base (PersistentMemory)

    Query: {{ query }}
    """
    pass
```

## Best Practices

### 1. Choose the Right Memory Type

✅ **WorkingMemory:**
- Prototyping
- Single-session apps
- No persistence needed

✅ **ContextMemory:**
- Multi-turn conversations
- Session-based apps
- Need message limits

✅ **PersistentMemory:**
- Long-running assistants
- Cross-session continuity
- User profiles

✅ **MemoryRAG:**
- Document search
- Knowledge retrieval
- Semantic matching

### 2. Set Appropriate Message Limits

```python
# ✅ Good: Reasonable limits
memory = MemoryManager(
    backend=ContextMemory(max_messages=50)  # ~10K tokens
)

# ❌ Bad: Too large, may hit context limits
memory = MemoryManager(
    backend=ContextMemory(max_messages=1000)  # Risky!
)
```

### 3. Enable Compression for Large Contexts

```python
from kagura import agent, CompressionPolicy

@agent(
    enable_memory=True,
    enable_compression=True,  # Auto-compress when near limits
    compression_policy=CompressionPolicy(
        strategy="smart",
        trigger_threshold=0.8  # Compress at 80% full
    )
)
async def assistant(query: str, memory: MemoryManager) -> str:
    """Handle {{ query }} with compression."""
    pass
```

### 4. Use Namespaces for Multi-Agent Systems

```python
# ✅ Good: Separate memory per agent
code_memory = MemoryManager(agent_name="code_reviewer")
chat_memory = MemoryManager(agent_name="chatbot")

# ❌ Bad: Shared memory (context confusion)
shared_memory = MemoryManager(agent_name="shared")  # Avoid!
```

### 5. Clean Up Old Memory

```python
# For PersistentMemory
memory = MemoryManager(backend=PersistentMemory(db_path=Path("./mem.db")))

# Delete old messages
await memory.clear()  # Clear all
await memory.clear(before_timestamp=cutoff_date)  # Clear old
```

## Memory Operations Reference

### Store Information
```python
# Add message
await memory.add_message("user", "Hello")
await memory.add_message("assistant", "Hi there!")

# Store fact
await memory.store("key", "value", metadata={"type": "fact"})
```

### Retrieve Information
```python
# Get recent messages
messages = await memory.get_messages(limit=10)

# Recall specific data
data = await memory.recall("key")

# Semantic search (RAG only)
results = await rag.recall_semantic("query", k=5)
```

### Memory Statistics
```python
stats = await memory.stats()
print(f"Total memories: {stats['total_memories']}")
print(f"Working memory size: {stats['working_memory_size']}")
```

## Advanced Features

### Context Compression (RFC-024)
Automatically compress memory when approaching limits:

```python
from kagura import CompressionPolicy

policy = CompressionPolicy(
    strategy="smart",      # or "fifo", "summary"
    max_tokens=4000,       # Target size after compression
    trigger_threshold=0.8  # Start at 80% full
)

@agent(
    enable_memory=True,
    compression_policy=policy
)
async def compressed_agent(query: str, memory: MemoryManager) -> str:
    """Answer {{ query }} with auto-compression."""
    pass
```

### Memory-Aware Routing
Route queries based on conversation history:

```python
from kagura.routing import MemoryAwareRouter

router = MemoryAwareRouter(
    memory=memory,
    context_window=5  # Use last 5 messages
)

router.register(code_agent, intents=["code", "programming"])
router.register(chat_agent, intents=["chat", "talk"])

# Route with context
await router.route("What did we discuss?")  # Context-aware
```

## Troubleshooting

### Issue: Memory not persisting
**Solution:** Check that `persist_dir` is writable and backend is PersistentMemory:
```python
memory = MemoryManager(
    backend=PersistentMemory(db_path=Path("./memory.db")),
    persist_dir=Path("./data")  # Ensure writable
)
```

### Issue: RAG search returns no results
**Solution:** Ensure documents are indexed before search:
```python
# Store first
await rag.store("Document content")

# Then search
results = await rag.recall_semantic("query", k=5)
```

### Issue: Context window exceeded
**Solution:** Enable compression or reduce max_messages:
```python
# Option 1: Compression
@agent(enable_compression=True)
async def agent(query: str, memory: MemoryManager) -> str:
    pass

# Option 2: Lower limit
memory = MemoryManager(backend=ContextMemory(max_messages=30))
```

### Issue: ChromaDB not found (for RAG)
**Solution:** Install chromadb:
```bash
pip install chromadb
# Or
pip install kagura-ai[memory]
```

## Next Steps

After mastering memory management, explore:
- [03_routing](../03_routing/) - Memory-aware routing
- [06_advanced](../06_advanced/) - Context compression
- [08_real_world](../08_real_world/) - Production memory patterns

## Documentation

- [RFC-018: Memory Management](../../ai_docs/rfcs/RFC_018_MEMORY_MANAGEMENT.md)
- [RFC-024: Context Compression](../../ai_docs/rfcs/RFC_024_CONTEXT_COMPRESSION.md)
- [API Reference - Memory](../../docs/en/api/memory.md)

---

**Start with `working_memory.py` to understand the basics, then progress to persistent and RAG-based memory!**
