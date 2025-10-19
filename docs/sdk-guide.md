# SDK Guide - Kagura AI

Complete guide to using Kagura AI as a Python SDK.

---

## Table of Contents

1. [Basic Agent Creation](#basic-agent-creation)
2. [Type-Safe Output](#type-safe-output)
3. [Built-in Tools](#built-in-tools)
4. [Custom Tools](#custom-tools)
5. [Memory Management](#memory-management)
6. [Multi-LLM Support](#multi-llm-support)
7. [Testing Agents](#testing-agents)

---

## Basic Agent Creation

### Simplest Example

```python
from kagura import agent

@agent
async def summarizer(text: str) -> str:
    '''Summarize in 3 points: {{ text }}'''

result = await summarizer("Long article text...")
```

### With Parameters

```python
@agent(model="gpt-4o", temperature=0.3)
async def analyzer(text: str) -> str:
    '''Analyze: {{ text }}'''
```

---

## Type-Safe Output

### Using Pydantic

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

---

## Built-in Tools

### Available Tools

- `web_search`: Search web (Brave Search)
- `web_fetch`: Fetch webpage content
- `file_read`: Read files (text, images, PDFs)
- `file_write`: Write files
- `execute_python`: Run Python code in sandbox

### Usage

```python
@agent(tools=["web_search", "web_fetch"])
async def researcher(topic: str) -> str:
    '''Research {{ topic }} using:
    - web_search(query): Search the web
    - web_fetch(url): Fetch webpage content
    '''
```

---

## Custom Tools

### Define Custom Tool

```python
from kagura import tool

@tool
async def search_database(query: str) -> list[dict]:
    '''Search internal database'''
    results = db.query(query)
    return results
```

### Use in Agent

```python
@agent(tools=[search_database])
async def data_agent(question: str) -> str:
    '''Answer using database: {{ question }}

    Use search_database(query) to find information.
    '''
```

---

## Memory Management

### Enable Memory

```python
@agent(enable_memory=True)
async def assistant(message: str) -> str:
    '''You remember our conversation.

    User says: {{ message }}'''

# Multi-turn conversation
await assistant("My favorite color is blue")
await assistant("What's my favorite color?")  # Remembers!
```

### Memory API

```python
@agent(enable_memory=True)
async def assistant(message: str, memory: MemoryManager) -> str:
    '''{{ message }}'''

    # Store
    await memory.store("user_pref", {"color": "blue"})

    # Recall
    pref = await memory.recall("user_pref")
```

### RAG Search

```python
from kagura.core.memory import MemoryRAG

@agent(enable_memory=True)
async def doc_qa(question: str) -> str:
    '''Answer based on documents.

    Use rag_search(query) to find relevant information.
    '''

# Index documents
rag = MemoryRAG()
await rag.index_directory("./docs")

# Query
answer = await doc_qa("What does the report say?")
```

---

## Multi-LLM Support

### OpenAI

```python
@agent(model="gpt-4o")
async def translator(text: str) -> str:
    '''Translate: {{ text }}'''
```

### Anthropic

```python
@agent(model="claude-3-5-sonnet-20241022")
async def writer(prompt: str) -> str:
    '''Write: {{ prompt }}'''
```

### Google Gemini

```python
@agent(model="gemini/gemini-2.0-flash")
async def analyzer(text: str) -> str:
    '''Analyze: {{ text }}'''
```

100+ models supported via LiteLLM.

---

## Testing Agents

### Basic Test

```python
import pytest

@pytest.mark.asyncio
async def test_translator():
    result = await translator("Hello", lang="ja")
    assert isinstance(result, str)
    assert len(result) > 0
```

### With Mocking

```python
from kagura.testing.mocking import LLMMock

@pytest.mark.asyncio
async def test_with_mock():
    with LLMMock("こんにちは"):
        result = await translator("Hello", lang="ja")
        assert result == "こんにちは"
```

### Semantic Assertions

```python
from kagura.testing import AgentTestCase

class TestMyAgent(AgentTestCase):
    async def test_sentiment(self):
        result = await analyzer("I love this!")

        # Semantic match (LLM-powered)
        self.assert_semantic_match(
            result,
            "positive sentiment"
        )
```

---

## Real-World Integration

### FastAPI

```python
from fastapi import FastAPI
from kagura import agent

app = FastAPI()

@agent
async def support_bot(question: str) -> str:
    '''Answer: {{ question }}'''

@app.post("/api/support")
async def handle_support(question: str):
    response = await support_bot(question)
    return {"answer": response}
```

### Data Pipeline

```python
from kagura import agent

@agent(tools=["web_search"])
async def data_enricher(company: str) -> dict:
    '''Enrich data for: {{ company }}

    Extract: industry, size, location
    '''

enriched = await data_enricher("Anthropic")
```

---

## Next Steps

- [Examples](../examples/) - 30+ code examples
- [Chat Guide](chat-guide.md) - Try interactive chat
- [API Reference](en/api/) - Complete API docs
