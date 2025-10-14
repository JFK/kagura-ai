# RFC-025 Phase 3 Implementation Plan: Streaming Support

**RFC**: [RFC-025](./RFC_025_PERFORMANCE_OPTIMIZATION.md)  
**Phase**: 3 of 3  
**Duration**: 3 days (Day 6-8)  
**Start Date**: 2025-10-14

---

## 📋 Overview

Phase 3 implements **streaming LLM responses** to achieve:
- ✅ Improved perceived latency (users see progress immediately)
- ✅ Better UX for long-running tasks
- ✅ Real-time token streaming
- ✅ `@agent(stream=True)` decorator support

---

## 🎯 Goals

### User Experience Targets

- ✅ First token latency: <500ms (vs 2-5s for full response)
- ✅ Streaming support for all LLM models
- ✅ Backward compatible (stream=False is default)
- ✅ Easy integration with UI/CLI

### Implementation Goals

- ✅ `call_llm_stream()` function
- ✅ `@agent(stream=True)` decorator support
- ✅ 18+ new tests
- ✅ Zero breaking changes

---

## 🔧 Day 6: Stream Handler (4-6 hours)

### Task 6.1: Streaming LLM Call Function (3 hours)

**Goal**: Implement streaming wrapper for litellm

**File**: `src/kagura/core/streaming.py`

```python
"""Streaming support for LLM responses"""

from typing import AsyncIterator, Any
import litellm
from .llm import LLMConfig


async def call_llm_stream(
    prompt: str,
    config: LLMConfig,
    **kwargs: Any
) -> AsyncIterator[str]:
    """Stream LLM response token by token
    
    Args:
        prompt: The prompt to send
        config: LLM configuration
        **kwargs: Additional litellm parameters
    
    Yields:
        Response tokens as they arrive
    
    Example:
        >>> config = LLMConfig(model="gpt-4o-mini")
        >>> async for chunk in call_llm_stream("Write a story", config):
        ...     print(chunk, end="", flush=True)
        Once upon a time...
    
    Note:
        - Streaming responses are NOT cached (non-deterministic)
        - OAuth2 authentication supported (same as call_llm)
    """
    # Build messages
    messages = [{"role": "user", "content": prompt}]
    
    # Get API key (OAuth2 support)
    api_key = config.get_api_key()
    
    # Prepare kwargs
    llm_kwargs = dict(kwargs)
    if api_key:
        llm_kwargs["api_key"] = api_key
    
    # Call litellm with streaming
    response = await litellm.acompletion(
        model=config.model,
        messages=messages,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        top_p=config.top_p,
        stream=True,  # Enable streaming
        **llm_kwargs
    )
    
    # Yield chunks as they arrive
    async for chunk in response:
        if hasattr(chunk, "choices") and chunk.choices:
            delta = chunk.choices[0].delta
            if hasattr(delta, "content") and delta.content:
                yield delta.content
```

**Tests**: `tests/core/test_streaming.py` (8 tests)
- test_call_llm_stream_basic
- test_call_llm_stream_yields_chunks
- test_call_llm_stream_full_response
- test_call_llm_stream_empty_response
- test_call_llm_stream_with_oauth2
- test_call_llm_stream_error_handling
- test_streaming_not_cached
- test_streaming_with_custom_config

---

## 🔧 Day 7: Agent Decorator Integration (4-6 hours)

### Task 7.1: Streaming Agent Decorator (4 hours)

**Goal**: Add `stream=True` support to @agent decorator

**File**: `src/kagura/core/decorators.py`

**Changes**:
1. Add `stream: bool = False` parameter
2. Modify wrapper to return `AsyncIterator[str]` when `stream=True`
3. Update type hints

