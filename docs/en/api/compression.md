# Context Compression API

RFC-024 Phase 1: Token Management

**Status**: Phase 1 Implemented
**Since**: v2.5.0

---

## Overview

The compression module provides token counting and context window management for efficient long-form conversations.

**Key Components**:
- `TokenCounter`: Accurate token counting for all major LLM models
- `ContextMonitor`: Real-time context window usage monitoring
- `ContextUsage`: Usage statistics dataclass

---

## TokenCounter

Count tokens for various LLM models using tiktoken.

### Constructor

```python
TokenCounter(model: str = "gpt-4o-mini")
```

**Parameters:**
- `model` (str): LLM model name. Supported models:
  - OpenAI: `gpt-4o-mini`, `gpt-4o`, `gpt-4-turbo`, `gpt-3.5-turbo`
  - Anthropic: `claude-3-5-sonnet`, `claude-3-opus`, `claude-3-sonnet`
  - Google: `gemini-1.5-pro`, `gemini-1.5-flash`

**Example:**
```python
from kagura.core.compression import TokenCounter

counter = TokenCounter(model="gpt-4o-mini")
```

---

### Methods

#### count_tokens

Count tokens in text.

```python
def count_tokens(text: str) -> int
```

**Parameters:**
- `text` (str): Text to count

**Returns:**
- `int`: Number of tokens

**Example:**
```python
counter = TokenCounter()
tokens = counter.count_tokens("Hello, world!")
print(f"Tokens: {tokens}")  # Tokens: 4
```

---

#### count_tokens_messages

Count tokens in message list (OpenAI format).

Includes overhead for message formatting (3 tokens per message + 3 tokens reply priming).

```python
def count_tokens_messages(messages: list[dict[str, Any]]) -> int
```

**Parameters:**
- `messages` (list[dict]): List of messages with `role` and `content` fields

**Returns:**
- `int`: Total token count including overhead

**Example:**
```python
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"},
    {"role": "assistant", "content": "Hi there!"}
]

tokens = counter.count_tokens_messages(messages)
print(f"Total tokens: {tokens}")
```

---

#### estimate_context_size

Estimate total context window usage.

```python
def estimate_context_size(
    messages: list[dict[str, Any]],
    system_prompt: str = "",
    max_tokens: int = 1000
) -> dict[str, int]
```

**Parameters:**
- `messages`: Conversation history
- `system_prompt`: System prompt (default: "")
- `max_tokens`: Max completion tokens (default: 1000)

**Returns:**
- Dictionary with keys:
  - `prompt_tokens` (int): Tokens in prompts
  - `completion_tokens` (int): Reserved for completion
  - `total_tokens` (int): Total tokens

**Example:**
```python
estimate = counter.estimate_context_size(
    messages=[{"role": "user", "content": "Hello"}],
    system_prompt="Be helpful.",
    max_tokens=1000
)

print(f"Prompt tokens: {estimate['prompt_tokens']}")
print(f"Total tokens: {estimate['total_tokens']}")
```

---

#### should_compress

Decide if compression is needed.

```python
def should_compress(
    current_tokens: int,
    max_tokens: int,
    threshold: float = 0.8
) -> bool
```

**Parameters:**
- `current_tokens`: Current token count
- `max_tokens`: Maximum allowed tokens
- `threshold`: Trigger compression at this ratio (default: 0.8 = 80%)

**Returns:**
- `bool`: True if compression should be triggered

**Example:**
```python
# Check if compression needed
if counter.should_compress(current_tokens=9000, max_tokens=10000):
    print("Time to compress!")
```

---

#### get_model_limits

Get token limits for specific model.

```python
def get_model_limits(model: str) -> dict[str, int]
```

**Parameters:**
- `model` (str): Model name

**Returns:**
- Dictionary with keys:
  - `context_window` (int): Maximum context window size
  - `max_completion` (int): Maximum completion tokens

**Example:**
```python
limits = counter.get_model_limits("gpt-4o-mini")
print(f"Context window: {limits['context_window']:,}")  # 128,000
print(f"Max completion: {limits['max_completion']:,}")  # 16,384
```

