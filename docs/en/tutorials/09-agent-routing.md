# Agent Routing Tutorial

Learn how to use agent routing to automatically select the best agent for user requests.

## What is Agent Routing?

Agent routing automatically selects the most appropriate agent based on user input, eliminating the need to manually choose which agent to call.

**Benefits:**
- 🎯 Automatic agent selection
- 🚀 Simplified user experience
- 🔄 Easy to add new agents
- 🌐 Multilingual support

## Quick Start

### Step 1: Install Kagura AI

```bash
pip install kagura-ai
```

### Step 2: Define Agents

```python
from kagura import agent

@agent
async def code_reviewer(code: str) -> str:
    '''Review code quality and suggest improvements.
    Code: {{ code }}'''
    pass

@agent
async def translator(text: str, target_lang: str = "en") -> str:
    '''Translate text to target language.
    Text: {{ text }}
    Target: {{ target_lang }}'''
    pass
```

### Step 3: Create Router

```python
from kagura.routing import AgentRouter

router = AgentRouter()

# Register agents with intent keywords
router.register(
    code_reviewer,
    intents=["review", "check", "analyze"],
    description="Reviews code for quality and bugs"
)

router.register(
    translator,
    intents=["translate", "翻訳", "translation"],
    description="Translates text between languages"
)
```

### Step 4: Use Automatic Routing

```python
# The router automatically selects the right agent!
result = await router.route("Please review this code")
# → code_reviewer is selected

result = await router.route("Translate 'Hello' to Japanese")
# → translator is selected
```

## Basic Usage

### Registering Agents

Agents are registered with **intent keywords** that help the router identify them:

```python
from kagura import agent
from kagura.routing import AgentRouter

@agent
async def python_expert(question: str) -> str:
    '''Python programming expert: {{ question }}'''
    pass

router = AgentRouter()

router.register(
    python_expert,
    intents=[
        "python",      # Programming language
        "decorator",   # Python-specific concepts
        "asyncio",
        "pip"
    ],
    description="Answers Python programming questions"
)
```

### Routing Requests

```python
# These will all route to python_expert
await router.route("How do I use Python decorators?")
await router.route("Explain asyncio in Python")
await router.route("What's the best way to use pip?")
```

## Confidence Threshold

The router calculates a **confidence score** for each agent. You can control the minimum required confidence:

```python
router = AgentRouter(confidence_threshold=0.5)
```

**How Confidence Works:**

```python
# Agent has intents: ["review", "check", "analyze"]
user_input = "review and check code"

# Scoring:
# - "review" ✓ matched
# - "check"  ✓ matched
# - "analyze" ✗ not matched
# Score = 2/3 = 0.67 → Above threshold (0.5) → Agent selected
```

**Lower threshold** = more lenient matching
**Higher threshold** = stricter matching

```python
# Lenient (more matches)
router = AgentRouter(confidence_threshold=0.3)

# Strict (fewer matches, higher accuracy)
router = AgentRouter(confidence_threshold=0.7)
```

## Fallback Agent

Always provide a **fallback agent** for requests that don't match any registered agent:

```python
@agent
async def general_assistant(query: str) -> str:
    '''General purpose assistant: {{ query }}'''
    pass

router = AgentRouter(
    fallback_agent=general_assistant,
    confidence_threshold=0.4
)

# If no agent matches or confidence is low, fallback is used
result = await router.route("What's the weather today?")
# → general_assistant (fallback) handles this
```

## Multilingual Support

Add intent keywords in multiple languages:

```python
router.register(
    translator,
    intents=[
        # English
        "translate", "translation",
        # Japanese
        "翻訳", "訳して",
        # Spanish
        "traducir", "traducción",
        # Korean
        "번역"
    ],
    description="Multilingual translator"
)

# Works with any language
await router.route("この文章を翻訳して")  # Japanese
await router.route("Traducir este texto")  # Spanish
await router.route("이것을 번역해주세요")  # Korean
```

## Checking Matched Agents

See which agents match and their confidence scores:

```python
matches = router.get_matched_agents("review my code", top_k=3)

for agent, score in matches:
    print(f"{agent.__name__}: {score:.2f}")

# Output:
# code_reviewer: 0.67
# quality_checker: 0.33
# general_assistant: 0.00
```

This is useful for:
- Debugging routing issues
- Tuning confidence thresholds
- Understanding why an agent was selected

## Semantic Routing (Advanced)

Semantic routing uses embedding-based similarity matching for more intelligent routing. Instead of keyword matching, it understands the **meaning** of user queries.

### Installation

```bash
pip install kagura-ai[ai]
```

### Basic Usage

```python
from kagura import agent
from kagura.routing import AgentRouter

@agent
async def code_reviewer(code: str) -> str:
    '''Review code: {{ code }}'''
    pass

@agent
async def translator(text: str, lang: str = "en") -> str:
    '''Translate: {{ text }} to {{ lang }}'''
    pass

# Create semantic router
router = AgentRouter(strategy="semantic")

# Register with sample queries (not keywords!)
router.register(
    code_reviewer,
    samples=[
        "Can you review this code?",
        "Check my implementation",
        "Look at this function",
        "このコードをレビューして"  # Japanese
    ]
)

router.register(
    translator,
    samples=[
        "Translate this text",
        "Convert to Japanese",
        "What does this mean in French?",
        "翻訳して"  # Japanese
    ]
)

# Semantic matching understands meaning!
await router.route("Could you look at my Python script?")
# → code_reviewer (understands "look at" ≈ "review")

await router.route("英語で何て言う？")
# → translator (understands Japanese intent)
```

