# Memory Management API

Kagura AI provides a comprehensive memory management system for building agents with persistent knowledge and context awareness.

## Overview

The memory system consists of four main components:

- **WorkingMemory**: Temporary storage during agent execution
- **ContextMemory**: Conversation history and session management
- **PersistentMemory**: Long-term storage using SQLite
- **MemoryManager**: Unified interface to all memory types

## MemoryManager

The main interface for memory operations.

### Constructor

```python
MemoryManager(
    agent_name: Optional[str] = None,
    persist_dir: Optional[Path] = None,
    max_messages: int = 100,
    enable_rag: Optional[bool] = None
)
```

**Parameters:**

- `agent_name`: Optional agent name for scoping persistent memory
- `persist_dir`: Directory for persistent storage (default: `~/.kagura`)
- `max_messages`: Maximum messages to keep in context
- `enable_rag`: Enable RAG (semantic search) with ChromaDB
  - `None` (default): Auto-detect - enables if chromadb is available
  - `True`: Explicitly enable RAG (requires chromadb)
  - `False`: Explicitly disable RAG

### Working Memory Methods

Temporary storage that's cleared when agent execution completes.

#### set_temp

```python
manager.set_temp(key: str, value: Any) -> None
```

Store temporary data.

**Example:**

```python
manager.set_temp("current_task", "summarization")
manager.set_temp("retry_count", 3)
```

#### get_temp

```python
manager.get_temp(key: str, default: Any = None) -> Any
```

Retrieve temporary data.

**Example:**

```python
task = manager.get_temp("current_task")  # Returns "summarization"
count = manager.get_temp("retry_count", 0)  # Returns 3
missing = manager.get_temp("nonexistent", "default")  # Returns "default"
```

#### has_temp

```python
manager.has_temp(key: str) -> bool
```

Check if temporary key exists.

#### delete_temp

```python
manager.delete_temp(key: str) -> None
```

Delete temporary data.

### Context Memory Methods

Manages conversation history with automatic pruning.

#### add_message

```python
manager.add_message(
    role: str,
    content: str,
    metadata: Optional[dict] = None
) -> None
```

Add message to conversation context.

**Parameters:**

- `role`: Message role (`"user"`, `"assistant"`, `"system"`)
- `content`: Message content
- `metadata`: Optional metadata dictionary

**Example:**

```python
manager.add_message("user", "What is machine learning?")
manager.add_message(
    "assistant",
    "Machine learning is...",
    metadata={"confidence": 0.95}
)
```

#### get_context

```python
manager.get_context(last_n: Optional[int] = None) -> list[Message]
```

Get conversation context as Message objects.

**Example:**

```python
# Get all messages
all_messages = manager.get_context()

# Get last 5 messages
recent = manager.get_context(last_n=5)
```

#### get_llm_context

```python
manager.get_llm_context(last_n: Optional[int] = None) -> list[dict]
```

Get context formatted for LLM API.

**Returns:** List of `{"role": str, "content": str}` dictionaries.

**Example:**

```python
context = manager.get_llm_context(last_n=10)
# [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
```

#### get_last_message

```python
manager.get_last_message(role: Optional[str] = None) -> Optional[Message]
```

Get the last message, optionally filtered by role.

**Example:**

```python
last_msg = manager.get_last_message()
last_user_msg = manager.get_last_message(role="user")
```

#### set_session_id / get_session_id

```python
manager.set_session_id(session_id: str) -> None
manager.get_session_id() -> Optional[str]
```

Manage session identifiers.

### Persistent Memory Methods

Long-term storage using SQLite with optional agent scoping.

#### remember

```python
manager.remember(
    key: str,
    value: Any,
    metadata: Optional[dict] = None
) -> None
```

Store persistent memory.

**Example:**

```python
manager.remember("user_preferences", {
    "theme": "dark",
    "language": "en"
})

manager.remember(
    "api_key",
    "sk-...",
    metadata={"created": "2025-01-01"}
)
```

#### recall

```python
manager.recall(key: str) -> Optional[Any]
```

Retrieve persistent memory.

**Example:**

```python
prefs = manager.recall("user_preferences")
api_key = manager.recall("api_key")
```

#### search_memory

```python
manager.search_memory(query: str, limit: int = 10) -> list[dict]
```

