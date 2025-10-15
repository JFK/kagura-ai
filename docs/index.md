---
title: Kagura AI - Python-First AI Agent Framework
description: Convert any Python function into an AI agent with a single decorator. Built-in memory, routing, multimodal RAG, web search, and context compression.
keywords:
  - AI Agents
  - Python AI framework
  - Memory Management
  - Agent Routing
  - Multimodal RAG
  - Web Integration
  - Context Compression
  - LLM integration
  - Pydantic
author: Fumikazu Kiyota
robots: index, follow
og_title: Kagura AI - Python-First AI Agent Framework
og_type: website
og_url: https://www.kagura-ai.com
og_description: Convert any Python function into an AI agent with a single decorator. Built-in memory, routing, multimodal RAG, web search, and context compression.
og_image: assets/kagura-logo.svg
twitter_card: summary_large_image
twitter_site: "@kagura_ai"
twitter_creator: "@JFK"
---

# Kagura AI

![Kagura AI Logo](assets/kagura-logo.svg)

**Python-First AI Agent Framework with Memory, Routing, and Multimodal RAG**

Kagura AI is a modern framework that makes building AI agents as simple as writing a Python function. With a single `@agent` decorator, you can transform any async function into a powerful AI agent with memory, routing, multimodal understanding, and web search capabilities.

---

## What is Kagura AI?

Kagura AI is a production-ready framework focused on developer experience and simplicity. You write agents in pure Python with familiar async/await patterns.

```python
from kagura import agent

@agent
async def hello(name: str) -> str:
    '''Say hello to {{ name }}'''
    pass

result = await hello("World")
# "Hello, World!"
```

## Key Features

### Core Features
- **One-Line Agent Creation**: `@agent` decorator converts functions to AI agents
- **Jinja2 Templates**: Dynamic prompts using template syntax in docstrings
- **Type-Based Parsing**: Automatic response conversion using Python type hints
- **Pydantic Support**: First-class structured output with Pydantic models
- **Code Execution**: Built-in safe Python code generation and execution
- **Multi-LLM Support**: Works with OpenAI, Anthropic, Google, and more

### Advanced Features
- **Memory Management**: Context, persistent, and RAG-based memory
- **Agent Routing**: Intelligent agent selection with intent and semantic matching
- **Multimodal RAG**: Index and search images, audio, video, and PDFs
- **Web Integration**: Real-time web search and content scraping
- **Context Compression**: Efficient token management for long conversations
- **Interactive Chat**: Full-featured chat REPL with memory and web search
- **Testing Framework**: Built-in testing utilities with semantic assertions
- **Observability**: Telemetry, cost tracking, and performance monitoring

## Core Concepts

### 1. Agent Decorator

Transform any async function into an AI agent:

```python
@agent
async def my_agent(input: str) -> str:
    '''Process {{ input }}'''
    pass
```

The decorator:
- Extracts the function signature
- Uses the docstring as a Jinja2 template
- Calls the LLM with rendered prompt
- Parses the response based on return type

### 2. Template Engine

Use Jinja2 templates in docstrings for dynamic prompts:

```python
@agent
async def translator(text: str, lang: str = "ja") -> str:
    '''Translate to {{ lang }}: {{ text }}'''
    pass
```

### 3. Type-Based Parser

Automatic response parsing based on return type hints:

```python
from pydantic import BaseModel

class Person(BaseModel):
    name: str
    age: int

@agent
async def extract_person(text: str) -> Person:
    '''Extract person info from: {{ text }}'''
    pass
```

Returns a fully validated Pydantic model instance.

### 4. Code Execution

Safe Python code generation and execution:

```python
from kagura.agents import execute_code

result = await execute_code("Calculate the factorial of 10")
# Generates code, executes safely, returns result
```

## Architecture

Kagura AI follows a clean, layered architecture:

```
┌─────────────────────────────────────┐
│         @agent Decorator            │
│  (Function → Agent transformation)  │
└───────────────┬─────────────────────┘
                │
┌───────────────▼─────────────────────┐
│       Template Engine (Jinja2)      │
│    (Docstring → Rendered prompt)    │
└───────────────┬─────────────────────┘
                │
┌───────────────▼─────────────────────┐
│         LLM Layer (LiteLLM)         │
│   (Prompt → LLM → Raw response)     │
└───────────────┬─────────────────────┘
                │
┌───────────────▼─────────────────────┐
│    Parser (Type-based parsing)      │
│  (Raw response → Typed Python obj)  │
└─────────────────────────────────────┘
```

## Design Philosophy

Kagura AI is built on these principles:

- **Python-First**: No external configuration files
- **Type Safety**: Leverages Python's type system
- **Developer Experience**: Simple API, fast iteration
- **Composability**: Agents are just async functions
- **Explicitness**: Clear data flow, no magic
- **Production-Ready**: Built-in testing, monitoring, and optimization tools

## Get Started

Ready to build your first agent?

- [Installation Guide](en/installation.md) - Install Kagura AI
- [Quick Start Tutorial](en/quickstart.md) - Build your first agent in 5 minutes
- [API Reference](en/api/) - Detailed API documentation
- [Examples](https://github.com/JFK/kagura-ai/tree/main/examples) - More examples and patterns

[Get Started →](en/installation.md){: .md-button .md-button--primary }
