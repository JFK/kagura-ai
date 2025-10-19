# RFC-024 Phase 4 Implementation Plan: Integration & Policy

**Phase**: 4 of 4 (Final)
**Duration**: Week 5 (7 days)
**Priority**: 🔥🔥🔥 Critical
**Depends on**: Phase 1 ✅, Phase 2 ✅, Phase 3 (pending)

---

## 📋 Overview

Phase 4では、すべての圧縮機能を統合し、ユーザーが簡単に使用できる統一インターフェースを提供します。`ContextManager`を実装し、`MemoryManager`と`@agent`デコレータに統合することで、自動的なコンテキスト圧縮を実現します。

### Goals

1. **CompressionPolicy**: 圧縮動作をカスタマイズ可能な設定クラス
2. **ContextManager**: すべての圧縮戦略を統合する統一インターフェース
3. **MemoryManager Integration**: 既存のMemoryManagerに圧縮機能を統合
4. **@agent Decorator Integration**: デコレータで自動圧縮を有効化

---

## 🎯 Success Criteria

### Functional
- ✅ CompressionPolicy実装（5つの戦略対応）
- ✅ ContextManager統合インターフェース
- ✅ MemoryManager統合（既存APIを壊さない）
- ✅ @agentデコレータ統合（デフォルトで有効）
- ✅ 自動圧縮トリガー（80%閾値）

### Quality
- ✅ 既存テスト（900+ tests）すべてパス
- ✅ 30+ 新規テスト全パス
- ✅ Pyright: 0 errors（strict mode）
- ✅ Ruff: All checks passed
- ✅ Coverage: 95%+

### Documentation
- ✅ ユーザーガイド完成
- ✅ APIリファレンス完成
- ✅ Migration guide完成
- ✅ Usage examples充実

### Performance
- ✅ 圧縮オーバーヘッド: <100ms（通常ケース）
- ✅ メモリ使用量: +10%以内

---

## 📦 Implementation

### File Structure

```
src/kagura/core/compression/
├── __init__.py              # Export all classes
├── policy.py                # NEW: CompressionPolicy
├── manager.py               # NEW: ContextManager
├── summarizer.py            # Existing (Phase 3)
├── token_counter.py         # Existing (Phase 1)
├── monitor.py              # Existing (Phase 1)
└── trimmer.py              # Existing (Phase 2)

src/kagura/core/memory/
└── manager.py               # MODIFIED: Add compression support

src/kagura/core/
└── decorators.py            # MODIFIED: Add compression params

tests/core/compression/
├── test_policy.py           # NEW: 5 tests
├── test_manager.py          # NEW: 15 tests
└── test_integration.py      # NEW: 10 tests (MemoryManager, @agent)
```

---

## 📝 Day-by-Day Plan

### Day 1: CompressionPolicy

**Goal**: 圧縮設定クラスの実装

**Tasks**:
1. `CompressionPolicy` dataclass作成
2. 5つの戦略（auto/trim/summarize/smart/off）定義
3. デフォルト値設定
4. バリデーション実装
5. テスト（5 tests）

