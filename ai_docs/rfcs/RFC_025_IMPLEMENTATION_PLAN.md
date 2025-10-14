# RFC-025 Implementation Plan: Performance Optimization

**RFC**: [RFC-025](./RFC_025_PERFORMANCE_OPTIMIZATION.md)  
**Issue**: [#170](https://github.com/JFK/kagura-ai/issues/170)  
**Duration**: 8 days  
**Start Date**: 2025-10-14

---

## 📋 Overview

This plan implements **LLM caching, parallelization, and streaming** to achieve:
- ✅ 70% response time reduction (cached queries)
- ✅ 60% API cost reduction
- ✅ 90% cache hit rate
- ✅ Streaming support for all agents

---

## 🎯 Phase 1: LLM Call Caching (Day 1-3)

### Day 1: Cache Manager Core

**Goal**: Implement memory-based LLM cache

#### Task 1.1: Cache Data Structures (2 hours)

```python
# src/kagura/core/cache.py
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

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
```

**Tests** (1 hour):
- `tests/core/test_cache_entry.py`: 5 tests

#### Task 1.2: Cache Manager (4 hours)

```python
# src/kagura/core/cache.py (continued)
import hashlib
import json

class LLMCache:
    """Intelligent LLM response caching"""
    
    def __init__(
        self,
        backend: Literal["memory", "redis", "disk"] = "memory",
        default_ttl: int = 3600,
        max_size: int = 1000
    ):
        self.backend = backend
        self.default_ttl = default_ttl
        self.max_size = max_size
        self._cache: dict[str, CacheEntry] = {}
        self._hits = 0
        self._misses = 0
    
    def _hash_key(self, prompt: str, model: str, **kwargs) -> str:
        """Generate deterministic cache key"""
        # Sort kwargs for consistency
        data = {
            "prompt": prompt,
            "model": model,
            **{k: v for k, v in sorted(kwargs.items())}
        }
        return hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()[:16]
    
    async def get(self, key: str) -> Any | None:
        """Get cached response"""
        if entry := self._cache.get(key):
            if not entry.is_expired:
                self._hits += 1
                return entry.response
            # Expired, remove
            del self._cache[key]
        
        self._misses += 1
        return None
    
    async def set(self, key: str, response: Any, ttl: int | None = None):
        """Cache response with LRU eviction"""
        # Evict if at capacity
        if len(self._cache) >= self.max_size:
            # Remove oldest entry
            oldest = min(self._cache.values(), key=lambda e: e.created_at)
            del self._cache[oldest.key]
        
        self._cache[key] = CacheEntry(
            key=key,
            response=response,
            created_at=datetime.now(),
            ttl=ttl or self.default_ttl,
            model="unknown"  # Will be passed in integration
        )
    
    async def invalidate(self, pattern: str | None = None):
        """Invalidate cache entries"""
        if pattern is None:
            self._cache.clear()
        else:
            # Pattern matching (simple contains)
            keys_to_delete = [
                k for k in self._cache.keys()
                if pattern in k
            ]
            for key in keys_to_delete:
                del self._cache[key]
    
    def stats(self) -> dict[str, Any]:
        """Get cache statistics"""
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0.0
        
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "backend": self.backend,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
        }
```

**Tests** (2 hours):
- `tests/core/test_cache.py`: 15 tests
  - test_cache_get_miss
  - test_cache_get_hit
  - test_cache_set
  - test_cache_expiration
  - test_cache_eviction_lru
  - test_hash_key_deterministic
  - test_hash_key_kwargs_order
  - test_invalidate_all
  - test_invalidate_pattern
  - test_stats
  - test_hit_rate_calculation
  - test_max_size_enforcement
  - test_concurrent_access (async)
  - test_large_response_caching
  - test_empty_cache

**Deliverables**:
- ✅ `src/kagura/core/cache.py` (150 lines)
- ✅ `tests/core/test_cache.py` (20 tests)
- ✅ Pyright 0 errors

---

### Day 2: Integration with call_llm()

**Goal**: Integrate cache into existing LLM call infrastructure

#### Task 2.1: Enhance call_llm() (3 hours)

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
    """Call LLM with automatic caching
    
    Args:
        prompt: The prompt to send
        model: Model to use
        use_cache: Enable caching (default: True)
        cache_ttl: Cache TTL in seconds (default: 3600)
        **kwargs: Additional LLM parameters
    
    Returns:
        LLM response (from cache or API)
    """
    # Check cache
    if use_cache:
        cache_key = _llm_cache._hash_key(prompt, model, **kwargs)
        if cached := await _llm_cache.get(cache_key):
            return cached
    
    # Call LLM API (existing implementation)
    response = await _call_llm_api(prompt, model, **kwargs)
    
    # Store in cache
    if use_cache:
        await _llm_cache.set(cache_key, response, ttl=cache_ttl)
    
    return response

def get_llm_cache() -> LLMCache:
    """Get global cache instance for inspection/invalidation"""
    return _llm_cache

def set_llm_cache(cache: LLMCache):
    """Set custom cache instance"""
    global _llm_cache
    _llm_cache = cache
```

#### Task 2.2: Update LLMConfig (2 hours)

```python
# src/kagura/core/llm.py
@dataclass
class LLMConfig:
    """LLM configuration"""
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 2000
    
    # Cache configuration
    enable_cache: bool = True
    cache_ttl: int = 3600  # 1 hour
    cache_backend: Literal["memory", "redis"] = "memory"
```

**Tests** (3 hours):
- `tests/core/test_llm_cache_integration.py`: 12 tests
  - test_call_llm_cache_hit
  - test_call_llm_cache_miss
  - test_call_llm_cache_disabled
  - test_call_llm_custom_ttl
  - test_get_llm_cache
  - test_set_llm_cache
  - test_cache_across_multiple_calls
  - test_cache_with_different_kwargs
  - test_cache_invalidation
  - test_llm_config_cache_settings
  - test_concurrent_cache_access
  - test_cache_stats_tracking

**Deliverables**:
- ✅ Enhanced `call_llm()` with caching
- ✅ 12 integration tests
- ✅ All existing tests still pass

---

### Day 3: Redis Backend & Documentation

**Goal**: Add Redis backend + docs

#### Task 3.1: Redis Cache Backend (3 hours)

```python
# src/kagura/core/cache_backends.py
from redis.asyncio import Redis
import pickle
from typing import Any

class RedisCache(LLMCache):
    """Redis-backed cache for production use"""
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        default_ttl: int = 3600,
        **kwargs
    ):
        super().__init__(backend="redis", default_ttl=default_ttl, **kwargs)
        self.redis = Redis.from_url(redis_url, decode_responses=False)
        self._key_prefix = "kagura:llm:"
    
    async def get(self, key: str) -> Any | None:
        """Get from Redis"""
        if data := await self.redis.get(f"{self._key_prefix}{key}"):
            self._hits += 1
            return pickle.loads(data)
        
        self._misses += 1
        return None
    
    async def set(self, key: str, response: Any, ttl: int | None = None):
        """Set in Redis with TTL"""
        await self.redis.setex(
            f"{self._key_prefix}{key}",
            ttl or self.default_ttl,
            pickle.dumps(response)
        )
    
    async def invalidate(self, pattern: str | None = None):
        """Invalidate Redis keys"""
        if pattern is None:
            # Delete all kagura:llm:* keys
            async for key in self.redis.scan_iter(f"{self._key_prefix}*"):
                await self.redis.delete(key)
        else:
            # Delete matching keys
            async for key in self.redis.scan_iter(f"{self._key_prefix}*{pattern}*"):
                await self.redis.delete(key)
    
    async def stats(self) -> dict[str, Any]:
        """Redis cache stats"""
        info = await self.redis.info("stats")
        base_stats = await super().stats()
        
        return {
            **base_stats,
            "redis_hits": info.get("keyspace_hits", 0),
            "redis_misses": info.get("keyspace_misses", 0),
        }
    
    async def close(self):
        """Close Redis connection"""
        await self.redis.close()
