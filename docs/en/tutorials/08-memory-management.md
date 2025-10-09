# Memory Management Tutorial

Learn how to build agents with memory capabilities using Kagura AI's memory management system.

## Introduction

Kagura AI provides a three-tier memory system:

1. **Working Memory**: Temporary data during execution
2. **Context Memory**: Conversation history
3. **Persistent Memory**: Long-term storage

All three are accessed through the unified `MemoryManager` interface.

## Quick Start

### Basic Memory Usage

```python
from kagura.core.memory import MemoryManager

# Create memory manager
memory = MemoryManager(agent_name="my_assistant")

# Store and recall persistent data
memory.remember("user_name", "Alice")
name = memory.recall("user_name")  # "Alice"

# Track conversation
memory.add_message("user", "Hello!")
memory.add_message("assistant", "Hi there!")

# Get conversation context
context = memory.get_llm_context()
```

### Agent with Memory

```python
from kagura import agent
from kagura.core.memory import MemoryManager

@agent(enable_memory=True)
async def greeter(name: str, memory: MemoryManager) -> str:
    """Greet {{ name }} personally"""

    # Remember this person
    memory.remember(f"greeted_{name}", True)

    # Check if we've met before
    met_before = memory.recall(f"greeted_{name}")

    if met_before:
        return f"Welcome back, {name}!"
    else:
        return f"Nice to meet you, {name}!"

# First time
result = await greeter("Alice")  # "Nice to meet you, Alice!"

# Second time
result = await greeter("Alice")  # "Welcome back, Alice!"
```

## Working Memory

Temporary storage that's cleared after execution.

### Use Cases

- Tracking loop iterations
- Storing intermediate results
- Temporary configuration

### Example

```python
from kagura.core.memory import MemoryManager

memory = MemoryManager()

# Store temporary data
memory.set_temp("retry_count", 0)
memory.set_temp("current_task", "data_processing")

# Retrieve
count = memory.get_temp("retry_count")  # 0
task = memory.get_temp("current_task")  # "data_processing"

# Check existence
if memory.has_temp("retry_count"):
    count = memory.get_temp("retry_count")
    memory.set_temp("retry_count", count + 1)

# Delete
memory.delete_temp("current_task")
```

## Context Memory

Manages conversation history with automatic pruning.

### Message Roles

- `"user"`: User messages
- `"assistant"`: Agent responses
- `"system"`: System prompts

### Basic Usage

```python
memory = MemoryManager(max_messages=100)

# Add messages
memory.add_message("user", "What is AI?")
memory.add_message("assistant", "AI stands for Artificial Intelligence...")

# Get all messages
messages = memory.get_context()

# Get last N messages
recent = memory.get_context(last_n=5)

# Get last user message
last_user = memory.get_last_message(role="user")
print(last_user.content)  # "What is AI?"
```

### LLM Integration

```python
# Get context for LLM API
llm_messages = memory.get_llm_context()

# Format: [{"role": "user", "content": "..."}, ...]
for msg in llm_messages:
    print(f"{msg['role']}: {msg['content']}")
```

### Auto-Pruning

Context memory automatically prunes old messages when exceeding the limit:

```python
memory = MemoryManager(max_messages=3)

memory.add_message("user", "Message 1")
memory.add_message("assistant", "Message 2")
memory.add_message("user", "Message 3")
# 3 messages stored

memory.add_message("assistant", "Message 4")
# Only last 3 kept: Message 2, 3, 4
```

### Metadata

Attach metadata to messages:

```python
memory.add_message(
    "assistant",
    "The answer is 42",
    metadata={
        "confidence": 0.95,
        "source": "knowledge_base",
        "timestamp": "2025-01-01T00:00:00Z"
    }
)

messages = memory.get_context()
print(messages[0].metadata["confidence"])  # 0.95
```

## Persistent Memory

Long-term storage using SQLite.

### Basic Operations

```python
from pathlib import Path

memory = MemoryManager(
    agent_name="my_agent",
    persist_dir=Path("./data")
)

# Store
memory.remember("api_key", "sk-...")
memory.remember("user_prefs", {"theme": "dark", "lang": "en"})

# Recall
api_key = memory.recall("api_key")
prefs = memory.recall("user_prefs")

# Delete
memory.forget("api_key")
```

### Search

Search using SQL LIKE patterns:

```python
# Store multiple items
memory.remember("user_name", "Alice")
memory.remember("user_email", "alice@example.com")
memory.remember("user_age", 25)
memory.remember("product_name", "Widget")

# Search for user-related items
results = memory.search_memory("user")
# Returns: user_name, user_email, user_age

for item in results:
    print(f"{item['key']}: {item['value']}")
```

### Agent Scoping

Memories can be scoped to specific agents:

```python
# Agent 1
memory1 = MemoryManager(agent_name="agent1")
memory1.remember("config", {"mode": "fast"})

# Agent 2
memory2 = MemoryManager(agent_name="agent2")
memory2.remember("config", {"mode": "accurate"})

# Each agent has separate memories
config1 = memory1.recall("config")  # {"mode": "fast"}
config2 = memory2.recall("config")  # {"mode": "accurate"}
```

### Maintenance

```python
# Prune old memories (older than 30 days)
deleted = memory.prune_old(older_than_days=30)
print(f"Deleted {deleted} old memories")

# Count memories
count = memory.persistent.count(agent_name="my_agent")
print(f"{count} memories stored")
```

## Session Management

Save and restore complete agent state.

### Saving Sessions

```python
memory = MemoryManager(agent_name="assistant")

# Have a conversation
memory.add_message("user", "What is machine learning?")
memory.add_message("assistant", "Machine learning is...")

# Store temporary data
memory.set_temp("conversation_step", 5)

# Save everything
memory.save_session("ml_discussion")
```