**Code**:
```python
# src/kagura/core/compression/policy.py

from dataclasses import dataclass
from typing import Literal

CompressionStrategy = Literal["auto", "trim", "summarize", "smart", "off"]

@dataclass
class CompressionPolicy:
    """Context compression configuration

    Example:
        >>> policy = CompressionPolicy(
        ...     strategy="smart",
        ...     max_tokens=4000,
        ...     trigger_threshold=0.8
        ... )
    """

    strategy: CompressionStrategy = "smart"
    """Compression strategy:
    - auto: Automatically choose best strategy
    - trim: Simple message trimming (fast, no LLM)
    - summarize: Summarize old messages (LLM-based)
    - smart: Preserve events + summarize routine (best quality)
    - off: No compression
    """

    max_tokens: int = 4000
    """Maximum context tokens (excluding completion tokens)"""

    trigger_threshold: float = 0.8
    """Trigger compression at this ratio (0.0 - 1.0)
    Example: 0.8 = compress when reaching 80% of max_tokens
    """

    preserve_recent: int = 5
    """Always preserve this many recent messages"""

    preserve_system: bool = True
    """Always preserve system message"""

    target_ratio: float = 0.5
    """After compression, aim for this ratio (0.0 - 1.0)
    Example: 0.5 = reduce to 50% of max_tokens
    """

    enable_summarization: bool = True
    """Allow LLM-based summarization (required for 'summarize' and 'smart')"""

    summarization_model: str = "gpt-4o-mini"
    """Model for summarization (should be fast and cheap)"""

    def __post_init__(self):
        """Validate configuration"""
        if not 0.0 <= self.trigger_threshold <= 1.0:
            raise ValueError("trigger_threshold must be between 0.0 and 1.0")

        if not 0.0 <= self.target_ratio <= 1.0:
            raise ValueError("target_ratio must be between 0.0 and 1.0")

        if self.max_tokens <= 0:
            raise ValueError("max_tokens must be positive")

        if self.preserve_recent < 0:
            raise ValueError("preserve_recent must be non-negative")

        # Check if summarization is required but disabled
        if self.strategy in ["summarize", "smart"] and not self.enable_summarization:
            raise ValueError(
                f"strategy '{self.strategy}' requires enable_summarization=True"
            )
```

**Tests**:
```python
# tests/core/compression/test_policy.py

import pytest
from kagura.core.compression import CompressionPolicy

def test_policy_defaults():
    """Test default policy values"""
    policy = CompressionPolicy()

    assert policy.strategy == "smart"
    assert policy.max_tokens == 4000
    assert policy.trigger_threshold == 0.8
    assert policy.preserve_recent == 5
    assert policy.preserve_system is True
    assert policy.target_ratio == 0.5

def test_policy_validation_trigger_threshold():
    """Test trigger_threshold validation"""
    with pytest.raises(ValueError, match="trigger_threshold"):
        CompressionPolicy(trigger_threshold=1.5)

    with pytest.raises(ValueError, match="trigger_threshold"):
        CompressionPolicy(trigger_threshold=-0.1)

def test_policy_summarization_requirement():
    """Test summarization strategy requires enable_summarization"""
    with pytest.raises(ValueError, match="requires enable_summarization"):
        CompressionPolicy(
            strategy="smart",
            enable_summarization=False
        )
```

---

### Day 2-3: ContextManager

**Goal**: 統合インターフェースの実装

**Tasks**:
1. `ContextManager`クラス作成
2. `compress()`メソッド実装（戦略ルーティング）
3. 各戦略の内部メソッド実装
4. `get_usage()`実装
5. テスト（10 tests）

