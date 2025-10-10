# Chat REPL Tutorial

The **Chat REPL** provides an interactive chat interface for conversing with AI directly from your terminal, without needing to define agents beforehand.

## Quick Start

### Starting Chat Session

```bash
kagura chat
```

You'll see a welcome screen:

```
╭─ Kagura AI Chat ─╮
│ Welcome to        │
│ Kagura Chat!      │
│                   │
│ Commands:         │
│  /help      Help  │
│  /translate Text  │
│  /summarize Text  │
│  /review    Code  │
│  /exit      Exit  │
╰───────────────────╯
```

### Basic Conversation

Simply type your message and press Enter:

```
[You] > What is Python?

[AI]
Python is a high-level, interpreted programming language known for its
readability and versatility. It's widely used for web development, data
science, automation, and more.
```

The AI maintains conversation context, so you can have multi-turn dialogues:

```
[You] > What are its main features?

[AI]
Python's main features include:
1. **Simple syntax** - Easy to read and write
2. **Dynamic typing** - No need to declare variable types
3. **Extensive libraries** - Rich ecosystem of packages
4. **Cross-platform** - Runs on Windows, macOS, Linux
5. **Community support** - Large, active developer community
```

## Preset Commands

### Translation (`/translate`)

Translate text to another language:

```
[You] > /translate Hello World to ja

╭─ Translation ─────╮
│ こんにちは世界      │
╰───────────────────╯
```

Default target language is Japanese:

```
[You] > /translate Good morning

╭─ Translation ─────╮
│ おはようございます  │
╰───────────────────╯
```

### Summarization (`/summarize`)

Summarize long text:

```
[You] > /summarize Artificial intelligence (AI) is intelligence demonstrated by machines, as opposed to natural intelligence displayed by animals including humans. AI research has been defined as the field of study of intelligent agents, which refers to any system that perceives its environment and takes actions that maximize its chance of achieving its goals.

╭─ Summary ──────────────────────────────────────╮
│ AI is machine intelligence that studies        │
│ intelligent agents capable of perceiving their │
│ environment and taking goal-oriented actions.  │
╰────────────────────────────────────────────────╯
```

### Code Review (`/review`)

Review code for issues and improvements:

```
[You] > /review

Paste your code (press Enter twice to finish):
def divide(a, b):
    return a / b

<press Enter twice>


[Code Review]

## Issues Found

1. **Division by Zero** - No check for `b == 0`
2. **Missing Type Hints** - Function parameters lack type annotations
3. **No Docstring** - Missing documentation

## Suggestions

```python
def divide(a: float, b: float) -> float:
    """
    Divide two numbers.

    Args:
        a: Numerator
        b: Denominator

    Returns:
        Result of division

    Raises:
        ValueError: If b is zero
    """
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
```

## Best Practices

- Always validate inputs
- Add type hints for better code clarity
- Document function behavior
```

## Session Management

### Saving Sessions

Save your conversation for later:

```
[You] > /save my_session

Session saved to: /home/user/.kagura/sessions/my_session.json
```

Auto-generate session name with timestamp:

```
[You] > /save

Session saved to: /home/user/.kagura/sessions/2025-10-10_14-30-15.json
```

### Loading Sessions

Resume a previous conversation:

```
[You] > /load my_session

Session loaded: my_session (12 messages)
```

All context and history will be restored.

### Clearing History

Clear the current conversation:

```
[You] > /clear

Conversation history cleared.
```

## Advanced Usage

### Using Different Models

Specify a different LLM model:

```bash
kagura chat --model gpt-4o
```

Available models:
- `gpt-4o-mini` (default, fastest)
- `gpt-4o` (most capable)
- `claude-3-5-sonnet-20241022` (Anthropic Claude)
- `gemini/gemini-2.0-flash-exp` (Google Gemini)

### Command Reference

| Command | Description | Example |
|---------|-------------|---------|
| `/help` | Show help message | `/help` |
| `/translate` | Translate text | `/translate Hello to es` |
| `/summarize` | Summarize text | `/summarize <long text>` |
| `/review` | Review code | `/review` |
| `/save [name]` | Save session | `/save my_session` |
| `/load <name>` | Load session | `/load my_session` |
| `/clear` | Clear history | `/clear` |
| `/exit` or `/quit` | Exit chat | `/exit` |

## Tips & Tricks

### 1. Paste Code Directly

You can paste code directly into the chat:

```
[You] > Review this code:
```python
def factorial(n):
    if n == 0:
        return 1
    return n * factorial(n - 1)
```

[AI]
This recursive factorial implementation is correct but...
```

### 2. Multi-Turn Conversations

The chat maintains context across multiple exchanges:

```
[You] > Explain recursion

[AI]
Recursion is when a function calls itself...

[You] > Can you give an example in Python?

[AI]
Sure! Here's a recursive function...
```

### 3. Quick Translations

For quick translations without typing the full command:

```
[You] > Translate "thank you" to French

[AI]
"merci"
```

### 4. Session Organization

Organize sessions by topic:

```bash
/save python_learning
/save work_project
/save research_notes
```

## Example Workflows

### Learning a New Concept

```
[You] > What is async/await in Python?

[AI]
Async/await is Python's syntax for asynchronous programming...

[You] > Show me an example

[AI]
```python
import asyncio

async def fetch_data():
    await asyncio.sleep(1)
    return "data"
```

[You] > How is this different from threading?

[AI]
Async/await uses cooperative multitasking...

[You] > /save async_learning
```

### Code Review Workflow

```
[You] > /review

<paste code>

[AI]
<detailed review>

[You] > Can you fix the issues you found?

[AI]
<provides corrected code>

[You] > /save code_review_2025-10-10
```

### Translation Workflow

```
[You] > /translate "Hello, how are you?" to ja

╭─ Translation ─────────────╮
│ こんにちは、お元気ですか？  │
╰───────────────────────────╯

[You] > /translate "I am fine, thank you" to ja

╭─ Translation ─────────────╮
│ 元気です、ありがとう        │
╰───────────────────────────╯
```

## Keyboard Shortcuts

- **Ctrl+C** - Cancel current input / Exit
- **Ctrl+D** - Exit chat (EOF)
- **Up/Down Arrow** - Navigate command history
- **Enter** - Submit message

## Next Steps

- Learn about [Custom Agents](./01-quick-start.md)
- Explore [Agent Routing](./09-agent-routing.md)
- Try [MCP Integration](./06-mcp-integration.md)

## Troubleshooting

### Chat doesn't start

Ensure you have a valid API key:

```bash
export OPENAI_API_KEY=your_key_here
```

### Slow responses

Try using a faster model:

```bash
kagura chat --model gpt-4o-mini
```

### Session not found

List available sessions:

```bash
ls ~/.kagura/sessions/
```

## Further Reading

- [Chat API Reference](../api/chat.md)
- [Memory Management](../api/memory.md)
- [Preset Agents](../api/chat.md#preset-agents)
