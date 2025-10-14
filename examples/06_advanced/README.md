# 06_advanced - Advanced Features

This directory contains examples demonstrating advanced Kagura AI features for production environments.

## Overview

Master advanced capabilities:
- **Workflows** - Multi-agent orchestration (@workflow decorator)
- **Code Execution** - Safe Python execution with security constraints
- **Context Compression** - Automatic memory compression (RFC-024)
- **LLM Caching** - Response caching for cost optimization
- **Streaming** - Real-time token-by-token responses
- **Parallelization** - Concurrent agent execution

## Advanced Features Architecture

```
┌──────────────────┐
│ Advanced Agent   │
├──────────────────┤
│ • Workflows      │ ← Multi-step orchestration
│ • Code Exec      │ ← Safe Python execution
│ • Compression    │ ← Auto memory management
│ • Caching        │ ← Response caching
│ • Streaming      │ ← Token streaming
│ • Parallelization│ ← Concurrent execution
└──────────────────┘
```

## Examples

### 1. full_featured_agent.py - All Features Combined
**Demonstrates:**
- Combining multiple advanced features
- Production-ready agent configuration
- Memory + compression + caching
- Tool integration

```python
from pathlib import Path
from kagura import agent, CompressionPolicy, LLMCache

cache = LLMCache()

@agent(
    model="gpt-4o-mini",
    enable_memory=True,
    persist_dir=Path("./memory"),
    enable_compression=True,
    compression_policy=CompressionPolicy(
        strategy="smart",
        max_tokens=4000,
        trigger_threshold=0.8
    ),
    tools=[calculate, search],
    enable_multimodal_rag=True,
    rag_directory=Path("./docs")
)
async def full_agent(query: str, memory, rag) -> str:
    """
    Full-featured assistant: {{ query }}

    Features:
    - Memory across sessions
    - Auto compression at 80%
    - Tool calling (calculate, search)
    - Document RAG search
    - Response caching
    """
    pass

# Use full-featured agent
result = await full_agent("Analyze sales data from Q3")
```

**Key Concepts:**
- Feature composition
- Production configuration
- Performance optimization
- Best for: Complex production agents

---

### 2. caching_demo.py - LLM Response Caching
**Demonstrates:**
- LLM response caching
- Cache configuration
- Cost optimization
- Cache invalidation

```python
from kagura import agent, LLMCache, get_llm_cache, set_llm_cache

# Configure global cache
cache = LLMCache(
    max_size_mb=100,
    ttl_seconds=3600  # 1 hour
)
set_llm_cache(cache)

@agent
async def cached_agent(query: str) -> str:
    """Answer: {{ query }}"""
    pass

# First call: hits LLM
result1 = await cached_agent("What is Python?")

# Second call: cache hit (no LLM call, no cost!)
result2 = await cached_agent("What is Python?")

# Check cache stats
stats = cache.stats()
print(f"Hit rate: {stats['hit_rate']:.1%}")
print(f"Cost saved: ${stats['cost_saved']:.2f}")
```

**Key Concepts:**
- Response caching
- Cost reduction
- Cache TTL management
- Best for: Repeated queries

**Benefits:**
- ⚡ Instant responses (cache hits)
- 💰 Cost savings (no LLM calls)
- 🔧 Configurable TTL
- 📊 Cache statistics

**Use Cases:**
- FAQ systems
- Repeated analytics
- Development/testing
- User onboarding

---

### 3. streaming_demo.py - Real-time Streaming
**Demonstrates:**
- Token-by-token streaming
- Improved perceived latency
- Progressive output display
- Streaming patterns

```python
from kagura.core.streaming import call_llm_stream
from kagura import LLMConfig

config = LLMConfig(model="gpt-4o-mini")

async def stream_response():
    prompt = "Write a story about a robot."

    # Stream tokens as they arrive
    async for chunk in call_llm_stream(prompt, config):
        print(chunk, end="", flush=True)

# First token arrives in <500ms (vs 2-5s for full response)
await stream_response()
```

**Key Concepts:**
- Progressive output
- Reduced perceived latency
- Better user experience
- Best for: Long-form content