**Code**:
```python
# src/kagura/core/compression/manager.py

from typing import Any, Optional
from kagura.core.llm import LLMConfig

from .policy import CompressionPolicy
from .token_counter import TokenCounter
from .monitor import ContextMonitor, ContextUsage
from .trimmer import MessageTrimmer
from .summarizer import ContextSummarizer

class ContextManager:
    """Unified context compression manager

    Integrates all compression strategies (Write, Select, Compress, Isolate)

    Example:
        >>> manager = ContextManager(
        ...     policy=CompressionPolicy(strategy="smart"),
        ...     model="gpt-4o-mini"
        ... )
        >>> compressed = await manager.compress(messages)
    """

    def __init__(
        self,
        policy: Optional[CompressionPolicy] = None,
        model: str = "gpt-4o-mini"
    ):
        """Initialize context manager

        Args:
            policy: Compression policy (default: CompressionPolicy())
            model: LLM model name
        """
        self.policy = policy or CompressionPolicy()
        self.counter = TokenCounter(model=model)
        self.monitor = ContextMonitor(self.counter, max_tokens=self.policy.max_tokens)
        self.trimmer = MessageTrimmer(self.counter)

        # Initialize summarizer if enabled
        if self.policy.enable_summarization:
            self.summarizer = ContextSummarizer(
                self.counter,
                llm_config=LLMConfig(
                    model=self.policy.summarization_model,
                    temperature=0.3
                )
            )
        else:
            self.summarizer = None

    async def compress(
        self,
        messages: list[dict[str, Any]],
        system_prompt: str = ""
    ) -> list[dict[str, Any]]:
        """Compress messages if needed

        Args:
            messages: Message history
            system_prompt: System prompt (if any)

        Returns:
            Compressed messages (or original if no compression needed)
        """
        # Check if compression needed
        usage = self.monitor.check_usage(messages, system_prompt)

        if not usage.should_compress:
            # No compression needed
            return messages

        if self.policy.strategy == "off":
            # Compression disabled
            return messages

        # Calculate target tokens
        target_tokens = int(self.policy.max_tokens * self.policy.target_ratio)

        # Apply compression strategy
        if self.policy.strategy == "trim":
            return self._compress_trim(messages, target_tokens)
        elif self.policy.strategy == "summarize":
            return await self._compress_summarize(messages, target_tokens)
        elif self.policy.strategy == "smart":
            return await self._compress_smart(messages, target_tokens)
        elif self.policy.strategy == "auto":
            return await self._compress_auto(messages, target_tokens)
        else:
            # Default to trim
            return self._compress_trim(messages, target_tokens)

    def _compress_trim(
        self,
        messages: list[dict[str, Any]],
        target_tokens: int
    ) -> list[dict[str, Any]]:
        """Trim-based compression (fast, no LLM)"""
        return self.trimmer.trim(
            messages,
            target_tokens,
            strategy="smart",
            preserve_system=self.policy.preserve_system
        )

    async def _compress_summarize(
        self,
        messages: list[dict[str, Any]],
        target_tokens: int
    ) -> list[dict[str, Any]]:
        """Summarization-based compression"""
        if not self.summarizer:
            # Fallback to trim
            return self._compress_trim(messages, target_tokens)

        # Preserve recent messages
        recent = messages[-self.policy.preserve_recent:] if messages else []
        to_summarize = messages[:-self.policy.preserve_recent] if len(messages) > self.policy.preserve_recent else []

        if not to_summarize:
            return messages

        # Calculate token budget
        recent_tokens = self.counter.count_tokens_messages(recent)
        summary_budget = target_tokens - recent_tokens

        if summary_budget < 100:
            # Not enough space, just trim
            return self._compress_trim(messages, target_tokens)

        # Summarize old messages
        summary = await self.summarizer.summarize_recursive(
            to_summarize,
            summary_budget
        )

        # Reconstruct
        summary_msg = {
            "role": "system",
            "content": f"[Previous conversation summary] {summary}"
        }

        return [summary_msg] + recent

    async def _compress_smart(
        self,
        messages: list[dict[str, Any]],
        target_tokens: int
    ) -> list[dict[str, Any]]:
        """Smart compression: preserve events + summarize"""
        if not self.summarizer:
            return self._compress_trim(messages, target_tokens)

        return await self.summarizer.compress_preserve_events(
            messages,
            target_tokens
        )

    async def _compress_auto(
        self,
        messages: list[dict[str, Any]],
        target_tokens: int
    ) -> list[dict[str, Any]]:
        """Automatically choose best strategy"""
        # Heuristic: if many messages, use smart; if few, use trim
        if len(messages) > 20:
            return await self._compress_smart(messages, target_tokens)
        else:
            return self._compress_trim(messages, target_tokens)

    def get_usage(
        self,
        messages: list[dict[str, Any]],
        system_prompt: str = ""
    ) -> ContextUsage:
        """Get current context usage

        Args:
            messages: Message history
            system_prompt: System prompt

        Returns:
            ContextUsage statistics
        """
        return self.monitor.check_usage(messages, system_prompt)
```

