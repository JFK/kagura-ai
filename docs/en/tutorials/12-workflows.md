# Workflows Tutorial

The **@workflow decorator** allows you to create multi-agent orchestrations that coordinate multiple agents and tools to accomplish complex tasks.

## What are Workflows?

Workflows are **multi-agent orchestrations** that combine agents and tools in a coordinated sequence:

- **Coordination**: Call multiple agents in sequence or parallel
- **Data Flow**: Pass results between agents
- **Complex Tasks**: Break down large problems into steps
- **Reusability**: Package multi-step processes

Unlike `@agent` (which calls an LLM) and `@tool` (which executes pure Python), `@workflow` executes the function body to orchestrate agent calls.

---

## Quick Start

### Basic Workflow

```python
from kagura import workflow, agent

@agent
async def search_agent(query: str) -> str:
    """Search for information about {{ query }}"""
    ...

@agent
async def summarize_agent(text: str) -> str:
    """Summarize: {{ text }}"""
    ...

@workflow
async def research_workflow(topic: str) -> dict:
    """Research a topic using multiple agents"""
    # Step 1: Search for information
    search_results = await search_agent(topic)

    # Step 2: Summarize findings
    summary = await summarize_agent(search_results)

    return {
        "topic": topic,
        "findings": search_results,
        "summary": summary
    }

# Use
result = await research_workflow("AI safety")
```

---

## Workflow Features

### 1. Sequential Execution

Execute agents in a specific order:

```python
@workflow
async def content_pipeline(topic: str) -> dict:
    """Create content through multiple stages"""
    # Research phase
    research = await research_agent(topic)

    # Writing phase
    draft = await writing_agent(research)

    # Editing phase
    final = await editing_agent(draft)

    return {
        "topic": topic,
        "draft": draft,
        "final": final
    }
```

### 2. Parallel Execution

Run agents concurrently using `asyncio.gather`:

```python
import asyncio

@workflow
async def multi_source_research(topic: str) -> dict:
    """Research from multiple sources in parallel"""
    # Execute in parallel
    results = await asyncio.gather(
        academic_search_agent(topic),
        news_search_agent(topic),
        social_media_agent(topic)
    )

    academic, news, social = results

    # Combine results
    combined = await synthesis_agent(
        f"Academic: {academic}\nNews: {news}\nSocial: {social}"
    )

    return {
        "academic": academic,
        "news": news,
        "social": social,
        "synthesis": combined
    }
```

### 3. Conditional Logic

Use branching logic based on results:

```python
@workflow
async def smart_analysis(text: str) -> dict:
    """Analyze text with conditional processing"""
    # Classify content type
    content_type = await classifier_agent(text)

    # Different processing based on type
    if content_type == "technical":
        analysis = await technical_analyzer(text)
    elif content_type == "creative":
        analysis = await creative_analyzer(text)
    else:
        analysis = await general_analyzer(text)

    return {
        "type": content_type,
        "analysis": analysis
    }
```

### 4. Error Handling

Handle failures gracefully:

```python
@workflow
async def robust_workflow(query: str) -> dict:
    """Workflow with error handling"""
    try:
        primary_result = await primary_agent(query)
    except Exception as e:
        # Fallback to secondary agent
        primary_result = await fallback_agent(query)

    # Validate result
    if not primary_result:
        raise ValueError("No results found")

    return {
        "query": query,
        "result": primary_result
    }
```

---

## Workflow Registry

All workflows are automatically registered in the global `workflow_registry`:

```python
from kagura.core.workflow_registry import workflow_registry

# List all workflows
print(workflow_registry.list_names())
# ['research_workflow', 'content_pipeline', ...]

# Get a specific workflow
workflow = workflow_registry.get("research_workflow")
result = await workflow("AI safety")

# Get all workflows
all_workflows = workflow_registry.get_all()
for name, func in all_workflows.items():
    print(f"{name}: {func.__doc__}")
```

---

## Examples

### Example 1: Document Processing Workflow

```python
@workflow
async def process_document(file_path: str) -> dict:
    """Complete document processing pipeline"""
    # Extract text
    text = await extract_text_tool(file_path)

    # Analyze sentiment
    sentiment = await sentiment_agent(text)

    # Extract key points
    key_points = await extraction_agent(text)

    # Generate summary
    summary = await summarization_agent(text)

    # Categorize
    category = await categorization_agent(text)

    return {
        "file": file_path,
        "sentiment": sentiment,
        "key_points": key_points,
        "summary": summary,
        "category": category
    }
```

### Example 2: Customer Support Workflow

```python
@workflow
async def customer_support_workflow(ticket: dict) -> dict:
    """Handle customer support ticket"""
    # Classify urgency
    urgency = await urgency_classifier(ticket["description"])

    # Route based on urgency
    if urgency == "high":
        # Immediate escalation
        response = await senior_support_agent(ticket)
    else:
        # Standard processing
        response = await support_agent(ticket)

    # Generate follow-up
    follow_up = await follow_up_agent(response)

    return {
        "ticket_id": ticket["id"],
        "urgency": urgency,
        "response": response,
        "follow_up": follow_up
    }
```

### Example 3: Data Analysis Workflow

