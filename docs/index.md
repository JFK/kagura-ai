![Kagura AI Logo](assets/kagura-logo.svg)

# Introduction to Kagura AI

Kagura is a powerful yet simple AI agent framework designed for building, configuring, and orchestrating AI systems through YAML files. Combining flexibility and modularity with ease of use, Kagura empowers developers to create sophisticated AI workflows effortlessly.

---

## Key Features

- **YAML-based Configuration**: Define agents, workflows, and state models in a human-readable format.
- **Multiple LLM Support**: Seamlessly integrate with OpenAI, Anthropic, Ollama, Google, and more via [LiteLLM](https://github.com/BerriAI/litellm).
- **State Management**: Type-safe state handling with Pydantic models.
- **Workflow Orchestration**: Build and control complex AI workflows through multi-agent composition.
- **Extensibility**: Customize tools, hooks, and plugins to extend functionality.
- **Multilingual**: Native support for multiple languages.
- **Assistant Interface**: Console-based interactions with optional Redis-backed memory for persistence.

## Core Components

### Agent Types
- **Atomic Agent**: Fundamental, stateful LLM agents with pre/post-processing hooks.
- **Function Agent**: Task-specific, independent data processors.
- **Orchestrator Agent**: Multi-agent workflow controller built on [LangGraph](https://www.langchain.com/langgraph).

### State Management
- Pydantic model validation for type-safe state handling.
- Inter-agent state sharing for seamless data transfer.
- YAML-based serialization for persistence and portability.

### Tool Integration
- Custom tool and hook support for extending agent capabilities.
- Pre/post-processing hooks for flexible data handling.
- Connectors for external services to enhance workflow integration.

### Assistant Interface
- Console-based interaction with a user-friendly interface.
- Optional persistent memory using Redis.
- [WIP] Ability to call Kagura agent functions directly from the console.

## Resources

- [Installation Guide](en/installation.md)
- [Configuration Guide](en/configuration.md)
- [Quick Start Tutorial](en/quickstart.md)

---

[Get Started →](en/installation.md){: .md-button .md-button--primary }