```

**Tests** (2 hours):
- `tests/core/test_redis_cache.py`: 10 tests (with Redis mock or pytest-redis)

#### Task 3.2: Optional Dependency (30 min)

```toml
# pyproject.toml
[project.optional-dependencies]
cache-redis = ["redis>=5.0.0"]
```

#### Task 3.3: Documentation (2 hours)

1. `docs/en/guides/caching.md`:
   - Cache configuration
   - Redis setup guide
   - Cache invalidation strategies
   - Performance benchmarks

2. `docs/en/api/cache.md`:
   - LLMCache API reference
   - Cache backends
   - Configuration options

**Deliverables**:
- ✅ Redis backend implementation
- ✅ 10 Redis cache tests
- ✅ 2 documentation files
- ✅ Optional dependency added

---

## 🎯 Phase 2: Parallelization (Day 4-5)

### Day 4: Parallel Executor & Routing

**Goal**: Parallelize independent LLM calls

#### Task 4.1: Parallel Helper (2 hours)

```python
# src/kagura/core/parallel.py
import asyncio
from typing import Callable, Any, TypeVar

T = TypeVar("T")

async def parallel_llm_calls(
    *calls: tuple[Callable[..., T], tuple, dict]
) -> list[T]:
    """Execute multiple LLM calls in parallel
    
    Args:
        *calls: Tuples of (function, args, kwargs)
    
    Returns:
        List of results (same order as input)
    
    Example:
        results = await parallel_llm_calls(
            (call_llm, ("prompt1", "gpt-4o"), {}),
            (call_llm, ("prompt2", "gpt-4o-mini"), {"temperature": 0.5})
        )
    """
    tasks = [
        func(*args, **kwargs)
        for func, args, kwargs in calls
    ]
    return await asyncio.gather(*tasks, return_exceptions=False)