**Supported Models:**

| Model | Context Window | Max Completion |
|-------|----------------|----------------|
| gpt-4o-mini | 128,000 | 16,384 |
| gpt-4o | 128,000 | 16,384 |
| gpt-4-turbo | 128,000 | 4,096 |
| gpt-3.5-turbo | 16,385 | 4,096 |
| claude-3-5-sonnet | 200,000 | 8,192 |
| claude-3-opus | 200,000 | 4,096 |
| gemini-1.5-pro | 2,000,000 | 8,192 |
| gemini-1.5-flash | 1,000,000 | 8,192 |
| *unknown* | 8,000 | 2,000 |

---

## ContextMonitor

Monitor context window usage and recommend compression.

### Constructor

```python
ContextMonitor(
    token_counter: TokenCounter,
    max_tokens: Optional[int] = None
)
```

**Parameters:**
- `token_counter`: TokenCounter instance
- `max_tokens`: Max context window (if None, auto-detect from model)

**Auto-detection:**
When `max_tokens=None`, the monitor automatically calculates the safe limit as:
```
max_tokens = model_context_window - 4000
```

This reserves 4000 tokens for completion.

**Example:**
```python
from kagura.core.compression import TokenCounter, ContextMonitor

counter = TokenCounter(model="gpt-4o-mini")

# Explicit limit
monitor = ContextMonitor(counter, max_tokens=10000)

# Auto-detect (128k - 4k = 124k for gpt-4o-mini)
monitor_auto = ContextMonitor(counter, max_tokens=None)
```

---

### Methods

#### check_usage

Check current context usage.

```python
def check_usage(
    messages: list[dict[str, Any]],
    system_prompt: str = ""
) -> ContextUsage
```

**Parameters:**
- `messages`: Message history
- `system_prompt`: System prompt (default: "")

**Returns:**
- `ContextUsage`: Usage statistics

**Example:**
```python
messages = [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi!"}
]

usage = monitor.check_usage(messages, system_prompt="Be helpful.")

print(f"Usage: {usage.usage_ratio:.1%}")  # e.g., 5.2%
print(f"Tokens: {usage.total_tokens} / {usage.max_tokens}")

if usage.should_compress:
    print("⚠️ Context is getting full. Compression recommended!")
```

---

## ContextUsage

Context usage statistics (dataclass).

### Attributes

- `prompt_tokens` (int): Tokens in prompts (messages + system prompt)
- `completion_tokens` (int): Reserved for completion
- `total_tokens` (int): Total tokens (prompt + completion)
- `max_tokens` (int): Maximum allowed tokens
- `usage_ratio` (float): Usage ratio (0.0 - 1.0)
- `should_compress` (bool): Whether compression is recommended

**Example:**
```python
>>> usage = monitor.check_usage(messages)
>>> usage
ContextUsage(
    prompt_tokens=500,
    completion_tokens=4000,
    total_tokens=4500,
    max_tokens=10000,
    usage_ratio=0.45,
    should_compress=False
)
```

---

## Exceptions

### CompressionError

Base exception for compression errors.

```python
class CompressionError(Exception)
```

### TokenCountError

Error during token counting.

```python
class TokenCountError(CompressionError)
```

**Example:**
```python
from kagura.core.compression import TokenCountError

try:
    tokens = counter.count_tokens(text)
except TokenCountError as e:
    print(f"Failed to count tokens: {e}")
```

### ModelNotSupportedError

Model is not supported.

```python
class ModelNotSupportedError(CompressionError)
```

---

## Installation

Install with compression support:

```bash
pip install kagura-ai[ai]

# Or install all features
pip install kagura-ai[all]
```

---

## See Also

- [Context Compression Guide](../guides/context-compression.md) - User guide with examples
- [RFC-024](../../ai_docs/rfcs/RFC_024_CONTEXT_COMPRESSION.md) - Full specification
- [Memory Management API](./memory.md) - Memory system (will integrate in Phase 4)

---

**Phase 1** provides token counting and monitoring. **Phases 2-4** will add trimming, summarization, and automatic compression.
