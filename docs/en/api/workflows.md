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

## Advanced Workflow Features

Kagura v2.2.0 introduces advanced workflow capabilities for complex multi-agent orchestration.

### Workflow Context Sharing

Share state across workflow steps using context dictionary:

```python
@workflow
async def context_workflow(input_data: str, workflow_context: dict) -> dict:
    """Workflow with shared context"""

    # Initialize context
    workflow_context["step_count"] = 0
    workflow_context["accumulated_data"] = []

    # Step 1
    workflow_context["step_count"] += 1
    result1 = await agent1(input_data)
    workflow_context["accumulated_data"].append(result1)

    # Step 2 - uses context from step 1
    workflow_context["step_count"] += 1
    result2 = await agent2(result1, previous_data=workflow_context["accumulated_data"])

    return {
        "final_result": result2,
        "steps_executed": workflow_context["step_count"]
    }

# Execute with context
context = {}
result = await context_workflow("input", workflow_context=context)
print(f"Executed {context['step_count']} steps")
```

### Conditional Branching

Implement conditional logic in workflows:

```python
@workflow
async def conditional_workflow(query: str) -> dict:
    """Workflow with conditional branches"""

    # Classify query
    classification = await classifier_agent(query)

    # Branch based on classification
    if classification == "technical":
        result = await technical_agent(query)
    elif classification == "business":
        result = await business_agent(query)
    else:
        result = await general_agent(query)

    return {"classification": classification, "result": result}
```

### Parallel Execution

Execute multiple agents in parallel:

```python
import asyncio

@workflow
async def parallel_workflow(input_data: str) -> dict:
    """Workflow with parallel agent execution"""

    # Execute agents in parallel
    results = await asyncio.gather(
        agent1(input_data),
        agent2(input_data),
        agent3(input_data)
    )

    # Combine results
    combined = await synthesis_agent(results)

    return {"individual": results, "combined": combined}
```

### Retry Logic

Implement automatic retry for failed steps:

```python
@workflow
async def retry_workflow(data: str, max_retries: int = 3) -> dict:
    """Workflow with retry logic"""

    for attempt in range(max_retries):
        try:
            result = await unreliable_agent(data)
            return {"success": True, "result": result, "attempts": attempt + 1}
        except Exception as e:
            if attempt == max_retries - 1:
                # Final attempt failed
                return {"success": False, "error": str(e), "attempts": attempt + 1}
            # Wait before retry
            await asyncio.sleep(2 ** attempt)  # Exponential backoff

    return {"success": False, "error": "Max retries exceeded"}
```

### Dynamic Agent Selection

Select agents dynamically based on runtime conditions:

```python
@workflow
async def dynamic_workflow(query: str, agent_pool: dict) -> dict:
    """Workflow with dynamic agent selection"""

    # Analyze query to determine best agent
    analysis = await analyzer_agent(query)

    # Select agent from pool
    selected_agent_name = analysis["recommended_agent"]
    selected_agent = agent_pool.get(selected_agent_name)

    if not selected_agent:
        raise ValueError(f"Agent {selected_agent_name} not found")

    # Execute selected agent
    result = await selected_agent(query)

    return {
        "selected_agent": selected_agent_name,
        "result": result
    }

# Usage
agents = {
    "translator": translator_agent,
    "summarizer": summarizer_agent,
    "analyzer": analyzer_agent
}

result = await dynamic_workflow("Translate to French", agent_pool=agents)
```

### Workflow Monitoring

Track workflow execution with telemetry:

```python
import time

@workflow
async def monitored_workflow(data: str) -> dict:
    """Workflow with execution monitoring"""

    start_time = time.time()
    steps_executed = []

    try:
        # Step 1
        step_start = time.time()
        result1 = await agent1(data)
        steps_executed.append({
            "step": "agent1",
            "duration": time.time() - step_start,
            "success": True
        })

        # Step 2
        step_start = time.time()
        result2 = await agent2(result1)
        steps_executed.append({
            "step": "agent2",
            "duration": time.time() - step_start,
            "success": True
        })

        return {
            "result": result2,
            "metadata": {
                "total_duration": time.time() - start_time,
                "steps": steps_executed
            }
        }

    except Exception as e:
        steps_executed.append({
            "step": "error",
            "error": str(e),
            "success": False
        })
        raise
```