async def parallel_gather(*awaitables):
    """Simplified gather wrapper"""
    return await asyncio.gather(*awaitables)
```

**Tests** (1 hour):
- `tests/core/test_parallel.py`: 5 tests

#### Task 4.2: Optimize MemoryAwareRouter (3 hours)

```python
# src/kagura/routing/memory_aware_router.py
import asyncio

async def route(self, query: str) -> str:
    """Route with parallel analysis + routing"""
    
    # Before: Serial (3s total)
    # context = await self.analyzer.analyze(query)  # 1.5s
    # enhanced = self.enhance_query(query, context)
    # agent = await self.router.route(enhanced)  # 1.5s
    
    # After: Parallel preliminary checks (1.5s total)
    context_task = self.analyzer.analyze(query)
    prelim_routing_task = self.router.route(query)
    
    context, prelim_agent = await asyncio.gather(
        context_task,
        prelim_routing_task
    )
    
    # If context doesn't need enhancement, use preliminary routing
    if not context.needs_enhancement:
        return prelim_agent
    
    # Otherwise, re-route with enhanced query
    enhanced_query = self.enhance_query(query, context)
    return await self.router.route(enhanced_query)
```

**Tests** (2 hours):
- Update existing routing tests
- Add performance benchmarks

**Deliverables**:
- ✅ Parallel execution helpers
- ✅ Optimized MemoryAwareRouter (40% faster)
- ✅ 5+ tests

---

### Day 5: Multimodal Parallelization

**Goal**: Parallelize multimodal file processing

#### Task 5.1: Parallel File Processing (4 hours)

```python
# src/kagura/multimodal/loader.py
import asyncio

async def load_directory(
    self, 
    directory: Path,
    max_concurrent: int = 5
) -> list[Document]:
    """Load all files in directory in parallel"""
    
    files = self.scanner.scan(directory)
    
    # Process files in batches
    documents = []
    for i in range(0, len(files), max_concurrent):
        batch = files[i:i + max_concurrent]
        
        # Process batch in parallel
        batch_docs = await asyncio.gather(*[
            self.process_file(file_path)
            for file_path in batch
        ])
        
        documents.extend(batch_docs)
    
    return documents
```

**Tests** (2 hours):
- `tests/multimodal/test_parallel_loading.py`: 8 tests

**Deliverables**:
- ✅ Parallel file processing (50% faster for large directories)
- ✅ 8 tests
- ✅ Benchmark comparison

---

## 🎯 Phase 3: Streaming Support (Day 6-8)

### Day 6: Stream Handler

**Goal**: Implement streaming infrastructure

#### Task 6.1: Streaming LLM Calls (4 hours)

```python
# src/kagura/core/streaming.py
from typing import AsyncIterator
import litellm

async def call_llm_stream(
    prompt: str,
    model: str = "gpt-4o-mini",
    **kwargs
) -> AsyncIterator[str]:
    """Stream LLM response chunk by chunk
    
    Args:
        prompt: The prompt
        model: Model to use
        **kwargs: Additional parameters
    
    Yields:
        Response chunks as they arrive
    
    Example:
        async for chunk in call_llm_stream("Write a story"):
            print(chunk, end="", flush=True)
    """
    response = await litellm.acompletion(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        stream=True,
        **kwargs
    )
    
    async for chunk in response:
        if content := chunk.choices[0].delta.content:
            yield content
```

**Tests** (2 hours):
- `tests/core/test_streaming.py`: 8 tests

**Deliverables**:
- ✅ Streaming LLM calls
- ✅ 8 tests

---

### Day 7: Agent Decorator Integration

**Goal**: Enable streaming in @agent decorator

#### Task 7.1: Streaming Agent Decorator (4 hours)

```python
# src/kagura/core/decorators.py
from typing import AsyncIterator

@agent(stream=True)
async def research_agent(query: str) -> AsyncIterator[str]:
    """Research {{ query }}"""
    pass