Search persistent memory using SQL LIKE pattern.

**Example:**

```python
# Find all user-related memories
results = manager.search_memory("user")

# Each result contains: key, value, created_at, updated_at, metadata
for mem in results:
    print(f"{mem['key']}: {mem['value']}")
```

#### forget

```python
manager.forget(key: str) -> None
```

Delete persistent memory.

**Example:**

```python
manager.forget("api_key")
```

#### prune_old

```python
manager.prune_old(older_than_days: int = 90) -> int
```

Remove old memories.

**Returns:** Number of deleted memories.

**Example:**

```python
# Delete memories older than 30 days
deleted = manager.prune_old(older_than_days=30)
print(f"Deleted {deleted} old memories")
```

### Session Management

#### save_session

```python
manager.save_session(session_name: str) -> None
```

Save current session (working + context memory) to persistent storage.

**Example:**

```python
manager.add_message("user", "Hello")
manager.set_temp("step", 1)
manager.save_session("my_session")
```

#### load_session

```python
manager.load_session(session_name: str) -> bool
```

Load saved session.

**Returns:** `True` if session was loaded successfully.

**Example:**

```python
if manager.load_session("my_session"):
    print("Session restored")
    messages = manager.get_context()
```

#### clear_all

```python
manager.clear_all() -> None
```

Clear all temporary and context memory (does not clear persistent memory).

**Example:**

```python
manager.clear_all()
```

## Message Class

Represents a single message in conversation context.

### Attributes

```python
@dataclass
class Message:
    role: str              # "user", "assistant", "system"
    content: str           # Message content
    timestamp: datetime    # When message was created
    metadata: Optional[dict] = None  # Optional metadata
```

### Methods

#### to_dict

```python
message.to_dict() -> dict
```

Convert to dictionary representation.

## WorkingMemory

Direct access to working memory (also available via `MemoryManager.working`).

### Methods

- `set(key: str, value: Any) -> None`
- `get(key: str, default: Any = None) -> Any`
- `has(key: str) -> bool`
- `delete(key: str) -> None`
- `clear() -> None`
- `keys() -> list[str]`
- `to_dict() -> dict`

## ContextMemory

Direct access to context memory (also available via `MemoryManager.context`).

### Methods

- `add_message(role: str, content: str, metadata: Optional[dict] = None) -> None`
- `get_messages(last_n: Optional[int] = None, role: Optional[str] = None) -> list[Message]`
- `get_last_message(role: Optional[str] = None) -> Optional[Message]`
- `clear() -> None`
- `set_session_id(session_id: str) -> None`
- `get_session_id() -> Optional[str]`
- `to_llm_format(last_n: Optional[int] = None) -> list[dict]`
- `to_dict() -> dict`

## PersistentMemory

Direct access to persistent memory (also available via `MemoryManager.persistent`).

### Methods

- `store(key: str, value: Any, agent_name: Optional[str] = None, metadata: Optional[dict] = None) -> None`
- `recall(key: str, agent_name: Optional[str] = None) -> Optional[Any]`
- `search(query: str, agent_name: Optional[str] = None, limit: int = 10) -> list[dict]`
- `forget(key: str, agent_name: Optional[str] = None) -> None`
- `prune(older_than_days: int = 90, agent_name: Optional[str] = None) -> int`
- `count(agent_name: Optional[str] = None) -> int`

## MemoryRAG

Vector-based semantic memory search using ChromaDB for Retrieval-Augmented Generation (RAG).

### Constructor

```python
from kagura.core.memory import MemoryRAG

rag = MemoryRAG(
    collection_name: str = "kagura_memory",
    persist_dir: Optional[Path] = None
)
```

**Parameters:**

- `collection_name`: Name for the vector collection (default: `"kagura_memory"`)
- `persist_dir`: Directory for persistent storage (default: `~/.kagura/vector_db`)

**Requires:** `pip install chromadb`

**Example:**

```python
from pathlib import Path
from kagura.core.memory import MemoryRAG

# Default location
rag = MemoryRAG()

# Custom location
rag = MemoryRAG(
    collection_name="my_agent_memory",
    persist_dir=Path.home() / ".myapp" / "vectors"
)
```

### store()

Store memory with automatic embedding.

