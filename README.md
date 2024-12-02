![Kagura AI Logo](https://www.kagura-ai.com/assets/kagura-logo.svg)

![Python versions](https://img.shields.io/pypi/pyversions/kagura-ai.svg)
![PyPI version](https://img.shields.io/pypi/v/kagura-ai.svg)
![PyPI - Downloads](https://img.shields.io/pypi/dm/kagura-ai)
![Codecov](https://img.shields.io/codecov/c/github/JFK/kagura-ai)
![Tests](https://img.shields.io/github/actions/workflow/status/JFK/kagura-ai/test.yml?label=tests)
![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)
![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)

# Kagura AI

Kagura AI is an open-source framework inspired by the Japanese traditional art form **Kagura (神楽)**, symbolizing harmony, connection, and respect. This framework enables developers to build, configure, and orchestrate intelligent agents efficiently, combining modularity with cutting-edge AI technologies.

---

## Why Kagura AI?

The name **Kagura AI** reflects the principles of Kagura: harmony, connection, and balance. By adopting these values, Kagura AI seeks to create responsible AI systems that prioritize collaboration, innovation, and ethical design.

- **Harmony**: Integrates diverse technologies into cohesive workflows.
- **Connection**: Facilitates seamless inter-agent communication.
- **Creativity**: Combines innovative AI solutions with timeless principles.

---

## Key Features

- **YAML-based Configuration**: Define agents, workflows, and state models in a human-readable format.
- **Multi-LLM Support**: Connect with OpenAI, Anthropic, Ollama, Google, and more via [LiteLLM](https://github.com/BerriAI/litellm).
- **State Management**: Pydantic-based type-safe state definitions.
- **Workflow Orchestration**: Build complex workflows using multi-agent systems.
- **Extensibility**: Add custom tools, hooks, and plugins for enhanced functionality.
- **Multilingual Support**: Native support for multiple languages.
- **Redis Integration**: Optional persistent memory for agents.

---

## Installation

### Install from GitHub
```bash
git clone https://github.com/JFK/kagura-ai.git
cd kagura-ai
poetry install
```

### Install from PyPI
```bash
pip install kagura-ai
```

---

## Quick Start

Kagura AI simplifies agent creation using YAML files. Below is an example of configuring an agent.

### Agent Configuration Example
```yaml
# ~/.config/kagura/agents/my_agent/agent.yml
llm:
  model: openai/gpt-4
  max_tokens: 4096
description:
  - language: en
    text: "A simple summarizer agent."
instructions:
  - language: en
    text: "Summarize the input text."
prompt:
  - language: en
    template: |
      Summarize this: {TEXT}
response_fields:
  - summary
```

---

## Usage

### Run Kagura AI
```bash
kagura
```

### CLI Commands
- `kagura`: Start the interactive agent interface.
- `kagura create`: Create a new agent configuration.
- `kagura --help`: Display available commands.

---

## Advanced Usage

### Multi-Agent Workflows
Design complex workflows with dynamic routing and inter-agent state sharing:
```yaml
workflow:
  agents:
    - name: text_fetcher
    - name: text_summarizer
  edges:
    - from: text_fetcher
      to: text_summarizer
```

### Redis Integration
Enable persistent memory:
```yaml
# ~/.config/kagura/agents/system.yml
redis:
  host: localhost
  port: 6379
```

---

## Roadmap

- 🌐 **Web API Interface**: Serve agents via RESTful APIs.
- 🧠 **Memory Management**: Persistent memory using Redis or similar backends.
- 📚 **Knowledge Integration**: Add RAG (Retrieval-Augmented Generation) support.
- 🐳 **Docker Deployment**: Simplify setup with Docker containers.

---

## Contributing to Kagura AI

We welcome all contributors! Whether you're a seasoned developer or new to open source, your input matters. Join us to shape the future of Kagura AI.

### Ways to Contribute
- Report issues or bugs.
- Propose new features or improvements.
- Submit code, documentation, or tests.
- Help review Pull Requests.

### Steps to Contribute
1. Read the [Contributing Guide (English)](./CONTRIBUTING.md) or [コントリビューションガイド (日本語)](./CONTRIBUTING_JA.md).
2. Fork the repository and clone it locally.
3. Create a branch, make your changes, and submit a Pull Request.

---

## Documentation and Resources

- [Full Documentation](https://www.kagura-ai.com/)
- [Quick Start Tutorial](https://www.kagura-ai.com/en/quickstart/)
- [Issues and Discussions](https://github.com/JFK/kagura-ai/issues)

---

Thank you for exploring Kagura AI! Let’s build harmonious, innovative, and responsible AI solutions together.
