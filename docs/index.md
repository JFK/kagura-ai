# Introduction to Kagura AI

![Kagura AI Logo](assets/kagura-logo.svg)

Kagura AI is a lightweight open-source framework specialized in building and orchestrating AI Multi Agents. Through simple YAML-based configurations, it enables developers to create sophisticated agent-based systems that work together to accomplish complex tasks with higher accuracy and efficiency.

---

## Design Philosophy

Kagura AI is built on a modular, state-driven architecture that prioritizes:

- **Simplicity**: Simple YAML configurations for complex AI systems
- **Flexibility**: Modular components that can be easily combined
- **Type Safety**: Strong typing and state validation throughout
- **Maintainability**: Clear separation of concerns and state management

## Core Components

### AI Multi Agents

#### Agent Types

- **Atomic Agent**: LLM-powered agents with state management and processing hooks
- **Tool Agent**: Task-specific data processors for independent operations
- **Workflow Agent**: Multi-agent workflow controller for complex task coordination

#### Implementation Structure
```
agents/
└── agent_name/
    ├── agent.yml         # Core configuration
    ├── state_model.yml   # State definition (optional)
    └── tools.py          # Custom tools (optional)
```

### State Architecture

- **Type-Safe Definitions**: Pydantic models ensure data consistency
- **Inter-Agent Communication**: Seamless state sharing between components
- **State Bindings**: Defined pathways for data flow between agents
- **YAML Serialization**: Clear and maintainable state definitions

### Tool Integration

- **Custom Tools**: Extend agent capabilities with custom implementations
- **Processing Hooks**: Pre/post hooks for flexible data handling
- **External Connectors**: Seamless integration with external services
- **LLM Support**: Connect with OpenAI, Anthropic, Ollama, Google via [LiteLLM](https://github.com/BerriAI/litellm)

## Key Features

- **Modular Design**: Each agent operates as a self-contained unit
- **Workflow Orchestration**: Complex task coordination through multi-agent composition
- **Type Safety**: Strong typing and validation throughout the system
- **Extensibility**: Easy addition of custom tools and hooks
- **Multilingual**: Native support for multiple languages

## Get Started

Explore our guides to start building with Kagura AI:

- [Quick Start Tutorial](en/quickstart.md)
- [Installation Guide](en/installation.md)
- [Configuration Guide](en/system-configuration.md)

---

[Get Started →](en/installation.md){: .md-button .md-button--primary }
