# Tutorial 03: Interactive Chat Experience

**Duration**: 5 minutes
**Level**: Beginner
**Prerequisites**: Installation complete

---

## Overview

`kagura chat` provides a Claude Code-like interactive experience where you can:
- Read and analyze files (PDFs, images, code)
- Search the web and fetch URLs
- Summarize YouTube videos
- Execute Python code safely
- Ask questions about your documents

All capabilities are available automatically - just start chatting!

---

## Quick Start

### 1. Start Chat

```bash
kagura chat
```

You'll see:
```
Kagura AI Chat (v2.5.10)

Type your message or use commands:
  /help     - Show all commands
  /exit     - Exit chat

[You] >
```

### 2. Try Basic Queries

```
[You] > Hello! What can you do?

[AI] > I can help you with:
      - File operations (read, write, search)
      - Image and PDF analysis
      - Web search and URL fetching
      - YouTube video summarization
      - Python code execution
      - And more!
```

---

## File Operations

### Read Files

```
[You] > Read src/main.py and explain what it does

[AI] > This file contains...
      - Main application entry point
      - FastAPI server initialization
      - Route definitions...
```

### Analyze PDFs

```
[You] > Summarize report.pdf in 3 bullet points

[AI] > Based on the PDF analysis:
      • Q3 revenue increased 25% YoY
      • Customer retention improved to 89%
      • Expansion into APAC market planned for Q4
```

### Image Analysis

```
[You] > Analyze diagram.png and explain the architecture

[AI] > This diagram shows a microservices architecture with:
      - API Gateway at the entry point
      - 4 backend services (Auth, Orders, Inventory, Notifications)
      - Message queue for async communication
      - Shared database cluster
```

---

## Web Capabilities

### Web Search

```
[You] > Search for Python best practices 2025

[AI] > I found these recent best practices:

      1. Type Hints Everywhere
         Source: realpython.com/python-type-checking
         - Use mypy/pyright for static type checking
         - Leverage Pydantic for runtime validation

      2. Async/Await for I/O
         Source: python.org/dev/peps/pep-0492
         - asyncio for concurrent operations
         - aiohttp for async HTTP requests

      ...
```

### Fetch Web Pages

```
[You] > Fetch https://example.com/article and summarize

[AI] > Article Summary:
      - Main topic: ...
      - Key points: ...
      - Conclusion: ...
```

### YouTube Videos

```
[You] > Summarize https://youtube.com/watch?v=...

[AI] > Video Summary (12:34 duration):
      - Introduction (0:00-2:00): ...
      - Main content (2:00-10:00): ...
      - Conclusion (10:00-12:34): ...

      Key takeaways:
      1. ...
      2. ...
```

---

## Code Execution

### Simple Calculations

```
[You] > Calculate the factorial of 20

[AI] > I'll calculate that using Python:

      ```python
      import math
      result = math.factorial(20)
      ```

      The factorial of 20 is: 2,432,902,008,176,640,000
```

### Data Analysis

```
[You] > I have sales.csv with columns: date, product, amount.
        What's the total sales per product?

[AI] > I'll analyze the CSV file:

      ```python
      import pandas as pd

      df = pd.read_csv('sales.csv')
      total_per_product = df.groupby('product')['amount'].sum()
      print(total_per_product)
      ```

      Results:
      - Product A: $15,230
      - Product B: $8,940
      - Product C: $22,105
```

---

## Chat Commands

### Built-in Commands

```
[You] > /help

Available commands:
  /translate <text>  - Translate text to Japanese
  /summarize <text>  - Summarize long text
  /review <code>     - Review code for issues
  /agent <name>      - Execute custom agent
  /help              - Show this help
  /exit              - Exit chat
```

### Translate

```
[You] > /translate Hello, how are you?

[AI] > こんにちは、お元気ですか？
```

### Summarize

```
[You] > /summarize <paste long article>

[AI] > Summary (3 key points):
      1. ...
      2. ...
      3. ...
```

### Code Review

