# Chat API Reference

API documentation for the Kagura Chat REPL system.

## ChatSession

The main class for managing interactive chat sessions.

### Constructor

```python
from kagura.chat import ChatSession

session = ChatSession(
    model="gpt-4o-mini",
    session_dir=None
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | `str` | `"gpt-4o-mini"` | LLM model to use for chat |
| `session_dir` | `Path \| None` | `~/.kagura/sessions` | Directory for session storage |

### Methods

#### `run()`

Start the interactive chat loop.

```python
async def run() -> None
```

**Example:**

```python
session = ChatSession()
await session.run()
```

---

#### `chat(user_input)`

Handle a single chat interaction.

```python
async def chat(user_input: str) -> None
```

**Parameters:**

- `user_input` (`str`): User message

**Example:**

```python
await session.chat("What is Python?")
```

---

#### `save_session(name)`

Save the current conversation session.

```python
async def save_session(name: str = "") -> None
```

**Parameters:**

- `name` (`str`, optional): Session name. If empty, uses timestamp.

**Example:**

```python
# Save with custom name
await session.save_session("my_session")

# Save with auto-generated name
await session.save_session()
```

---

#### `load_session(name)`

Load a previously saved session.

```python
async def load_session(name: str) -> None
```

**Parameters:**

- `name` (`str`): Session name to load

**Example:**

```python
await session.load_session("my_session")
```

---

#### `clear_history()`

Clear the conversation history.

```python
def clear_history() -> None
```

**Example:**

```python
session.clear_history()
```

---

#### `show_welcome()`

Display the welcome message.

```python
def show_welcome() -> None
```

---

#### `show_help()`

Display the help message.

```python
def show_help() -> None
```

---

### Preset Commands

#### `preset_translate(args)`

Translate text using the built-in translation agent.

```python
async def preset_translate(args: str) -> None
```

**Parameters:**

- `args` (`str`): Translation arguments in format: `"text [to language]"`

**Example:**

```python
await session.preset_translate("Hello to ja")
await session.preset_translate("Bonjour to en")
```

---

#### `preset_summarize(args)`

Summarize text using the built-in summarization agent.

```python
async def preset_summarize(args: str) -> None
```

**Parameters:**

- `args` (`str`): Text to summarize

**Example:**

```python
await session.preset_summarize("Long text here...")
```

---

#### `preset_review(args)`

Review code using the built-in code review agent.

```python
async def preset_review(args: str) -> None
```

**Parameters:**

- `args` (`str`): Code to review (or empty to prompt for input)

**Example:**

```python
code = """
def divide(a, b):
    return a / b
"""
await session.preset_review(code)
```

---

## Preset Agents

### TranslateAgent

Translate text to a target language.

```python
from kagura.chat import TranslateAgent

