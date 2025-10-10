# Testing Examples

This directory contains examples demonstrating how to test AI agents using Kagura's testing framework.

## Overview

Testing AI agents presents unique challenges due to non-deterministic LLM outputs. Kagura provides:
- **AgentTestCase**: Base class with specialized assertions
- **Mock Support**: Test without making API calls
- **Performance Testing**: Latency, throughput, cost tracking
- **Semantic Assertions**: Flexible assertions for LLM outputs

## Examples

### 1. Basic Testing (`test_basic.py`)

Demonstrates fundamental testing techniques:
- Using `AgentTestCase` base class
- Basic assertions (`assert_not_empty`, `assert_contains`)
- Length assertions (`assert_min_length`, `assert_max_length`)
- Regex matching (`assert_matches_regex`)
- Testing multiple scenarios
- Error handling

**Run:**
```bash
pytest examples/testing/test_basic.py -v
```

**Key Assertions:**
```python
# Check output exists
self.assert_not_empty(result)

# Check content
self.assert_contains(result, "expected text")

# Check length
self.assert_min_length(result, 10)
self.assert_max_length(result, 200)

# Check patterns
self.assert_matches_regex(result, r"(?i)pattern")
self.assert_matches_any(result, [r"pattern1", r"pattern2"])
```

---

### 2. Testing with Mocks (`test_with_mocks.py`)

Shows how to test agents without making API calls:
- Mocking LLM responses
- Sequential mocks for conversations
- Testing offline
- Mock side effects
- Exception testing
- Prompt generation testing

**Run:**
```bash
pytest examples/testing/test_with_mocks.py -v
```

**Key Patterns:**
```python
# Basic mocking
with self.mock_llm_response("Mocked output"):
    result = await self.agent("input")
    assert result == "Mocked output"

# Multiple calls
with self.mock_llm_response("Response 1"):
    result1 = await self.agent("query 1")

with self.mock_llm_response("Response 2"):
    result2 = await self.agent("query 2")

# Using unittest.mock
from unittest.mock import patch

with patch('kagura.core.llm.LLMClient.generate') as mock:
    mock.return_value = "Mocked"
    result = await agent("test")
```

---

### 3. Performance Testing (`test_performance.py`)

Demonstrates performance and cost testing:
- Latency measurement
- Throughput testing (sequential and concurrent)
- Token usage tracking
- Cost estimation
- Memory performance
- Stress testing
- Benchmarking

**Run:**
```bash
# Run quick tests
pytest examples/testing/test_performance.py -v

# Run all tests including slow ones
pytest examples/testing/test_performance.py -v -m ""
```

**Key Metrics:**
```python
# Latency
start_time = time.time()
result = await agent("query")
latency = time.time() - start_time

# Throughput (concurrent)
tasks = [agent(f"query {i}") for i in range(10)]
results = await asyncio.gather(*tasks)
throughput = len(results) / elapsed_time

# Token usage
# Track via LLM client metrics or telemetry
```

---

## Test Organization

### Test File Structure

```python
import pytest
from kagura import agent
from kagura.testing import AgentTestCase

# Define agent
@agent(model="gpt-4o-mini")
async def my_agent(input: str) -> str:
    """Process {{ input }}"""
    pass

# Test class
class TestMyAgent(AgentTestCase):
    agent = my_agent

    @pytest.mark.asyncio
    async def test_basic_behavior(self):
        result = await self.agent("test input")
        self.assert_not_empty(result)
```

### Test Markers

Use pytest markers to organize tests:

```python
@pytest.mark.asyncio  # Required for async tests
async def test_async_agent():
    pass

@pytest.mark.slow  # Mark slow tests
async def test_long_running():
    pass

@pytest.mark.integration  # Mark integration tests
async def test_with_real_api():
    pass
```

**Run specific markers:**
```bash
# Skip slow tests
pytest -m "not slow"

# Run only integration tests
pytest -m integration
```

---

## Best Practices

### 1. Use Mocks for Fast Tests

