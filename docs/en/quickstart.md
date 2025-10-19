# Quick Start

Get started with Kagura AI in 5 minutes.

---

## Installation

```bash
pip install kagura-ai[full]
```

---

## Set API Key

```bash
export OPENAI_API_KEY=sk-...
```

Supports OpenAI, Anthropic, Google, and 100+ providers via LiteLLM.

---

## Your First Agent (30 seconds)

```python
from kagura import agent

@agent
async def translator(text: str, lang: str = "ja") -> str:
    '''Translate to {{ lang }}: {{ text }}'''

# Use it
import asyncio

async def main():
    result = await translator("Hello World", lang="ja")
    print(result)  # "こんにちは世界"

asyncio.run(main())
```

Save as `hello.py` and run:

```bash
python hello.py
```

That's it. One decorator, done.

---

## Type-Safe Structured Output

```python
from kagura import agent
from pydantic import BaseModel

class Person(BaseModel):
    name: str
    age: int
    occupation: str

@agent
async def extract_person(text: str) -> Person:
    '''Extract person info from: {{ text }}'''

# Use it
async def main():
    person = await extract_person(
        "Alice is 30 and works as an engineer"
    )
    print(f"{person.name}, {person.age}, {person.occupation}")
    # "Alice, 30, engineer"

asyncio.run(main())
```

Fully typed. IDE autocomplete works.

---

## With Built-in Tools

```python
@agent(tools=["web_search"])
async def researcher(topic: str) -> str:
    '''Research {{ topic }} using web_search(query) tool.'''

# Environment variable needed:
# export BRAVE_SEARCH_API_KEY=...

async def main():
    result = await researcher("Python 3.13 features")
    print(result)

asyncio.run(main())
```

Built-in tools: `web_search`, `web_fetch`, `file_read`, `file_write`, `execute_python`, and more.

---

## With Memory

```python
@agent(enable_memory=True)
async def assistant(message: str) -> str:
    '''Remember our conversation. User says: {{ message }}'''

async def main():
    # First message
    await assistant("My favorite color is blue")

    # Second message - remembers!
    response = await assistant("What's my favorite color?")
    print(response)  # "Your favorite color is blue"

asyncio.run(main())
```

---

## Real-World: FastAPI Integration

```python
from fastapi import FastAPI
from kagura import agent

app = FastAPI()

@agent
async def support_bot(question: str) -> str:
    '''Answer customer support question: {{ question }}'''

@app.post("/api/support")
async def handle_support(question: str):
    response = await support_bot(question)
    return {"answer": response}

# Run with: uvicorn main:app
```

---

## Bonus: Interactive Chat

Don't want to write code yet?

```bash
kagura chat
```

Try all SDK features interactively:

```
[You] > Read design.pdf and extract requirements

[AI] > (Analyzes PDF, extracts info)

[You] > Search for best practices

[AI] > (Uses web search, finds resources)
```

All SDK features work automatically in chat.

---

## Next Steps

### SDK Integration
- [SDK Guide](../sdk-guide.md) - Complete guide to @agent, @tool, memory
- [Examples](https://github.com/JFK/kagura-ai/tree/main/examples) - 30+ code examples
- [API Reference](api/) - Detailed API docs

### Interactive Exploration
- [Chat Guide](../chat-guide.md) - Full chat features guide
- [MCP Integration](tutorials/06-mcp-integration.md) - Use in Claude Desktop

---

**Ready to build? Start with the [SDK Guide](../sdk-guide.md)**
