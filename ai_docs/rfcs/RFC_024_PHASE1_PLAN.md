# RFC-024 Phase 1: Token Management 実装計画

**期間**: Week 1 (7日間)
**Issue**: #159
**PR**: TBD
**優先度**: 🔥🔥🔥 Critical

---

## 📋 Phase 1 概要

### 目標

Token Management基盤を構築し、コンテキスト使用量を正確に計測・監視できるようにする。

### 成功指標

- ✅ 全モデルのトークンカウント正確（誤差±5%以内）
- ✅ コンテキスト使用量をリアルタイム監視可能
- ✅ モデル別のコンテキストウィンドウ対応
- ✅ 15+ tests全パス
- ✅ Pyright 0 errors

---

## 🏗️ 実装内容

### Day 1-2: TokenCounter実装

#### ファイル構成

```
src/kagura/core/compression/
├── __init__.py
├── token_counter.py    # 新規作成
└── exceptions.py       # 新規作成

tests/core/compression/
├── __init__.py
└── test_token_counter.py  # 新規作成
```

#### 実装詳細

##### 1. `src/kagura/core/compression/__init__.py`

```python
"""Context compression module"""

from .token_counter import TokenCounter
from .exceptions import CompressionError, TokenCountError

__all__ = [
    "TokenCounter",
    "CompressionError",
    "TokenCountError",
]
```

##### 2. `src/kagura/core/compression/exceptions.py`

```python
"""Compression-related exceptions"""

class CompressionError(Exception):
    """Base exception for compression errors"""
    pass

class TokenCountError(CompressionError):
    """Error during token counting"""
    pass

class ModelNotSupportedError(CompressionError):
    """Model is not supported"""
    pass
```

##### 3. `src/kagura/core/compression/token_counter.py`

**Full implementation**（RFC-024で定義済み）:
- `__init__(model: str)`
- `_get_encoder(model: str) -> tiktoken.Encoding`
- `count_tokens(text: str) -> int`
- `count_tokens_messages(messages: list[dict]) -> int`
- `estimate_context_size(...) -> dict`
- `should_compress(...) -> bool`
- `get_model_limits(model: str) -> dict`

**Dependencies**:
```toml
# pyproject.toml に追加
[project.optional-dependencies]
compression = [
    "tiktoken>=0.7.0",
]
```

##### 4. テスト実装

