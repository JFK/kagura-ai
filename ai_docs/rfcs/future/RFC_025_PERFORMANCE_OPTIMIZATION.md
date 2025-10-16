# RFC-025: Performance Optimization System

**Status**: Draft  
**Created**: 2025-10-14  
**Issue**: [#170](https://github.com/JFK/kagura-ai/issues/170)  
**Priority**: 🥈 Medium-High (Tier 2)

---

## 📋 Problem Statement

Kagura AI 2.0 makes **multiple serial LLM calls** across various subsystems, resulting in:

### Performance Issues

1. **Slow Response Times**
   - Routing: ~2.5s (2 LLM calls)
   - Meta Agent generation: 5-10s
   - Context Summarization: 3-8s
   - **Total latency**: 10-20s for complex workflows

2. **High API Costs**
   - Redundant LLM calls (same prompt, same result)
   - No caching mechanism
   - No batching optimization

3. **Poor Scalability**
   - Serial execution (no parallelization)
   - Can't handle concurrent users efficiently
   - Memory usage grows linearly

### Root Causes

1. **No LLM Response Caching**
   ```python
   # Current: Every call hits the API
   result1 = await call_llm("translate 'hello'", model="gpt-4o-mini")
   result2 = await call_llm("translate 'hello'", model="gpt-4o-mini")  # Duplicate!
   ```

2. **Serial Execution**
   ```python
   # Current: Serial (3s)
   context = await analyzer.analyze(query)  # 1.5s
   enhanced = enhance_query(query, context)
   agent = await router.route(enhanced)  # 1.5s
   
   # Could be: Parallel (1.5s)
   context, routing_result = await asyncio.gather(
       analyzer.analyze(query),
       router.route_preliminary(query)
   )
   ```

3. **No Streaming for Long Tasks**
   - Users wait 10s+ with no feedback
   - Poor perceived performance

---

## 💡 Proposed Solution

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Performance Layer                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ LLM Cache    │  │ Parallel     │  │ Streaming    │      │
│  │ Manager      │  │ Executor     │  │ Handler      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                 │                  │               │
│         └─────────────────┴──────────────────┘               │
│                           │                                  │
│                    ┌──────▼──────┐                           │
│                    │  call_llm() │  (Enhanced)              │
│                    └─────────────┘                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Goals

### Performance Targets

- ✅ **Response time reduction**: 70%+ for cached queries
- ✅ **API cost reduction**: 60%+ through caching
- ✅ **Cache hit rate**: 90%+ for common queries
- ✅ **Parallel execution**: 40%+ speedup for independent operations
- ✅ **Streaming**: Perceived latency reduction for long tasks

### Non-Goals

- ❌ Query result caching at application level (out of scope)
- ❌ Model fine-tuning for speed (separate effort)
- ❌ Hardware acceleration (GPU/TPU)

---

## 🔧 Technical Design

### Phase 1: LLM Call Caching (3 days)

#### 1.1 Cache Manager

```python
# src/kagura/core/cache.py
from typing import Any, Literal
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class CacheEntry:
    """Cached LLM response"""
    key: str
    response: Any
    created_at: datetime
    ttl: int  # seconds
    model: str
    
    @property
    def is_expired(self) -> bool:
        return datetime.now() > self.created_at + timedelta(seconds=self.ttl)

class LLMCache:
    """Intelligent LLM response caching"""
    
    def __init__(
        self,
        backend: Literal["memory", "redis", "disk"] = "memory",
        default_ttl: int = 3600,  # 1 hour
        max_size: int = 1000
    ):
        self.backend = backend
        self.default_ttl = default_ttl
        self.max_size = max_size
        self._cache: dict[str, CacheEntry] = {}
    
    def _hash_key(self, prompt: str, model: str, **kwargs) -> str:
        """Generate cache key from prompt + params"""
        data = {
            "prompt": prompt,
            "model": model,
            **kwargs
        }
        return hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()[:16]
    
    async def get(self, key: str) -> Any | None:
        """Get cached response"""
        if entry := self._cache.get(key):
            if not entry.is_expired:
                return entry.response
            # Expired, remove
            del self._cache[key]
        return None
    
    async def set(self, key: str, response: Any, ttl: int | None = None):
        """Cache response"""
        if len(self._cache) >= self.max_size:
            # Evict oldest
            oldest = min(self._cache.values(), key=lambda e: e.created_at)
            del self._cache[oldest.key]
        
        self._cache[key] = CacheEntry(
            key=key,
            response=response,
            created_at=datetime.now(),
            ttl=ttl or self.default_ttl,
            model="unknown"  # TODO: pass model
        )
    
    async def invalidate(self, pattern: str | None = None):
        """Invalidate cache entries"""
        if pattern is None:
            self._cache.clear()
        else:
            # Pattern matching
            keys_to_delete = [
                k for k in self._cache.keys()
                if pattern in k
            ]
            for key in keys_to_delete:
                del self._cache[key]
    
    def stats(self) -> dict[str, Any]:
        """Get cache statistics"""
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "backend": self.backend,
        }
```

#### 1.2 Integration with call_llm()

```python
# src/kagura/core/llm.py
from .cache import LLMCache

# Global cache instance
_llm_cache = LLMCache(backend="memory", default_ttl=3600)

async def call_llm(
    prompt: str,
    model: str = "gpt-4o-mini",
    use_cache: bool = True,
    cache_ttl: int | None = None,
    **kwargs
) -> str:
    """Call LLM with automatic caching"""
    
    if use_cache:
        cache_key = _llm_cache._hash_key(prompt, model, **kwargs)
        if cached := await _llm_cache.get(cache_key):
            return cached
    
    # Call LLM API
    response = await _call_llm_api(prompt, model, **kwargs)
    
    if use_cache:
        await _llm_cache.set(cache_key, response, ttl=cache_ttl)
    
    return response

def get_llm_cache() -> LLMCache:
    """Get global cache instance"""
    return _llm_cache
```

#### 1.3 Redis Backend (Optional)

```python
# src/kagura/core/cache_backends.py
from redis.asyncio import Redis
import pickle

class RedisCache(LLMCache):
    """Redis-backed cache for production"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", **kwargs):
        super().__init__(backend="redis", **kwargs)
        self.redis = Redis.from_url(redis_url, decode_responses=False)
    
    async def get(self, key: str) -> Any | None:
        if data := await self.redis.get(f"kagura:llm:{key}"):
            return pickle.loads(data)
        return None
    
    async def set(self, key: str, response: Any, ttl: int | None = None):
        await self.redis.setex(
            f"kagura:llm:{key}",
            ttl or self.default_ttl,
            pickle.dumps(response)
        )
```

### Phase 2: Parallelization (2 days)

#### 2.1 Parallel Executor

```python
# src/kagura/core/parallel.py
import asyncio
from typing import Callable, Any

async def parallel_llm_calls(
    *calls: tuple[Callable, tuple, dict]
) -> list[Any]:
    """Execute multiple LLM calls in parallel"""
    tasks = [
        func(*args, **kwargs)
        for func, args, kwargs in calls
    ]
    return await asyncio.gather(*tasks, return_exceptions=True)
```

#### 2.2 Integration Examples

```python
# src/kagura/routing/memory_aware_router.py
async def route(self, query: str):
    # Before: Serial (3s)
    # context = await self.analyzer.analyze(query)  # 1.5s
    # agent = await self.router.route(query)  # 1.5s
    
    # After: Parallel (1.5s)
    from kagura.core.parallel import parallel_llm_calls
    
    context, routing_result = await asyncio.gather(
        self.analyzer.analyze(query),
        self.router.route(query)
    )
    
    # Merge results intelligently
    if context.needs_enhancement:
        enhanced_query = self.enhance_query(query, context)
        return await self.router.route(enhanced_query)
    
    return routing_result
```

### Phase 3: Streaming Support (3 days)

#### 3.1 Stream Handler

```python
# src/kagura/core/streaming.py
from typing import AsyncIterator

async def call_llm_stream(
    prompt: str,
    model: str = "gpt-4o-mini",
    **kwargs
) -> AsyncIterator[str]:
    """Stream LLM response"""
    async for chunk in litellm.acompletion(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        stream=True,
        **kwargs
    ):
        if content := chunk.choices[0].delta.content:
            yield content
```

#### 3.2 Agent Decorator Support

```python
# src/kagura/core/decorators.py
@agent(stream=True)
async def research_agent(query: str) -> AsyncIterator[str]:
    """Research {{ query }}"""
    pass

# Usage
async for chunk in research_agent("AI trends 2025"):
    print(chunk, end="", flush=True)
```

---

## 📊 Performance Benchmarks

### Before Optimization

| Operation | Time | Cost |
|-----------|------|------|
| Routing (2 LLM calls) | 2.5s | $0.004 |
| Meta Agent generation | 8s | $0.012 |
| Summarization | 5s | $0.008 |
| **Total** | **15.5s** | **$0.024** |

### After Optimization (Estimated)

| Operation | Time | Cost | Improvement |
|-----------|------|------|-------------|
| Routing (cached 90%) | 0.8s | $0.0004 | 68% faster, 90% cheaper |
| Meta Agent (cached 50%) | 4.5s | $0.006 | 44% faster, 50% cheaper |
| Summarization (cached 70%) | 2s | $0.0024 | 60% faster, 70% cheaper |
| **Total** | **7.3s** | **$0.0088** | **53% faster, 63% cheaper** |

---

## 🧪 Testing Strategy

### Unit Tests

```python
# tests/core/test_cache.py
async def test_cache_hit():
    cache = LLMCache()
    key = cache._hash_key("test", "gpt-4o-mini")
    await cache.set(key, "response")
    assert await cache.get(key) == "response"

async def test_cache_expiration():
    cache = LLMCache(default_ttl=1)
    key = cache._hash_key("test", "gpt-4o-mini")
    await cache.set(key, "response")
    await asyncio.sleep(2)
    assert await cache.get(key) is None

async def test_cache_eviction():
    cache = LLMCache(max_size=2)
    # Fill cache
    # Test LRU eviction
```

### Integration Tests

```python
# tests/integration/test_performance.py
async def test_routing_performance():
    # Measure time without cache
    start = time.time()
    await router.route("query")
    uncached_time = time.time() - start
    
    # Measure time with cache
    start = time.time()
    await router.route("query")  # Should hit cache
    cached_time = time.time() - start
    
    assert cached_time < uncached_time * 0.3  # 70% faster
```

### Performance Tests

```python
# tests/performance/test_benchmarks.py
@pytest.mark.benchmark
async def test_cache_hit_rate():
    # Run 100 queries
    # Measure cache hit rate
    assert hit_rate > 0.90
```

---

## 📚 Documentation Plan

### User Guides

1. `docs/en/guides/performance-optimization.md`
   - Caching strategies
   - Parallelization examples
   - Streaming best practices

2. `docs/en/guides/caching.md`
   - Cache configuration
   - Redis setup
   - Cache invalidation

### API Reference

1. `docs/en/api/cache.md`
   - LLMCache API
   - Cache backends
   - Configuration options

---

## 🎯 Success Criteria

### Phase 1: LLM Caching
- ✅ Cache hit rate: 90%+
- ✅ Response time reduction: 70%+ (cached queries)
- ✅ API cost reduction: 60%+
- ✅ 20+ tests (100% coverage)

### Phase 2: Parallelization
- ✅ Routing speedup: 40%+
- ✅ Multimodal processing: 50%+ faster
- ✅ No regression in existing tests

### Phase 3: Streaming
- ✅ Streaming support for all agents
- ✅ Perceived latency reduction
- ✅ 10+ streaming examples

### Overall
- ✅ 50+ new tests (all passing)
- ✅ Pyright: 0 errors
- ✅ Ruff: All checks passed
- ✅ CI: All tests pass

---

## 📅 Timeline

**Total Duration**: 8 days (1 week + 1 day)

### Week 1

**Day 1-3**: Phase 1 - LLM Caching
- Day 1: Cache Manager implementation
- Day 2: Integration with call_llm()
- Day 3: Redis backend + tests

**Day 4-5**: Phase 2 - Parallelization
- Day 4: Parallel executor + routing optimization
- Day 5: Multimodal parallelization + tests

**Day 6-8**: Phase 3 - Streaming
- Day 6: Stream handler implementation
- Day 7: Agent decorator integration
- Day 8: Documentation + final tests

---

## 🔗 Related Work

- RFC-010: Observability (performance monitoring integration)
- RFC-021: Agent Observability Dashboard (metrics display)
- Issue #171: Test execution time reduction (similar optimization)

---

## 📝 Open Questions

1. **Q**: Should we cache streaming responses?
   **A**: No, streaming is inherently non-cacheable. Only cache final results.

2. **Q**: What's the default TTL?
   **A**: 1 hour for most queries, configurable per call.

3. **Q**: Redis vs memory cache?
   **A**: Memory for development, Redis for production (persistent, shared).

4. **Q**: Cache invalidation strategy?
   **A**: TTL-based (automatic), manual invalidation for critical updates.

---

**Status**: Ready for implementation  
**Next Step**: Create implementation plan (Day-by-day tasks)
