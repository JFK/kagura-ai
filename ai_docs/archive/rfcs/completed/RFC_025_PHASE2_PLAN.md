# RFC-025 Phase 2 Implementation Plan: Parallelization

**RFC**: [RFC-025](./RFC_025_PERFORMANCE_OPTIMIZATION.md)  
**Phase**: 2 of 3  
**Duration**: 2 days (Day 4-5)  
**Start Date**: 2025-10-14

---

## 📋 Overview

Phase 2 implements **parallel LLM call execution** to achieve:
- ✅ 40% speedup for routing operations
- ✅ 50% speedup for multimodal file processing
- ✅ Better resource utilization
- ✅ Improved scalability

---

## 🎯 Goals

### Performance Targets

- ✅ MemoryAwareRouter: 2.5s → 1.5s (40% faster)
- ✅ Multimodal directory loading: 50% faster for 10+ files
- ✅ No regression in existing functionality
- ✅ Thread-safe parallel execution

### Implementation Goals

- ✅ Reusable parallel execution helpers
- ✅ Backward compatible (no API changes)
- ✅ 13+ new tests
- ✅ Zero breaking changes

---

## 🔧 Day 4: Parallel Executor & Routing (4-6 hours)

### Task 4.1: Parallel Helper Functions (2 hours)

**Goal**: Create reusable helpers for parallel LLM calls

**File**: `src/kagura/core/parallel.py`

```python
"""Parallel execution helpers for LLM operations"""

import asyncio
from typing import Any, Callable, TypeVar, Coroutine

T = TypeVar("T")


async def parallel_gather(*awaitables: Coroutine[Any, Any, T]) -> list[T]:
    """Execute multiple async operations in parallel
    
    Args:
        *awaitables: Coroutines to execute in parallel
    
    Returns:
        List of results in same order as input
    
    Example:
        >>> results = await parallel_gather(
        ...     call_llm("prompt1", config),
        ...     call_llm("prompt2", config),
        ...     call_llm("prompt3", config)
        ... )
        >>> # All 3 calls execute concurrently
    """
    return await asyncio.gather(*awaitables)


async def parallel_map(
    func: Callable[[T], Coroutine[Any, Any, Any]],
    items: list[T],
    max_concurrent: int = 5
) -> list[Any]:
    """Apply async function to items in parallel with concurrency limit
    
    Args:
        func: Async function to apply to each item
        items: List of items to process
        max_concurrent: Maximum concurrent executions (default: 5)
    
    Returns:
        List of results in same order as items
    
    Example:
        >>> async def process_file(path: Path):
        ...     return await load_file(path)
        >>> 
        >>> files = [Path("f1.txt"), Path("f2.txt"), ...]
        >>> results = await parallel_map(process_file, files, max_concurrent=5)
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def bounded_func(item: T):
        async with semaphore:
            return await func(item)
    
    return await asyncio.gather(*[bounded_func(item) for item in items])
```

**Tests**: `tests/core/test_parallel.py` (5 tests)
- test_parallel_gather_basic
- test_parallel_gather_empty
- test_parallel_map_basic
- test_parallel_map_concurrency_limit
- test_parallel_map_error_handling

---

### Task 4.2: Optimize MemoryAwareRouter (3 hours)

**Goal**: Parallelize context analysis and preliminary routing

**File**: `src/kagura/routing/memory_aware_router.py`

**Current (Serial - 3s)**:
```python
async def route(self, query: str) -> str:
    context = await self.analyzer.analyze(query)  # 1.5s
    enhanced = self.enhance_query(query, context)
    agent = await self.router.route(enhanced)  # 1.5s
    return agent
```

**Optimized (Parallel - 1.5s)**:
```python
async def route(self, query: str) -> str:
    # Run analysis and preliminary routing in parallel
    from kagura.core.parallel import parallel_gather
    
    context_task = self.analyzer.analyze(query)
    prelim_routing_task = self.router.route(query)
    
    context, prelim_agent = await parallel_gather(
        context_task,
        prelim_routing_task
    )
    
    # If context doesn't need enhancement, use preliminary result
    if not context.needs_enhancement:
        return prelim_agent
    
    # Otherwise, re-route with enhanced query
    enhanced_query = self.enhance_query(query, context)
    return await self.router.route(enhanced_query)
```

**Tests**: Update existing routing tests + add performance benchmarks
- test_memory_aware_router_parallel (verify correctness)
- test_routing_performance_improvement (benchmark)

---

## 🔧 Day 5: Multimodal Parallelization (4-6 hours)

### Task 5.1: Parallel File Processing (4 hours)