```python
@workflow
async def data_analysis_workflow(dataset: str) -> dict:
    """Analyze dataset with multiple techniques"""
    # Load and validate data
    data = await data_loader_tool(dataset)

    # Statistical analysis
    stats = await statistical_agent(data)

    # Pattern detection
    patterns = await pattern_detection_agent(data)

    # Visualization
    viz = await visualization_agent(data, patterns)

    # Report generation
    report = await report_agent(
        f"Stats: {stats}\nPatterns: {patterns}"
    )

    return {
        "dataset": dataset,
        "statistics": stats,
        "patterns": patterns,
        "visualization": viz,
        "report": report
    }
```

### Example 4: Content Creation Workflow

```python
@workflow
async def content_creation_workflow(
    topic: str,
    target_audience: str
) -> dict:
    """Create content tailored to audience"""
    # Research topic
    research = await research_agent(f"{topic} for {target_audience}")

    # Generate outline
    outline = await outline_agent(research)

    # Write content sections in parallel
    sections = await asyncio.gather(
        intro_writer_agent(outline[0]),
        body_writer_agent(outline[1]),
        conclusion_writer_agent(outline[2])
    )

    # Combine sections
    full_content = "\n\n".join(sections)

    # Edit for audience
    edited = await editor_agent(
        f"Edit for {target_audience}: {full_content}"
    )

    # SEO optimization
    seo_optimized = await seo_agent(edited, topic)

    return {
        "topic": topic,
        "audience": target_audience,
        "research": research,
        "outline": outline,
        "content": seo_optimized
    }
```

---

## Integration with Agents and Tools

### Combining Agents and Tools

```python
from kagura import workflow, agent, tool

@tool
def calculate_metrics(data: list) -> dict:
    """Calculate statistical metrics"""
    return {
        "mean": sum(data) / len(data),
        "max": max(data),
        "min": min(data)
    }

@agent
async def insights_agent(metrics: dict) -> str:
    """Generate insights from {{ metrics }}"""
    ...

@workflow
async def analytics_workflow(data: list) -> dict:
    """Analyze data and generate insights"""
    # Use tool for calculations
    metrics = calculate_metrics(data)

    # Use agent for insights
    insights = await insights_agent(metrics)

    return {
        "metrics": metrics,
        "insights": insights
    }
```

---

## Best Practices

### 1. Clear Workflow Structure

```python
@workflow
async def well_structured_workflow(input_data: str) -> dict:
    """
    Process data through multiple stages.

    Stages:
    1. Validation
    2. Processing
    3. Analysis
    4. Reporting
    """
    # Stage 1: Validation
    validated = await validation_agent(input_data)

    # Stage 2: Processing
    processed = await processing_agent(validated)

    # Stage 3: Analysis
    analyzed = await analysis_agent(processed)

    # Stage 4: Reporting
    report = await reporting_agent(analyzed)

    return {
        "validated": validated,
        "processed": processed,
        "analyzed": analyzed,
        "report": report
    }
```

### 2. Error Recovery

```python
@workflow
async def resilient_workflow(task: str) -> dict:
    """Workflow with retry logic"""
    max_retries = 3

    for attempt in range(max_retries):
        try:
            result = await unreliable_agent(task)
            break
        except Exception as e:
            if attempt == max_retries - 1:
                # Final fallback
                result = await fallback_agent(task)
            else:
                # Retry with backoff
                await asyncio.sleep(2 ** attempt)

    return {"task": task, "result": result}
```

### 3. Progress Tracking

```python
@workflow
async def tracked_workflow(items: list) -> dict:
    """Track progress through workflow"""
    results = []
    total = len(items)

    for i, item in enumerate(items, 1):
        print(f"Processing {i}/{total}: {item}")
        result = await processing_agent(item)
        results.append(result)

    return {
        "total": total,
        "processed": len(results),
        "results": results
    }
```

### 4. Modular Design

```python
# Define reusable sub-workflows
@workflow
async def data_prep_workflow(raw_data: str) -> dict:
    """Reusable data preparation"""
    cleaned = await cleaning_agent(raw_data)
    normalized = await normalization_agent(cleaned)
    return {"cleaned": cleaned, "normalized": normalized}

@workflow
async def main_workflow(input_data: str) -> dict:
    """Main workflow using sub-workflows"""
    # Reuse data prep
    prepared = await data_prep_workflow(input_data)

    # Continue with analysis
    analysis = await analysis_agent(prepared["normalized"])

    return {
        "prepared": prepared,
        "analysis": analysis
    }
```

---

## Troubleshooting

### Workflow not found in registry

```python
from kagura.core.workflow_registry import workflow_registry

# Check if workflow is registered
if "my_workflow" not in workflow_registry.list_names():
    print("Workflow not found!")
    print("Available workflows:", workflow_registry.list_names())
```

### Workflow name conflicts

```python
# This will raise ValueError
@workflow
def duplicate():
    pass

@workflow
def duplicate():  # Error: already registered!
    pass

# Solution: Use custom names
@workflow(name="duplicate_v2")
async def duplicate():
    pass
```

### Async/await issues

```python
# ❌ Wrong: Forgot await
@workflow
async def broken_workflow(query: str) -> str:
    result = search_agent(query)  # Missing await!
    return result

# ✅ Correct: Always await agent calls
@workflow
async def correct_workflow(query: str) -> str:
    result = await search_agent(query)
    return result
```

---

## Next Steps

- Learn about [MCP Integration](./06-mcp-integration.md)
- Explore [Agent Routing](./09-agent-routing.md)
- Try [Chat REPL](./10-chat-repl.md)

## Further Reading

- [Workflows API Reference](../api/workflows.md)
- [Workflow Registry API](../api/workflows.md#workflow-registry)
- [MCP Workflows Integration](../api/mcp.md#workflows)
