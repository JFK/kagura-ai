# Context Compression Guide

**RFC-024 Phase 1**: Token Management

**Since**: v2.5.0

---

## Overview

Context compression enables efficient long-form conversations by managing token usage and preventing context window overflow.

**Phase 1** (current) provides:
- ✅ Accurate token counting for all major LLM models
- ✅ Real-time context usage monitoring
- ✅ Compression recommendations

**Future phases** will add:
- 📋 Phase 2: Message trimming (Week 2)
- 📋 Phase 3: LLM-based summarization (Week 3-4)
- 📋 Phase 4: Automatic compression (Week 5)

---

## Installation

```bash
# Install with compression support
pip install kagura-ai[compression]

# Or install all features
pip install kagura-ai[all]
```

**Dependencies:**
- `tiktoken>=0.7.0` - OpenAI's token counting library

---

## Quick Start

### Basic Token Counting

```python
from kagura.core.compression import TokenCounter

# Create counter
counter = TokenCounter(model="gpt-4o-mini")

# Count tokens in text
text = "Hello, world!"
tokens = counter.count_tokens(text)
print(f"Tokens: {tokens}")  # Tokens: 4

# Count tokens in messages
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"},
    {"role": "assistant", "content": "Hi there!"}
]

total_tokens = counter.count_tokens_messages(messages)
print(f"Total tokens: {total_tokens}")  # Includes message overhead
```

---

### Context Usage Monitoring

```python
from kagura.core.compression import TokenCounter, ContextMonitor

# Create counter and monitor
counter = TokenCounter(model="gpt-4o-mini")
monitor = ContextMonitor(counter, max_tokens=10000)

# Check usage
messages = [...]  # Your conversation history
usage = monitor.check_usage(messages, system_prompt="Be helpful.")

# Display usage
print(f"Usage: {usage.usage_ratio:.1%}")  # e.g., 45.3%
print(f"Tokens: {usage.total_tokens:,} / {usage.max_tokens:,}")

if usage.should_compress:
    print("⚠️ Context is getting full!")
    print("Consider compressing (Phase 2+)")
```

---

## Advanced Usage

### Auto-Detect Model Limits

```python
# Automatically detect max tokens from model
counter = TokenCounter(model="claude-3-5-sonnet")
monitor = ContextMonitor(counter, max_tokens=None)

print(f"Max tokens: {monitor.max_tokens:,}")
# For Claude 3.5 Sonnet: 196,000 (200k - 4k reserved)
```

### Custom Compression Threshold

```python
# Trigger compression at 70% instead of default 80%
should_compress = counter.should_compress(
    current_tokens=usage.total_tokens,
    max_tokens=usage.max_tokens,
    threshold=0.7  # 70%
)

if should_compress:
    print("Time to compress!")
```

### Estimate Context Size

```python
# Estimate how much context a conversation will use
estimate = counter.estimate_context_size(
    messages=messages,
    system_prompt="You are helpful.",
    max_tokens=1000  # Reserve for completion
)

print(f"Prompt: {estimate['prompt_tokens']:,} tokens")
print(f"Completion: {estimate['completion_tokens']:,} tokens")
print(f"Total: {estimate['total_tokens']:,} tokens")
```

---

## Model Support

### Supported Models

All major LLM providers are supported:

```python
# OpenAI
counter_openai = TokenCounter(model="gpt-4o-mini")

# Anthropic Claude
counter_claude = TokenCounter(model="claude-3-5-sonnet")

# Google Gemini
counter_gemini = TokenCounter(model="gemini-1.5-pro")
```

### Model Limits

Get token limits for any model:

```python
limits = counter.get_model_limits("gpt-4o-mini")
print(f"Context window: {limits['context_window']:,}")  # 128,000
print(f"Max completion: {limits['max_completion']:,}")  # 16,384
```

**Available Limits:**

| Model | Context Window | Max Completion |
|-------|----------------|----------------|
| gpt-4o-mini | 128,000 | 16,384 |
| gpt-4o | 128,000 | 16,384 |
| claude-3-5-sonnet | 200,000 | 8,192 |
| gemini-1.5-pro | 2,000,000 | 8,192 |

