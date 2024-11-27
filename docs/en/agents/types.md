# Agent Types

Kagura provides three core agent types, each tailored for specific tasks and workflows. Understanding these types will help you choose the best one for your project.

---

## **Atomic Agent**

### Overview
The Atomic Agent is the foundational building block for stateful AI tasks. It interacts with LLMs and supports flexible configurations for complex processing.

### Key Features
- **Stateful LLM Processing**: Manages input and output states using YAML-defined models.
- **Pre/Post-Processing Hooks**: Allows for additional customization before and after LLM interactions.
- **Structured Outputs**: Ensures consistency through type-safe validation.

### Use Cases
- Generating structured content like summaries or reports.
- Answering complex queries with context-aware responses.
- Processing multi-step LLM workflows.

### Example Configuration
```yaml
# agent.yml
llm:
  model: openai/gpt-4
  max_tokens: 2048
  retry_count: 3
description:
  - language: en
    text: An agent for summarizing documents.
prompt:
  - language: en
    template: |
      Summarize: {TEXT}
response_fields:
  - summary
```

---

## **Function Agent**

### Overview
The Function Agent is designed for tasks that do not involve LLMs. It excels at fast data transformations and external API integrations.

### Key Features
- **No LLM Dependency**: Focuses on computational tasks.
- **Fast Execution**: Optimized for quick processing.
- **Extensibility**: Supports integration with custom tools and APIs.

### Use Cases
- Fetching data from external sources.
- Transforming or validating structured data.
- Integrating with external APIs for domain-specific tasks.

### Example Configuration
```yaml
# agent.yml
custom_tool: kagura.tools.data_fetcher
response_fields:
  - data
```

---

## **Orchestrator Agent**

### Overview
The Orchestrator Agent coordinates workflows involving multiple agents. It manages state sharing, conditional routing, and error handling across agents.

### Key Features
- **Multi-Agent Workflows**: Integrates and coordinates multiple agents (Atomic Agent and Function Agent) in a single workflow.
- **State Binding**: Shares and transfers state between agents seamlessly.
- **Conditional Routing**: Supports dynamic transitions between workflow nodes based on runtime conditions.
- **Error Recovery**: Handles errors gracefully with retry mechanisms and fallback options.
- **No State Model Requirement**: Relies on predefined configurations of Atomic Agent and Function Agent, eliminating the need for its own `state_model.yml`.

### Use Cases
- Coordinating a pipeline for document analysis and summarization.
- Managing workflows that combine data processing and LLM interactions.
- Implementing complex multi-step decision-making systems.

### Example Configuration
```yaml
# agent.yml
entry_point: data_collector
nodes:
  - data_collector
  - analyzer
  - summarizer

edges:
  - from: data_collector
    to: analyzer
  - from: analyzer
    to: summarizer

state_field_bindings:
  - from: data_collector.data
    to: analyzer.input_text
  - from: analyzer.result.text
    to: summarizer.context
```

---

## Choosing the Right Agent

| Agent Type     | Use When You Need                         |
|----------------|------------------------------------------|
| Atomic Agent    | Context-aware LLM interactions.          |
| Function Agent | Fast data transformations and API calls. |
| Orchestrator Agent   | Complex, multi-step workflows.           |