**Benefits:**
- ⚡ First token < 500ms
- 👀 Better UX (progressive display)
- 🎯 User engagement
- ⏱️ Perceived speed improvement

**Use Cases:**
- Chatbots
- Content generation
- Code writing
- Long explanations

---

### 4. parallel_execution.py - Concurrent Agents
**Demonstrates:**
- Running agents in parallel
- asyncio.gather for concurrency
- Performance optimization
- Error handling in parallel

```python
import asyncio
from kagura import agent

@agent
async def sentiment_agent(text: str) -> str:
    """Analyze sentiment of: {{ text }}"""
    pass

@agent
async def keywords_agent(text: str) -> str:
    """Extract keywords from: {{ text }}"""
    pass

@agent
async def summary_agent(text: str) -> str:
    """Summarize: {{ text }}"""
    pass

async def analyze_parallel(text: str):
    # Run all agents in parallel
    results = await asyncio.gather(
        sentiment_agent(text),
        keywords_agent(text),
        summary_agent(text)
    )

    return {
        "sentiment": results[0],
        "keywords": results[1],
        "summary": results[2]
    }

# 3x faster than sequential!
analysis = await analyze_parallel("Long article text...")
```

**Key Concepts:**
- Concurrent execution
- asyncio.gather
- Independent task parallelization
- Best for: Multiple independent tasks

**Benefits:**
- ⚡ N× faster (N = number of agents)
- 🔄 Concurrent LLM calls
- 💡 Resource optimization
- 📊 Batch processing

---

## Prerequisites

```bash
# Install Kagura AI with all features
pip install kagura-ai[all]

# Or install specific features
pip install kagura-ai[memory,multimodal,web]

# Set API key
export OPENAI_API_KEY="your-key"
```

## Running Examples

```bash
# Run any example
python full_featured_agent.py
python caching_demo.py
python streaming_demo.py
python parallel_execution.py
```

## Feature Comparison

| Feature | Use Case | Performance | Complexity | Cost Impact |
|---------|----------|-------------|------------|-------------|
| **Workflows** | Multi-step tasks | Medium | High | Neutral |
| **Code Execution** | Dynamic computation | Fast | Medium | Free |
| **Compression** | Long conversations | Medium | Low | Reduces tokens |
| **Caching** | Repeated queries | Instant | Low | Saves $$$ |
| **Streaming** | Long responses | Fast | Low | Neutral |
| **Parallelization** | Independent tasks | N× faster | Medium | Neutral |

## Common Patterns

### Pattern 1: Production Agent Template
```python
from pathlib import Path
from kagura import agent, CompressionPolicy, LLMCache

# Global cache
cache = LLMCache(max_size_mb=100, ttl_seconds=3600)

@agent(
    model="gpt-4o-mini",
    temperature=0.7,
    enable_memory=True,
    persist_dir=Path("./memory"),
    enable_compression=True,
    compression_policy=CompressionPolicy(
        strategy="smart",
        max_tokens=4000
    ),
    tools=[custom_tool],
    max_retries=3  # Retry failed calls
)
async def production_agent(query: str, memory) -> str:
    """Production-ready agent: {{ query }}"""
    pass
```

### Pattern 2: Workflow Orchestration
```python
from kagura import workflow

@workflow
async def data_pipeline(data_path: str) -> dict:
    """Process data through multi-step pipeline"""
    # Step 1: Load and validate
    data = await load_agent(data_path)

    # Step 2: Analyze (parallel)
    stats, insights = await asyncio.gather(
        stats_agent(data),
        insights_agent(data)
    )

    # Step 3: Generate report
    report = await report_agent({
        "stats": stats,
        "insights": insights
    })

    return {"report": report, "status": "success"}

# Execute workflow
result = await data_pipeline("sales_data.csv")
```

### Pattern 3: Smart Caching Strategy
```python
from kagura import agent, LLMCache

cache = LLMCache(max_size_mb=100)

@agent
async def smart_cached_agent(query: str, use_cache: bool = True) -> str:
    """Agent with optional caching"""
    pass

# Cache for static queries
faq_answer = await smart_cached_agent("What are your hours?")

# Skip cache for dynamic queries
current_status = await smart_cached_agent(
    "What's the current system status?",
    use_cache=False
)
```

