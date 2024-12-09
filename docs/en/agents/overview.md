# Overview

Kagura AI Agents are the core building blocks of the Kagura AI system. These modular components enable developers to create flexible, reusable, and scalable workflows for various applications.

---

## What is a Kagura AI Agent?

A Kagura agent is a self-contained unit designed to:

- Perform specific tasks in an AI workflow.
- Manage state data through YAML-defined models.
- Interact with other agents via state sharing and orchestration.

Agents are configurable and extensible, making them adaptable to diverse use cases.

---

## Core Agent Properties

1. **Independence**: Each agent operates as a standalone module with its own state and logic.
2. **Collaboration**: Agents can share states and collaborate within workflows.
3. **Extensibility**: Agents can include custom tools and pre/post-processing hooks.
4. **Type Safety**: All data is validated using Pydantic models, ensuring consistency.

---

## Agent Types

Kagura offers three primary agent types, each designed for specific use cases:

**Atomic Agent**:

 - Core stateful agent for LLM tasks.
 - Supports pre- and post-processing hooks for flexibility.
 - Generates structured outputs with type-safe validation.

**Tool Agent**:

 - Focuses on non-LLM data processing.
 - Ideal for data transformations, API integrations, and fast execution.

**Workflow Agent**:

  - Manages workflows involving multiple agents.
  - Enables conditional routing, error recovery, and progress monitoring.
  - Uses predefined Atomic Agent and Tool Agent to orchestrate tasks.


For a detailed description of each agent type, see the [Agent Types](types.md) document.

---

## Agent Configuration

Agents are configured using YAML files, which define their roles, state models, and interactions. The basic structure of an agent is as follows:

```
agents/
└── agent_name/
    ├── agent.yml         # Core configuration
    ├── state_model.yml   # State definition
    └── tools.py          # Custom tools
```

To learn more about setting up agents, refer to the [Agent Configuration](configuration.md) document.

---

## Workflow Integration

Agents are orchestrated to form complex workflows. The workflow agent handles state sharing, data transformations, and conditional logic between agents. For more information on orchestrating agents, see the [Workflow Agent](types.md#workflow-agent) section.

---

## Custom Tools

Agents can be extended with custom tools for specialized tasks. These tools integrate seamlessly into the agent’s lifecycle, providing additional functionality. See the [Custom Tool](configuration.md#custom-tools) section for more details.

---

## Next Steps

To start building with Kagura agents:

- Understand the available [Agent Types](types.md).
- Learn how to set up [Agent Configurations](configuration.md).

These guides will help you effectively utilize Kagura agents in your projects.
