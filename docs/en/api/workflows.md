# Workflows API Reference

## Overview

The Workflows API provides decorators and utilities for creating multi-agent orchestrations that coordinate agents and tools to accomplish complex tasks.

---

## `@workflow` Decorator

Convert an async function into a registered workflow.

### Signature

```python
@workflow
async def function_name(...) -> ReturnType:
    """Function docstring"""
    # Orchestration logic
    pass

# Or with custom name
@workflow(name="custom_name")
async def function_name(...) -> ReturnType:
    """Function docstring"""
    # Orchestration logic
    pass
```

### Parameters

- **fn** (`Callable[P, Awaitable[T]] | None`): Function to decorate (optional, for use without parentheses)
- **name** (`str | None`): Custom workflow name (defaults to function name)

### Returns

- **Callable[P, Awaitable[T]]**: Decorated async function

### Behavior

1. **Execution**: Executes the function body (unlike @agent which calls LLM)
2. **Registry Integration**: Automatically registers workflow in global `workflow_registry`
3. **Metadata Preservation**: Preserves function name, docstring, and signature
4. **Async Support**: Fully supports async/await patterns

### Metadata Attributes

Decorated functions have the following metadata attributes:

- **`_is_workflow`** (`bool`): Always `True` for workflow-decorated functions
- **`_workflow_name`** (`str`): Workflow name (function name or custom name)
- **`_workflow_signature`** (`inspect.Signature`): Function signature
- **`_workflow_docstring`** (`str`): Function docstring

### Examples

#### Basic Workflow

```python
from kagura import workflow, agent

@agent
async def search(query: str) -> str:
    """Search for {{ query }}"""
    ...

@agent
async def summarize(text: str) -> str:
    """Summarize: {{ text }}"""
    ...

@workflow
async def research(topic: str) -> dict:
    """Research workflow"""
    results = await search(topic)
    summary = await summarize(results)
    return {"results": results, "summary": summary}

data = await research("AI safety")
```

#### Workflow with Custom Name

```python
@workflow(name="analysis_pipeline")
async def analyze(data: str) -> dict:
    """Data analysis pipeline"""
    validated = await validate_agent(data)
    processed = await process_agent(validated)
    return {"validated": validated, "processed": processed}

# Registered as "analysis_pipeline"
```

#### Sequential Execution

```python
@workflow
async def content_pipeline(topic: str) -> dict:
    """Create content through stages"""
    research = await research_agent(topic)
    draft = await writing_agent(research)
    final = await editing_agent(draft)
    return {"research": research, "draft": draft, "final": final}
```

#### Parallel Execution

```python
import asyncio

@workflow
async def multi_source(topic: str) -> dict:
    """Gather from multiple sources"""
    results = await asyncio.gather(
        source_a_agent(topic),
        source_b_agent(topic),
        source_c_agent(topic)
    )
    a, b, c = results
    combined = await synthesis_agent(f"A: {a}\nB: {b}\nC: {c}")
    return {"sources": results, "synthesis": combined}
```

#### Conditional Logic

```python
@workflow
async def adaptive(text: str) -> dict:
    """Adapt processing based on content"""
    category = await classifier_agent(text)

    if category == "technical":
        result = await technical_processor(text)
    else:
        result = await general_processor(text)

    return {"category": category, "result": result}
```

#### Error Handling

```python
@workflow
async def resilient(task: str) -> dict:
    """Workflow with error handling"""
    try:
        result = await primary_agent(task)
    except Exception:
        result = await fallback_agent(task)

    return {"task": task, "result": result}
```

---

## Workflow Registry

### `WorkflowRegistry` Class

Global registry for all Kagura workflows.

#### Methods

##### `register(name: str, func: Callable[..., Any]) -> None`

Register a workflow.

**Parameters**:
- `name` (`str`): Workflow name (must be unique)
- `func` (`Callable`): Workflow function

**Raises**:
- `ValueError`: If workflow name is already registered

**Example**:
```python
from kagura.core.workflow_registry import workflow_registry

async def my_workflow():
    return "result"

workflow_registry.register("my_workflow", my_workflow)
```

##### `get(name: str) -> Callable[..., Any] | None`

Get workflow by name.

**Parameters**:
- `name` (`str`): Workflow name

**Returns**:
- Workflow function, or `None` if not found

**Example**:
```python
workflow = workflow_registry.get("my_workflow")
if workflow:
    result = await workflow()
```

##### `get_all() -> dict[str, Callable[..., Any]]`

Get all registered workflows.

**Returns**:
- Dictionary of `workflow_name` → `workflow_function`

**Example**:
```python
all_workflows = workflow_registry.get_all()
for name, func in all_workflows.items():
    print(f"{name}: {func.__doc__}")
```

##### `list_names() -> list[str]`

List all workflow names.

**Returns**:
- List of workflow names

**Example**:
```python
names = workflow_registry.list_names()
print(names)  # ['research', 'analysis', 'content_pipeline']
```

##### `unregister(name: str) -> None`

Unregister a workflow.

**Parameters**:
- `name` (`str`): Workflow name

**Raises**:
- `KeyError`: If workflow is not registered

**Example**:
```python
workflow_registry.unregister("my_workflow")
```

##### `clear() -> None`

Clear all workflows from registry.

**Example**:
```python
workflow_registry.clear()
assert len(workflow_registry.list_names()) == 0
```

##### `auto_discover(module_path: str) -> None`

Auto-discover workflows in a module.

Scans a module for functions decorated with `@workflow` and automatically registers them.

**Parameters**:
- `module_path` (`str`): Python module path (e.g., `"my_package.workflows"`)

