# Agent Routing API

Automatic agent selection based on user input patterns.

## Overview

The routing system provides intent-based routing to automatically select the most appropriate agent for a given user input. Agents are registered with intent keywords, and the router calculates confidence scores to determine the best match.

**Key Features:**
- Intent-based keyword matching
- Confidence scoring
- Fallback mechanism
- Case-insensitive matching
- Unicode support

## AgentRouter Class

Routes user input to appropriate agents using intent-based matching.

### Constructor

```python
AgentRouter(
    strategy: str = "intent",
    fallback_agent: Callable | None = None,
    confidence_threshold: float = 0.3
)
```

**Parameters:**

- `strategy`: Routing strategy (currently only `"intent"` is supported)
- `fallback_agent`: Default agent to use when no match is found or confidence is below threshold
- `confidence_threshold`: Minimum confidence score (0.0-1.0) required for routing. Lower values are more lenient. Default: 0.3

**Raises:**
- `InvalidRouterStrategyError`: If strategy is not valid

**Example:**

```python
from kagura.routing import AgentRouter

# Basic router
router = AgentRouter()

# Router with fallback
router = AgentRouter(
    fallback_agent=general_assistant,
    confidence_threshold=0.5
)
```

### Methods

#### register

```python
router.register(
    agent: Callable,
    intents: list[str] | None = None,
    description: str = "",
    name: str | None = None
) -> None
```

Register an agent with routing patterns.

**Parameters:**

- `agent`: Agent function to register
- `intents`: List of intent keywords/patterns for matching. Case-insensitive matching is used.
- `description`: Human-readable description of the agent
- `name`: Agent name (defaults to function name)

**Example:**

```python
from kagura import agent

@agent
async def code_reviewer(code: str) -> str:
    '''Review code: {{ code }}'''
    pass

router.register(
    code_reviewer,
    intents=["review", "check", "analyze"],
    description="Reviews code for quality and bugs"
)
```

#### route

```python
async router.route(
    user_input: str,
    context: dict[str, Any] | None = None,
    **kwargs: Any
) -> Any
```

Route user input to the most appropriate agent.

**Parameters:**

- `user_input`: User's natural language input
- `context`: Optional context information (reserved for future use)
- `**kwargs`: Additional arguments to pass to the selected agent

**Returns:**
- Result from executing the selected agent

**Raises:**
- `NoAgentFoundError`: When no suitable agent is found and no fallback agent is configured

**Example:**

```python
# Automatic routing
result = await router.route("Please review this code")
# → Automatically selects and executes code_reviewer

# With additional arguments
result = await router.route(
    "Translate this text",
    target_lang="ja"
)
```

#### get_matched_agents

```python
router.get_matched_agents(
    user_input: str,
    top_k: int = 3
) -> list[tuple[Callable, float]]
```

Get top-k matched agents with confidence scores.

**Parameters:**

- `user_input`: User input to match against
- `top_k`: Number of top matches to return

**Returns:**
- List of `(agent_function, confidence_score)` tuples, sorted by confidence (highest first)

**Example:**

```python
matches = router.get_matched_agents("review my code", top_k=3)

for agent, score in matches:
    print(f"{agent.__name__}: {score:.2f}")
# Output:
# code_reviewer: 0.67
# general_assistant: 0.33
```

#### list_agents

```python
router.list_agents() -> list[str]
```

List all registered agent names.

**Returns:**
- List of registered agent names

**Example:**

```python
agents = router.list_agents()
print(agents)
# ['code_reviewer', 'translator', 'data_analyzer']
```

#### get_agent_info

```python
router.get_agent_info(agent_name: str) -> dict[str, Any]
```

Get information about a registered agent.

**Parameters:**

- `agent_name`: Name of the agent

**Returns:**
- Dictionary containing agent metadata:
  - `name`: Agent name
  - `intents`: List of intent keywords
  - `description`: Agent description

**Raises:**
- `AgentNotRegisteredError`: If agent is not registered

**Example:**

```python
info = router.get_agent_info("code_reviewer")
print(info["description"])
# Reviews code for quality and bugs

print(info["intents"])
# ['review', 'check', 'analyze']
```

## Exceptions

### RoutingError

Base exception for routing errors.

```python
class RoutingError(Exception):
    pass
```

### NoAgentFoundError

Raised when no suitable agent is found for routing.

```python
class NoAgentFoundError(RoutingError):
    def __init__(
        self,
        message: str,
        user_input: str | None = None
    ):
        ...

    user_input: str | None  # User input that failed to route
```

**Example:**

```python
from kagura.routing import NoAgentFoundError

try:
    result = await router.route("Unknown request")
except NoAgentFoundError as e:
    print(f"Failed to route: {e.user_input}")
```

### AgentNotRegisteredError

Raised when trying to access an unregistered agent.

```python
class AgentNotRegisteredError(RoutingError):
    def __init__(self, agent_name: str):
        ...

    agent_name: str  # Name of unregistered agent
```

### InvalidRouterStrategyError

Raised when an invalid routing strategy is specified.