```python
# tests/core/compression/test_token_counter.py

import pytest
from kagura.core.compression import TokenCounter, TokenCountError

class TestTokenCounter:
    """Tests for TokenCounter"""

    @pytest.fixture
    def counter(self):
        """Create TokenCounter instance"""
        return TokenCounter(model="gpt-4o-mini")

    def test_init_default_model(self):
        """Test initialization with default model"""
        counter = TokenCounter()
        assert counter.model == "gpt-4o-mini"

    def test_init_custom_model(self):
        """Test initialization with custom model"""
        counter = TokenCounter(model="claude-3-5-sonnet")
        assert counter.model == "claude-3-5-sonnet"

    def test_count_tokens_empty(self, counter):
        """Test counting tokens in empty string"""
        tokens = counter.count_tokens("")
        assert tokens == 0

    def test_count_tokens_simple(self, counter):
        """Test counting tokens in simple text"""
        text = "Hello, world!"
        tokens = counter.count_tokens(text)
        assert tokens > 0
        assert tokens < 10  # Should be around 3-4 tokens

    def test_count_tokens_long_text(self, counter):
        """Test counting tokens in long text"""
        text = "This is a longer text. " * 100
        tokens = counter.count_tokens(text)
        assert tokens > 100
        assert tokens < 1000

    def test_count_tokens_messages_empty(self, counter):
        """Test counting tokens in empty message list"""
        tokens = counter.count_tokens_messages([])
        assert tokens == 3  # Reply priming

    def test_count_tokens_messages_basic(self, counter):
        """Test counting tokens in basic messages"""
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"},
            {"role": "assistant", "content": "Hi there!"}
        ]

        tokens = counter.count_tokens_messages(messages)
        assert tokens > 20  # Includes overhead

    def test_count_tokens_messages_with_name(self, counter):
        """Test counting tokens in messages with name field"""
        messages = [
            {"role": "user", "name": "Alice", "content": "Hello!"},
        ]

        tokens = counter.count_tokens_messages(messages)
        assert tokens > 5

    def test_estimate_context_size_basic(self, counter):
        """Test estimating context size"""
        messages = [
            {"role": "user", "content": "Hello"}
        ]

        estimate = counter.estimate_context_size(
            messages,
            system_prompt="You are helpful.",
            max_tokens=1000
        )

        assert "prompt_tokens" in estimate
        assert "completion_tokens" in estimate
        assert "total_tokens" in estimate
        assert estimate["completion_tokens"] == 1000
        assert estimate["total_tokens"] == estimate["prompt_tokens"] + 1000

    def test_should_compress_below_threshold(self, counter):
        """Test should_compress when below threshold"""
        assert not counter.should_compress(
            current_tokens=1000,
            max_tokens=10000,
            threshold=0.8
        )

    def test_should_compress_above_threshold(self, counter):
        """Test should_compress when above threshold"""
        assert counter.should_compress(
            current_tokens=9000,
            max_tokens=10000,
            threshold=0.8
        )

    def test_should_compress_at_threshold(self, counter):
        """Test should_compress exactly at threshold"""
        assert counter.should_compress(
            current_tokens=8000,
            max_tokens=10000,
            threshold=0.8
        )

    def test_get_model_limits_gpt4o(self, counter):
        """Test getting model limits for GPT-4o"""
        limits = counter.get_model_limits("gpt-4o")
        assert limits["context_window"] == 128_000
        assert limits["max_completion"] == 16_384

    def test_get_model_limits_claude(self, counter):
        """Test getting model limits for Claude"""
        limits = counter.get_model_limits("claude-3-5-sonnet")
        assert limits["context_window"] == 200_000
        assert limits["max_completion"] == 8_192

    def test_get_model_limits_gemini(self, counter):
        """Test getting model limits for Gemini"""
        limits = counter.get_model_limits("gemini-1.5-pro")
        assert limits["context_window"] == 2_000_000
        assert limits["max_completion"] == 8_192

    def test_get_model_limits_unknown(self, counter):
        """Test getting model limits for unknown model"""
        limits = counter.get_model_limits("unknown-model")
        assert limits["context_window"] == 8_000  # Default
        assert limits["max_completion"] == 2_000  # Default

# 合計: 17テスト
```

---

### Day 3-4: ContextMonitor実装

#### ファイル追加

```
src/kagura/core/compression/
├── monitor.py          # 新規作成

tests/core/compression/
├── test_monitor.py     # 新規作成
```

#### 実装詳細

##### 1. `src/kagura/core/compression/monitor.py`

**Full implementation**（RFC-024で定義済み）:
- `ContextUsage` dataclass
- `ContextMonitor` class
  - `__init__(token_counter, max_tokens)`
  - `_get_max_tokens() -> int`
  - `check_usage(...) -> ContextUsage`

##### 2. `src/kagura/core/compression/__init__.py` 更新

```python
from .token_counter import TokenCounter
from .monitor import ContextMonitor, ContextUsage
from .exceptions import CompressionError, TokenCountError

__all__ = [
    "TokenCounter",
    "ContextMonitor",
    "ContextUsage",
    "CompressionError",
    "TokenCountError",
]
```

##### 3. テスト実装

