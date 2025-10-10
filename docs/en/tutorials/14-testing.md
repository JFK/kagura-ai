# Tutorial 14: Agent Testing

Learn how to test AI agents using Kagura's testing framework, designed to handle the non-deterministic nature of LLM outputs.

## Prerequisites

- Python 3.11 or higher
- Kagura AI installed (`pip install kagura-ai`)
- pytest installed (`pip install pytest`)
- Completion of [Tutorial 1: Basic Agent](01-basic-agent.md)

## Goal

By the end of this tutorial, you will:
- Understand testing challenges with AI agents
- Use AgentTestCase for agent testing
- Write assertions for LLM behavior
- Mock LLM responses for deterministic testing
- Measure performance and cost

## The Challenge of Testing AI Agents

Unlike traditional functions, AI agents are non-deterministic:

```python
# Traditional function - predictable
def add(a, b):
    return a + b

assert add(2, 3) == 5  # Always passes

# AI agent - non-deterministic
@agent
async def hello(name: str) -> str:
    '''Say hello to {{ name }}'''
    pass

result = await hello("Alice")
# Could be: "Hello, Alice!"
# Could be: "Hi Alice! How are you?"
# Could be: "Hello there, Alice! Nice to meet you!"
```

**Solution:** Test for patterns, not exact matches.

## Step 1: Basic Test Setup

Create a file called `test_agents.py`:

```python
import pytest
from kagura import agent
from kagura.testing import AgentTestCase


# Define agent to test
@agent
async def greeter(name: str) -> str:
    '''Say hello to {{ name }}'''
    pass


# Create test class
class TestGreeter(AgentTestCase):
    agent = greeter

    @pytest.mark.asyncio
    async def test_basic_greeting(self):
        """Test that agent produces a greeting."""
        result = await self.agent("Alice")

        # Assert response is not empty
        self.assert_not_empty(result)

        # Assert response contains the name
        self.assert_contains(result, "Alice")
```

Run the test:

```bash
pytest test_agents.py -v
```

## Step 2: Content Assertions

AgentTestCase provides many assertion methods:

### assert_contains

```python
@pytest.mark.asyncio
async def test_contains_name(self):
    result = await self.agent("Bob")
    self.assert_contains(result, "Bob")
```

### assert_contains_any

```python
@pytest.mark.asyncio
async def test_greeting_style(self):
    result = await self.agent("Charlie")

    # Accept any common greeting
    self.assert_contains_any(result, [
        "Hello",
        "Hi",
        "Hey",
        "Greetings"
    ])
```

### assert_not_contains

```python
@pytest.mark.asyncio
async def test_no_profanity(self):
    result = await self.agent("Test")
    self.assert_not_contains(result, "bad_word")
```

### assert_matches_pattern

```python
@pytest.mark.asyncio
async def test_email_format(self):
    @agent
    async def email_extractor(text: str) -> str:
        '''Extract email from: {{ text }}'''
        pass

    result = await email_extractor("Contact: alice@example.com")

    # Use regex pattern
    self.assert_matches_pattern(result, r'\w+@\w+\.\w+')
```

## Step 3: Language Detection

Test multilingual agents:

```python
@agent
async def translator(text: str, target_lang: str) -> str:
    '''Translate "{{ text }}" to {{ target_lang }}'''
    pass


class TestTranslator(AgentTestCase):
    agent = translator

    @pytest.mark.asyncio
    async def test_japanese_translation(self):
        result = await self.agent("Hello", target_lang="Japanese")

        # Requires: pip install langdetect
        self.assert_language(result, "ja")

    @pytest.mark.asyncio
    async def test_french_translation(self):
        result = await self.agent("Hello", target_lang="French")
        self.assert_language(result, "fr")
```

**Note:** Requires `langdetect`:
```bash
pip install langdetect
```

## Step 4: LLM Behavior Assertions

Test LLM call characteristics:

### assert_llm_calls

```python
@pytest.mark.asyncio
async def test_single_llm_call(self):
    with self.record_llm_calls():
        result = await self.agent("Test")

    # Assert exactly one LLM call was made
    self.assert_llm_calls(count=1)


@pytest.mark.asyncio
async def test_correct_model(self):
    with self.record_llm_calls():
        result = await self.agent("Test")

    # Assert specific model was used
    self.assert_llm_calls(model="gpt-4o-mini")
```

### assert_token_usage

```python
@pytest.mark.asyncio
async def test_token_budget(self):
    with self.record_llm_calls():
        result = await self.agent("Test")

    # Assert token usage within limit
    self.assert_token_usage(max_tokens=500)
```

### assert_tool_calls

```python
def search_web(query: str) -> str:
    return f"Results for: {query}"


@agent(tools=[search_web])
async def researcher(query: str) -> str:
    '''Search for: {{ query }}'''
    pass


class TestResearcher(AgentTestCase):
    agent = researcher

    @pytest.mark.asyncio
    async def test_uses_search_tool(self):
        result = await self.agent("Python tutorials")

        # Assert search tool was called
        self.assert_tool_calls(["search_web"])
```

## Step 5: Performance Testing

### Test Execution Duration

