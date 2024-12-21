# Agent Configuration

Kagura agents are configured using YAML files, allowing you to define their roles, behavior, and state models. This document provides an overview of the configuration structure and examples for each agent type.

---

## Configuration Basics

Each agent requires at least one YAML file:

1. **`agent.yml`**: Defines the agent's behavior, prompts, and tools.

For Atomic Agent and Tool Agent, an optional **`state_model.yml`** can be used to specify the state model. Orchestrator Agent dose not require a `state_model.yml` as they rely on predefined Atomic Agent and Tool Agent configurations.

### Directory Structure
```
agents/
└── agent_name/
    ├── agent.yml         # Core configuration
    ├── state_model.yml   # State definition
    └── tools.py          # Custom tools
```

---

## agent.yml

The `agent.yml` file defines the agent's role, behavior, and processing logic.

### Key Configuration Fields

#### Atomic Agent

- **`llm`**: Configuration for the language model (e.g., `model`, `max_tokens`, `retry_count`).
- **`response_fields`**: Specifies the expected output fields of the agent. Each field listed here must also be included in the `state_model.yml` under `state_fields` to ensure consistency.
- **`post_custom_tool`**: Specifies a custom tool to be executed as a post-processing hook for state data.
- **`pre_custom_tool`**: Specifies a custom tool to be executed as a pre-processing hook for state data.

#### Tool Agent

- **`custom_tool`**: Defines the path to a custom tool that the agent will use. This is the primary configuration field for Tool Agents, allowing them to execute custom logic for specific tasks.
- **`response_fields`**: Required when specifying the fields that the tool is expected to produce. These fields must align with the `state_model.yml` definitions for consistency.

#### Orchestrator Agent

- **`entry_point`**: Specifies the starting node in a workflow. Orchestrator Agents are built using predefined Atomic Agent and Tool Agent configurations and do not require their own `state_model.yml`.
- **`nodes`**: Lists the agents involved in the workflow.
- **`edges`**: Defines the connections between workflow nodes.
- **`state_field_bindings`**: Maps the state fields between agents in the workflow.
- **`conditional_edges`**: Defines conditional transitions between nodes based on runtime evaluations.

---

### Example: Atomic Agent

```yaml
type: atomic  # atomic, tool, or workflow
llm:
  model: openai/gpt-4o-mini # Cusomize the LLM model to use (optional)
  max_tokens: 2048
  retry_count: 3
description:
  - language: en
    text: An agent for summarizing documents.
instructions:
  - language: en
    text: Summarize the following text.
prompt:
  - language: en
    template: |
      {content}
response_fields:
  - summary
input_fields:
  - content
post_custom_tool: agent_name.tools.postprocess_summary  # Finalize the summary output
```

### Example: Tool Agent

```yaml
type: tool
custom_tool: agents.[agent_name].tools.data_fetcher
response_fields: # state fields that the tool produces or updates
  - data
input_fields: # state fields that the tool expects
  - url
  - params
```

### Example: Workflow Agent

```yaml
type: workflow
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
    to: analyzer.input_data
  - from: analyzer.result.text
    to: summarizer.context

conditional_edges:
  - analyzer:
      condition_function: kagura.conditions.check_analysis
      conditions:
        success: summarizer
        retry: analyzer
        failure: error_handler
```

---

## state_model.yml

The `state_model.yml` file defines the input, output, and intermediate state fields for the agent. This file is optional for Atomic Agent and Tool Agent and not used by Orchestrator Agent agents.

### Example: Atomic Agent State Model

```yaml
custom_models: # You can define own custom models here
  - name: SummaryData
    fields:
      - name: text
        type: str
        description:
          - language: en
            text: Text to summarize
      - name: summary
        type: str
        description:
          - language: en
            text: Generated summary

state_fields: # Define the state fields used by the agent and tools
  - name: input_text
    type: str
    description:
      - language: en
        text: Input text for summarization
  - name: output_summary
    type: SummaryData
    description:
      - language: en
        text: Generated summary data
```

---

## Custom Tools

Custom tools can be used to extend the functionality of agents. These tools should be located in the `agent_name/` directory and defined in the `agent.yml` file.
You can change the name of `tools.py` to any other name, but make sure to update the path in the `agent.yml` file.

### Example: Custom Tool

```python
from kagura.core.models import StateModel

async def fetch_data(state: StateModel) -> StateModel:
    """
    Custom tool for fetching data from an external API.
    """
    try:
        state.data = await external_api_fetch(state.url)
        return state
    except Exception as e:
        raise Exception(f"Data fetching failed: {str(e)}")
```

---

## Best Practices

- Keep YAML configurations simple and focused on the agent's specific role.
- Use descriptive field names and comments to ensure maintainability.
- Validate your state models using tools like `pydantic` to avoid runtime errors.
- Leverage pre- and post-processing hooks to customize state data.