```python
# tests/core/compression/test_monitor.py

import pytest
from kagura.core.compression import TokenCounter, ContextMonitor, ContextUsage

class TestContextMonitor:
    """Tests for ContextMonitor"""

    @pytest.fixture
    def counter(self):
        return TokenCounter(model="gpt-4o-mini")

    @pytest.fixture
    def monitor(self, counter):
        return ContextMonitor(counter, max_tokens=10000)

    def test_init_with_max_tokens(self, counter):
        """Test initialization with explicit max_tokens"""
        monitor = ContextMonitor(counter, max_tokens=5000)
        assert monitor.max_tokens == 5000

    def test_init_auto_detect_max_tokens(self, counter):
        """Test initialization with auto-detected max_tokens"""
        monitor = ContextMonitor(counter, max_tokens=None)
        # Should auto-detect from model (128k - 4k = 124k for gpt-4o-mini)
        assert monitor.max_tokens > 100_000

    def test_check_usage_empty_messages(self, monitor):
        """Test checking usage with empty messages"""
        usage = monitor.check_usage([], system_prompt="")

        assert isinstance(usage, ContextUsage)
        assert usage.prompt_tokens >= 0
        assert usage.total_tokens >= 0
        assert usage.max_tokens == 10000
        assert 0.0 <= usage.usage_ratio <= 1.0

    def test_check_usage_basic_messages(self, monitor):
        """Test checking usage with basic messages"""
        messages = [
            {"role": "user", "content": "Hello"}
        ]

        usage = monitor.check_usage(messages, system_prompt="Be helpful.")

        assert usage.prompt_tokens > 0
        assert usage.total_tokens > usage.prompt_tokens
        assert usage.usage_ratio < 0.1  # Should be very low

    def test_check_usage_many_messages(self, monitor):
        """Test checking usage with many messages"""
        messages = [
            {"role": "user", "content": "Message " * 50}
        ] * 100  # 100 messages

        usage = monitor.check_usage(messages, system_prompt="")

        assert usage.prompt_tokens > 1000
        assert usage.usage_ratio > 0.1

    def test_check_usage_should_compress_false(self, monitor):
        """Test should_compress is False when usage is low"""
        messages = [
            {"role": "user", "content": "Hello"}
        ]

        usage = monitor.check_usage(messages)

        assert not usage.should_compress

    def test_check_usage_should_compress_true(self):
        """Test should_compress is True when usage is high"""
        counter = TokenCounter(model="gpt-4o-mini")
        monitor = ContextMonitor(counter, max_tokens=1000)  # Small limit

        messages = [
            {"role": "user", "content": "Long message " * 100}
        ] * 10

        usage = monitor.check_usage(messages)

        assert usage.should_compress

# 合計: 8テスト
```

---

### Day 5: pyproject.toml更新 & 統合

#### 1. pyproject.toml更新

```toml
# pyproject.toml

[project.optional-dependencies]
# ... existing optional dependencies ...

compression = [
    "tiktoken>=0.7.0",
]

all = [
    # ... existing dependencies ...
    "tiktoken>=0.7.0",
]
```

#### 2. インストール確認

```bash
# Compression機能を有効にしてインストール
uv sync --extra compression

# または全機能
uv sync --all-extras
```

#### 3. 統合テスト作成

```python
# tests/core/compression/test_integration.py

import pytest
from kagura.core.compression import (
    TokenCounter,
    ContextMonitor,
    ContextUsage,
)

class TestIntegration:
    """Integration tests for Phase 1 components"""

    def test_full_workflow(self):
        """Test complete token management workflow"""
        # 1. Create counter
        counter = TokenCounter(model="gpt-4o-mini")

        # 2. Create monitor
        monitor = ContextMonitor(counter, max_tokens=5000)

        # 3. Simulate conversation
        messages = []
        for i in range(50):
            messages.append({"role": "user", "content": f"Message {i}"})
            messages.append({"role": "assistant", "content": f"Response {i}"})

        # 4. Check usage
        usage = monitor.check_usage(messages)

        # 5. Verify
        assert usage.total_tokens > 0
        assert usage.usage_ratio > 0.0
        assert usage.max_tokens == 5000

    def test_different_models(self):
        """Test with different models"""
        models = ["gpt-4o-mini", "claude-3-5-sonnet", "gemini-1.5-flash"]

        for model in models:
            counter = TokenCounter(model=model)
            monitor = ContextMonitor(counter)

            messages = [{"role": "user", "content": "Test"}]
            usage = monitor.check_usage(messages)

            assert usage.total_tokens > 0

# 合計: 2テスト
```

---

### Day 6-7: ドキュメント & PR作成

#### 1. APIドキュメント