### Loading Sessions

```python
# Later... create new memory manager
new_memory = MemoryManager(agent_name="assistant")

# Restore session
if new_memory.load_session("ml_discussion"):
    print("Session restored!")

    # Context is restored
    messages = new_memory.get_context()
    print(f"Restored {len(messages)} messages")

    # Session ID is restored
    session_id = new_memory.get_session_id()
else:
    print("Session not found")
```

## Agent Integration

### Enable Memory

Use `enable_memory=True` in the `@agent` decorator:

```python
from kagura import agent
from kagura.core.memory import MemoryManager

@agent(enable_memory=True)
async def chatbot(message: str, memory: MemoryManager) -> str:
    """Chat: {{ message }}"""

    # Memory is automatically injected
    memory.add_message("user", message)

    # Use memory for personalization
    user_name = memory.recall("user_name")
    if user_name:
        response = f"Hello {user_name}! You said: {message}"
    else:
        response = f"Hello! You said: {message}"

    memory.add_message("assistant", response)
    return response
```

### Custom Configuration

```python
from pathlib import Path

@agent(
    enable_memory=True,
    persist_dir=Path("./agent_data"),
    max_messages=50
)
async def my_agent(query: str, memory: MemoryManager) -> str:
    """Process: {{ query }}"""
    # Custom persist directory and message limit
    pass
```

## Practical Examples

### Personal Assistant

```python
@agent(enable_memory=True)
async def personal_assistant(query: str, memory: MemoryManager) -> str:
    """Answer: {{ query }}"""

    memory.add_message("user", query)

    # Learn user preferences
    if "my favorite color is" in query.lower():
        color = query.split("my favorite color is")[-1].strip()
        memory.remember("favorite_color", color)

    if "my name is" in query.lower():
        name = query.split("my name is")[-1].strip()
        memory.remember("user_name", name)

    # Use learned information
    name = memory.recall("user_name") or "there"
    fav_color = memory.recall("favorite_color") or "unknown"

    response = f"Hi {name}! Your favorite color is {fav_color}."
    memory.add_message("assistant", response)

    return response

# Usage
await personal_assistant("Hi, my name is Alice")
await personal_assistant("my favorite color is blue")
await personal_assistant("what's my name?")
# "Hi Alice! Your favorite color is blue."
```

### Multi-Turn Conversation

```python
@agent(enable_memory=True, max_messages=20)
async def conversational_agent(query: str, memory: MemoryManager) -> str:
    """Continue conversation: {{ query }}

    Previous context:
    {% for msg in context %}
    {{ msg.role }}: {{ msg.content }}
    {% endfor %}
    """

    # Get recent context for prompt
    context = memory.get_context(last_n=5)

    # Add current message
    memory.add_message("user", query)

    # Response would come from LLM
    response = "..."  # LLM processes with full context

    memory.add_message("assistant", response)
    return response
```

### Task Tracker

```python
@agent(enable_memory=True)
async def task_tracker(command: str, memory: MemoryManager) -> str:
    """Manage tasks: {{ command }}"""

    if command.startswith("add"):
        task = command[4:].strip()
        tasks = memory.recall("tasks") or []
        tasks.append(task)
        memory.remember("tasks", tasks)
        return f"Added task: {task}"

    elif command == "list":
        tasks = memory.recall("tasks") or []
        if not tasks:
            return "No tasks"
        return "Tasks:\n" + "\n".join(f"- {t}" for t in tasks)

    elif command.startswith("done"):
        task = command[5:].strip()
        tasks = memory.recall("tasks") or []
        if task in tasks:
            tasks.remove(task)
            memory.remember("tasks", tasks)
            return f"Completed: {task}"
        return "Task not found"

    return "Unknown command"

# Usage
await task_tracker("add Write documentation")
await task_tracker("add Review code")
await task_tracker("list")
# "Tasks:\n- Write documentation\n- Review code"
await task_tracker("done Write documentation")
```

## Best Practices

### 1. Use Appropriate Memory Types

- **Working Memory**: Temporary state, loop counters, intermediate results
- **Context Memory**: Conversation history, user interactions
- **Persistent Memory**: User preferences, learned facts, configuration

### 2. Set Reasonable Limits

```python
# For chat applications
memory = MemoryManager(max_messages=50)  # Keep last 50 messages

# For long-running agents
memory = MemoryManager(max_messages=200)  # More context
```

### 3. Clean Up Old Data

```python
# Periodically prune old memories
if datetime.now().day == 1:  # First day of month
    deleted = memory.prune_old(older_than_days=90)
    print(f"Pruned {deleted} old memories")
```

### 4. Use Agent Scoping

```python
# Separate memories for different agents
translator = MemoryManager(agent_name="translator")
summarizer = MemoryManager(agent_name="summarizer")
```

### 5. Add Metadata

```python
memory.remember(
    "api_key",
    "sk-...",
    metadata={
        "created": "2025-01-01",
        "expires": "2026-01-01",
        "environment": "production"
    }
)
```

## Troubleshooting

### Memory Not Persisting

Ensure `persist_dir` exists:

```python
from pathlib import Path

persist_dir = Path("./data")
persist_dir.mkdir(exist_ok=True)

memory = MemoryManager(persist_dir=persist_dir)
```

### Context Too Large

Reduce `max_messages`:

```python
memory = MemoryManager(max_messages=20)
```

### Agent-Specific Memories

Always use `agent_name`:

```python
memory = MemoryManager(agent_name="my_unique_agent")
```

## Next Steps

- [Memory Management API Reference](../api/memory.md)
- [Code Execution Tutorial](./04-code-execution.md)
- [Shell Integration Tutorial](./07-shell-integration.md)
