## Advanced Workflows Examples

This directory contains examples demonstrating advanced workflow patterns for building robust, efficient, and production-ready agent systems.

## Overview

Advanced workflows provide:
- **Conditional Branching**: Route execution based on runtime conditions
- **Parallel Execution**: Run multiple agents concurrently for better performance
- **Retry Logic**: Handle failures gracefully with retry strategies
- **Error Handling**: Robust error handling and fallback mechanisms
- **Workflow Composition**: Combine patterns for complex systems

## Examples

### 1. Conditional Workflow (`conditional_workflow.py`)

Demonstrates conditional branching and routing:
- Sentiment-based branching
- Content type classification
- Multi-level conditional logic
- Context-aware routing
- State machine workflows
- Priority-based routing

**Run:**
```bash
python examples/advanced_workflows/conditional_workflow.py
```

**Key Patterns:**
```python
@workflow
async def conditional_workflow(text: str) -> str:
    sentiment = await sentiment_analyzer(text)

    if "positive" in sentiment.lower():
        return await positive_responder(text)
    elif "negative" in sentiment.lower():
        return await negative_responder(text)
    else:
        return await neutral_responder(text)
```

---

### 2. Parallel Workflow (`parallel_workflow.py`)

Shows parallel execution patterns:
- Basic parallel execution
- Multi-language translation
- Batch processing
- Mixed parallel/sequential
- Error handling in parallel
- Performance comparison

**Run:**
```bash
python examples/advanced_workflows/parallel_workflow.py
```

**Key Patterns:**
```python
@workflow
async def parallel_workflow(text: str) -> dict:
    # Run multiple agents in parallel
    sentiment, keywords, summary = await asyncio.gather(
        sentiment_analyzer(text),
        keyword_extractor(text),
        summarizer(text)
    )

    return {
        "sentiment": sentiment,
        "keywords": keywords,
        "summary": summary
    }
```

---

### 3. Retry Workflow (`retry_workflow.py`)

Demonstrates retry logic and error handling:
- Basic retry with max attempts
- Exponential backoff
- Fallback strategies
- Partial retry
- Circuit breaker pattern
- Graceful degradation
- Retry budgets

**Run:**
```bash
python examples/advanced_workflows/retry_workflow.py
```

**Key Patterns:**
```python
@workflow
async def retry_workflow(text: str, max_retries: int = 3) -> str:
    for attempt in range(max_retries):
        try:
            result = await unreliable_agent(text)
            return result
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

---

## Workflow Patterns

### Pattern 1: Conditional Routing

```python
@workflow
async def smart_router(query: str) -> str:
    """Route based on query analysis."""
    query_type = await classify_query(query)

    if "question" in query_type:
        return await question_handler(query)
    elif "request" in query_type:
        return await request_handler(query)
    else:
        return await general_handler(query)
```

### Pattern 2: Parallel Analysis

```python
@workflow
async def parallel_analysis(text: str) -> dict:
    """Run multiple analyses in parallel."""
    results = await asyncio.gather(
        sentiment_analyzer(text),
        keyword_extractor(text),
        summarizer(text),
        language_detector(text)
    )

    return {
        "sentiment": results[0],
        "keywords": results[1],
        "summary": results[2],
        "language": results[3]
    }
```

### Pattern 3: Retry with Fallback

```python
@workflow
async def resilient_workflow(text: str) -> str:
    """Try primary agent, fallback on failure."""
    try:
        # Try primary (faster but less reliable)
        return await fast_agent(text)
    except Exception:
        # Fallback (slower but more reliable)
        return await reliable_agent(text)
```

### Pattern 4: Pipeline with Error Handling

```python
@workflow
async def robust_pipeline(text: str) -> dict:
    """Pipeline with per-step error handling."""
    results = {}

    # Step 1
    try:
        results["step1"] = await step1_agent(text)
    except Exception as e:
        results["step1"] = f"Failed: {e}"
        return results  # Early exit

    # Step 2 (depends on step 1)
    try:
        results["step2"] = await step2_agent(results["step1"])
    except Exception as e:
        results["step2"] = f"Failed: {e}"

    return results
```

### Pattern 5: Hybrid Parallel-Sequential

```python
@workflow
async def hybrid_workflow(text: str) -> str:
    """Mix parallel and sequential execution."""
    # Phase 1: Parallel analysis
    sentiment, keywords = await asyncio.gather(
        sentiment_analyzer(text),
        keyword_extractor(text)
    )

    # Phase 2: Sequential processing using Phase 1 results
    enriched = f"Text ({sentiment}) with keywords: {keywords}"
    summary = await summarizer(enriched)

    return summary
