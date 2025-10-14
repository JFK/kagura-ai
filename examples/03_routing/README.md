# 03_routing - Agent Routing

This directory contains examples demonstrating intelligent agent selection and routing.

## Overview

Kagura AI's routing system automatically selects the most appropriate agent for a given query using:
- **KeywordRouter** - Rule-based routing with keyword patterns
- **LLMRouter** - AI-powered agent selection
- **SemanticRouter** - Vector similarity-based routing (RAG)
- **MemoryAwareRouter** - Context-aware routing with conversation history

## Routing Strategies

```
User Query
    │
    ▼
┌───────────────┐
│ Router        │
│ - Keywords    │
│ - LLM         │
│ - Semantic    │
│ - Memory-Aware│
└───────┬───────┘
        │
        ▼
  Select Agent
   ┌────┬────┐
   │    │    │
   ▼    ▼    ▼
Agent1 Agent2 Agent3
```

## Examples

### 1. keyword_routing.py - Rule-based Routing
**Demonstrates:**
- KeywordRouter with pattern matching
- Multiple agent registration
- Fallback handling

```python
from kagura.core.routing import KeywordRouter

router = KeywordRouter(
    routes={
        "weather": weather_agent,
        "math": math_agent,
        "general": general_agent
    },
    patterns={
        "weather": ["weather", "temperature", "rain", "forecast"],
        "math": ["calculate", "math", "equation", "solve"]
    },
    default_route="general"  # Fallback
)

# Route query
agent = router.route("What's the weather today?")
result = await agent("What's the weather today?")
```

**Key Concepts:**
- Fast, deterministic routing
- Pattern-based matching
- No LLM calls for routing
- Best for: Well-defined domains

**Use Cases:**
- Customer support (FAQ routing)
- Department-specific bots
- Clear intent categories

**Pros:**
- ⚡ Fast (no LLM call)
- 💰 Free (no API cost)
- 🎯 Predictable

**Cons:**
- ❌ Brittle (exact keyword match)
- ❌ No semantic understanding
- ❌ Manual pattern maintenance

---

### 2. semantic_routing.py - Vector Similarity Routing
**Demonstrates:**
- SemanticRouter with embeddings
- Similarity-based matching
- Intent descriptions

```python
from kagura.routing import SemanticRouter

router = SemanticRouter()

# Register agents with intent descriptions
router.register(
    code_agent,
    intents=[
        "Review code for bugs and improvements",
        "Analyze code quality",
        "Suggest refactoring"
    ]
)

router.register(
    docs_agent,
    intents=[
        "Write documentation",
        "Explain API usage",
        "Create tutorials"
    ]
)

# Route by semantic similarity
result = await router.route("Check my code for errors")
# → Selects code_agent (semantically similar to "Review code")
```

**Key Concepts:**
- Vector embeddings for semantic matching
- ChromaDB backend
- Similarity threshold tuning
- Best for: Fuzzy intent matching

**Use Cases:**
- Natural language interfaces
- Overlapping domains
- User intent classification

**Pros:**
- ✅ Semantic understanding
- ✅ Handles paraphrasing
- ✅ No keyword maintenance

**Cons:**
- 💰 Embedding costs (small)
- 🐢 Slower than keywords
- 📦 Requires ChromaDB

---

### 3. memory_aware_routing.py - Context-aware Routing
**Demonstrates:**
- MemoryAwareRouter with conversation history
- Context-enhanced queries
- Pronoun resolution
- Follow-up question handling

```python
from kagura.routing import MemoryAwareRouter
from kagura.core.memory import MemoryManager

memory = MemoryManager(agent_name="router")

router = MemoryAwareRouter(
    memory=memory,
    context_window=5  # Use last 5 messages
)

router.register(translator, intents=["translate"])
router.register(calculator, intents=["calculate"])

# First query
await router.route("Translate 'hello' to French")
# → Selects translator

# Context-aware follow-up
await router.route("What about Spanish?")
# → Understands context, selects translator again
# (resolves "it" to "hello" from context)
```