```
[You] > /review
        def calculate(x, y):
            return x / y

[AI] > Code Review:

      Issues Found:
      1. Division by zero not handled
      2. No type hints
      3. Function name too generic

      Suggestions:
      - Add zero check: if y == 0: raise ValueError
      - Add type hints: def calculate(x: float, y: float) -> float
      - Rename to be more specific: divide_numbers
```

---

## Advanced Features

### Multi-Turn Conversation

Chat remembers context within the session:

```
[You] > Read config.yaml

[AI] > The config file contains:
      - Database connection: PostgreSQL
      - API port: 8000
      - Debug mode: false

[You] > What's the database type?

[AI] > According to the config file I just read, the database type is PostgreSQL.
```

### Custom Agents

If you have custom agents in `~/.kagura/agents/`:

```
[You] > /agent my_analyzer some_input

[AI] > (executes your custom agent)
```

---

## Tips & Tricks

### 1. File Paths

Use absolute or relative paths:
```
[You] > Read ./src/main.py
[You] > Read /Users/username/project/data.csv
```

### 2. Multiple Files

```
[You] > Compare src/old_version.py and src/new_version.py

[AI] > (reads both files and compares)
```

### 3. Chaining Tasks

```
[You] > Read report.pdf, search for related articles on the web,
        and write a summary combining both

[AI] > (performs all tasks in sequence)
```

### 4. Code Generation

```
[You] > Write a FastAPI endpoint for user registration

[AI] > (generates complete code with validation)
```

---

## Configuration

### Change Model

Start chat with a different model:

```bash
kagura chat --model gpt-4o
kagura chat --model claude-3-5-sonnet-20241022
```

### Environment Variables

Set these for full functionality:

```bash
# Required (at least one)
export OPENAI_API_KEY=sk-...

# Optional: Web search
export BRAVE_SEARCH_API_KEY=...

# Optional: Multimodal (Gemini)
export GOOGLE_API_KEY=...
```

See [Environment Variables](../configuration/environment-variables.md) for details.

---

## What's Happening Behind the Scenes

When you use `kagura chat`, the system automatically:

1. **Detects Intent**: Understands what you want to do
2. **Selects Tools**: Chooses appropriate tools (file read, web search, etc.)
3. **Executes**: Runs tools safely in sandboxes
4. **Presents Results**: Formats output with Rich markdown

All of this happens transparently - you just chat naturally!

---

## Common Use Cases

### 1. Code Review Workflow

```
[You] > Read all .py files in src/ and identify code smells

[AI] > (analyzes all Python files, reports issues)

[You] > Fix the most critical issue in src/auth.py

[AI] > (generates fix, shows diff)
```

### 2. Research Workflow

```
[You] > Research "Python async best practices"

[AI] > (searches web, reads articles, synthesizes)

[You] > Create a markdown document with the findings

[AI] > (writes research_notes.md)
```

### 3. Data Analysis Workflow

```
[You] > Load data.csv and show statistics

[AI] > (executes pandas code, shows stats)

[You] > Create a bar chart of the top 5 categories

[AI] > (generates matplotlib code, saves chart.png)

[You] > Analyze the chart and tell me the insights

[AI] > (reads generated chart, provides analysis)
```

---

## Troubleshooting

### Chat not starting

**Problem**: `ModuleNotFoundError: No module named 'kagura.chat'`

**Solution**:
```bash
pip install kagura-ai[full]  # Ensure full installation
```

### Web search not working

**Problem**: "Web search unavailable"

**Solution**:
```bash
# Set API key or use DuckDuckGo (no key required)
export BRAVE_SEARCH_API_KEY=...
```

### Multimodal features unavailable

**Problem**: "Gemini API not available"

**Solution**:
```bash
# Install web extras
pip install kagura-ai[web]

# Set API key
export GOOGLE_API_KEY=...
```

---

## Next Steps

- **[Tutorial 04: Memory Management](04-memory.md)** - Make agents remember
- **[Tutorial 05: Web & Multimodal](05-web-multimodal.md)** - Deep dive into web/multimodal
- **[Guide: Chat Features](../guides/chat-features.md)** - Advanced chat features

---

**Explore the chat experience and discover what Kagura can do for you!**