```python
@pytest.mark.asyncio
async def test_response_time(self):
    with self.measure_time() as timer:
        result = await self.agent("Test")

    # Assert response within 5 seconds
    self.assert_duration(5.0)
```

### Test Cost Budget

```python
@pytest.mark.asyncio
async def test_cost_budget(self):
    with self.record_llm_calls():
        result = await self.agent("Test")

    # Assert cost under $0.01
    self.assert_cost(0.01)
```

## Step 6: Mocking LLM Responses

For fast, deterministic testing, mock LLM responses:

```python
@pytest.mark.asyncio
async def test_with_mock_llm(self):
    with self.mock_llm("Mocked response"):
        result = await self.agent("Test")

    # Now we can assert exact match
    assert result == "Mocked response"
```

### Use Case: Test Error Handling

```python
@agent
async def safe_agent(query: str) -> str:
    '''Process: {{ query }}'''
    pass


class TestSafeAgent(AgentTestCase):
    agent = safe_agent

    @pytest.mark.asyncio
    async def test_handles_empty_response(self):
        with self.mock_llm(""):
            result = await self.agent("Test")

            # Agent should handle empty response gracefully
            # (Implementation-dependent)
```

## Step 7: Structured Output Testing

Test agents that return Pydantic models:

```python
from pydantic import BaseModel


class Person(BaseModel):
    name: str
    age: int
    occupation: str


@agent
async def extract_person(text: str) -> Person:
    '''Extract person info from: {{ text }}'''
    pass


class TestPersonExtractor(AgentTestCase):
    agent = extract_person

    @pytest.mark.asyncio
    async def test_extracts_person(self):
        result = await self.agent(
            "Alice is 30 years old and works as a software engineer"
        )

        # Assert result is valid Person model
        self.assert_valid_model(result, Person)

        # Assert specific field values
        self.assert_field_value(result, "name", "Alice")
        self.assert_field_value(result, "age", 30)
        self.assert_field_value(result, "occupation", "software engineer")
```

## Step 8: Mocking Tools

Test agents with tools without executing real tools:

```python
def expensive_api_call(query: str) -> dict:
    """Simulate expensive API call."""
    # Real implementation would call external API
    pass


@agent(tools=[expensive_api_call])
async def api_agent(query: str) -> str:
    '''Query API: {{ query }}'''
    pass


class TestAPIAgent(AgentTestCase):
    agent = api_agent

    @pytest.mark.asyncio
    async def test_with_mocked_tool(self):
        mock_data = {"result": "mocked data"}

        with self.mock_tool("expensive_api_call", return_value=mock_data):
            result = await self.agent("test query")

            # Agent receives mocked data instead of real API call
            self.assert_not_empty(result)
```

## Complete Example: Comprehensive Test Suite

```python
import pytest
from pydantic import BaseModel
from kagura import agent
from kagura.testing import AgentTestCase


# Agent definition
@agent(model="gpt-4o-mini", temperature=0.7)
async def sentiment_analyzer(text: str) -> str:
    '''Analyze sentiment (positive/negative/neutral) of: {{ text }}'''
    pass


# Test suite
class TestSentimentAnalyzer(AgentTestCase):
    agent = sentiment_analyzer

    @pytest.mark.asyncio
    async def test_positive_sentiment(self):
        """Test positive sentiment detection."""
        result = await self.agent("I love this product!")

        self.assert_not_empty(result)
        self.assert_contains_any(result, ["positive", "Positive"])

    @pytest.mark.asyncio
    async def test_negative_sentiment(self):
        """Test negative sentiment detection."""
        result = await self.agent("This is terrible.")

        self.assert_not_empty(result)
        self.assert_contains_any(result, ["negative", "Negative"])

    @pytest.mark.asyncio
    async def test_neutral_sentiment(self):
        """Test neutral sentiment detection."""
        result = await self.agent("It's okay.")

        self.assert_not_empty(result)
        self.assert_contains_any(result, ["neutral", "Neutral"])

    @pytest.mark.asyncio
    async def test_uses_correct_model(self):
        """Test correct model is used."""
        with self.record_llm_calls():
            result = await self.agent("Test")

        self.assert_llm_calls(count=1, model="gpt-4o-mini")

    @pytest.mark.asyncio
    async def test_performance(self):
        """Test response time."""
        with self.measure_time():
            result = await self.agent("Test")

        self.assert_duration(5.0)

    @pytest.mark.asyncio
    async def test_token_efficiency(self):
        """Test token usage."""
        with self.record_llm_calls():
            result = await self.agent("Test")

        self.assert_token_usage(max_tokens=200)

    @pytest.mark.asyncio
    async def test_deterministic_with_mock(self):
        """Test with mocked LLM response."""
        with self.mock_llm("Positive sentiment detected"):
            result = await self.agent("Test")

        assert result == "Positive sentiment detected"
```

Run the suite:

```bash
pytest test_agents.py -v
```

## Best Practices

### 1. Test Patterns, Not Exact Text

```python
# Good
self.assert_contains_any(result, ["hello", "hi", "greetings"])

# Bad
assert result == "Hello, World!"  # Too brittle
```