**Key Concepts:**
- Conversation context integration
- Pronoun and reference resolution
- Multi-turn routing
- Best for: Conversational apps

**Use Cases:**
- Multi-turn conversations
- Contextual assistants
- Follow-up questions
- Clarification handling

**Pros:**
- ✅ Context awareness
- ✅ Natural conversations
- ✅ Handles references

**Cons:**
- 💰 LLM cost (context enhancement)
- 📝 Requires memory management
- 🐢 Slower (LLM call)

---

## Prerequisites

```bash
# Install Kagura AI
pip install kagura-ai

# For semantic routing (optional)
pip install chromadb

# Or install all routing features
pip install kagura-ai[routing]
```

## Running Examples

```bash
# Run any example
python keyword_routing.py

# Semantic routing (requires chromadb)
python semantic_routing.py

# Memory-aware routing
python memory_aware_routing.py
```

## Routing Strategy Comparison

| Feature | Keyword | Semantic | Memory-Aware |
|---------|---------|----------|--------------|
| **Speed** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **Cost** | Free | Low | Medium |
| **Accuracy** | Medium | High | Very High |
| **Context Awareness** | ❌ No | ❌ No | ✅ Yes |
| **Setup Complexity** | Low | Medium | High |
| **Best For** | Simple FAQs | Intent classification | Conversations |
| **Dependencies** | None | ChromaDB | Memory system |

## Choosing the Right Router

### Use KeywordRouter when:
- ✅ Clear, distinct intent categories
- ✅ Cost-sensitive (no API calls)
- ✅ Speed is critical
- ✅ Predictable queries

### Use SemanticRouter when:
- ✅ Fuzzy intent boundaries
- ✅ Natural language variety
- ✅ No context needed
- ✅ One-shot queries

### Use MemoryAwareRouter when:
- ✅ Multi-turn conversations
- ✅ Context references (it, that, this)
- ✅ Follow-up questions
- ✅ Conversational interfaces

## Common Patterns

### Pattern 1: Hybrid Routing (Keyword + Semantic Fallback)
```python
from kagura.routing import KeywordRouter, SemanticRouter

# Try keyword first (fast)
keyword_router = KeywordRouter(patterns={"code": ["code", "bug"]})
agent = keyword_router.route(query, allow_none=True)

if agent is None:
    # Fallback to semantic (slower but smarter)
    semantic_router = SemanticRouter()
    agent = await semantic_router.route(query)

result = await agent(query)
```

### Pattern 2: Confidence Thresholds
```python
from kagura.routing import SemanticRouter

router = SemanticRouter(similarity_threshold=0.7)

# Route with confidence check
agent, score = router.route_with_score(query)

if score < 0.7:
    # Low confidence, use fallback
    agent = default_agent

result = await agent(query)
```

### Pattern 3: Multi-Agent Workflow
```python
from kagura.routing import AgentRouter

router = AgentRouter()
router.register(analyzer, intents=["analyze"])
router.register(summarizer, intents=["summarize"])
router.register(reporter, intents=["report"])

# Route multi-step workflow
analysis = await router.route("Analyze the data")(data)
summary = await router.route("Summarize findings")(analysis)
report = await router.route("Generate report")(summary)
```

### Pattern 4: Dynamic Agent Registration
```python
# Register agents dynamically
agents = {
    "code": code_reviewer,
    "docs": doc_writer,
    "test": test_generator
}

router = AgentRouter()
for name, agent in agents.items():
    router.register(agent, intents=[name])

# Route at runtime
task = "Review this code"
result = await router.route(task)(code)
```

## Best Practices

### 1. Define Clear Intent Boundaries

✅ **Good:**
```python
router.register(weather_agent, intents=[
    "weather forecast",
    "temperature query",
    "precipitation check"
])

router.register(news_agent, intents=[
    "latest news",
    "current events",
    "breaking stories"
])
```

❌ **Bad:**
```python
router.register(agent1, intents=["general", "misc", "other"])  # Too vague
router.register(agent2, intents=["stuff", "things"])  # Overlapping
```

### 2. Provide Fallback Handling