```python
rag.store(
    content: str,
    metadata: Optional[dict[str, Any]] = None,
    agent_name: Optional[str] = None
) -> str
```

**Parameters:**

- `content`: Content to store (will be automatically embedded)
- `metadata`: Optional metadata dictionary
- `agent_name`: Optional agent name for scoping

**Returns:** Content hash (unique ID)

**Example:**

```python
# Store facts
rag.store("Python is a programming language created by Guido van Rossum")
rag.store("The Eiffel Tower is in Paris, France")

# With metadata
rag.store(
    "User prefers dark mode",
    metadata={"category": "preference", "user_id": "123"},
    agent_name="assistant"
)
```

### recall()

Semantic search for memories using vector similarity.

```python
rag.recall(
    query: str,
    top_k: int = 5,
    agent_name: Optional[str] = None
) -> list[dict[str, Any]]
```

**Parameters:**

- `query`: Search query (will be embedded automatically)
- `top_k`: Number of results to return (sorted by similarity)
- `agent_name`: Optional agent name filter

**Returns:** List of memory dictionaries containing:
- `content` (`str`): Original memory text
- `distance` (`float`): Cosine distance (lower = more similar, range 0.0-2.0)
- `metadata` (`dict`): Optional metadata

**Example:**

```python
# Store knowledge
rag.store("Python is a programming language")
rag.store("Java is a programming language")
rag.store("The Eiffel Tower is in Paris")

# Semantic search
results = rag.recall("What is Python?", top_k=2)

for result in results:
    print(f"Content: {result['content']}")
    print(f"Distance: {result['distance']:.3f}")  # e.g., 0.342
    print(f"Metadata: {result.get('metadata')}")
```

### delete_all()

Delete all memories.

```python
rag.delete_all(agent_name: Optional[str] = None) -> None
```

**Parameters:**

