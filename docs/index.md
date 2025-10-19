---
title: Kagura AI - Python-First AI Agent SDK
description: Build production-ready AI agents with one decorator. Full type safety, built-in tools, comprehensive testing framework.
keywords:
  - AI SDK
  - Python AI
  - AI Agents
  - Type-safe AI
  - LLM integration
  - Pydantic
  - Production AI
author: Fumikazu Kiyota
robots: index, follow
og_title: Kagura AI - Python-First AI Agent SDK
og_type: website
og_url: https://www.kagura-ai.com
og_description: Build production-ready AI agents with one decorator. Full type safety, built-in tools, comprehensive testing framework.
og_image: assets/kagura-logo.svg
twitter_card: summary_large_image
twitter_site: "@kagura_ai"
twitter_creator: "@JFK"
---

# Kagura AI

![Kagura AI Logo](assets/kagura-logo.svg)

**Python-First AI Agent SDK**

Build production-ready AI agents with one decorator. Full type safety, built-in tools, and comprehensive testing framework.

---

## What is Kagura AI?

A Python SDK that makes building AI agents as simple as writing a function. Add one `@agent` decorator and you're done.

```python
from kagura import agent

@agent
async def translator(text: str, lang: str = "ja") -> str:
    '''Translate to {{ lang }}: {{ text }}'''

result = await translator("Hello World", lang="ja")
# "こんにちは世界"
```

No configuration files. No complex setup. Just Python.

---

## Why Kagura AI?

### For Python Developers

- **One Decorator**: `@agent` is all you need
- **Type-Safe**: Full pyright strict mode support
- **Production-Ready**: Built-in memory, tools, testing
- **Fast Integration**: Add to existing apps in minutes

### vs Other SDKs

| Feature | LangChain | AutoGen | **Kagura AI** |
|---------|-----------|---------|--------------|
| Setup | 50+ lines | 30+ lines | **1 decorator** ✅ |
| Type Safety | ❌ | ❌ | **✅ Full** |
| Memory | Manual | Basic | **✅ 3-tier** |
| Testing | Manual | ❌ | **✅ Built-in** |
| Web Search | Plugin | ❌ | **✅ Built-in** |

---

## Core Features

### SDK Essentials

- ✅ **@agent Decorator** - One-line AI agent creation
- ✅ **Type-Safe Output** - Automatic Pydantic parsing
- ✅ **Built-in Tools** - Web search, file ops, code exec
- ✅ **Memory System** - Context, persistent, RAG
- ✅ **Testing Framework** - Test your agents easily
- ✅ **Multi-LLM** - OpenAI, Anthropic, Google, 100+ more

### Bonus Features

- ✅ **Interactive Chat** - Try features without code
- ✅ **MCP Integration** - Use in Claude Desktop
- ✅ **Streaming** - Real-time responses
- ✅ **Cost Tracking** - Monitor API usage

---

## Quick Examples

### Type-Safe Structured Output

```python
from pydantic import BaseModel

class Analysis(BaseModel):
    sentiment: str
    keywords: list[str]
    confidence: float

@agent
async def analyze(text: str) -> Analysis:
    '''Analyze: {{ text }}'''

result = await analyze("I love Python!")
print(result.sentiment)  # Type-safe!
```

### With Built-in Tools

```python
@agent(tools=["web_search"])
async def researcher(topic: str) -> str:
    '''Research {{ topic }} using web_search(query) tool.'''

result = await researcher("Python 3.13 features")
```

### With Memory

```python
@agent(enable_memory=True)
async def assistant(message: str) -> str:
    '''Remember our conversation. User says: {{ message }}'''

await assistant("My favorite color is blue")
await assistant("What's my favorite color?")  # Remembers!
```

---

## Real-World Integration

### FastAPI Example

```python
from fastapi import FastAPI
from kagura import agent

app = FastAPI()

@agent
async def support_bot(question: str) -> str:
    '''Answer support question: {{ question }}'''

@app.post("/api/support")
async def handle_support(question: str):
    response = await support_bot(question)
    return {"answer": response}
```

### Data Pipeline

```python
@agent(tools=["web_search"])
async def data_enricher(company: str) -> dict:
    '''Enrich data for: {{ company }}

    Extract: industry, size, location
    '''

enriched = await data_enricher("Anthropic")
```

---

## Bonus: Interactive Chat

Want to try without writing code?

```bash
kagura chat
```

Claude Code-like experience with all SDK features:

```
[You] > Read report.pdf and summarize

[AI] > (Uses SDK's file_read + Gemini Vision)

      Key findings:
      1. Revenue up 23% YoY
      2. New market expansion
      3. Team doubled

[You] > Search for industry trends

[AI] > (Uses SDK's web_search tool)
```

---

## Get Started

Choose your path:

### For SDK Integration
1. [Quick Start](quickstart.md) - 5-minute tutorial
2. [SDK Guide](sdk-guide.md) - Complete SDK guide
3. [Examples](https://github.com/JFK/kagura-ai/tree/main/examples) - Code examples

### For Exploration
1. [Chat Guide](chat-guide.md) - Try interactive chat
2. [Installation](en/installation.md) - Setup guide

[Get Started →](quickstart.md){: .md-button .md-button--primary }

---

## Architecture

Built on proven technologies:

- **LLM**: OpenAI SDK (direct) + LiteLLM (100+ providers)
- **Memory**: ChromaDB (vector storage)
- **Validation**: Pydantic v2
- **Testing**: pytest + custom framework
- **Type Safety**: pyright strict mode

**Quality Metrics**:
- 1,300+ tests (90%+ coverage)
- 100% typed (pyright strict)
- Production-ready

---

## Community

- [GitHub](https://github.com/JFK/kagura-ai) - Source code & issues
- [PyPI](https://pypi.org/project/kagura-ai/) - Package downloads
- [Examples](https://github.com/JFK/kagura-ai/tree/main/examples) - 30+ examples

---

**Built with ❤️ for Python developers**