```python
@overload
def agent(
    fn: Callable[P, Awaitable[T]],
    *,
    config: Optional[LLMConfig] = None,
    stream: bool = False,  # NEW
    # ... existing params
) -> Callable[P, Awaitable[T] | AsyncIterator[str]]: ...  # Updated return type

def agent(
    fn: Callable[P, Awaitable[T]] | None = None,
    *,
    config: Optional[LLMConfig] = None,
    stream: bool = False,  # NEW
    # ... existing params
):
    """Convert function into AI agent.
    
    Args:
        stream: Enable streaming responses (default: False)
        # ... existing docs
    
    Example:
        # Streaming agent
        @agent(stream=True)
        async def storyteller(topic: str) -> AsyncIterator[str]:
            '''Write a story about {{ topic }}'''
            pass
        
        # Use streaming
        async for chunk in storyteller("dragons"):
            print(chunk, end="", flush=True)
    """
    
    def decorator(func: Callable[P, Awaitable[T]]):
        # ... existing setup code
        
        if stream:
            # Streaming wrapper
            @functools.wraps(func)
            async def streaming_wrapper(*args, **kwargs):
                # ... render prompt (same as before)
                
                # Use call_llm_stream instead of call_llm
                from .streaming import call_llm_stream
                
                async for chunk in call_llm_stream(prompt, llm_config, **llm_kwargs):
                    yield chunk
            
            return streaming_wrapper
        else:
            # Non-streaming wrapper (existing code)
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                # ... existing implementation
                pass
            
            return wrapper
    
    return decorator if fn is None else decorator(fn)
```

**Tests**: `tests/core/test_agent_streaming.py` (10 tests)
- test_agent_streaming_basic
- test_agent_streaming_yields_chunks
- test_agent_streaming_full_text
- test_agent_streaming_with_config
- test_agent_streaming_with_memory (should work)
- test_agent_streaming_with_tools (should raise error)
- test_agent_non_streaming_default
- test_streaming_not_cached
- test_streaming_async_iteration
- test_streaming_error_handling

---

## 🔧 Day 8: Documentation & Finalization (4-6 hours)

### Task 8.1: User Documentation (3 hours)

**File**: `docs/en/guides/performance-streaming.md`

Content:
- Overview of streaming
- Quick start examples
- `@agent(stream=True)` usage
- UI integration patterns
- Error handling
- Best practices
- Performance comparison

### Task 8.2: Update Existing Docs (1 hour)

Update:
- `docs/en/guides/performance-optimization.md` - Add streaming section
- `docs/en/guides/performance-caching.md` - Note streaming not cached

### Task 8.3: Final Testing (2 hours)

- Run full test suite (900+ tests)
- Verify no regressions
- Performance benchmarks
- CI/CD validation

---

## 📊 Success Criteria

### Phase 3: Streaming
- ✅ Streaming LLM calls implemented
- ✅ `@agent(stream=True)` works
- ✅ 18+ tests (all passing)
- ✅ First token latency <500ms
- ✅ Documentation complete

### Overall RFC-025
- ✅ 100+ new tests (Phases 1-3)
- ✅ Pyright: 0 errors
- ✅ Ruff: All checks passed
- ✅ CI: All tests pass
- ✅ Complete documentation

---

## 📅 Daily Checklist

### Day 6
- [ ] Create `src/kagura/core/streaming.py` (100 lines)
- [ ] `call_llm_stream()` function
- [ ] OAuth2 support in streaming
- [ ] 8 tests in `test_streaming.py`
- [ ] Pyright 0 errors
- [ ] Ruff all checks passed

### Day 7
- [ ] Add `stream` parameter to @agent decorator
- [ ] Update type hints for streaming
- [ ] Streaming wrapper implementation
- [ ] 10 tests in `test_agent_streaming.py`
- [ ] Verify memory/tools compatibility
- [ ] All existing tests still pass

### Day 8
- [ ] Create `performance-streaming.md` guide
- [ ] Update `performance-optimization.md`
- [ ] Update `performance-caching.md`
- [ ] Run full test suite (verify no regressions)
- [ ] Commit and push
- [ ] Create PR
- [ ] CI validation

---

## 🚀 Expected Performance

### Perceived Latency

**Without streaming**:
```
User sends query
    ↓
[Wait 2-5s with no feedback]
    ↓
Full response appears
```

**With streaming**:
```
User sends query
    ↓
[500ms] First tokens appear ⚡
    ↓
[Tokens stream in real-time]
    ↓
Complete response (same 2-5s total, but better UX)
```

### Use Cases

✅ **Good for streaming**:
- Long-form content generation
- Step-by-step explanations
- Creative writing
- Code generation

❌ **Not suitable for streaming**:
- Structured JSON responses (needs complete response)
- Pydantic model parsing (needs complete response)
- Single-word answers

---

**Ready to implement Phase 3!**  
**First task**: Create Issue #179 for Phase 3