```python
# ✅ Fast: Mocked
with self.mock_llm_response("Quick response"):
    result = await agent("query")

# ❌ Slow: Real API call
result = await agent("query")  # Costs time and money
```

### 2. Test Agent Logic, Not LLM Behavior

```python
# ✅ Good: Test agent's handling
with self.mock_llm_response("Mocked"):
    result = await agent("input")
    self.assert_not_empty(result)  # Tests agent returns output

# ❌ Bad: Test LLM's exact output
result = await agent("What is 2+2?")
assert result == "4"  # Too brittle, LLM output varies
```

### 3. Use Semantic Assertions

```python
# ✅ Flexible: Semantic checking
self.assert_contains(result, "machine learning")
self.assert_matches_regex(result, r"(?i)AI")

# ❌ Brittle: Exact matching
assert result == "Machine learning is..."  # Will break
```

### 4. Separate Fast and Slow Tests

```python
# Fast tests (with mocks)
class TestQuick(AgentTestCase):
    @pytest.mark.asyncio
    async def test_fast(self):
        with self.mock_llm_response("Mock"):
            result = await agent("query")

# Slow tests (real API calls)
class TestIntegration(AgentTestCase):
    @pytest.mark.asyncio
    @pytest.mark.slow
    @pytest.mark.integration
    async def test_real_api(self):
        result = await agent("real query")
```

### 5. Track Performance Baselines

```python
# Establish baseline
def test_latency_baseline():
    # Record average latency
    # Alert if performance degrades
    avg_latency = measure_latency(agent, num_calls=10)
    assert avg_latency < BASELINE_THRESHOLD
```

---

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest examples/testing/ -v

# Run specific file
pytest examples/testing/test_basic.py -v

# Run specific test
pytest examples/testing/test_basic.py::TestGreeterAgent::test_greets_with_name -v

# Skip slow tests
pytest examples/testing/ -v -m "not slow"
```

### With Coverage

```bash
# Coverage report
pytest examples/testing/ --cov=kagura --cov-report=html

# View coverage
open htmlcov/index.html
```

### Continuous Integration

```yaml
# .github/workflows/test.yml
- name: Run tests
  run: |
    pytest examples/testing/ -v -m "not slow"
```

---

## Common Patterns

### Pattern 1: Testing Multiple Inputs

```python
@pytest.mark.asyncio
async def test_multiple_inputs(self):
    test_cases = [
        ("input1", "expected_pattern1"),
        ("input2", "expected_pattern2"),
    ]

    for input_val, pattern in test_cases:
        result = await self.agent(input_val)
        self.assert_matches_regex(result, pattern)
```

### Pattern 2: Testing Error Handling

```python
@pytest.mark.asyncio
async def test_handles_errors(self):
    with self.mock_llm_response("Error response"):
        result = await self.agent("bad input")
        self.assert_contains(result, "error")
```

### Pattern 3: Testing Conversations

```python
@pytest.mark.asyncio
async def test_conversation(self):
    # First turn
    with self.mock_llm_response("Hello!"):
        result1 = await agent("Hi")

    # Second turn (with context)
    with self.mock_llm_response("I can help with that"):
        result2 = await agent("Can you help?")
```

---

## API Reference

For complete API documentation, see:
- [Testing API Reference](../../docs/en/api/testing.md)
- [AgentTestCase Documentation](../../docs/en/api/testing.md#agenttestcase)

## Related Examples

- [AgentBuilder Examples](../agent_builder/) - Creating testable agents
- [Observability Examples](../observability/) - Monitoring test results

## Troubleshooting

### Tests are slow
- Use mocks to avoid API calls
- Mark slow tests with `@pytest.mark.slow`
- Run fast tests first: `pytest -m "not slow"`

### Tests are flaky
- Use semantic assertions instead of exact matches
- Avoid testing exact LLM outputs
- Test agent logic, not LLM behavior

### API rate limits
- Use mocks for most tests
- Reserve real API calls for integration tests
- Run integration tests less frequently

---

**Remember**: Test the agent's behavior and logic, not the LLM's creativity!