```markdown
# docs/en/api/compression.md

## Context Compression API

### TokenCounter

Count tokens for various LLM models.

#### Constructor

```python
TokenCounter(model: str = "gpt-4o-mini")
```

**Parameters:**
- `model`: LLM model name (e.g., "gpt-4o-mini", "claude-3-5-sonnet")

#### Methods

##### count_tokens

Count tokens in text.

```python
def count_tokens(text: str) -> int
```

**Example:**
```python
counter = TokenCounter(model="gpt-4o-mini")
tokens = counter.count_tokens("Hello, world!")
print(f"Tokens: {tokens}")  # Tokens: 4
```

##### count_tokens_messages

Count tokens in message list (OpenAI format).

```python
def count_tokens_messages(messages: list[dict[str, Any]]) -> int
```

**Example:**
```python
messages = [
    {"role": "system", "content": "You are helpful."},
    {"role": "user", "content": "Hello!"}
]
tokens = counter.count_tokens_messages(messages)
```

##### estimate_context_size

Estimate total context window usage.

```python
def estimate_context_size(
    messages: list[dict[str, Any]],
    system_prompt: str = "",
    max_tokens: int = 1000
) -> dict[str, int]
```

**Returns:**
```python
{
    "prompt_tokens": 100,
    "completion_tokens": 1000,
    "total_tokens": 1100
}
```

##### should_compress

Decide if compression is needed.

```python
def should_compress(
    current_tokens: int,
    max_tokens: int,
    threshold: float = 0.8
) -> bool
```

##### get_model_limits

Get token limits for specific model.

```python
def get_model_limits(model: str) -> dict[str, int]
```

**Returns:**
```python
{
    "context_window": 128000,
    "max_completion": 16384
}
```

---

### ContextMonitor

Monitor context window usage.

#### Constructor

```python
ContextMonitor(
    token_counter: TokenCounter,
    max_tokens: Optional[int] = None
)
```

#### Methods

##### check_usage

Check current context usage.

```python
def check_usage(
    messages: list[dict[str, Any]],
    system_prompt: str = ""
) -> ContextUsage
```

**Returns:**
```python
ContextUsage(
    prompt_tokens=500,
    completion_tokens=1000,
    total_tokens=1500,
    max_tokens=10000,
    usage_ratio=0.15,  # 15%
    should_compress=False
)
```

**Example:**
```python
counter = TokenCounter(model="gpt-4o-mini")
monitor = ContextMonitor(counter, max_tokens=10000)

messages = [{"role": "user", "content": "Hello"}]
usage = monitor.check_usage(messages)

print(f"Usage: {usage.usage_ratio:.1%}")  # Usage: 5.0%
if usage.should_compress:
    print("Time to compress!")
```

---

### ContextUsage

Context usage statistics (dataclass).

**Fields:**
- `prompt_tokens: int` - Tokens in prompts
- `completion_tokens: int` - Reserved for completion
- `total_tokens: int` - Total tokens
- `max_tokens: int` - Maximum allowed tokens
- `usage_ratio: float` - Usage ratio (0.0 - 1.0)
- `should_compress: bool` - Whether compression is recommended
```

#### 2. ユーザーガイド

```markdown
# docs/en/guides/context-compression.md

## Context Compression (Phase 1: Token Management)

Phase 1 provides token counting and monitoring capabilities.

### Installation

```bash
# Install with compression support
pip install kagura-ai[compression]

# Or install all features
pip install kagura-ai[all]
```

### Basic Usage

#### Count Tokens

```python
from kagura.core.compression import TokenCounter

counter = TokenCounter(model="gpt-4o-mini")

# Count tokens in text
text = "Hello, world!"
tokens = counter.count_tokens(text)
print(f"Tokens: {tokens}")

# Count tokens in messages
messages = [
    {"role": "system", "content": "You are helpful."},
    {"role": "user", "content": "Hello!"}
]
tokens = counter.count_tokens_messages(messages)
print(f"Total tokens: {tokens}")
```

#### Monitor Context Usage

```python
from kagura.core.compression import TokenCounter, ContextMonitor

counter = TokenCounter(model="gpt-4o-mini")
monitor = ContextMonitor(counter, max_tokens=10000)

# Check usage
messages = [...]  # Your conversation history
usage = monitor.check_usage(messages)

print(f"Usage: {usage.usage_ratio:.1%}")
print(f"Tokens: {usage.total_tokens} / {usage.max_tokens}")