**Tests**:
```python
# tests/core/compression/test_manager.py

import pytest
from unittest.mock import AsyncMock, patch
from kagura.core.compression import ContextManager, CompressionPolicy

@pytest.mark.asyncio
async def test_compress_no_compression_needed():
    """Test when no compression is needed"""
    policy = CompressionPolicy(max_tokens=10000)
    manager = ContextManager(policy=policy)

    messages = [{"role": "user", "content": "Short message"}]

    compressed = await manager.compress(messages)

    # Should return original
    assert compressed == messages

@pytest.mark.asyncio
async def test_compress_disabled():
    """Test compression disabled"""
    policy = CompressionPolicy(strategy="off")
    manager = ContextManager(policy=policy)

    messages = [{"role": "user", "content": "Test"}] * 100

    compressed = await manager.compress(messages)

    # Should not compress
    assert compressed == messages

@pytest.mark.asyncio
async def test_compress_trim_strategy():
    """Test trim strategy"""
    policy = CompressionPolicy(strategy="trim", max_tokens=500)
    manager = ContextManager(policy=policy)

    messages = [{"role": "user", "content": "Message " * 50}] * 20

    compressed = await manager.compress(messages)

    # Should be compressed
    assert len(compressed) < len(messages)

@pytest.mark.asyncio
@patch("kagura.core.compression.summarizer.call_llm", new_callable=AsyncMock)
async def test_compress_smart_strategy(mock_call_llm):
    """Test smart strategy"""
    mock_call_llm.return_value = "Summary"

    policy = CompressionPolicy(strategy="smart", max_tokens=500)
    manager = ContextManager(policy=policy)

    messages = [
        {"role": "user", "content": "Normal message " * 20},
        {"role": "user", "content": "IMPORTANT: Key decision made"},
        {"role": "user", "content": "Normal message " * 20},
    ] * 10

    compressed = await manager.compress(messages)

    # Should be compressed
    assert len(compressed) < len(messages)

    # Should preserve key events
    contents = [m["content"] for m in compressed]
    assert any("IMPORTANT" in c for c in contents)

def test_get_usage():
    """Test usage statistics"""
    manager = ContextManager()

    messages = [{"role": "user", "content": "Test"}] * 10

    usage = manager.get_usage(messages)

    assert usage.total_tokens > 0
    assert usage.max_tokens > 0
    assert 0.0 <= usage.usage_ratio <= 1.0
```

---

### Day 4: MemoryManager Integration

**Goal**: 既存のMemoryManagerに圧縮機能を統合

**Tasks**:
1. `MemoryManager.__init__()`に圧縮パラメータ追加
2. `get_context()`で圧縮適用
3. `get_usage_stats()`追加
4. 既存テスト全パス確認
5. 統合テスト（5 tests）

**Code**:
```python
# src/kagura/core/memory/manager.py (既存ファイルを拡張)

from typing import Any, Optional
from kagura.core.compression import ContextManager, CompressionPolicy

class MemoryManager:
    """Memory manager with compression support"""

    def __init__(
        self,
        agent_name: str,
        # ... existing parameters ...
        enable_compression: bool = True,
        compression_policy: Optional[CompressionPolicy] = None,
    ):
        """Initialize memory manager

        Args:
            agent_name: Agent identifier
            enable_compression: Enable automatic context compression
            compression_policy: Compression configuration
        """
        # ... existing initialization ...

        # Compression
        self.enable_compression = enable_compression
        if enable_compression:
            self.context_manager = ContextManager(
                policy=compression_policy or CompressionPolicy(),
                model=self.llm_config.model
            )
        else:
            self.context_manager = None

    async def get_context(
        self,
        compress: bool = True
    ) -> list[dict[str, Any]]:
        """Get conversation history with optional compression

        Args:
            compress: Whether to apply compression

        Returns:
            Message history (compressed if enabled)
        """
        messages = self.context_memory.get_history()

        if compress and self.context_manager:
            # Apply compression
            messages = await self.context_manager.compress(messages)

        return messages

    def get_usage_stats(self) -> dict[str, Any]:
        """Get context usage statistics

        Returns:
            Dict with compression stats
        """
        if not self.context_manager:
            return {"compression_enabled": False}

        messages = self.context_memory.get_history()
        usage = self.context_manager.get_usage(messages)

        return {
            "compression_enabled": True,
            "total_tokens": usage.total_tokens,
            "max_tokens": usage.max_tokens,
            "usage_ratio": usage.usage_ratio,
            "should_compress": usage.should_compress,
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens
        }
```