For unknown models, defaults to 8,000 / 2,000.

---

## Best Practices

### 1. Monitor Usage Regularly

```python
# Check usage after each turn
usage = monitor.check_usage(messages)

if usage.usage_ratio > 0.7:
    print(f"⚠️ Warning: {usage.usage_ratio:.0%} full")

if usage.should_compress:
    print("🚨 Compression recommended")
    # In Phase 2+: await compress(messages)
```

### 2. Reserve Space for Completion

When creating a monitor, ensure you reserve enough tokens for model responses:

```python
# Good: Auto-detect reserves 4000 tokens
monitor = ContextMonitor(counter, max_tokens=None)

# Custom: Reserve explicit amount
model_limit = 128_000
reserved_for_completion = 8_000
monitor = ContextMonitor(counter, max_tokens=model_limit - reserved_for_completion)
```

### 3. Choose Appropriate Model

For long conversations, prefer models with larger context windows:

```python
# Small context (16k) - frequent compression needed
counter_small = TokenCounter(model="gpt-3.5-turbo")

# Large context (128k) - less compression needed
counter_large = TokenCounter(model="gpt-4o-mini")

# Huge context (2M) - minimal compression needed
counter_huge = TokenCounter(model="gemini-1.5-pro")
```

---

## Examples

### Example 1: Track Conversation Growth

```python
from kagura.core.compression import TokenCounter, ContextMonitor

counter = TokenCounter(model="gpt-4o-mini")
monitor = ContextMonitor(counter, max_tokens=50000)

messages = [{"role": "system", "content": "You are helpful."}]

for turn in range(100):
    # Add user message
    messages.append({"role": "user", "content": f"Question {turn}"})

    # Check usage before responding
    usage = monitor.check_usage(messages)
    print(f"Turn {turn}: {usage.usage_ratio:.1%} full")

    if usage.should_compress:
        print(f"⚠️ Compression needed at turn {turn}")
        break

    # Add assistant response
    messages.append({"role": "assistant", "content": f"Answer {turn}"})
```

### Example 2: Multi-Model Comparison

```python
models = ["gpt-4o-mini", "claude-3-5-sonnet", "gemini-1.5-pro"]

text = "The quick brown fox jumps over the lazy dog."

for model in models:
    counter = TokenCounter(model=model)
    tokens = counter.count_tokens(text)
    limits = counter.get_model_limits(model)

    print(f"{model}:")
    print(f"  Tokens: {tokens}")
    print(f"  Context window: {limits['context_window']:,}")
```

Output:
```
gpt-4o-mini:
  Tokens: 10
  Context window: 128,000

claude-3-5-sonnet:
  Tokens: 10
  Context window: 200,000

gemini-1.5-pro:
  Tokens: 10
  Context window: 2,000,000
```

---

## Troubleshooting

### Q: Token count seems inaccurate

**A:** Different models use different tokenizers. TokenCounter uses `tiktoken` which is optimized for OpenAI models. For Claude and Gemini, it uses `cl100k_base` as an approximation (±10% accuracy).

### Q: What if I exceed context window?

**A:** Phase 1 only monitors usage. Phases 2-4 will provide automatic compression:
- **Phase 2**: Message trimming
- **Phase 3**: LLM-based summarization
- **Phase 4**: Automatic compression

### Q: How accurate is token counting?

**A:** Very accurate for OpenAI models (±1%). For other models: ±5-10%.

### Q: Can I use this with streaming?

**A:** Yes! Count tokens before and after streaming to track usage.

---

## Next Steps

**Phase 1 (current)** provides monitoring only.

**Coming soon:**
- **Phase 2** (Week 2): Message trimming with 4 strategies
- **Phase 3** (Week 3-4): Context summarization
- **Phase 4** (Week 5): Automatic compression integrated with `@agent` decorator

Stay tuned for updates!

---

## See Also

- [Compression API Reference](../api/compression.md) - Detailed API documentation
- [RFC-024](../../ai_docs/rfcs/RFC_024_CONTEXT_COMPRESSION.md) - Full specification
- [Memory Management](./memory-management.md) - Memory system (integrates in Phase 4)

---

**Phase 1 implementation provides the foundation for efficient long-form conversations!**