### Benefits of Semantic Routing

✅ **Understands synonyms**: "check", "review", "analyze" all match
✅ **Cross-language**: Matches meaning across languages
✅ **Context-aware**: Understands similar phrases
✅ **No keyword tuning**: Just provide natural examples

### Intent vs Semantic Comparison

| Feature | Intent (Keyword) | Semantic (Embedding) |
|---------|------------------|---------------------|
| **Speed** | ⚡ Very fast (<1ms) | 🐢 Slower (~50-200ms) |
| **Cost** | 💰 Free | 💵 API calls required |
| **Accuracy** | ✓ Good for exact keywords | ✓✓ Better for natural language |
| **Setup** | Simple keywords | Sample queries needed |
| **Offline** | ✅ Yes | ❌ No (needs API) |

**When to use Intent:**
- High-volume routing
- Offline applications
- Clear keyword patterns
- Cost-sensitive applications

**When to use Semantic:**
- Natural language queries
- Multilingual support
- Complex intent understanding
- User-facing chatbots

### Configuration

```python
# OpenAI encoder (default)
router = AgentRouter(
    strategy="semantic",
    encoder="openai"
)

# Cohere encoder
router = AgentRouter(
    strategy="semantic",
    encoder="cohere"
)

# With fallback and threshold
router = AgentRouter(
    strategy="semantic",
    fallback_agent=general_assistant,
    confidence_threshold=0.7,
    encoder="openai"
)
```

**Environment Variables:**

```bash
# For OpenAI
export OPENAI_API_KEY="sk-..."

# For Cohere
export COHERE_API_KEY="..."
```

## Practical Examples

### Example 1: Customer Support Bot

```python
from kagura import agent
from kagura.routing import AgentRouter

# Define specialized agents
@agent
async def billing_agent(query: str) -> str:
    '''Handle billing inquiries: {{ query }}'''
    pass

@agent
async def technical_agent(query: str) -> str:
    '''Handle technical issues: {{ query }}'''
    pass

@agent
async def general_agent(query: str) -> str:
    '''General customer support: {{ query }}'''
    pass

# Create router
router = AgentRouter(
    fallback_agent=general_agent,
    confidence_threshold=0.4
)

# Register agents
router.register(
    billing_agent,
    intents=["billing", "payment", "invoice", "charge", "subscription"],
    description="Handles billing and payment questions"
)

router.register(
    technical_agent,
    intents=["technical", "bug", "error", "crash", "not working"],
    description="Handles technical support issues"
)

# Use in chat loop
async def customer_support_chat():
    print("Customer Support Bot (type 'exit' to quit)")

    while True:
        query = input("\nCustomer: ")
        if query.lower() == "exit":
            break

        response = await router.route(query)
        print(f"Support: {response}")

# Run
await customer_support_chat()

# Example conversation:
# Customer: I was charged twice for my subscription
# Support: [billing_agent handles this]
#
# Customer: The app keeps crashing on startup
# Support: [technical_agent handles this]
#
# Customer: What are your business hours?
# Support: [general_agent handles this]
```

### Example 2: Development Assistant

```python
@agent
async def code_generator(description: str) -> str:
    '''Generate code from description: {{ description }}'''
    pass

@agent
async def code_reviewer(code: str) -> str:
    '''Review code quality: {{ code }}'''
    pass

@agent
async def bug_finder(code: str) -> str:
    '''Find bugs in code: {{ code }}'''
    pass

@agent
async def documenter(code: str) -> str:
    '''Generate documentation: {{ code }}'''
    pass

router = AgentRouter(confidence_threshold=0.3)

router.register(code_generator, intents=["generate", "create", "write"])
router.register(code_reviewer, intents=["review", "check", "assess"])
router.register(bug_finder, intents=["bug", "error", "issue", "debug"])
router.register(documenter, intents=["document", "docs", "comment"])

# Automatic task routing
await router.route("Generate a function to sort a list")
# → code_generator

await router.route("Check this code for issues")
# → code_reviewer

await router.route("Find bugs in this code")
# → bug_finder

await router.route("Add documentation to this function")
# → documenter
```

### Example 3: Educational Platform