**Tests**:
```python
# tests/core/compression/test_integration.py

import pytest
from unittest.mock import AsyncMock, patch
from kagura.core.memory import MemoryManager
from kagura.core.compression import CompressionPolicy

@pytest.mark.asyncio
@patch("kagura.core.compression.summarizer.call_llm", new_callable=AsyncMock)
async def test_memory_manager_compression(mock_call_llm):
    """Test MemoryManager with compression enabled"""
    mock_call_llm.return_value = "Summary"

    memory = MemoryManager(
        agent_name="test",
        enable_compression=True,
        compression_policy=CompressionPolicy(max_tokens=500)
    )

    # Add many messages
    for i in range(50):
        await memory.context_memory.add_message("user", f"Message {i} " * 20)

    # Get context (should trigger compression)
    context = await memory.get_context(compress=True)

    # Should be compressed
    assert len(context) < 50

def test_memory_manager_usage_stats():
    """Test usage statistics"""
    memory = MemoryManager(
        agent_name="test",
        enable_compression=True
    )

    # Add messages
    for i in range(10):
        memory.context_memory.add_message("user", f"Message {i}")

    # Check usage stats
    stats = memory.get_usage_stats()

    assert stats["compression_enabled"] is True
    assert "usage_ratio" in stats
    assert "total_tokens" in stats
```

---

### Day 5: @agent Decorator Integration

**Goal**: デコレータで自動圧縮を有効化

**Tasks**:
1. `@agent`にcompressionパラメータ追加
2. デフォルトで圧縮有効化
3. 既存テスト全パス確認
4. E2Eテスト（5 tests）

**Code**:
```python
# src/kagura/core/decorators.py (既存ファイルを拡張)

from typing import Optional
from kagura.core.compression import CompressionPolicy

def agent(
    model: str = "gpt-4o-mini",
    # ... existing parameters ...
    enable_compression: bool = True,
    compression_policy: Optional[CompressionPolicy] = None,
):
    """Agent decorator with compression support

    Args:
        model: LLM model name
        enable_compression: Enable automatic context compression
        compression_policy: Compression configuration

    Example:
        >>> @agent(
        ...     model="gpt-4o-mini",
        ...     enable_compression=True,
        ...     compression_policy=CompressionPolicy(strategy="smart")
        ... )
        ... async def assistant(query: str) -> str:
        ...     return "Response"
    """
    def decorator(func):
        # ... existing code ...

        # Setup compression
        if enable_memory and enable_compression:
            memory_manager.enable_compression = True
            memory_manager.context_manager = ContextManager(
                policy=compression_policy or CompressionPolicy(),
                model=model
            )

        # ... existing code ...

    return decorator
```

**Tests**:
```python
# tests/core/compression/test_integration.py (continued)

@pytest.mark.asyncio
@patch("kagura.core.llm.call_llm", new_callable=AsyncMock)
async def test_agent_decorator_compression(mock_call_llm):
    """Test @agent with compression enabled"""
    from kagura import agent

    mock_call_llm.return_value = "Response"

    @agent(
        model="gpt-4o-mini",
        enable_memory=True,
        enable_compression=True,
        compression_policy=CompressionPolicy(max_tokens=500)
    )
    async def test_agent(query: str) -> str:
        """Test agent"""
        pass

    # Call multiple times to build up context
    for i in range(30):
        await test_agent(f"Query {i} " * 20)

    # Compression should have been applied automatically
    # (verified via internal memory state)
```

---