# Implementation
def agent(
    func: Callable | None = None,
    stream: bool = False,
    **config_kwargs
):
    """Agent decorator with streaming support"""
    
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Render prompt
            prompt = render_prompt(func, args, kwargs)
            
            if stream:
                # Return async iterator
                return call_llm_stream(prompt, **config_kwargs)
            else:
                # Return response
                return await call_llm(prompt, **config_kwargs)
        
        return wrapper
    
    return decorator(func) if func else decorator
```

**Tests** (2 hours):
- `tests/core/test_agent_streaming.py`: 10 tests

**Deliverables**:
- ✅ Streaming agent decorator
- ✅ 10 tests
- ✅ Backward compatibility

---

### Day 8: Documentation & Final Testing

**Goal**: Complete documentation + comprehensive testing

#### Task 8.1: User Documentation (3 hours)

1. `docs/en/guides/performance-optimization.md`:
   - Overview of performance features
   - Caching strategies
   - Parallelization examples
   - Streaming best practices
   - Benchmarks

2. `docs/en/guides/streaming.md`:
   - Streaming agents
   - UI integration
   - Error handling

3. Update `docs/en/tutorials/`:
   - Add streaming examples
   - Add caching examples

#### Task 8.2: API Documentation (2 hours)

1. `docs/en/api/cache.md`:
   - LLMCache API
   - RedisCache API
   - Configuration

2. `docs/en/api/streaming.md`:
   - call_llm_stream()
   - Streaming decorator
   - AsyncIterator patterns

#### Task 8.3: Final Testing (3 hours)

- Run full test suite (900+ tests)
- Performance benchmarks
- Integration tests
- CI/CD validation

**Deliverables**:
- ✅ Complete documentation (1000+ lines)
- ✅ All tests pass
- ✅ Performance benchmarks validated

---

## 📊 Success Criteria Checklist

### Phase 1: Caching
- ✅ LLMCache implemented (150 lines)
- ✅ 20+ unit tests
- ✅ Redis backend implemented
- ✅ Cache hit rate: 90%+ (measured)
- ✅ Response time reduction: 70%+ (cached)

### Phase 2: Parallelization
- ✅ Parallel executor implemented
- ✅ MemoryAwareRouter optimized (40% faster)
- ✅ Multimodal processing parallelized (50% faster)
- ✅ 13+ tests

### Phase 3: Streaming
- ✅ Streaming LLM calls implemented
- ✅ Agent decorator streaming support
- ✅ 18+ tests
- ✅ Documentation complete

### Overall
- ✅ 50+ new tests (all passing)
- ✅ Pyright: 0 errors
- ✅ Ruff: All checks passed
- ✅ CI: All 950+ tests pass
- ✅ Performance benchmarks meet targets

---

## 📅 Daily Checklist

### Day 1
- [ ] CacheEntry dataclass
- [ ] LLMCache class (150 lines)
- [ ] 20 unit tests
- [ ] Pyright 0 errors

### Day 2
- [ ] Enhance call_llm() with caching
- [ ] Update LLMConfig
- [ ] 12 integration tests
- [ ] All existing tests pass

### Day 3
- [ ] RedisCache backend
- [ ] 10 Redis tests
- [ ] Documentation (caching.md, cache.md)
- [ ] Optional dependency added

### Day 4
- [ ] Parallel execution helpers
- [ ] Optimize MemoryAwareRouter
- [ ] 5+ tests
- [ ] Benchmark: 40% speedup

### Day 5
- [ ] Parallel multimodal loading
- [ ] 8 tests
- [ ] Benchmark: 50% speedup

### Day 6
- [ ] call_llm_stream() implementation
- [ ] 8 streaming tests
- [ ] Streaming works end-to-end

### Day 7
- [ ] Streaming agent decorator
- [ ] 10 tests
- [ ] Backward compatibility verified

### Day 8
- [ ] Complete documentation (1000+ lines)
- [ ] All 950+ tests pass
- [ ] CI/CD green
- [ ] Performance benchmarks validated

---

## 🚀 Deployment Plan

### PR Structure

Single PR with all 3 phases:
- Title: `feat(performance): RFC-025 - LLM Caching, Parallelization & Streaming (#170)`
- Description: Performance improvements summary
- Benchmarks included in PR description

### Breaking Changes

- ✅ None! All changes are backward compatible
- `use_cache=True` is default, but can be disabled

### Migration Guide

No migration needed. Users automatically benefit from:
- Automatic LLM caching
- Parallel routing
- Streaming (opt-in via `stream=True`)

---

## 📝 Post-Implementation Tasks

1. Blog post: "How We Made Kagura AI 70% Faster"
2. Twitter thread with benchmarks
3. Update CHANGELOG.md
4. Release v2.5.1 (performance improvements)

---

**Ready to start implementation!**  
**First task**: Create branch from Issue #170 → `gh issue develop 170 --checkout`
