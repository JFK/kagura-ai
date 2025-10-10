# Testing API

Framework for testing AI agents with assertions designed for non-deterministic LLM outputs.

## Overview

The `kagura.testing` module provides tools for testing AI agents:
- **AgentTestCase**: Base class with assertion methods
- **LLMMock/LLMRecorder**: Mock and record LLM calls
- **ToolMock**: Mock tool executions
- **Timer**: Measure execution time

## Class: AgentTestCase

Base class for testing Kagura agents.

```python
from kagura.testing import AgentTestCase
import pytest


class TestMyAgent(AgentTestCase):
    agent = my_agent  # Agent to test

    @pytest.mark.asyncio
    async def test_example(self):
        result = await self.agent("test input")
        self.assert_not_empty(result)
```

### Constructor

```python
def __init__(self) -> None
```

Initializes test case with empty telemetry tracking.

---

## Content Assertions

### assert_contains()

Assert text contains substring.

```python
def assert_contains(self, text: str, substring: str) -> None
```

**Parameters:**
- **text** (`str`): Text to check
- **substring** (`str`): Expected substring

**Raises:** `AssertionError` if substring not found

**Example:**
```python
result = await self.agent("Hello, Alice")
self.assert_contains(result, "Alice")
```

---

### assert_contains_any()

Assert text contains at least one of the options.

```python
def assert_contains_any(self, text: str, options: list[str]) -> None
```

**Parameters:**
- **text** (`str`): Text to check
- **options** (`list[str]`): List of possible substrings

**Raises:** `AssertionError` if none of the options found

**Example:**
```python
result = await self.agent("greet")
self.assert_contains_any(result, ["Hello", "Hi", "Hey"])
```

---

### assert_not_contains()

Assert text does not contain substring.

```python
def assert_not_contains(self, text: str, substring: str) -> None
```

**Parameters:**
- **text** (`str`): Text to check
- **substring** (`str`): Forbidden substring

**Raises:** `AssertionError` if substring found

**Example:**
```python
result = await self.agent("test")
self.assert_not_contains(result, "error")
```

---

### assert_matches_pattern()

Assert text matches regex pattern.

```python
def assert_matches_pattern(self, text: str, pattern: str) -> None
```

**Parameters:**
- **text** (`str`): Text to check
- **pattern** (`str`): Regex pattern

**Raises:** `AssertionError` if pattern doesn't match

**Example:**
```python
result = await self.agent("extract email")
self.assert_matches_pattern(result, r'\w+@\w+\.\w+')
```

---

### assert_not_empty()

Assert text is not empty.

```python
def assert_not_empty(self, text: str) -> None
```

**Parameters:**
- **text** (`str`): Text to check

**Raises:** `AssertionError` if text is empty or only whitespace

**Example:**
```python
result = await self.agent("test")
self.assert_not_empty(result)
```

---

### assert_language()

Assert text is in expected language.

```python
def assert_language(self, text: str, expected_lang: str) -> None
```

**Parameters:**
- **text** (`str`): Text to check
- **expected_lang** (`str`): Expected language code (e.g., `"en"`, `"ja"`, `"fr"`)

**Raises:**
- `AssertionError`: If language doesn't match
- `ImportError`: If `langdetect` not installed

**Requires:** `pip install langdetect`

**Example:**
```python
result = await self.agent("translate to French")
self.assert_language(result, "fr")
```

---

## LLM Behavior Assertions

### assert_llm_calls()

Assert number and characteristics of LLM calls.

```python
def assert_llm_calls(
    self,
    count: Optional[int] = None,
    model: Optional[str] = None,
) -> None
```

**Parameters:**
- **count** (`Optional[int]`): Expected number of LLM calls
- **model** (`Optional[str]`): Expected model name

**Raises:** `AssertionError` if LLM calls don't match expectations

**Example:**
```python
with self.record_llm_calls():
    result = await self.agent("test")

# Assert exactly 1 call
self.assert_llm_calls(count=1)

# Assert correct model
self.assert_llm_calls(model="gpt-4o-mini")

# Assert both
self.assert_llm_calls(count=1, model="gpt-4o-mini")
```

---

### assert_token_usage()

Assert token usage is within bounds.

```python
def assert_token_usage(
    self,
    max_tokens: Optional[int] = None,
    min_tokens: Optional[int] = None,
) -> None
```

**Parameters:**
- **max_tokens** (`Optional[int]`): Maximum allowed tokens
- **min_tokens** (`Optional[int]`): Minimum expected tokens