### 2. Use Mocks for Fast Tests

```python
# Fast (mocked)
with self.mock_llm("Mocked"):
    result = await self.agent("Test")

# Slow (real LLM call)
result = await self.agent("Test")
```

### 3. Test Edge Cases

```python
@pytest.mark.asyncio
async def test_empty_input(self):
    result = await self.agent("")
    # Handle edge case

@pytest.mark.asyncio
async def test_very_long_input(self):
    long_text = "word " * 1000
    result = await self.agent(long_text)
    # Handle long input
```

### 4. Parametrize Tests

```python
@pytest.mark.asyncio
@pytest.mark.parametrize("text,expected", [
    ("I love it", "positive"),
    ("I hate it", "negative"),
    ("It's okay", "neutral"),
])
async def test_sentiment(self, text, expected):
    result = await self.agent(text)
    self.assert_contains(result.lower(), expected)
```

## Common Testing Patterns

### Pattern 1: Golden Test

Store expected output and compare:

```python
@pytest.mark.asyncio
async def test_golden_output(self):
    with self.mock_llm("Expected output"):
        result = await self.agent("Test")

    # Load golden output from file
    with open("golden_output.txt") as f:
        expected = f.read()

    assert result == expected
```

### Pattern 2: Regression Test

Ensure behavior doesn't change:

```python
@pytest.mark.asyncio
async def test_no_regression(self):
    # Use fixed mock to ensure consistent behavior
    with self.mock_llm("Previous version output"):
        result = await self.agent("Test")

    # Test should always pass
    self.assert_not_empty(result)
```

### Pattern 3: Integration Test

Test multiple agents together:

```python
@pytest.mark.asyncio
async def test_agent_pipeline(self):
    @agent
    async def analyzer(text: str) -> str:
        '''Analyze: {{ text }}'''
        pass

    @agent
    async def summarizer(text: str) -> str:
        '''Summarize: {{ text }}'''
        pass

    # Test pipeline
    analysis = await analyzer("Long text...")
    summary = await summarizer(analysis)

    self.assert_not_empty(summary)
```

## Common Mistakes

### 1. Testing Exact LLM Output

```python
# Wrong - LLM output varies
assert result == "Hello, World!"

# Correct - Test pattern
self.assert_contains(result, "World")
```

### 2. Not Using Mocks

```python
# Slow - Real LLM calls in every test
result = await self.agent("Test")

# Fast - Mocked responses
with self.mock_llm("Mocked"):
    result = await self.agent("Test")
```

### 3. Missing @pytest.mark.asyncio

```python
# Wrong - Async test without decorator
async def test_agent(self):
    result = await self.agent("Test")

# Correct
@pytest.mark.asyncio
async def test_agent(self):
    result = await self.agent("Test")
```

## Practice Exercises

### Exercise 1: Test Translation Agent

Create tests for a translation agent:

```python
@agent
async def translator(text: str, target_lang: str) -> str:
    '''Translate to {{ target_lang }}: {{ text }}'''
    pass

# Your tests here:
class TestTranslator(AgentTestCase):
    agent = translator

    # TODO: Test Japanese translation
    # TODO: Test French translation
    # TODO: Test empty input
    # TODO: Test performance
```

### Exercise 2: Test with Multiple Assertions

Create a comprehensive test with multiple assertions:

```python
@pytest.mark.asyncio
async def test_comprehensive(self):
    with self.record_llm_calls():
        with self.measure_time():
            result = await self.agent("Test")

    # TODO: Add multiple assertions
    # - Not empty
    # - Contains specific text
    # - LLM call count
    # - Duration
    # - Token usage
```

### Exercise 3: Mock Tool Testing

Test an agent with tools:

```python
def calculator(expr: str) -> float:
    return eval(expr)

@agent(tools=[calculator])
async def math_agent(question: str) -> str:
    '''Answer: {{ question }}'''
    pass

# TODO: Create tests with mocked calculator
```

## Key Concepts Learned

### 1. Non-Deterministic Testing

Test patterns, not exact matches:
```python
self.assert_contains_any(result, ["option1", "option2"])
```

### 2. LLM Behavior Assertions

Assert on LLM characteristics:
```python
self.assert_llm_calls(count=1, model="gpt-4o-mini")
self.assert_token_usage(max_tokens=500)
```

### 3. Mocking for Determinism

Use mocks for fast, predictable tests:
```python
with self.mock_llm("Fixed output"):
    result = await self.agent("Test")
```

### 4. Performance Testing

Measure duration and cost:
```python
self.assert_duration(5.0)
self.assert_cost(0.01)
```

## Next Steps

- [Tutorial 15: Observability](15-observability.md) - Monitor agent performance
- [API Reference: Testing](../api/testing.md) - Complete testing API
- [Tutorial 13: Agent Builder](13-agent-builder.md) - Build complex agents

## Summary

You learned:
- ✓ How to test non-deterministic AI agents
- ✓ How to use AgentTestCase assertions
- ✓ How to mock LLM responses and tools
- ✓ How to test performance and cost
- ✓ How to test structured outputs

Continue to [Tutorial 15: Observability](15-observability.md) to learn agent monitoring!