### Workflow Composition

Compose workflows from sub-workflows:

```python
@workflow
async def data_processing_workflow(data: str) -> dict:
    """Sub-workflow for data processing"""
    cleaned = await clean_agent(data)
    normalized = await normalize_agent(cleaned)
    return {"cleaned": cleaned, "normalized": normalized}


@workflow
async def analysis_workflow(data: dict) -> dict:
    """Sub-workflow for analysis"""
    insights = await analysis_agent(data["normalized"])
    summary = await summary_agent(insights)
    return {"insights": insights, "summary": summary}


@workflow
async def master_workflow(raw_data: str) -> dict:
    """Master workflow composing sub-workflows"""

    # Execute sub-workflows in sequence
    processed = await data_processing_workflow(raw_data)
    analyzed = await analysis_workflow(processed)

    # Combine results
    return {
        "processing": processed,
        "analysis": analyzed,
        "pipeline": "master_workflow"
    }
```

### Complete Advanced Example

```python
import asyncio
import time
from kagura import agent, workflow


@agent
async def classifier(text: str) -> str:
    '''Classify {{ text }} as: technical, business, or general'''
    pass


@agent
async def technical_expert(query: str) -> str:
    '''Technical answer: {{ query }}'''
    pass


@agent
async def business_expert(query: str) -> str:
    '''Business answer: {{ query }}'''
    pass


@agent
async def summarizer(text: str) -> str:
    '''Summarize: {{ text }}'''
    pass


@workflow
async def intelligent_workflow(
    query: str,
    workflow_context: dict,
    max_retries: int = 3
) -> dict:
    """Advanced workflow with multiple features"""

    start_time = time.time()
    workflow_context["steps"] = []

    # Step 1: Classification
    classification = await classifier(query)
    workflow_context["steps"].append({"step": "classification", "result": classification})

    # Step 2: Conditional routing with retry
    for attempt in range(max_retries):
        try:
            if classification == "technical":
                response = await technical_expert(query)
            elif classification == "business":
                response = await business_expert(query)
            else:
                # Parallel execution for general queries
                responses = await asyncio.gather(
                    technical_expert(query),
                    business_expert(query)
                )
                response = " | ".join(responses)

            workflow_context["steps"].append({"step": "response", "attempt": attempt + 1})
            break

        except Exception as e:
            if attempt == max_retries - 1:
                workflow_context["steps"].append({"step": "error", "error": str(e)})
                raise
            await asyncio.sleep(1)

    # Step 3: Summarization
    summary = await summarizer(response)
    workflow_context["steps"].append({"step": "summary"})

    # Return comprehensive result
    return {
        "classification": classification,
        "response": response,
        "summary": summary,
        "metadata": {
            "duration": time.time() - start_time,
            "steps_executed": len(workflow_context["steps"])
        }
    }


# Execute
async def main():
    context = {}
    result = await intelligent_workflow(
        "Explain machine learning",
        workflow_context=context
    )

    print(f"Classification: {result['classification']}")
    print(f"Summary: {result['summary']}")
    print(f"Steps executed: {result['metadata']['steps_executed']}")


asyncio.run(main())
```

### Best Practices for Advanced Workflows

1. **Use Context Judiciously**: Only share state that's truly needed across steps
2. **Handle Errors Gracefully**: Implement proper error handling and recovery
3. **Monitor Performance**: Track execution time and identify bottlenecks
4. **Keep It Modular**: Break complex workflows into reusable sub-workflows
5. **Document Branching Logic**: Make conditional logic clear and well-documented

---

## See Also

- [Workflows Tutorial](../tutorials/12-workflows.md)
- [Agent Decorator](./agents.md)
- [Tool Decorator](./tools.md)
- [MCP Integration](./mcp.md)
- [RFC-001: Advanced Workflow System](../../ai_docs/rfcs/RFC_001_WORKFLOWS.md)