result = await TranslateAgent(
    text="Hello World",
    target_language="ja"
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `text` | `str` | - | Text to translate |
| `target_language` | `str` | `"ja"` | Target language code |

**Returns:** `str` - Translated text

**Example:**

```python
# Translate to Japanese (default)
result = await TranslateAgent("Good morning")
# Output: "おはようございます"

# Translate to Spanish
result = await TranslateAgent("Hello", target_language="es")
# Output: "Hola"

# Translate to French
result = await TranslateAgent("Thank you", target_language="fr")
# Output: "Merci"
```

---

### SummarizeAgent

Summarize long text into a concise summary.

```python
from kagura.chat import SummarizeAgent

result = await SummarizeAgent(
    text="Long text here...",
    max_sentences=3
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `text` | `str` | - | Text to summarize |
| `max_sentences` | `int` | `3` | Maximum sentences in summary |

**Returns:** `str` - Summarized text

**Example:**

```python
long_text = """
Artificial intelligence (AI) is intelligence demonstrated by machines,
as opposed to natural intelligence displayed by animals including humans.
AI research has been defined as the field of study of intelligent agents,
which refers to any system that perceives its environment and takes actions
that maximize its chance of achieving its goals.
"""

summary = await SummarizeAgent(long_text, max_sentences=2)
# Output: "AI is machine intelligence. It studies intelligent
#          agents that perceive and act to achieve goals."
```

---

### CodeReviewAgent

Review code and provide feedback on issues, improvements, and best practices.

```python
from kagura.chat import CodeReviewAgent

result = await CodeReviewAgent(
    code="def add(a, b): return a + b",
    language="python"
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `code` | `str` | - | Code to review |
| `language` | `str` | `"python"` | Programming language |

**Returns:** `str` - Code review in markdown format

**Example:**

```python
code = """
def divide(a, b):
    return a / b
"""

review = await CodeReviewAgent(code)
# Output: Detailed markdown review with:
# - Issues found (division by zero, missing type hints)
# - Improvement suggestions
# - Best practices recommendations
```

---

## CLI Command

### `kagura chat`

Start an interactive chat session.

```bash
kagura chat [OPTIONS]
```

**Options:**

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--model` | `-m` | `str` | `gpt-4o-mini` | LLM model to use |

**Examples:**

```bash
# Start with default model
kagura chat

# Use GPT-4o
kagura chat --model gpt-4o

# Use Claude
kagura chat -m claude-3-5-sonnet-20241022

# Use Gemini
kagura chat -m gemini/gemini-2.0-flash-exp
```

---

## Session File Format

Session files are stored as JSON in `~/.kagura/sessions/`.

**Format:**

```json
{
  "name": "my_session",
  "created_at": "2025-10-10T14:30:15.123456",
  "messages": [
    {
      "role": "user",
      "content": "What is Python?"
    },
    {
      "role": "assistant",
      "content": "Python is a high-level programming language..."
    }
  ]
}
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Session name |
| `created_at` | `str` | ISO 8601 timestamp |
| `messages` | `list[dict]` | List of messages |

**Message format:**

| Field | Type | Description |
|-------|------|-------------|
| `role` | `str` | Message role (`user`, `assistant`, `system`) |
| `content` | `str` | Message content |

---

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required for OpenAI models |
| `ANTHROPIC_API_KEY` | Anthropic API key | Required for Claude models |
| `GOOGLE_API_KEY` | Google API key | Required for Gemini models |

### Session Directory

Default: `~/.kagura/sessions/`

Override with `ChatSession(session_dir=Path("/custom/path"))`

### History File

Chat history is stored in: `~/.kagura/sessions/chat_history.txt`

Accessible via up/down arrows in the chat interface.

---

## Integration Examples

### Programmatic Chat

```python
from kagura.chat import ChatSession

async def automated_chat():
    session = ChatSession(model="gpt-4o-mini")

    # Simulate chat interactions
    await session.chat("Explain recursion")
    await session.chat("Give me an example in Python")

    # Save session
    await session.save_session("recursion_tutorial")

# Run
import asyncio
asyncio.run(automated_chat())
```

### Custom Preset Agent

```python
from kagura import agent

@agent(model="gpt-4o-mini", temperature=0.3)
async def CustomPresetAgent(text: str, task: str) -> str:
    """
    Perform {{ task }} on the following text:

    {{ text }}

    Provide a concise result.
    """
    pass

# Use in Chat Session
session = ChatSession()
result = await CustomPresetAgent(
    text="Sample text",
    task="sentiment analysis"
)
```

### Session Management

```python
from pathlib import Path
from kagura.chat import ChatSession

# Use custom session directory
session_dir = Path("./my_sessions")
session = ChatSession(session_dir=session_dir)

# Save multiple sessions
await session.chat("Python tutorial")
await session.save_session("python_basics")

session.clear_history()

await session.chat("JavaScript tutorial")
await session.save_session("js_basics")

# List all sessions
sessions = list(session_dir.glob("*.json"))
print(f"Available sessions: {[s.stem for s in sessions]}")
```

---

## Error Handling

### API Key Missing

```python
# Raises: openai.error.AuthenticationError
session = ChatSession()
await session.run()
```

**Solution:** Set environment variable

```bash
export OPENAI_API_KEY=your_key_here
```

### Session Not Found

```python
await session.load_session("nonexistent")
# Prints: "Session not found: nonexistent"
```

### Invalid Model

```python
session = ChatSession(model="invalid-model")
# Raises: litellm.exceptions.BadRequestError
```

---

## Best Practices

### 1. Save Important Conversations

```python
# Before exiting, save valuable sessions
await session.save_session("important_discussion")
```

### 2. Use Appropriate Models

```python
# Fast responses for simple tasks
session = ChatSession(model="gpt-4o-mini")

# Higher quality for complex tasks
session = ChatSession(model="gpt-4o")
```

### 3. Clear History for New Topics

```python
# Start fresh conversation
session.clear_history()
await session.chat("New topic...")
```

### 4. Organize Sessions

```python
# Use descriptive names
await session.save_session("python_debugging_2025-10-10")
await session.save_session("code_review_auth_module")
```

---

## See Also

- [Chat REPL Tutorial](../tutorials/10-chat-repl.md)
- [Memory Management API](./memory.md)
- [Agent Decorator](./decorators.md)
- [CLI Reference](./cli.md)