```python
@agent
async def math_tutor(question: str) -> str:
    '''Math tutor: {{ question }}'''
    pass

@agent
async def physics_tutor(question: str) -> str:
    '''Physics tutor: {{ question }}'''
    pass

@agent
async def chemistry_tutor(question: str) -> str:
    '''Chemistry tutor: {{ question }}'''
    pass

@agent
async def general_tutor(question: str) -> str:
    '''General education tutor: {{ question }}'''
    pass

router = AgentRouter(
    fallback_agent=general_tutor,
    confidence_threshold=0.4
)

router.register(
    math_tutor,
    intents=["math", "algebra", "calculus", "geometry", "trigonometry"],
    description="Mathematics tutor"
)

router.register(
    physics_tutor,
    intents=["physics", "mechanics", "thermodynamics", "electricity"],
    description="Physics tutor"
)

router.register(
    chemistry_tutor,
    intents=["chemistry", "molecule", "reaction", "element"],
    description="Chemistry tutor"
)

# Smart subject routing
await router.route("How do I solve quadratic equations?")
# → math_tutor

await router.route("Explain Newton's laws of motion")
# → physics_tutor

await router.route("What is a covalent bond?")
# → chemistry_tutor

await router.route("How do I study effectively?")
# → general_tutor (fallback)
```

## Managing Agents

### List Registered Agents

```python
agents = router.list_agents()
print(f"Registered agents: {', '.join(agents)}")
# Registered agents: code_reviewer, translator, data_analyzer
```

### Get Agent Information

```python
info = router.get_agent_info("code_reviewer")
print(f"Description: {info['description']}")
print(f"Intents: {info['intents']}")

# Output:
# Description: Reviews code for quality and bugs
# Intents: ['review', 'check', 'analyze']
```

## Error Handling

### No Agent Found

```python
from kagura.routing import NoAgentFoundError

try:
    result = await router.route("Unknown request")
except NoAgentFoundError as e:
    print(f"No agent found for: {e.user_input}")
    # Handle the error gracefully
```

### With Fallback (Recommended)

```python
@agent
async def fallback(query: str) -> str:
    '''Fallback handler: {{ query }}'''
    pass

router = AgentRouter(fallback_agent=fallback)

# No exception raised - fallback is used automatically
result = await router.route("Any request")
```

## Best Practices

### 1. Use Specific Intent Keywords

```python
# ✅ Good: Specific, distinctive keywords
router.register(
    code_reviewer,
    intents=["review", "code quality", "static analysis"]
)

# ❌ Bad: Generic, overlapping keywords
router.register(
    code_reviewer,
    intents=["help", "check", "look"]
)
```

### 2. Provide Agent Descriptions

```python
# ✅ Good: Clear description
router.register(
    translator,
    intents=["translate"],
    description="Translates text between 50+ languages"
)

# ❌ Bad: No description
router.register(translator, intents=["translate"])
```

### 3. Test Edge Cases

```python
# Test ambiguous inputs
test_cases = [
    "review and translate",  # Matches multiple agents
    "",  # Empty input
    "xyz123",  # Random input
    "こんにちは",  # Unicode
]

for test in test_cases:
    try:
        matches = router.get_matched_agents(test)
        print(f"{test}: {len(matches)} matches")
    except Exception as e:
        print(f"{test}: Error - {e}")
```

### 4. Monitor Confidence Scores

```python
# Log routing decisions
matches = router.get_matched_agents(user_input, top_k=1)
if matches:
    agent, score = matches[0]
    print(f"Selected: {agent.__name__} (confidence: {score:.2f})")

    if score < 0.5:
        print("Warning: Low confidence routing")
```

### 5. Always Use Fallback

```python
# ✅ Good: Always have a fallback
router = AgentRouter(fallback_agent=general_agent)

# ❌ Bad: No fallback (exceptions for unmatched inputs)
router = AgentRouter()
```

## Troubleshooting

### Agent Not Being Selected

**Problem:** Expected agent is not selected

**Solution:** Check intent keywords and scoring

```python
# Debug: Check matched agents
matches = router.get_matched_agents(user_input, top_k=5)
for agent, score in matches:
    print(f"{agent.__name__}: {score:.2f}")

# If score is too low, add more intent keywords
router.register(
    my_agent,
    intents=["original", "keywords", "plus", "more", "variants"]
)
```

### Fallback Always Used

**Problem:** Fallback agent is always selected

**Solution:** Lower confidence threshold or add more intent keywords

```python
# Option 1: Lower threshold
router = AgentRouter(
    fallback_agent=fallback,
    confidence_threshold=0.2  # More lenient
)

# Option 2: Add more intents
router.register(
    my_agent,
    intents=["many", "different", "keyword", "variations"]
)
```

### Multiple Agents Match

**Problem:** Multiple agents have similar scores

**Solution:** Make intents more specific

```python
# Before: Generic intents
router.register(agent1, intents=["check", "analyze"])
router.register(agent2, intents=["check", "review"])

# After: Specific intents
router.register(agent1, intents=["performance check", "load analysis"])
router.register(agent2, intents=["code review", "quality review"])
```

## Next Steps

- **Phase 2**: Semantic routing with embedding-based matching
- **Phase 3**: Agent chaining and conditional routing
- **Integration**: Use with Chat REPL for conversational AI

## See Also

- [Agent Routing API Reference](https://github.com/JFK/kagura-ai/tree/main/src/kagura/routing)
- [Agent Decorator Guide](./01-basic-agent.md)
- [RFC-016: Agent Routing System](../../ai_docs/rfcs/RFC_016_AGENT_ROUTING.md)