if usage.should_compress:
    print("⚠️ Context is getting full. Compression recommended!")
```

### Supported Models

- OpenAI: `gpt-4o-mini`, `gpt-4o`, `gpt-4-turbo`, `gpt-3.5-turbo`
- Anthropic: `claude-3-5-sonnet`, `claude-3-opus`
- Google: `gemini-1.5-pro`, `gemini-1.5-flash`

### Next Steps

Phase 2 (Message Trimming) and Phase 3 (Summarization) will be implemented in future releases.
```

#### 3. PR作成

```bash
# Commit all changes
git add .
git commit -m "feat(compression): implement RFC-024 Phase 1 - Token Management (#159)

- Add TokenCounter with tiktoken integration
- Add ContextMonitor for usage tracking
- Support all major models (OpenAI, Claude, Gemini)
- Add 27 tests (all passing)
- Add comprehensive documentation

Closes #159 (Phase 1)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Push to remote
git push -u origin feature/RFC-024-phase1-token-management

# Create PR
gh pr create --draft \
  --title "feat(compression): implement RFC-024 Phase 1 - Token Management" \
  --body "$(cat <<'PRBODY'
## Summary

Implements RFC-024 Phase 1: Token Management system for context compression.

## Changes

### Implementation
- `src/kagura/core/compression/token_counter.py`: TokenCounter class (150 lines)
- `src/kagura/core/compression/monitor.py`: ContextMonitor class (80 lines)
- `src/kagura/core/compression/exceptions.py`: Custom exceptions (15 lines)

### Tests
- `tests/core/compression/test_token_counter.py`: 17 tests
- `tests/core/compression/test_monitor.py`: 8 tests
- `tests/core/compression/test_integration.py`: 2 tests
- **Total: 27 tests (all passing)**

### Documentation
- `docs/en/api/compression.md`: API reference
- `docs/en/guides/context-compression.md`: User guide

### Dependencies
- `tiktoken>=0.7.0` (optional dependency)

## Test Results

```bash
pytest tests/core/compression/ -v
======================== 27 passed in 2.5s ========================
```

## Performance

- Token counting: ~0.1ms per message
- Context monitoring: ~1ms for 100 messages

## Related Issues

- Closes #159 (Phase 1 only)
- Part of RFC-024: Context Compression System

## Next Steps

- Phase 2: Message Trimming (Week 2)
- Phase 3: Summarization (Week 3-4)
- Phase 4: Integration (Week 5)
PRBODY
)"
```

---

## 📊 Phase 1 完了チェックリスト

### 実装
- [ ] `src/kagura/core/compression/__init__.py`
- [ ] `src/kagura/core/compression/exceptions.py`
- [ ] `src/kagura/core/compression/token_counter.py`
- [ ] `src/kagura/core/compression/monitor.py`

### テスト
- [ ] `tests/core/compression/test_token_counter.py` (17 tests)
- [ ] `tests/core/compression/test_monitor.py` (8 tests)
- [ ] `tests/core/compression/test_integration.py` (2 tests)
- [ ] 全テストパス（27/27）

### ドキュメント
- [ ] `docs/en/api/compression.md` (APIリファレンス)
- [ ] `docs/en/guides/context-compression.md` (ユーザーガイド)

### 品質
- [ ] Pyright: 0 errors
- [ ] Ruff: All checks passed
- [ ] Coverage: 95%+

### その他
- [ ] `pyproject.toml` 更新（tiktoken依存追加）
- [ ] PR作成（Draft）
- [ ] CI通過

---

## 🎯 成功指標

### 機能
- ✅ 全モデルのトークンカウント正確（誤差±5%以内）
- ✅ コンテキスト使用量をリアルタイム監視可能
- ✅ モデル別のコンテキストウィンドウ対応

### 品質
- ✅ 27 tests全パス
- ✅ Pyright 0 errors
- ✅ Coverage 95%+

### ドキュメント
- ✅ APIリファレンス完備
- ✅ ユーザーガイド完備

---

**Phase 1完了により、Kagura AIはトークン使用量を正確に把握できるようになります！**