```

### Pattern 6: Conditional Parallel

```python
@workflow
async def conditional_parallel(text: str, mode: str) -> dict:
    """Conditionally execute in parallel."""
    if mode == "quick":
        # Quick mode: single agent
        result = await quick_agent(text)
        return {"result": result}

    elif mode == "comprehensive":
        # Comprehensive mode: multiple agents in parallel
        results = await asyncio.gather(
            detailed_agent1(text),
            detailed_agent2(text),
            detailed_agent3(text)
        )
        return {
            "agent1": results[0],
            "agent2": results[1],
            "agent3": results[2]
        }
```

### Pattern 7: Circuit Breaker

```python
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3):
        self.failures = 0
        self.threshold = failure_threshold
        self.state = "closed"  # closed, open, half-open

    def is_open(self) -> bool:
        return self.state == "open"

    def record_success(self):
        self.failures = 0
        self.state = "closed"

    def record_failure(self):
        self.failures += 1
        if self.failures >= self.threshold:
            self.state = "open"

breaker = CircuitBreaker()

@workflow
async def protected_workflow(text: str) -> str:
    """Use circuit breaker to prevent cascading failures."""
    if breaker.is_open():
        raise Exception("Circuit breaker is open")

    try:
        result = await unreliable_agent(text)
        breaker.record_success()
        return result
    except Exception as e:
        breaker.record_failure()
        raise
```

### Pattern 8: Graceful Degradation

```python
@workflow
async def degrading_workflow(text: str) -> dict:
    """Provide partial results on failures."""
    results = {}

    # Try premium features
    try:
        results["detailed_analysis"] = await premium_agent(text)
    except Exception:
        # Fallback to basic features
        try:
            results["basic_analysis"] = await basic_agent(text)
        except Exception:
            results["error"] = "All agents failed"

    return results
```

---

## Async Best Practices

### Using asyncio.gather

```python
# Run multiple coroutines concurrently
results = await asyncio.gather(
    agent1(text),
    agent2(text),
    agent3(text)
)

# With error handling
results = await asyncio.gather(
    agent1(text),
    agent2(text),
    return_exceptions=True  # Return exceptions instead of raising
)
```

### Using asyncio.wait_for (Timeout)

```python
# Set timeout for individual operation
try:
    result = await asyncio.wait_for(
        slow_agent(text),
        timeout=5.0  # 5 second timeout
    )
except asyncio.TimeoutError:
    result = "Agent timed out"
```

### Using asyncio.create_task

```python
# Create tasks for more control
task1 = asyncio.create_task(agent1(text))
task2 = asyncio.create_task(agent2(text))

# Do other work...

# Wait for results
result1 = await task1
result2 = await task2
```

### Task Cancellation

```python
# Cancel tasks if needed
task = asyncio.create_task(long_running_agent(text))

try:
    result = await asyncio.wait_for(task, timeout=5.0)
except asyncio.TimeoutError:
    task.cancel()  # Cancel the task
    result = "Operation cancelled"
```

---

## Retry Strategies

### 1. Simple Retry

```python
max_retries = 3
for attempt in range(max_retries):
    try:
        return await agent(text)
    except Exception:
        if attempt == max_retries - 1:
            raise
```

### 2. Exponential Backoff

```python
for attempt in range(max_retries):
    try:
        return await agent(text)
    except Exception:
        if attempt == max_retries - 1:
            raise
        wait_time = 2 ** attempt  # 1s, 2s, 4s, 8s...
        await asyncio.sleep(wait_time)
```

### 3. Jittered Backoff

```python
import random

for attempt in range(max_retries):
    try:
        return await agent(text)
    except Exception:
        if attempt == max_retries - 1:
            raise
        base_wait = 2 ** attempt
        jitter = random.uniform(0, base_wait * 0.1)
        await asyncio.sleep(base_wait + jitter)
```

### 4. Fixed Delay

```python
for attempt in range(max_retries):
    try:
        return await agent(text)
    except Exception:
        if attempt == max_retries - 1:
            raise
        await asyncio.sleep(1.0)  # Fixed 1s delay
