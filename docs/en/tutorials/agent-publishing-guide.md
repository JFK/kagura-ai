# Kagura Agent Publishing Guide

This guide provides instructions on how to create, test, and publish agents for the Kagura platform.

## Repository Structure
```
kagura-agents/
├── src/
│   └── agent_name/
│       ├── agent.yml
│       ├── state_model.yml
│       └── tools.py
├── tests/
│   └── agent_name/
│       └── test_agent.py
├── examples/
│   └── agent_name/
│       └── example.py
├── pyproject.toml
├── uv.lock
└── README.md
```

## Creating an Agent

Before creating a new agent, make sure to install the Kagura CLI and create a new agent template.

### Building An Agent

See: [Building Your First Agent](first-agent.md)


###  Testing (tests/agent_name/test_agent.py)
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
Also see the [CONTIBUTING](https://github.com/JFK/kagura-ai/blob/main/CONTRIBUTING.md) guide for more information.

```bash
pytest tests/agent_name/test_agent.py
```

### Example Usage (examples/agent_name/example.py)
```python
from kagura.core.agent import Agent

async def run_example():
    agent = Agent.assigner("agent_name")
    result = await agent.execute({
        "input": "example data"
    })
    print(result.output)
```

### Agent Documentation (agents/agent_name/README.md)
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