**Raises:** `AssertionError` if token usage out of bounds

**Example:**
```python
with self.record_llm_calls():
    result = await self.agent("test")

# Assert under budget
self.assert_token_usage(max_tokens=500)

# Assert meaningful response
self.assert_token_usage(min_tokens=10)
```

---

### assert_tool_calls()

Assert specific tools were called.

```python
def assert_tool_calls(self, expected_tools: list[str]) -> None
```

**Parameters:**
- **expected_tools** (`list[str]`): List of expected tool names

**Raises:** `AssertionError` if expected tools not called

**Example:**
```python
result = await self.agent("search for Python")
self.assert_tool_calls(["search_web"])
```

---

## Performance Assertions

### assert_duration()

Assert execution duration is within limit.

```python
def assert_duration(self, max_seconds: float) -> None
```

**Parameters:**
- **max_seconds** (`float`): Maximum allowed duration in seconds

**Raises:** `AssertionError` if duration exceeds limit

**Example:**
```python
with self.measure_time():
    result = await self.agent("test")

self.assert_duration(5.0)  # Must complete within 5 seconds
```

---

### assert_cost()

Assert execution cost is within budget.

```python
def assert_cost(self, max_cost: float) -> None
```

**Parameters:**
- **max_cost** (`float`): Maximum allowed cost in USD

**Raises:** `AssertionError` if cost exceeds budget

**Example:**
```python
with self.record_llm_calls():
    result = await self.agent("test")

self.assert_cost(0.01)  # Must cost less than $0.01
```

---

## Structured Output Assertions

### assert_valid_model()

Assert result is valid instance of Pydantic model.

```python
def assert_valid_model(self, result: Any, model_class: type) -> None
```

**Parameters:**
- **result** (`Any`): Result to check
- **model_class** (`type`): Expected Pydantic model class

**Raises:** `AssertionError` if result is not instance of model_class

**Example:**
```python
from pydantic import BaseModel

class Person(BaseModel):
    name: str
    age: int

result = await self.agent("extract person")
self.assert_valid_model(result, Person)
```

---

### assert_field_value()

Assert model field has expected value.

```python
def assert_field_value(
    self, result: Any, field: str, expected: Any
) -> None
```

**Parameters:**
- **result** (`Any`): Pydantic model instance
- **field** (`str`): Field name
- **expected** (`Any`): Expected value

**Raises:** `AssertionError` if field value doesn't match

**Example:**
```python
person = await self.agent("extract person")
self.assert_field_value(person, "name", "Alice")
self.assert_field_value(person, "age", 30)
```

---

## Context Managers

### record_llm_calls()

Context manager to record LLM calls.

```python
def record_llm_calls(self) -> LLMRecorder
```

**Returns:** `LLMRecorder` context manager

**Example:**
```python
with self.record_llm_calls():
    result = await self.agent("test")

self.assert_llm_calls(count=1)
```

---

### mock_llm()

Context manager to mock LLM responses.

```python
def mock_llm(self, response: str) -> LLMMock
```

**Parameters:**
- **response** (`str`): Mock response to return

**Returns:** `LLMMock` context manager

**Example:**
```python
with self.mock_llm("Mocked response"):
    result = await self.agent("test")

assert result == "Mocked response"
```

---

### mock_tool()

Context manager to mock tool calls.

```python
def mock_tool(self, tool_name: str, return_value: Any) -> ToolMock
```

**Parameters:**
- **tool_name** (`str`): Name of tool to mock
- **return_value** (`Any`): Value to return

**Returns:** `ToolMock` context manager

**Example:**
```python
with self.mock_tool("search_web", return_value=["result1", "result2"]):
    result = await self.agent("search query")
```

---

### measure_time()

Context manager to measure execution time.

```python
def measure_time(self) -> Timer
```

**Returns:** `Timer` context manager

**Example:**
```python
with self.measure_time() as timer:
    result = await self.agent("test")

print(f"Took {timer.duration:.2f}s")
self.assert_duration(5.0)
```

---

## Complete Example