### Pattern 4: Streaming with Accumulation
```python
from kagura.core.streaming import call_llm_stream

async def stream_and_save(prompt: str):
    """Stream while accumulating full response"""
    chunks = []

    async for chunk in call_llm_stream(prompt, config):
        print(chunk, end="", flush=True)
        chunks.append(chunk)

    full_response = "".join(chunks)

    # Save for later
    await save_to_db(full_response)

    return full_response
```

### Pattern 5: Parallel + Sequential Workflow
```python
@workflow
async def complex_workflow(input_data: str) -> dict:
    """Combine parallel and sequential steps"""
    # Parallel phase 1
    results_phase1 = await asyncio.gather(
        agent1(input_data),
        agent2(input_data),
        agent3(input_data)
    )

    # Sequential phase 2 (depends on phase 1)
    combined = await combiner_agent(results_phase1)

    # Parallel phase 3
    final_results = await asyncio.gather(
        finalizer1(combined),
        finalizer2(combined)
    )

    return {"phase1": results_phase1, "final": final_results}
```

## Best Practices

### 1. Enable Compression for Long Conversations

✅ **Good:**
```python
@agent(
    enable_memory=True,
    enable_compression=True,
    compression_policy=CompressionPolicy(
        strategy="smart",
        trigger_threshold=0.8  # Compress at 80% full
    )
)
async def long_conversation_agent(query: str, memory) -> str:
    pass
```

❌ **Bad:**
```python
@agent(enable_memory=True)  # No compression, will hit limits
async def agent(query: str, memory) -> str:
    pass
```

### 2. Cache Static Content, Not Dynamic

```python
# ✅ Good: Cache FAQ
@agent
async def faq_agent(question: str) -> str:
    """FAQ: {{ question }}"""
    pass

# ❌ Bad: Cache time-sensitive data
@agent
async def stock_price_agent(symbol: str) -> str:
    """Current price for {{ symbol }}"""  # Changes constantly!
    pass
```

### 3. Use Streaming for Long Responses

```python
# ✅ Good: Stream long content
async def generate_article(topic: str):
    async for chunk in call_llm_stream(f"Write article: {topic}", config):
        yield chunk  # Progressive display

# ❌ Bad: Wait for entire response
async def generate_article(topic: str):
    response = await agent(topic)  # User waits 10+ seconds
    return response
```

### 4. Parallelize Independent Tasks Only

```python
# ✅ Good: Independent tasks
results = await asyncio.gather(
    sentiment_agent(text),
    keyword_agent(text),
    summary_agent(text)
)

# ❌ Bad: Dependent tasks (sequential required)
step1 = await preprocess(data)
step2 = await analyze(step1)  # Depends on step1
step3 = await report(step2)   # Depends on step2
```

### 5. Handle Parallel Errors Gracefully

```python
# ✅ Good: Error handling
results = await asyncio.gather(
    agent1(input),
    agent2(input),
    agent3(input),
    return_exceptions=True  # Don't fail all if one fails
)

for i, result in enumerate(results):
    if isinstance(result, Exception):
        print(f"Agent {i} failed: {result}")
    else:
        process_result(result)

# ❌ Bad: No error handling
results = await asyncio.gather(...)  # One failure breaks all
```

## Advanced Techniques

### Dynamic Compression Strategy
```python
from kagura import CompressionPolicy

def get_compression_policy(conversation_length: int):
    """Dynamic compression based on context size"""
    if conversation_length < 10:
        # No compression for short conversations
        return CompressionPolicy(strategy="none")
    elif conversation_length < 50:
        # FIFO for medium conversations
        return CompressionPolicy(strategy="fifo", max_tokens=4000)
    else:
        # Smart compression for long conversations
        return CompressionPolicy(strategy="smart", max_tokens=4000)

@agent(
    enable_memory=True,
    compression_policy=get_compression_policy(len(conversation))
)
async def adaptive_agent(query: str, memory) -> str:
    pass
```

