# Memory-Aware Routing Examples

This directory contains examples demonstrating Kagura's memory-aware routing capabilities for context-sensitive agent selection and semantic understanding.

## Overview

Memory-aware routing enhances agent routing by:
- **Conversation Context**: Maintaining chat history for context-dependent queries
- **Pronoun Resolution**: Understanding references like "it", "that", "them"
- **Semantic Search (RAG)**: Vector-based similarity matching for better intent understanding
- **Context Enhancement**: Enriching queries with relevant past information

## Examples

### 1. Context-Aware Routing (`context_routing.py`)

Demonstrates routing that maintains conversation context:
- Basic intent-based routing
- Context-dependent query handling
- Multi-turn conversations
- Pronoun resolution
- Context window management
- Context persistence

**Run:**
```bash
python examples/memory_routing/context_routing.py
```

**Key Concepts:**
```python
from kagura.routing import MemoryAwareRouter
from kagura.core.memory import MemoryManager

# Initialize with memory
memory = MemoryManager(agent_name="demo")
router = MemoryAwareRouter(memory=memory, context_window=5)

# Register agents
router.register(translator, intents=["translate"])
router.register(calculator, intents=["calculate"])

# First query
await router.route("Translate 'hello' to French")

# Follow-up with context
await router.route("What about Spanish?")
# Router understands this refers to translation
```

---

### 2. Semantic Routing with RAG (`semantic_routing.py`)

Shows semantic understanding through vector similarity:
- Building knowledge bases
- Semantic query matching
- RAG-enhanced context
- Topic clustering
- Cross-domain linking
- Memory management

**Run:**
```bash
python examples/memory_routing/semantic_routing.py
```

**Requirements:**
```bash
pip install chromadb
```

**Key Concepts:**
```python
# Enable RAG
memory = MemoryManager(
    agent_name="semantic_demo",
    enable_rag=True
)

router = MemoryAwareRouter(memory=memory)

# Build knowledge base
memory.rag.store("Python is great for ML")
memory.rag.store("JavaScript powers the web")

# Semantic query matching
await router.route("What's good for machine learning?")
# Router uses semantic similarity to find Python
```

---

## MemoryAwareRouter API

### Initialization

```python
from kagura.routing import MemoryAwareRouter
from kagura.core.memory import MemoryManager

# Basic setup
memory = MemoryManager(agent_name="router")
router = MemoryAwareRouter(
    memory=memory,
    context_window=5  # Number of messages to keep in context
)

# With RAG enabled
memory = MemoryManager(agent_name="router", enable_rag=True)
router = MemoryAwareRouter(memory=memory, context_window=10)
```

### Registering Agents

```python
# Register with intents
router.register(translator, intents=["translate", "translation"])
router.register(calculator, intents=["calculate", "math", "compute"])
router.register(fallback_agent, intents=["general"])

# Multiple agents can share intents
router.register(python_expert, intents=["python", "programming"])
router.register(js_expert, intents=["javascript", "programming"])
```

### Routing Queries

```python
# Basic routing
result = await router.route("Translate 'hello' to French")

# Context-dependent routing
await router.route("Translate 'hello' to French")
result = await router.route("What about Spanish?")
# Router understands "What about Spanish?" means translation

# With metadata
result = await router.route(
    "Calculate 2 + 2",
    metadata={"user_id": "123"}
)
```

---

## Context-Aware Patterns

### Pattern 1: Follow-up Questions

```python
# First query establishes context
await router.route("What is machine learning?")

# Follow-up leverages context
await router.route("Can you explain it in simpler terms?")
# Router knows "it" refers to machine learning
```

### Pattern 2: Multi-step Tasks

```python
# Step 1: Start calculation
await router.route("Calculate 100 + 50")

# Step 2: Continue with result
await router.route("Multiply that by 2")

# Step 3: Further operations
await router.route("What about dividing by 3?")
# All steps maintain context
```

### Pattern 3: Pronoun Resolution

```python
# Establish subject
await router.route("Tell me about Docker")

# Pronouns automatically resolved
await router.route("What is it used for?")  # "it" = Docker
await router.route("How do I install it?")  # "it" = Docker
await router.route("Show me examples")      # Understands "examples" = Docker examples
```

### Pattern 4: Context Switching

```python
# Context 1: Translation
await router.route("Translate 'hello' to French")
await router.route("What about Spanish?")  # Translation context

# Context 2: Calculation (explicit switch)
await router.route("Calculate 2 + 2")  # New context

# Context 3: Back to translation (explicit)
await router.route("Translate 'goodbye' to German")
```

---

## Semantic Routing Patterns

### Pattern 1: Knowledge Base Building

```python
# Store domain knowledge
memory.rag.store("Python is excellent for data science")
memory.rag.store("JavaScript is the web's programming language")
memory.rag.store("Rust focuses on memory safety and performance")

# Query semantically
await router.route("What language should I use for web development?")
# Semantically matches JavaScript
```

### Pattern 2: Semantic Similarity Matching

```python
# Store specific knowledge
memory.rag.store("Docker containers simplify deployment")

# Query with different wording
await router.route("Tell me about containerization")
# Semantically similar to Docker, routes appropriately
```

### Pattern 3: Topic Clustering

```python
# Store related facts
memory.rag.store("NumPy handles numerical computing in Python")
memory.rag.store("Pandas simplifies data manipulation in Python")
memory.rag.store("Matplotlib creates visualizations in Python")

# Query retrieves cluster
await router.route("What tools are good for data analysis?")
# RAG retrieves all related Python data science tools
```

