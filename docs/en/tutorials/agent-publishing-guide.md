# Kagura Agent Publishing Guide

This guide provides instructions on how to create, test, and publish agents for the Kagura platform.

## Repository Structure
```
kagura-agents/
├── agents/
│   └── agent_name/
│       ├── agent.yml
│       ├── state_model.yml
│       ├── requirements.txt
│       └── README.md
├── tests/
│   └── agent_name/
│       └── test_agent.py
├── examples/
│   └── agent_name/
│       └── example.py
├── pyproject.toml
└── README.md
```

## Creating an Agent

Before creating a new agent, make sure to install the Kagura CLI and create a new agent template.

See: [Creating a new agent template](agent-template.md)

### Agent Configuration (agent.yml)
```yaml
description:
  - language: en
    text: Agent purpose description
  - language: ja
    text: エージェントの説明

instructions:
  - language: en
    description: System behavior instructions
  - language: ja
    description: システムの動作指示

prompt:
  - language: en
    template: Template with {variables}
  - language: ja
    template: 変数付き{variables}テンプレート

response_fields:
  - field1
  - field2
```

### 2. State Model (state_model.yml)
```yaml
custom_models:
  - name: CustomType
    fields:
      - name: field_name
        type: str
        description:
          - language: en
            text: Field description
          - language: ja
            text: フィールドの説明

state_fields:
  - name: state_field
    type: CustomType
    description:
      - language: en
        text: State field description
      - language: ja
        text: 状態フィールドの説明
```

### 3. Testing (tests/agent_name/test_agent.py)
```python
import pytest
from kagura.core.agent import Agent

@pytest.mark.asyncio
async def test_agent():
    agent = Agent.assigner("agent_name")
    result = await agent.execute({
        "input": "test data"
    })
    assert result.SUCCESS
```

Make sure to run the tests before publishing the agent.

```bash
pytest tests/agent_name/test_agent.py
```

### 4. Example Usage (examples/agent_name/example.py)
```python
from kagura.core.agent import Agent

async def run_example():
    agent = Agent.assigner("agent_name")
    result = await agent.execute({
        "input": "example data"
    })
    print(result.output)
```

### 5. Agent Documentation (agents/agent_name/README.md)
```markdown
# Agent Name

## Purpose
Brief description of what the agent does.

## Configuration
Key configuration options and their meanings.

## Usage
Example of how to use the agent.

## Dependencies
List of required packages.
```

## Publishing

1. Create GitHub repository
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/username/kagura-agents.git
git push -u origin main
```

2. Install agents using Kagura CLI
```bash
kagura install https://github.com/username/kagura-agents
```

## Best Practices

1. Documentation
    - Include clear README for each agent
    - Document all configuration options
    - Provide usage examples

2. Testing
    - Write unit tests for each agent
    - Include edge cases
    - Test multilingual support

3. Dependencies
    - List all requirements
    - Use version constraints
    - Keep dependencies minimal

4. Code Quality
    - Follow Python style guide
    - Use type hints
    - Add proper error handling