```python
import pytest
from pydantic import BaseModel
from kagura import agent
from kagura.testing import AgentTestCase


class Person(BaseModel):
    name: str
    age: int
    occupation: str


@agent(model="gpt-4o-mini")
async def person_extractor(text: str) -> Person:
    '''Extract person information from: {{ text }}'''
    pass


class TestPersonExtractor(AgentTestCase):
    agent = person_extractor

    @pytest.mark.asyncio
    async def test_extracts_person(self):
        """Test person extraction."""
        text = "Alice is 30 years old and works as a software engineer"
        result = await self.agent(text)

        # Structured output assertions
        self.assert_valid_model(result, Person)
        self.assert_field_value(result, "name", "Alice")
        self.assert_field_value(result, "age", 30)
        self.assert_field_value(result, "occupation", "software engineer")

    @pytest.mark.asyncio
    async def test_llm_behavior(self):
        """Test LLM call characteristics."""
        with self.record_llm_calls():
            result = await self.agent("Test input")

        # LLM behavior assertions
        self.assert_llm_calls(count=1, model="gpt-4o-mini")
        self.assert_token_usage(max_tokens=200)

    @pytest.mark.asyncio
    async def test_performance(self):
        """Test performance requirements."""
        with self.measure_time():
            result = await self.agent("Test input")

        # Performance assertions
        self.assert_duration(5.0)

    @pytest.mark.asyncio
    async def test_with_mock(self):
        """Test with mocked LLM response."""
        mock_person = Person(name="Mock", age=25, occupation="tester")

        with self.mock_llm(mock_person.model_dump_json()):
            result = await self.agent("Test input")

        self.assert_field_value(result, "name", "Mock")

    @pytest.mark.asyncio
    async def test_multiple_assertions(self):
        """Test with multiple assertion types."""
        text = "Bob is 40 years old and is a doctor"

        # Execute
        with self.record_llm_calls():
            with self.measure_time():
                result = await self.agent(text)

        # Content assertions
        self.assert_valid_model(result, Person)

        # LLM behavior assertions
        self.assert_llm_calls(count=1)
        self.assert_token_usage(max_tokens=300)

        # Performance assertions
        self.assert_duration(5.0)
```

---

## Best Practices

### 1. Test Patterns, Not Exact Text

```python
# Good - flexible
self.assert_contains_any(result, ["hello", "hi", "greetings"])

# Bad - brittle
assert result == "Hello, World!"
```

### 2. Use Mocks for Fast Tests

```python
# Fast - mocked (use for unit tests)
with self.mock_llm("Mocked"):
    result = await self.agent("test")

# Slow - real LLM call (use for integration tests)
result = await self.agent("test")
```

### 3. Combine Assertions

```python
@pytest.mark.asyncio
async def test_comprehensive(self):
    with self.record_llm_calls():
        with self.measure_time():
            result = await self.agent("test")

    # Multiple assertions in one test
    self.assert_not_empty(result)
    self.assert_llm_calls(count=1)
    self.assert_token_usage(max_tokens=500)
    self.assert_duration(5.0)
```

### 4. Parametrize Tests

```python
@pytest.mark.asyncio
@pytest.mark.parametrize("text,expected_lang", [
    ("Hello", "en"),
    ("Bonjour", "fr"),
    ("こんにちは", "ja"),
])
async def test_languages(self, text, expected_lang):
    result = await self.agent(text)
    self.assert_language(result, expected_lang)
```

---

## Common Patterns

### Pattern 1: Golden Test

```python
@pytest.mark.asyncio
async def test_golden_output(self):
    with self.mock_llm("Expected output"):
        result = await self.agent("test")

    with open("golden_output.txt") as f:
        expected = f.read()

    assert result == expected
```

### Pattern 2: Regression Test

```python
@pytest.mark.asyncio
async def test_no_regression(self):
    with self.mock_llm("Previous version output"):
        result = await self.agent("test")

    self.assert_not_empty(result)
```

### Pattern 3: Error Handling

```python
@pytest.mark.asyncio
async def test_handles_empty_response(self):
    with self.mock_llm(""):
        result = await self.agent("test")

    # Agent should handle gracefully
    # (implementation-dependent)
```

---

## Error Handling

```python
from pydantic import ValidationError
from litellm import APIError

@pytest.mark.asyncio
async def test_validation_error(self):
    """Test validation error handling."""
    with pytest.raises(ValidationError):
        result = await self.agent("invalid input")

@pytest.mark.asyncio
async def test_api_error(self):
    """Test API error handling."""
    with pytest.raises(APIError):
        result = await self.agent("test")
```

---

## Related

- [Tutorial: Testing](../tutorials/14-testing.md) - Step-by-step testing guide
- [@agent Decorator](agent.md) - Core agent decorator
- [Tutorial: Agent Builder](../tutorials/13-agent-builder.md) - Building agents

---

## See Also

- [Quick Start](../quickstart.md) - Getting started
- [Tutorial: Observability](../tutorials/15-observability.md) - Monitoring agents