```python
# ✅ Good: Always have a fallback
router = KeywordRouter(
    routes={...},
    default_route="general_agent"  # Handles unknown intents
)

# ❌ Bad: No fallback
router = KeywordRouter(routes={...})  # May raise NoAgentFoundError
```

### 3. Use Context Window Wisely

```python
# ✅ Good: Reasonable context window
router = MemoryAwareRouter(
    memory=memory,
    context_window=5  # Last 5 messages (~1K tokens)
)

# ❌ Bad: Too large (expensive, slow)
router = MemoryAwareRouter(
    memory=memory,
    context_window=50  # Overkill!
)
```

### 4. Test Routing Accuracy

```python
# Unit test routing
test_cases = [
    ("What's 2+2?", math_agent),
    ("Translate hello", translator),
    ("Tell me a joke", chat_agent)
]

for query, expected_agent in test_cases:
    selected = router.route(query)
    assert selected == expected_agent, f"Failed for: {query}"
```

### 5. Monitor Routing Performance

```python
from kagura.observability import EventStore

# Route and track
agent = router.route(query)
result = await agent(query)

# Analyze routing patterns
store = EventStore()
stats = store.get_routing_stats()
print(f"Most selected agent: {stats['top_agent']}")
print(f"Routing accuracy: {stats['accuracy']:.1%}")
```

## Advanced Techniques

### Custom Router Implementation
```python
from kagura.routing import AgentRouter

class CustomRouter(AgentRouter):
    def route(self, query: str):
        # Custom routing logic
        if "urgent" in query.lower():
            return self.high_priority_agent
        elif len(query) > 100:
            return self.detailed_agent
        else:
            return super().route(query)

router = CustomRouter()
```

### Weighted Intent Matching
```python
from kagura.routing import SemanticRouter

router = SemanticRouter()

# Register with importance weights
router.register(
    critical_agent,
    intents=["critical issue", "urgent problem"],
    weight=2.0  # Higher priority
)

router.register(
    general_agent,
    intents=["general question"],
    weight=1.0  # Normal priority
)
```

### Multi-Agent Consensus
```python
# Route to multiple agents and combine results
agents = [
    router.route("Analyze sentiment")(text),
    router.route("Extract entities")(text),
    router.route("Summarize")(text)
]

results = await asyncio.gather(*agents)
combined = combine_results(results)
```

## Troubleshooting

### Issue: Router selects wrong agent
**Solution:** Review intent descriptions and add more specific keywords:
```python
# Before
router.register(agent, intents=["code"])

# After (more specific)
router.register(agent, intents=[
    "review code for bugs",
    "analyze code quality",
    "suggest code improvements"
])
```

### Issue: NoAgentFoundError
**Solution:** Add a default/fallback agent:
```python
router = KeywordRouter(
    routes={...},
    default_route="fallback_agent"  # Always available
)
```

### Issue: Routing is too slow
**Solution:** Use KeywordRouter for common queries, SemanticRouter for edge cases:
```python
# Fast path: keyword
if keyword_router.can_route(query):
    agent = keyword_router.route(query)
else:
    # Slow path: semantic
    agent = semantic_router.route(query)
```

### Issue: Context not working in MemoryAwareRouter
**Solution:** Ensure memory is shared and properly initialized:
```python
# ✅ Good: Shared memory
memory = MemoryManager(agent_name="router")
router = MemoryAwareRouter(memory=memory)

# Add messages to memory before routing
await memory.add_message("user", "Previous message")
await router.route("Follow-up question")
```

## Next Steps

After mastering routing, explore:
- [02_memory](../02_memory/) - Memory management
- [06_advanced](../06_advanced/) - Advanced workflows
- [08_real_world](../08_real_world/) - Production routing patterns

## Documentation

- [API Reference - Routing](../../docs/en/api/routing.md)
- [RFC-019: Memory-Aware Routing](../../ai_docs/rfcs/RFC_019_MEMORY_AWARE_ROUTING.md)
- [Semantic Router Guide](../../docs/en/guides/semantic_routing.md)

---

**Start with `keyword_routing.py` for the basics, then progress to semantic and memory-aware routing!**