- `agent_name`: Optional agent name filter (deletes only that agent's memories)

**Example:**

```python
# Delete all memories
rag.delete_all()

# Delete only specific agent's memories
rag.delete_all(agent_name="assistant")
```

### count()

Count stored memories.

```python
rag.count(agent_name: Optional[str] = None) -> int
```

**Parameters:**

- `agent_name`: Optional agent name filter

**Returns:** Number of memories

**Example:**

```python
total = rag.count()
print(f"Total memories: {total}")

agent_memories = rag.count(agent_name="assistant")
print(f"Assistant memories: {agent_memories}")
```

### MemoryManager Integration

RAG is automatically enabled in MemoryManager when chromadb is available:

```python
from kagura.core.memory import MemoryManager

# Auto-detect (enables RAG if chromadb is installed)
memory = MemoryManager(agent_name="my_agent")

# Explicitly enable RAG
memory = MemoryManager(
    agent_name="my_agent",
    enable_rag=True  # Requires chromadb
)

# Explicitly disable RAG
memory = MemoryManager(
    agent_name="my_agent",
    enable_rag=False  # No RAG, even if chromadb is available
)

# Store semantically (works if RAG is enabled)
if memory.rag:
    memory.store_semantic("Python is great for AI development")

# Semantic recall
results = memory.recall_semantic("Tell me about Python", top_k=3)
for result in results:
    print(result['content'])
```

**Note:** When RAG is enabled (auto-detected or explicitly set to `True`), MemoryManager provides both working and persistent RAG capabilities for semantic retrieval.

### Complete RAG Example

```python
from kagura.core.memory import MemoryRAG

# Initialize
rag = MemoryRAG(collection_name="knowledge_base")

# Store domain knowledge
rag.store("Machine learning is a subset of artificial intelligence")
rag.store("Deep learning uses neural networks with multiple layers")
rag.store("Natural language processing deals with text and speech")
rag.store("Computer vision focuses on image and video analysis")

# Semantic search
query = "What is deep learning?"
results = rag.recall(query, top_k=2)

print(f"Query: {query}\n")
for i, result in enumerate(results, 1):
    print(f"{i}. {result['content']}")
    print(f"   Similarity: {1 - result['distance']/2:.2%}\n")

# Output:
# Query: What is deep learning?
#
# 1. Deep learning uses neural networks with multiple layers
#    Similarity: 89%
#
# 2. Machine learning is a subset of artificial intelligence
#    Similarity: 72%
```

### RAG with Agent Integration

```python
from kagura import agent
from kagura.core.memory import MemoryManager

@agent(enable_memory=True)
async def knowledge_agent(query: str, memory: MemoryManager) -> str:
    """Answer {{ query }} using semantic memory"""

    # Store query in RAG (if RAG enabled in MemoryManager)
    memory.add_message("user", query)

    # Semantic search over past conversations
    if memory.rag:
        relevant = memory.recall_semantic(query, top_k=3)
        context = "\n".join([r['content'] for r in relevant])
        enriched_query = f"Context: {context}\n\nQuery: {query}"
        # Use enriched_query for LLM call
    else:
        enriched_query = query

    # Process with LLM...
    response = f"Processing: {enriched_query}"
    memory.add_message("assistant", response)

    return response
```

### Best Practices

1. **Meaningful Content**: Store complete, self-contained information
   ```python
   # Good
   rag.store("The capital of France is Paris")

   # Less good (lacks context)
   rag.store("Paris")
   ```

2. **Use Metadata for Filtering**:
   ```python
   rag.store("User prefers Python", metadata={"type": "preference"})
   rag.store("Project deadline is March 1", metadata={"type": "deadline"})
   ```

3. **Agent Scoping**:
   ```python
   # Separate knowledge per agent
   rag.store("Translation context", agent_name="translator")
   rag.store("Code review context", agent_name="reviewer")

   # Query specific agent's knowledge
   results = rag.recall("translate", agent_name="translator")
   ```

4. **Semantic vs Keyword Search**:
   ```python
   # Semantic search - finds conceptually similar content
   rag.recall("programming languages")  # Finds "Python", "Java", etc.

   # Keyword search would miss variations
   memory.search_memory("programming language")  # Exact match only
   ```

## Agent Integration

Enable memory in agents using the `enable_memory` parameter:

```python
from kagura import agent
from kagura.core.memory import MemoryManager

@agent(enable_memory=True, max_messages=50)
async def my_agent(query: str, memory: MemoryManager) -> str:
    """Answer {{ query }} using memory"""

    # Add to context
    memory.add_message("user", query)

    # Remember facts
    memory.remember("last_query", query)

    # Recall past information
    past = memory.recall("user_name")

    response = f"Processing {query}"
    memory.add_message("assistant", response)

    return response
```

### Parameters

- `enable_memory`: Enable memory management (default: `False`)
- `persist_dir`: Custom directory for persistent storage
- `max_messages`: Maximum messages in context (default: 100)

## Examples

### Basic Usage

```python
from kagura.core.memory import MemoryManager

# Create manager
memory = MemoryManager(agent_name="my_agent")

# Store and recall
memory.remember("api_key", "sk-...")
api_key = memory.recall("api_key")

# Conversation context
memory.add_message("user", "Hello")
memory.add_message("assistant", "Hi there!")
context = memory.get_llm_context()

# Search
results = memory.search_memory("api")
```

### Session Persistence

```python
# Save session
memory.add_message("user", "What is AI?")
memory.add_message("assistant", "AI stands for...")
memory.save_session("conversation_1")

# Later... restore session
new_memory = MemoryManager(agent_name="my_agent")
if new_memory.load_session("conversation_1"):
    messages = new_memory.get_context()
    print(f"Restored {len(messages)} messages")
```

### Agent with Memory

```python
@agent(enable_memory=True, persist_dir=Path("./data"))
async def assistant(query: str, memory: MemoryManager) -> str:
    """Personal assistant: {{ query }}"""

    # Track conversation
    memory.add_message("user", query)

    # Remember user preferences
    if "my name is" in query.lower():
        name = query.split("my name is")[-1].strip()
        memory.remember("user_name", name)

    # Use remembered information
    user_name = memory.recall("user_name") or "there"
    response = f"Hello {user_name}! How can I help?"

    memory.add_message("assistant", response)
    return response

# Usage
result = await assistant("Hello, my name is Alice")
# "Hello Alice! How can I help?"

result = await assistant("What's the weather?")
# "Hello Alice! How can I help?" (remembers name)
```

## See Also

- [Memory Management Tutorial](../tutorials/08-memory-management.md)
- [@agent Decorator API](./agent.md)
- [Code Execution API](./executor.md)
