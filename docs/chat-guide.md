# Chat Guide - Kagura AI

Interactive chat experience for trying Kagura AI features.

---

## What is Kagura Chat?

A Claude Code-like interactive environment where you can:
- Try all SDK features without writing code
- Analyze files (PDFs, images, code)
- Search the web and fetch URLs
- Execute Python code safely
- Ask questions with full context memory

**Think of it as**: A playground for the Kagura SDK.

---

## Getting Started

### Launch Chat

```bash
kagura chat
```

### First-Time Setup (Optional)

```bash
kagura init  # Set your name, location, preferences
```

This personalizes the built-in personal tools (news, weather, recipes, events).

---

## Basic Usage

### Ask Anything

```
[You] > What's the weather in Tokyo?

[AI] > (Uses weather_forecast tool)

      Current: 18°C, Partly cloudy
      Forecast: High 22°C, Low 15°C
      Tip: Light jacket recommended
```

### File Operations

```
[You] > Read design.pdf and extract key requirements

[AI] > (Analyzes PDF with Gemini)

      Key requirements:
      1. User authentication system
      2. Real-time notifications
      3. Mobile responsive design
```

### Web Search

```
[You] > Search for Python best practices 2025

[AI] > (Uses Brave Search)

      Found 5 results:
      1. PEP 20 - The Zen of Python
         https://peps.python.org/pep-0020/
      ...
```

### Code Execution

```
[You] > Calculate fibonacci(10)

[AI] > (Writes and executes Python code)

      Result: 55

      Code executed:
      def fibonacci(n):
          if n <= 1: return n
          return fibonacci(n-1) + fibonacci(n-2)
```

---

## Built-in Tools (Auto-detected)

Chat automatically uses these tools when needed:

- **file_read**: Read text, images, PDFs, audio, video
- **file_write**: Create/modify files (auto-backup)
- **file_search**: Find files by pattern
- **execute_python**: Run Python code safely
- **shell_exec**: Execute shell commands (with confirmation)
- **brave_search**: Web search
- **url_fetch**: Fetch webpage content
- **youtube_transcript**: Get YouTube transcripts
- **youtube_metadata**: Get video information

---

## Personal Tools (v3.0)

Activated with `kagura init`:

- **daily_news**: Get news briefing
- **weather_forecast**: Weather updates
- **search_recipes**: Find recipes
- **find_events**: Discover events

Usage:
```
[You] > Get me tech news
[AI] > (Uses daily_news tool, streams results)

[You] > Find recipes with chicken
[AI] > (Uses search_recipes tool)
```

---

## Commands

### Session Management

- `/save [name]` - Save conversation
- `/load <name>` - Load saved session
- `/clear` - Clear history

### Agent Management

- `/create agent <desc>` - Generate custom agent (v3.0)
- `/reload` - Reload custom agents
- `/agent` - List/use custom agents

### Monitoring

- `/stats` - Token usage & costs (v3.0)
- `/stats export <file>` - Export to JSON/CSV
- `/list` - List all tools

### Other

- `/model [name]` - Switch LLM model
- `/help` - Show help
- `/exit` - Exit chat

---

## Keyboard Shortcuts

- **Enter×2**: Send message
- **Ctrl+P/N**: History navigation
- **Ctrl+R**: Search history
- **Tab**: Autocomplete

---

## Example Session

```
[You] > Read sales.csv and analyze the trend

[AI] > I'll analyze the CSV file.

      (Reads file, writes pandas code, executes)

      Sales trend analysis:
      - Q1: $1.2M (+15% YoY)
      - Q2: $1.5M (+25% YoY)
      - Q3: $1.8M (+20% YoY)

      Trend: Consistent growth, accelerating in Q2

[You] > Create a chart

[AI] > (Writes matplotlib code, executes)

      Chart saved to: sales_trend.png

[You] > What's driving Q2 growth?

[AI] > Based on the data...
      (Remembers previous context, provides analysis)
```

---

## Advanced Features

### Multimodal Analysis

```
[You] > Analyze diagram.png and explain the architecture

[AI] > (Uses Gemini Vision)

      This diagram shows a microservices architecture with:
      - API Gateway at the front
      - 3 backend services (Auth, Data, Notifications)
      - PostgreSQL database
      - Redis cache layer
```

### YouTube Summarization

```
[You] > Summarize https://youtube.com/watch?v=xxx

[AI] > (Gets transcript and metadata)

      Video: "Python 3.13 New Features" (15:32)

      Key points:
      1. JIT compiler improvements
      2. Better error messages
      3. Free-threaded Python (experimental)
```

---

## Tips

- **Just ask naturally** - Tools are auto-detected
- **Use /stats** - Monitor your API costs
- **Create custom agents** - Use `/create agent <description>`
- **Save sessions** - Use `/save` to continue later

---

## For Developers

Want to build on this chat functionality?

```python
from kagura.chat import ChatSession

session = ChatSession(model="gpt-4o")
await session.run()  # Launches interactive chat
```

Or integrate chat tools into your own application - see [SDK Guide](sdk-guide.md).

---

## Next Steps

- [SDK Guide](sdk-guide.md) - Use Kagura in your code
- [Examples](../examples/) - Code examples
- [API Reference](en/api/) - Complete API docs
