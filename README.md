# Kagura AI

![Kagura AI Logo](https://www.kagura-ai.com/assets/kagura-logo.svg)

![Python versions](https://img.shields.io/pypi/pyversions/kagura-ai.svg)
![PyPI version](https://img.shields.io/pypi/v/kagura-ai.svg)
![PyPI - Downloads](https://img.shields.io/pypi/dm/kagura-ai)
![Codecov](https://img.shields.io/codecov/c/github/JFK/kagura-ai)
![Tests](https://img.shields.io/github/actions/workflow/status/JFK/kagura-ai/test.yml?label=tests)
![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)
![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)

Kagura AI is a lightweight open-source framework specialized in building and orchestrating AI Multi Agents. Named after the traditional Japanese performance art "Kagura (神楽)", it enables sophisticated AI agent systems through simple YAML-based configurations while embodying the principles of harmony, connection, and respect.

---

## Why Kagura AI?

The name **Kagura AI** reflects the principles of Kagura: harmony, connection, and balance. By adopting these values, Kagura AI seeks to create responsible AI systems that prioritize collaboration, innovation, and ethical design.

- **Harmony**: Integrates diverse technologies into cohesive workflows, just as Kagura weaves music, dance, and ritual into a unified performance.
- **Connection**: Facilitates seamless inter-agent communication, mirroring Kagura's role in linking humanity, nature, and the divine.
- **Creativity**: Combines innovative AI solutions with timeless principles, embodying Kagura's balance between tradition and artistic expression.

These principles form the foundation of Kagura AI's **Core Concepts**, ensuring a flexible, reliable, and ethical framework for building and orchestrating intelligent agents.

---

## Core Concepts

### Atomic Agent
- **Task-Specific Operations**: Atomic Agents are designed to handle high-granularity, specialized tasks efficiently and independently.
- **Modular and Decoupled**: Operates as standalone units or integrates with other agents via loose coupling, akin to microservices.
- **Flexibility**: Can interact with functions, tools, or external APIs, enabling seamless integration in larger workflows.

### Orchestration Framework
- **Multi-Agent Coordination**: Combines multiple Atomic Agents to execute complex, multi-step workflows.
- **Dynamic Routing**: Supports conditional branching and flow control for advanced task orchestration.
- **Collaborative Functionality**: Acts as a unified system while maintaining individual agent autonomy.

### State and Response Management
- **Type-Safe State Handling**: Uses Pydantic models to ensure data integrity and consistency across workflows.
- **Response Customization**: Modular responses allow rapid adaptation to changing requirements.
- **Debugging and Transparency**: Centralized state management simplifies error tracking and improves overall system reliability.

---

## Key Features

- **Atomic Agent Design**: High-granularity, task-specific agents that execute independently or as part of workflows
- **Workflow Orchestration**: Coordinate complex, multi-step processes with dynamic routing
- **State and Response Management**: Ensure data safety and modularity with type-safe states and customizable responses
- **YAML-Based Configuration**: Define agents and workflows in a human-readable format
- **Multi-LLM Support**: Seamlessly connect with OpenAI, Anthropic, Ollama, Google, and more via [LiteLLM](https://github.com/BerriAI/litellm)
- **Extensibility**: Add custom tools, hooks, and plugins for domain-specific tasks
- **Multilingual Support**: Native support for multiple languages
- **Redis Integration**: Optional persistent memory for agents

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
  model: openai/gpt-4o-mini # e.g. ollama/qwen2.5:14b (LiteLLM provider/model)
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

### CLI Commands

- `kagura chat`: Start an interactive chatbot
- `kagura create`: [WIP] Interactively generate AI agent templates
- `kagura --help`: Display available commands


---

## Advanced Usage

### Atomic Agent and Function Integration
Leverage loose coupling to connect agents with functions or external tools for efficient task execution:

```python
async def process_data(state: StateModel) -> StateModel:
    # Custom data processing logic
    return processed_state
```

### Multi-Agent Workflows
Design complex workflows with dynamic routing and inter-agent state sharing:
```yaml
nodes:
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

- 🌐 **Web API Interface**: Serve agents via RESTful APIs
- 🧠 **Agent Memory**: Enhanced state and context management per agent
- 📚 **Agent Knowledge Base**: Knowledge base and RAG integration accessible per agent
- 🐳 **Docker Deployment**: Simplify setup with Docker containers

---

## Contributing to Kagura AI

We welcome all contributors! Whether you're a seasoned developer or new to open source, your input matters. Join us to shape the future of Kagura AI.

### Ways to Contribute
- Report issues or bugs
- Propose new features or improvements
- Submit code, documentation, or tests
- Help review Pull Requests

### Steps to Contribute
1. Read the [Contributing Guide](./CONTRIBUTING.md)
2. Fork the repository and clone it locally
3. Create a branch, make your changes, and submit a Pull Request

---

## Documentation and Resources

- [Full Documentation](https://www.kagura-ai.com/)
- [Quick Start Tutorial](https://www.kagura-ai.com/en/quickstart/)
- [Issues and Discussions](https://github.com/JFK/kagura-ai/issues)

---

Thank you for exploring Kagura AI! Let's build harmonious, innovative, and responsible AI solutions together.
