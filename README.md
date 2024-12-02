![Kagura AI Logo](https://www.kagura-ai.com/assets/kagura-logo.svg)

![Python versions](https://img.shields.io/pypi/pyversions/kagura-ai.svg)
![PyPI version](https://img.shields.io/pypi/v/kagura-ai.svg)
![PyPI - Downloads](https://img.shields.io/pypi/dm/kagura-ai)
![Codecov](https://img.shields.io/codecov/c/github/JFK/kagura-ai)
![Tests](https://img.shields.io/github/actions/workflow/status/JFK/kagura-ai/test.yml?label=tests)
![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)
![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)

# Kagura AI

Kagura AI is a flexible and modular framework designed for building, configuring, and orchestrating AI agents. Its YAML-based configuration system emphasizes simplicity, while its extensible architecture supports advanced workflows and complex integrations.

**You can find the full documentation on our:**
[kagura-ai.com](https://www.kagura-ai.com)

**You can also find Kagura AI on PyPI:**
[kagura-ai](https://pypi.org/project/kagura-ai/)

**ChatGPTs may help you to build own Kagura AI agents:**
[Kagura AI Agent Builder](https://chatgpt.com/g/g-674c1cfed1a88191bd594e13c2840a44-kagura-ai-agent-builder)

---

## Introduction

Kagura AI simplifies the process of creating intelligent agents by offering a structured approach to agent management. With Kagura, developers can seamlessly integrate language models, process stateful data, and design orchestrated workflows.

Whether you're building a simple chatbot, data processor, or a sophisticated multi-agent system, Kagura provides the tools to define, extend, and deploy AI solutions efficiently.

---

## Core Concepts

### Modular Agent Design
- **Agents**: Independent components with specific roles, configurable via YAML.
- **State Management**: Type-safe state definitions using Pydantic models.
- **Workflows**: Dynamic multi-agent orchestration with conditional routing.

### Extensibility
- **Pre/Post Processing Hooks**: Customize agent behavior at every stage.
- **Custom Tools**: Add bespoke functionality for domain-specific tasks.
- **Plugin Architecture**: Expand capabilities with reusable modules.

### Multi-LLM Support
- Easily integrate multiple LLM providers via [LiteLLM](https://docs.litellm.ai/).
  - OpenAI, Anthropic, Ollama, Google, and more.

---

## Features

- 🛠 **YAML Configuration**: Intuitive and human-readable setup.
- 🔄 **State Management**: Pydantic-based validation for reliable data handling.
- 🌊 **Workflow Orchestration**: Design multi-step workflows with conditional branching.
- 🌍 **Multilingual Support**: Create agents that operate in multiple languages.
- 🔌 **Custom Tools**: Add functionality specific to your project.
- 💾 **Redis Integration**: Optional memory persistence for agents.

---

## Installation

### Using Git

```bash
git clone https://github.com/JFK/kagura-ai.git
cd kagura-ai
poetry install
```

### Using PyPI
```bash
pip update -U pip
pip install kagura-ai
```

---

## Configuration

Define agents using YAML files for simple and scalable setup.

### Example
```yaml
# ~/.config/kagura/agents/my_agent/agent.yml
llm:
  model: openai/gpt-4o-mini  # e.g. ollama/qwen2.5:14b
  max_tokens: 4096
description:
  - language: en
    text: My custom agent for summarizing text.
instructions:
  - language: en
    text: Summarize the input text.
prompt:
  - language: en
    template: |
      Summarize this: {TEXT}
response_fields:
  - summary
```

---

## Usage

### Starting Kagura
```bash
kagura
```

### CLI Commands
- `kagura`: Start the chatbot interface.
- `kagura create`: Create a new agent (experimental).
- `kagura --help`: Show command options.

---

## Advanced Features

### Redis Setup (Optional)
Enable persistent memory for agents using Redis.

```yaml
# ~/.config/kagura/agents/system.yml
redis:
  host: localhost
  port: 6379
  db: 0
```

### Multi-LLM Support
Switch seamlessly between supported LLMs:
```yaml
llm:
  model: ollama/gemma2.5
```

---

## Roadmap

🚧 **Roadmap**:
- Web API interface
- Memory-based agent state management
- RAG-based knowledge integration
- Docker deployment