### Day 6: Comprehensive Testing

**Goal**: 全テスト通過（既存900+ + 新規30+）

**Tasks**:
1. 全テスト実行（既存900+ tests）
2. 新規テスト実行（30+ tests）
3. カバレッジ確認（95%+）
4. Pyright・Ruff確認

**Commands**:
```bash
# All tests
pytest

# Coverage
pytest --cov=src/kagura --cov-report=html

# Type check
pyright src/kagura/

# Lint
ruff check src/
```

---

### Day 7: Documentation & PR

**Goal**: ドキュメント完成・PR作成

**Tasks**:
1. `__init__.py` exports更新
2. `ai_docs/NEXT_STEPS.md` 更新
3. ユーザーガイド作成
4. APIリファレンス更新
5. Draft PR作成
6. CI確認

**Documentation**:

```markdown
# User Guide: Context Compression

## Quick Start

```python
from kagura import agent

# Default: compression enabled
@agent(model="gpt-4o-mini")
async def assistant(query: str) -> str:
    """Assistant with auto compression"""
    pass

# Custom policy
from kagura.core.compression import CompressionPolicy

@agent(
    model="gpt-4o-mini",
    compression_policy=CompressionPolicy(
        strategy="smart",
        max_tokens=4000,
        trigger_threshold=0.8
    )
)
async def custom_assistant(query: str) -> str:
    """Assistant with custom compression"""
    pass
```

## Compression Strategies

1. **auto**: Automatically choose best strategy (recommended)
2. **trim**: Simple message trimming (fast, no LLM calls)
3. **summarize**: LLM-based summarization (slower, better quality)
4. **smart**: Preserve key events + summarize routine (best quality)
5. **off**: Disable compression

## Monitoring

```python
from kagura.core.memory import MemoryManager

memory = MemoryManager(agent_name="assistant")

# Check usage
stats = memory.get_usage_stats()
print(f"Usage: {stats['usage_ratio']:.1%}")
print(f"Tokens: {stats['total_tokens']} / {stats['max_tokens']}")
```

## Best Practices

1. Use **auto** strategy for most cases
2. Monitor token usage in production
3. Use **trim** for cost-sensitive applications
4. Use **smart** for conversation quality
```

---

## 🎯 Deliverables

### Code
- ✅ `src/kagura/core/compression/policy.py` (~100 lines)
- ✅ `src/kagura/core/compression/manager.py` (~200 lines)
- ✅ `src/kagura/core/memory/manager.py` (modified, +50 lines)
- ✅ `src/kagura/core/decorators.py` (modified, +20 lines)
- ✅ Updated `__init__.py` exports

### Tests
- ✅ `tests/core/compression/test_policy.py` (5 tests)
- ✅ `tests/core/compression/test_manager.py` (15 tests)
- ✅ `tests/core/compression/test_integration.py` (10 tests)
- ✅ 全既存テスト（900+）パス

### Documentation
- ✅ User guide完成
- ✅ APIリファレンス更新
- ✅ Migration guide
- ✅ `ai_docs/NEXT_STEPS.md` 更新

### PR
- ✅ Draft PR作成
- ✅ CI通過
- ✅ Ready for review

---

## 📊 Quality Metrics

### Functional
- All 5 compression strategies working
- Automatic compression trigger (80%)
- MemoryManager integration seamless
- @agent decorator support

### Quality
- Existing tests: 900+ all passing
- New tests: 30+ all passing
- Pyright: 0 errors (strict mode)
- Ruff: All checks passed
- Coverage: 95%+

### Performance
- Compression overhead: <100ms
- Memory usage: +10% max

---

## 🎉 v2.5.0 Release

After Phase 4 completion:
- **All 4 Phases完了**
- **100+ 新規テスト全パス**
- **Production-ready Context Compression**
- **v2.5.0リリース準備完了**

---

**Phase 4完了により、Kagura AIは完全なContext Compression機能を獲得し、長時間会話対応のProduction-readyフレームワークになります！**