```

---

## Error Handling Patterns

### Pattern 1: Try-Except per Step

```python
@workflow
async def safe_pipeline(text: str) -> dict:
    """Handle errors at each step."""
    results = {}

    try:
        results["step1"] = await step1(text)
    except Exception as e:
        results["step1"] = None
        results["error"] = str(e)
        return results

    # Continue only if step1 succeeded
    try:
        results["step2"] = await step2(results["step1"])
    except Exception as e:
        results["step2"] = None
        results["error"] = str(e)

    return results
```

### Pattern 2: Collect All Errors

```python
@workflow
async def collect_errors(text: str) -> dict:
    """Continue execution and collect all errors."""
    results = {}
    errors = []

    try:
        results["analysis1"] = await agent1(text)
    except Exception as e:
        errors.append(f"Agent1: {e}")

    try:
        results["analysis2"] = await agent2(text)
    except Exception as e:
        errors.append(f"Agent2: {e}")

    return {
        "results": results,
        "errors": errors
    }
```

### Pattern 3: Fail Fast

```python
@workflow
async def fail_fast(text: str) -> dict:
    """Stop on first error."""
    # No try-except, let exceptions propagate
    step1 = await critical_agent1(text)
    step2 = await critical_agent2(step1)
    step3 = await critical_agent3(step2)

    return {"final": step3}
```

---

## Performance Optimization

### Measure Performance

```python
import time

@workflow
async def measured_workflow(text: str) -> tuple:
    """Measure execution time."""
    start = time.time()

    result = await agent(text)

    elapsed = time.time() - start

    return result, elapsed
```

### Parallel vs Sequential

```python
# Sequential (slow)
result1 = await agent1(text)
result2 = await agent2(text)
result3 = await agent3(text)
# Total time: T1 + T2 + T3

# Parallel (fast)
result1, result2, result3 = await asyncio.gather(
    agent1(text),
    agent2(text),
    agent3(text)
)
# Total time: max(T1, T2, T3)
```

### Batch Processing

```python
@workflow
async def batch_process(items: list[str]) -> list:
    """Process items in parallel."""
    tasks = [agent(item) for item in items]
    results = await asyncio.gather(*tasks)
    return results
```

---

## Production Considerations

### 1. Logging

```python
import logging

@workflow
async def logged_workflow(text: str) -> str:
    """Workflow with logging."""
    logging.info(f"Starting workflow for: {text[:50]}")

    try:
        result = await agent(text)
        logging.info("Workflow completed successfully")
        return result
    except Exception as e:
        logging.error(f"Workflow failed: {e}")
        raise
```

### 2. Monitoring

```python
from kagura.observability import EventStore

@workflow
async def monitored_workflow(text: str) -> str:
    """Workflow with monitoring."""
    store = EventStore()

    result = await agent(text)

    # Check execution metrics
    executions = store.get_executions(agent_name="agent", limit=1)
    if executions:
        metrics = executions[0].get("metrics", {})
        if metrics.get("total_cost", 0) > 0.01:
            logging.warning("High cost detected")

    return result
```

### 3. Rate Limiting

```python
import asyncio

class RateLimiter:
    def __init__(self, max_per_second: int):
        self.max_per_second = max_per_second
        self.tokens = max_per_second
        self.last_update = asyncio.get_event_loop().time()

    async def acquire(self):
        while self.tokens < 1:
            await asyncio.sleep(0.1)
            now = asyncio.get_event_loop().time()
            elapsed = now - self.last_update
            self.tokens = min(
                self.max_per_second,
                self.tokens + elapsed * self.max_per_second
            )
            self.last_update = now

        self.tokens -= 1

limiter = RateLimiter(max_per_second=10)

@workflow
async def rate_limited_workflow(text: str) -> str:
    """Workflow with rate limiting."""
    await limiter.acquire()
    return await agent(text)
```

---

## API Reference

For complete API documentation, see:
- [Workflows API Reference](../../docs/en/api/workflows.md)

## Related Examples

- [AgentBuilder Examples](../agent_builder/) - Creating workflow agents
- [Memory-Aware Routing](../memory_routing/) - Routing in workflows
- [Observability Examples](../observability/) - Monitoring workflows

---

**Best Practices Summary:**

1. **Always set timeouts** to prevent hanging
2. **Use exponential backoff** for retries
3. **Implement fallbacks** for critical paths
4. **Run independent operations in parallel** for performance
5. **Handle errors gracefully** with try-except
6. **Log workflow execution** for debugging
7. **Monitor costs and performance** in production
8. **Test failure scenarios** thoroughly