**Raises**:
- `ValueError`: If module is not found

**Example**:
```python
# my_package/workflows.py
from kagura import workflow

@workflow
async def workflow1():
    return 1

@workflow
async def workflow2():
    return 2

# main.py
from kagura.core.workflow_registry import workflow_registry

workflow_registry.auto_discover("my_package.workflows")
print(workflow_registry.list_names())  # ['workflow1', 'workflow2']
```

### Global Registry Instance

The global `workflow_registry` instance is automatically created and available for import:

```python
from kagura.core.workflow_registry import workflow_registry

# Check if workflow exists
if "my_workflow" in workflow_registry.list_names():
    workflow = workflow_registry.get("my_workflow")
    result = await workflow()
```

---

## Common Patterns

### Chaining Agents

```python
@workflow
async def chain(input_data: str) -> str:
    """Chain multiple agents"""
    step1 = await agent1(input_data)
    step2 = await agent2(step1)
    step3 = await agent3(step2)
    return step3
```

### Fan-Out/Fan-In

```python
@workflow
async def fan_out_fan_in(input_data: str) -> str:
    """Process in parallel, then combine"""
    # Fan-out: Process in parallel
    results = await asyncio.gather(
        processor1(input_data),
        processor2(input_data),
        processor3(input_data)
    )

    # Fan-in: Combine results
    combined = await combiner_agent(results)
    return combined
```

### Loop Processing

```python
@workflow
async def batch_process(items: list) -> list:
    """Process multiple items"""
    results = []
    for item in items:
        result = await processing_agent(item)
        results.append(result)
    return results
```

### Conditional Branching

```python
@workflow
async def route_by_type(data: str) -> dict:
    """Route based on data type"""
    data_type = await type_detector(data)

    if data_type == "A":
        result = await handler_a(data)
    elif data_type == "B":
        result = await handler_b(data)
    else:
        result = await default_handler(data)

    return {"type": data_type, "result": result}
```

### Retry Logic

```python
@workflow
async def with_retry(task: str) -> dict:
    """Retry on failure"""
    max_attempts = 3

    for attempt in range(max_attempts):
        try:
            result = await unreliable_agent(task)
            return {"task": task, "result": result, "attempts": attempt + 1}
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            await asyncio.sleep(2 ** attempt)

    raise RuntimeError("Should not reach here")
```

---

## Integration

### With Agents

```python
from kagura import workflow, agent

@agent
async def my_agent(query: str) -> str:
    """Process {{ query }}"""
    ...

@workflow
async def my_workflow(input_data: str) -> dict:
    """Use agents in workflow"""
    result1 = await my_agent(input_data)
    result2 = await my_agent(result1)
    return {"result1": result1, "result2": result2}
```

### With Tools

```python
from kagura import workflow, tool, agent

@tool
def calculate(x: float, y: float) -> float:
    """Calculate something"""
    return x * y

@agent
async def analyzer(result: float) -> str:
    """Analyze {{ result }}"""
    ...

@workflow
async def hybrid(x: float, y: float) -> dict:
    """Combine tools and agents"""
    # Use tool
    calculation = calculate(x, y)

    # Use agent
    analysis = await analyzer(calculation)

    return {"calculation": calculation, "analysis": analysis}
```

### With MCP

Workflows are automatically exposed via MCP:

```python
@workflow
async def mcp_workflow(query: str) -> dict:
    """This workflow is available via MCP"""
    result = await process_agent(query)
    return {"query": query, "result": result}

# Automatically available in MCP
# Run: kagura mcp start
```

---

## Best Practices

### 1. Clear Documentation

```python
@workflow
async def documented_workflow(input_data: str) -> dict:
    """
    Process data through multiple stages.

    Args:
        input_data: Raw input to process

    Returns:
        Dictionary with processed results

    Workflow Stages:
        1. Validation
        2. Processing
        3. Analysis
        4. Reporting
    """
    validated = await validation_agent(input_data)
    processed = await processing_agent(validated)
    analyzed = await analysis_agent(processed)
    report = await reporting_agent(analyzed)

    return {
        "validated": validated,
        "processed": processed,
        "analyzed": analyzed,
        "report": report
    }
```

### 2. Error Handling

```python
@workflow
async def safe_workflow(task: str) -> dict:
    """Workflow with comprehensive error handling"""
    try:
        result = await risky_agent(task)
    except ValueError as e:
        # Handle specific error
        result = await fallback_agent(task)
    except Exception as e:
        # Handle any other error
        raise RuntimeError(f"Workflow failed: {e}") from e

    return {"task": task, "result": result}
```

### 3. Modular Design

```python
# Reusable sub-workflows
@workflow
async def data_prep(raw: str) -> dict:
    """Reusable data preparation"""
    cleaned = await clean_agent(raw)
    normalized = await normalize_agent(cleaned)
    return {"cleaned": cleaned, "normalized": normalized}

@workflow
async def main_workflow(input_data: str) -> dict:
    """Main workflow using sub-workflows"""
    prepared = await data_prep(input_data)
    analysis = await analysis_agent(prepared["normalized"])
    return {"prepared": prepared, "analysis": analysis}
```

### 4. Type Hints

```python
@workflow
async def typed_workflow(
    data: list[str],
    options: dict[str, Any]
) -> dict[str, list[str]]:
    """Workflow with clear type hints"""
    results = []
    for item in data:
        result = await process_agent(item, options)
        results.append(result)

    return {"processed": results}
```

---

## See Also

- [Workflows Tutorial](../tutorials/12-workflows.md)
- [Agent Decorator](./agents.md)
- [Tool Decorator](./tools.md)
- [MCP Integration](./mcp.md)