### Cascading Cache with Fallback
```python
from kagura import LLMCache

# L1 cache: Fast, small
l1_cache = LLMCache(max_size_mb=50, ttl_seconds=300)

# L2 cache: Slower, larger
l2_cache = LLMCache(max_size_mb=500, ttl_seconds=3600)

async def cached_call(prompt: str):
    # Try L1
    result = l1_cache.get(prompt)
    if result:
        return result

    # Try L2
    result = l2_cache.get(prompt)
    if result:
        l1_cache.set(prompt, result)  # Promote to L1
        return result

    # Cache miss: call LLM
    result = await agent(prompt)
    l1_cache.set(prompt, result)
    l2_cache.set(prompt, result)
    return result
```

### Streaming with Realtime Processing
```python
async def stream_with_processing(prompt: str):
    """Stream and process chunks in real-time"""
    buffer = ""
    sentence_count = 0

    async for chunk in call_llm_stream(prompt, config):
        print(chunk, end="", flush=True)
        buffer += chunk

        # Process complete sentences
        if chunk in ".!?":
            sentence_count += 1
            if sentence_count % 5 == 0:
                # Emit event every 5 sentences
                await emit_progress_event(buffer)
                buffer = ""
```

### Adaptive Parallelization
```python
async def adaptive_parallel(tasks, max_workers=5):
    """Dynamically adjust parallelization based on load"""
    semaphore = asyncio.Semaphore(max_workers)

    async def run_task(task):
        async with semaphore:
            return await task

    results = await asyncio.gather(
        *[run_task(task) for task in tasks],
        return_exceptions=True
    )
    return results
```

## Performance Optimization

### 1. Measure and Profile
```python
import time
from kagura.observability import EventStore

start = time.time()
result = await agent(query)
duration = time.time() - start

# Track performance
store = EventStore()
stats = store.get_performance_stats(agent_name="my_agent")
print(f"Avg latency: {stats['avg_latency']:.2f}s")
```

### 2. Optimize Compression Threshold
```python
# Monitor token usage
from kagura.core.compression import ContextMonitor

monitor = ContextMonitor(max_tokens=8000)
usage = monitor.check_usage(messages)

print(f"Token usage: {usage.percentage:.1%}")
if usage.should_compress:
    # Trigger compression
    compressed = await compress_messages(messages)
```

### 3. Cache Warming
```python
# Pre-warm cache with common queries
common_queries = [
    "What are your hours?",
    "How do I contact support?",
    "What's your refund policy?"
]

for query in common_queries:
    await faq_agent(query)  # Cache these responses

# Now cache is warm for real users
```

## Troubleshooting

### Issue: Compression not triggering
**Solution:** Check threshold and enable compression:
```python
@agent(
    enable_compression=True,  # Must be True
    compression_policy=CompressionPolicy(
        trigger_threshold=0.8  # Trigger at 80%
    )
)
async def agent(query: str, memory) -> str:
    pass
```

### Issue: Cache not working
**Solution:** Ensure global cache is set:
```python
from kagura import LLMCache, set_llm_cache

cache = LLMCache()
set_llm_cache(cache)  # Set globally

# Now all agents use cache
```

### Issue: Streaming is slow
**Solution:** Check network and model selection:
```python
# Use faster model for streaming
config = LLMConfig(
    model="gpt-4o-mini",  # Faster than gpt-4
    stream=True
)
```

### Issue: Parallel execution not faster
**Solution:** Ensure tasks are truly independent:
```python
# ✅ Independent (can parallelize)
results = await asyncio.gather(
    agent1(input),
    agent2(input)
)

# ❌ Dependent (must be sequential)
result1 = await agent1(input)
result2 = await agent2(result1)  # Depends on result1
```

## Next Steps

After mastering advanced features, explore:
- [08_real_world](../08_real_world/) - Production examples
- [02_memory](../02_memory/) - Memory management
- [07_presets](../07_presets/) - Pre-configured agents

## Documentation

- [RFC-024: Context Compression](../../ai_docs/rfcs/RFC_024_CONTEXT_COMPRESSION.md)
- [RFC-025: Streaming](../../ai_docs/rfcs/RFC_025_STREAMING.md)
- [API Reference - Advanced](../../docs/en/api/advanced.md)

---

**Master these advanced features to build production-ready, high-performance AI agents!**
