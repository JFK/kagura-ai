# Multi-step Workflow Example

Demonstrates composing multiple agents to create complex workflows.

## Overview

This example shows how to:
- **Compose agents**: Chain multiple agents together
- **Data flow**: Pass data between agents
- **Pydantic models**: Use structured data for agent communication
- **Jinja2 loops**: Iterate over collections in templates
- **Multi-step workflows**: Implement plan → execute → review pattern

## Architecture

```
Goal (str)
    ↓
create_plan (agent)
    ↓
Plan (Pydantic)
    ↓
execute_step (agent) × N
    ↓
Results (list[str])
    ↓
review_results (agent)
    ↓
Review (str)
```

## Code

### 1. Define Data Models

```python
from pydantic import BaseModel
from typing import List

class Step(BaseModel):
    title: str
    description: str
    order: int

class Plan(BaseModel):
    goal: str
    steps: List[Step]
```

### 2. Create Planning Agent

```python
@agent
async def create_plan(goal: str) -> Plan:
    """Create a detailed plan to achieve this goal: {{ goal }}

    Break it down into concrete, actionable steps.
    """
    pass
```

### 3. Create Execution Agent

```python
@agent
async def execute_step(step_title: str, step_description: str) -> str:
    """Execute this step:
    Title: {{ step_title }}
    Description: {{ step_description }}
    """
    pass
```

### 4. Create Review Agent

```python
@agent
async def review_results(goal: str, results: list[str]) -> str:
    """Review the results:
    Goal: {{ goal }}

    Results:
    {% for result in results %}
    - {{ result }}
    {% endfor %}
    """
    pass
```

### 5. Compose the Workflow

```python
async def run_workflow(goal: str):
    # Create plan
    plan = await create_plan(goal)

    # Execute steps
    results = []
    for step in plan.steps:
        result = await execute_step(step.title, step.description)
        results.append(result)

    # Review results
    review = await review_results(goal, results)

    return plan, results, review
```

## Running the Example

```bash
python agent.py
```

## Expected Output

```
=== Multi-step Workflow Example ===

Example 1: Web Application Development
============================================================
🎯 Goal: Build a simple web application with user authentication

📋 Step 1: Creating plan...
   Created plan with 5 steps

📝 Plan:
   1. Set up project structure
      Create project directories and initialize version control
   2. Design database schema
      Define user model and authentication tables
   3. Implement authentication
      Add login, logout, and registration endpoints
   4. Create frontend pages
      Build HTML templates for auth pages
   5. Test the application
      Write and run tests for all features

⚙️  Step 2: Executing plan...
   Executing: Set up project structure
   ✓ Initialize a new directory, create virtual environment, install Flask...
   ...

🔍 Step 3: Reviewing results...
   The plan was successfully executed. All authentication features are implemented...
```

## Key Concepts

### Agent Composition

Agents are just async functions, so they can call each other:

```python
result1 = await agent1(input)
result2 = await agent2(result1)
result3 = await agent3(result2)
```

### Data Flow

Use Pydantic models to ensure type safety between agents:

```python
plan: Plan = await create_plan(goal)  # Structured output
for step in plan.steps:              # Type-safe iteration
    result = await execute_step(step.title, step.description)
```

### Jinja2 Loops

Use loops in templates to handle collections:

```python
"""
{% for item in items %}
- {{ item }}
{% endfor %}
"""
```

### Workflow Patterns

Common patterns:
- **Linear**: A → B → C
- **Fan-out**: A → [B1, B2, B3]
- **Conditional**: A → (B if condition else C)
- **Loop**: A → B → (back to A until done)

## Advanced Example

### Parallel Execution

```python
import asyncio

# Execute steps in parallel
results = await asyncio.gather(
    execute_step(steps[0].title, steps[0].description),
    execute_step(steps[1].title, steps[1].description),
    execute_step(steps[2].title, steps[2].description),
)
```

### Conditional Workflows

```python
plan = await create_plan(goal)

if plan.needs_research:
    research = await do_research(plan.topic)
    plan = await refine_plan(plan, research)

results = await execute_plan(plan)
```

### Error Handling

```python
results = []
for step in plan.steps:
    try:
        result = await execute_step(step.title, step.description)
        results.append({"success": True, "result": result})
    except Exception as e:
        results.append({"success": False, "error": str(e)})
```

## Next Steps

- See [simple_chat](../simple_chat/) for basic agent usage
- See [data_extractor](../data_extractor/) for Pydantic models
- See [code_generator](../code_generator/) for code execution
- Combine workflows with code execution for powerful automation