```python
class InvalidRouterStrategyError(RoutingError):
    def __init__(
        self,
        strategy: str,
        valid_strategies: list[str]
    ):
        ...

    strategy: str  # Invalid strategy name
    valid_strategies: list[str]  # List of valid strategies
```

## Complete Example

```python
from kagura import agent
from kagura.routing import AgentRouter

# Define agents
@agent
async def code_reviewer(code: str) -> str:
    '''Review code quality: {{ code }}'''
    pass

@agent
async def translator(text: str, target_lang: str = "en") -> str:
    '''Translate {{ text }} to {{ target_lang }}'''
    pass

@agent
async def data_analyzer(data: str) -> str:
    '''Analyze data: {{ data }}'''
    pass

@agent
async def general_assistant(query: str) -> str:
    '''General assistant: {{ query }}'''
    pass

# Create router with fallback
router = AgentRouter(
    fallback_agent=general_assistant,
    confidence_threshold=0.4
)

# Register agents
router.register(
    code_reviewer,
    intents=["review", "check", "analyze"],
    description="Code review and quality analysis"
)

router.register(
    translator,
    intents=["translate", "翻訳", "translation"],
    description="Text translation between languages"
)

router.register(
    data_analyzer,
    intents=["analyze", "statistics", "データ分析"],
    description="Data analysis and statistics"
)

# Use routing
async def main():
    # Code review request
    result1 = await router.route("Please review this Python code")
    # → code_reviewer is automatically selected

    # Translation request
    result2 = await router.route("Translate 'Hello' to Japanese")
    # → translator is automatically selected

    # Unknown request → fallback
    result3 = await router.route("What's the weather today?")
    # → general_assistant (fallback) is used

    # Check matched agents
    matches = router.get_matched_agents("Check code quality")
    for agent, score in matches:
        print(f"{agent.__name__}: {score:.2f}")

# Run
await main()
```

## Intent Matching Algorithm

The intent matching algorithm works as follows:

1. **Keyword Matching**: For each registered agent, check if any of its intent keywords appear in the user input (case-insensitive)
2. **Score Calculation**: Score = (number of matched intents) / (total number of intents)
3. **Ranking**: Agents are ranked by score in descending order
4. **Threshold Check**: If the top agent's score is below `confidence_threshold`, use fallback agent
5. **Execution**: Execute the top-ranked agent with the user input

**Example Scoring:**

```python
# Agent registered with intents: ["review", "check", "analyze"]
user_input = "review and check code"

# Matching:
# - "review" ✓ found in input
# - "check"  ✓ found in input
# - "analyze" ✗ not found in input

# Score = 2 / 3 = 0.67
```

## Best Practices

### 1. Choose Specific Intents

Use specific, distinctive keywords that clearly identify the agent's purpose:

```python
# ✅ Good: Specific intents
router.register(
    billing_agent,
    intents=["billing", "payment", "invoice", "subscription"]
)

# ❌ Bad: Generic intents
router.register(
    billing_agent,
    intents=["help", "question", "issue"]
)
```

### 2. Set Appropriate Threshold

Adjust `confidence_threshold` based on your use case:

```python
# Strict matching (fewer false positives)
router = AgentRouter(confidence_threshold=0.6)

# Lenient matching (better coverage)
router = AgentRouter(confidence_threshold=0.3)
```

### 3. Always Provide Fallback

Ensure there's a fallback agent for unmatched requests:

```python
@agent
async def general_assistant(query: str) -> str:
    '''General purpose assistant: {{ query }}'''
    pass

router = AgentRouter(fallback_agent=general_assistant)
```

### 4. Support Multiple Languages

Include multilingual intent keywords for international support:

```python
router.register(
    translator,
    intents=[
        "translate", "翻訳", "번역",  # English, Japanese, Korean
        "translation", "traduire"     # English, French
    ]
)
```

### 5. Test Your Intents

Test with various user inputs to ensure correct routing:

```python
# Test suite
test_cases = [
    ("review this code", "code_reviewer"),
    ("check code quality", "code_reviewer"),
    ("translate to Japanese", "translator"),
    ("what's the weather", "fallback"),
]

for input_text, expected in test_cases:
    matches = router.get_matched_agents(input_text, top_k=1)
    if matches:
        assert matches[0][0].__name__ == expected
```

## Performance Considerations

- **Matching Speed**: ~1ms for intent-based matching (very fast)
- **Memory Usage**: Minimal (stores only intent keywords per agent)
- **Scalability**: Efficient for up to 100+ registered agents

## Limitations

### Phase 1 Limitations

- Only supports intent-based (keyword) matching
- No semantic understanding (e.g., synonyms)
- Simple substring matching (not NLP-based)

**Future Phases:**
- **Phase 2**: Semantic routing with embeddings
- **Phase 3**: Agent chaining and conditional routing

## See Also

- [Agent Routing Tutorial](../tutorials/09-agent-routing.md)
- [Agent Decorator API](./agent.md)
- [RFC-016: Agent Routing System](../../ai_docs/rfcs/RFC_016_AGENT_ROUTING.md)