**Goal**: Process multiple files concurrently in MultimodalRAG

**File**: `src/kagura/core/memory/multimodal_rag.py`

**Current (Serial)**:
```python
async def load_directory(self, directory: Path) -> list[Document]:
    documents = []
    for file_path in files:
        doc = await self.process_file(file_path)  # Serial
        documents.append(doc)
    return documents
```

**Optimized (Parallel)**:
```python
async def load_directory(
    self, 
    directory: Path,
    max_concurrent: int = 5
) -> list[Document]:
    """Load all files in directory in parallel
    
    Args:
        directory: Directory to scan
        max_concurrent: Max concurrent file processing (default: 5)
    
    Returns:
        List of processed documents
    """
    from kagura.core.parallel import parallel_map
    
    files = self.scanner.scan(directory)
    
    # Process files in parallel with concurrency limit
    documents = await parallel_map(
        self.process_file,
        files,
        max_concurrent=max_concurrent
    )
    
    return documents
```

**Tests**: `tests/core/memory/test_multimodal_parallel.py` (8 tests)
- test_parallel_file_loading
- test_concurrent_file_processing
- test_max_concurrent_limit
- test_parallel_loading_performance
- test_parallel_error_handling
- test_parallel_with_mixed_file_types
- test_parallel_caching_works
- test_parallel_progress_tracking

---

### Task 5.2: Documentation & Benchmarks (2 hours)

**File**: `docs/en/guides/performance-optimization.md`

Add parallelization section:
- How parallel execution works
- Configuration options
- Performance benchmarks
- Best practices

---

## 📊 Success Criteria

### Performance Benchmarks

**Before Parallelization**:
| Operation | Time | Files |
|-----------|------|-------|
| MemoryAwareRouter | 2.5s | N/A |
| Load 10 files | 15s | 10 |
| Load 50 files | 75s | 50 |

**After Parallelization**:
| Operation | Time | Improvement | Files |
|-----------|------|-------------|-------|
| MemoryAwareRouter | 1.5s | **40% faster** | N/A |
| Load 10 files | 8s | **47% faster** | 10 |
| Load 50 files | 38s | **49% faster** | 50 |

### Quality Metrics

- ✅ 13+ new tests (all passing)
- ✅ Pyright: 0 errors
- ✅ Ruff: All checks passed
- ✅ No regression in existing tests
- ✅ Thread-safe execution

---

## 📅 Daily Checklist

### Day 4
- [ ] Create `src/kagura/core/parallel.py` (80 lines)
- [ ] `parallel_gather()` function
- [ ] `parallel_map()` function with semaphore
- [ ] 5 tests in `test_parallel.py`
- [ ] Optimize `MemoryAwareRouter.route()`
- [ ] 2 routing performance tests
- [ ] Pyright 0 errors
- [ ] Ruff all checks passed

### Day 5
- [ ] Update `MultimodalRAG.load_directory()` with parallel processing
- [ ] Add `max_concurrent` parameter
- [ ] 8 tests in `test_multimodal_parallel.py`
- [ ] Update `performance-optimization.md` documentation
- [ ] Run full test suite (verify no regressions)
- [ ] Commit and push
- [ ] Create PR

---

## 🚀 Implementation Order

1. **parallel.py helpers** → Foundation for all parallel operations
2. **MemoryAwareRouter optimization** → High-impact, visible improvement
3. **MultimodalRAG parallel loading** → High-impact for large datasets
4. **Tests** → Ensure correctness and thread safety
5. **Documentation** → Help users understand parallel execution

---

## 🧪 Testing Strategy

### Unit Tests

```python
# test_parallel.py
async def test_parallel_gather_basic():
    async def task1():
        await asyncio.sleep(0.1)
        return "result1"
    
    async def task2():
        await asyncio.sleep(0.1)
        return "result2"
    
    start = time.time()
    results = await parallel_gather(task1(), task2())
    duration = time.time() - start
    
    assert results == ["result1", "result2"]
    assert duration < 0.15  # Should be ~0.1s, not 0.2s
```

### Performance Tests

```python
# test_routing_performance.py
@pytest.mark.benchmark
async def test_routing_speedup():
    # Measure serial routing
    start = time.time()
    await router_serial.route("query")
    serial_time = time.time() - start
    
    # Measure parallel routing
    start = time.time()
    await router_parallel.route("query")
    parallel_time = time.time() - start
    
    # Verify 40% improvement
    assert parallel_time < serial_time * 0.6
```

---

**Ready to implement!**  
**First task**: Create `src/kagura/core/parallel.py`