### Pattern 4: Cross-Domain Knowledge

```python
# Store cross-domain facts
memory.rag.store("Python applications can be containerized with Docker")
memory.rag.store("FastAPI is a modern Python web framework")
memory.rag.store("Docker works well with CI/CD pipelines")

# Complex query
await router.route("How do I deploy a Python web app?")
# Router leverages knowledge from Python, Docker, and DevOps
```

---

## Configuration Options

### Context Window Size

```python
# Small context (last 3 messages)
router = MemoryAwareRouter(memory=memory, context_window=3)
# Good for: Simple Q&A, low memory usage

# Medium context (last 10 messages)
router = MemoryAwareRouter(memory=memory, context_window=10)
# Good for: Most conversations

# Large context (last 50 messages)
router = MemoryAwareRouter(memory=memory, context_window=50)
# Good for: Long conversations, complex context
```

### RAG Configuration

```python
# RAG disabled (default)
memory = MemoryManager(agent_name="router")
# Uses only conversation history

# RAG enabled
memory = MemoryManager(agent_name="router", enable_rag=True)
# Uses conversation history + semantic search

# Custom RAG settings
from kagura.core.memory import MemoryRAG

rag = MemoryRAG(
    collection_name="my_knowledge",
    persist_dir=Path("./my_vector_db")
)

memory = MemoryManager(agent_name="router")
memory.rag = rag
```

### Memory Persistence

```python
# Persistent memory
memory = MemoryManager(
    agent_name="router",
    persist_dir=Path.home() / ".my_app" / "memory",
    enable_rag=True
)

router = MemoryAwareRouter(memory=memory)

# Save session
memory.save_session("user_123_session")

# Later... load session
new_memory = MemoryManager(agent_name="router", enable_rag=True)
new_memory.load_session("user_123_session")
```

---

## Context Enhancement

### How Context Enhancement Works

```python
# Two-stage enhancement:

# Stage 1: Conversation History
# - Last N messages from context window
# - Provides recent conversation flow

# Stage 2: Semantic Context (if RAG enabled)
# - Vector similarity search
# - Retrieves relevant past information
# - Enhances understanding

# Example:
query = "What about Python?"

# Enhanced query sent to router:
"""
Previous context:
  User: What's good for data science?
  Assistant: Python is excellent for data science

Semantic context (RAG):
  - Python is great for machine learning
  - NumPy and Pandas are essential Python libraries

Current query: What about Python?
"""
```

### Manual Context Enhancement

```python
# Access context analyzer
from kagura.routing import ContextAnalyzer

analyzer = ContextAnalyzer()

# Check if query needs context
needs_context = analyzer.needs_context_enhancement(
    query="What about it?",
    conversation_history=memory.get_context()
)

if needs_context:
    print("Query will be enhanced with context")
```

---

## Best Practices

### 1. Choose Appropriate Context Window

```python
# Short conversations: 3-5 messages
router = MemoryAwareRouter(memory=memory, context_window=3)

# Medium conversations: 10-20 messages
router = MemoryAwareRouter(memory=memory, context_window=10)

# Long conversations: 30-50 messages
router = MemoryAwareRouter(memory=memory, context_window=30)
```

### 2. Use RAG for Knowledge-Heavy Domains

```python
# Enable RAG when:
# - Building knowledge bases
# - Need semantic understanding
# - Cross-referencing past information
# - Topic clustering required

memory = MemoryManager(agent_name="kb", enable_rag=True)
```

### 3. Clear Context When Appropriate

```python
# Clear for new conversation
memory.clear_all()

# Clear for new user
memory = MemoryManager(agent_name=f"user_{user_id}")
```

### 4. Provide Clear Intents

```python
# Good: Specific, distinct intents
router.register(translator, intents=["translate", "translation"])
router.register(calculator, intents=["calculate", "math", "compute"])

# Avoid: Overlapping intents
# router.register(agent1, intents=["help", "info"])
# router.register(agent2, intents=["help", "assist"])  # "help" conflicts
```

### 5. Monitor Context Usage

```python
# Check context size
context = memory.get_context()
print(f"Context messages: {len(context)}")

# Check RAG memory
if memory.rag:
    print(f"Semantic memories: {memory.rag.count()}")
```

---

## Troubleshooting

### Issue: Router doesn't understand follow-up questions

**Solution:**
```python
# Increase context window
router = MemoryAwareRouter(memory=memory, context_window=10)  # Was 3

# Enable RAG for better semantic understanding
memory = MemoryManager(agent_name="router", enable_rag=True)
```

### Issue: Slow routing with large context

**Solution:**
```python
# Reduce context window
router = MemoryAwareRouter(memory=memory, context_window=5)

# Or clear old context periodically
if len(memory.get_context()) > 100:
    memory.clear_all()
```

### Issue: RAG not finding relevant memories

**Solution:**
```python
# Check memory count
print(f"Memories: {memory.rag.count()}")

# Verify storage
memory.rag.store("Test knowledge")
results = memory.rag.recall("Test", top_k=1)
print(results)

# Increase top_k for recall
results = memory.rag.recall(query, top_k=10)  # Was 5
```

---

## API Reference

For complete API documentation, see:
- [Routing API Reference](../../docs/en/api/routing.md)
- [Memory API Reference](../../docs/en/api/memory.md)

## Related Examples

- [AgentBuilder Examples](../agent_builder/) - Creating routable agents
- [Advanced Workflows](../advanced_workflows/) - Routing in workflows

---

**Note:** RAG features require ChromaDB: `pip install chromadb`
