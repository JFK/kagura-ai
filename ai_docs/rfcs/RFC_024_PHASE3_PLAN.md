# RFC-024 Phase 3 Implementation Plan: Context Summarization

**Phase**: 3 of 4
**Duration**: Week 3-4 (10-14 days)
**Priority**: 🔥🔥🔥 Critical
**Depends on**: Phase 1 ✅, Phase 2 ✅

---

## 📋 Overview

Phase 3では、LLMを使用した会話履歴の要約機能を実装します。単純なトリミングでは情報が失われる場合に、重要な情報を保持しながらトークン数を大幅に削減します。

### Goals

1. **Recursive Summarization**: 再帰的に要約を生成し、任意の長さの会話を圧縮
2. **Hierarchical Summarization**: 3段階（brief/detailed/full）の要約を生成
3. **Event-Preserving Compression**: 重要なイベント（決定事項、エラー、設定等）を保持しながら圧縮

---

## 🎯 Success Criteria

### Functional
- ✅ Recursive summarization動作（10,000メッセージ→500トークン）
- ✅ Hierarchical summarization生成（brief: 10%, detailed: 30%, full: 70%）
- ✅ Key event preservation（95%+の重要イベント保持）
- ✅ 非同期処理対応（async/await）

### Quality
- ✅ 要約品質: 人間評価で4/5以上
- ✅ 情報保持率: 90%+（重要情報）
- ✅ トークン削減率: 80%+（summarization時）
- ✅ 25+ tests全パス

### Performance
- ✅ 処理速度: <5s/1000メッセージ（LLM呼び出し含む）
- ✅ LLMコスト: <$0.01/1000メッセージ（gpt-4o-mini使用時）

### Code Quality
- ✅ Pyright: 0 errors（strict mode）
- ✅ Ruff: All checks passed
- ✅ Coverage: 95%+

---

## 📦 Implementation

### File Structure

```
src/kagura/core/compression/
├── __init__.py              # Export ContextSummarizer
├── summarizer.py            # NEW: ContextSummarizer実装
├── token_counter.py         # Existing (Phase 1)
├── monitor.py              # Existing (Phase 1)
└── trimmer.py              # Existing (Phase 2)

tests/core/compression/
├── test_summarizer.py       # NEW: 25+ tests
├── test_token_counter.py    # Existing
├── test_monitor.py          # Existing
└── test_trimmer.py          # Existing
```

---

## 📝 Day-by-Day Plan

### Week 3: Core Summarization

#### Day 1-2: Recursive Summarization
**Goal**: 再帰的要約の基本実装

**Tasks**:
1. `ContextSummarizer`クラス作成
2. `summarize_recursive()`実装
3. `_messages_to_text()`ヘルパー実装
4. `_split_into_chunks()`実装
5. 基本テスト（5 tests）

**Files**:
- `src/kagura/core/compression/summarizer.py`
- `tests/core/compression/test_summarizer.py`

**Code**:
```python
# src/kagura/core/compression/summarizer.py

from typing import Any, Optional
from kagura.core.llm import call_llm, LLMConfig
from .token_counter import TokenCounter

class ContextSummarizer:
    """Summarize conversation history to reduce tokens"""

    def __init__(
        self,
        token_counter: TokenCounter,
        llm_config: Optional[LLMConfig] = None
    ):
        self.counter = token_counter
        self.llm_config = llm_config or LLMConfig(
            model="gpt-4o-mini",
            temperature=0.3
        )

    async def summarize_recursive(
        self,
        messages: list[dict[str, Any]],
        target_tokens: int
    ) -> str:
        """Recursively summarize conversation history"""
        conversation = self._messages_to_text(messages)
        current_tokens = self.counter.count_tokens(conversation)

        if current_tokens <= target_tokens:
            return conversation

        # Summarize
        summary_prompt = f"""Summarize the following conversation concisely while preserving all important information, decisions, user preferences, and context:

{conversation}

Summary:"""

        summary = await call_llm(summary_prompt, self.llm_config)
        summary_tokens = self.counter.count_tokens(summary)

        if summary_tokens <= target_tokens:
            return summary

        # Recursively summarize if still too large
        chunks = self._split_into_chunks(conversation, target_tokens)
        chunk_summaries = []

        for chunk in chunks:
            chunk_summary = await self._summarize_chunk(chunk)
            chunk_summaries.append(chunk_summary)

        combined = "\n\n".join(chunk_summaries)

        return await self.summarize_recursive(
            [{"role": "user", "content": combined}],
            target_tokens
        )

    def _messages_to_text(self, messages: list[dict[str, Any]]) -> str:
        """Convert message list to readable text"""
        lines = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            lines.append(f"{role.upper()}: {content}")
        return "\n\n".join(lines)

    async def _summarize_chunk(self, chunk: str) -> str:
        """Summarize a single chunk"""
        prompt = f"""Summarize this conversation segment concisely:

{chunk}

Summary:"""
        return await call_llm(prompt, self.llm_config)

    def _split_into_chunks(self, text: str, target_tokens: int) -> list[str]:
        """Split text into chunks of target size"""
        sentences = text.split(". ")
        chunks = []
        current_chunk = []
        current_tokens = 0

        for sentence in sentences:
            sentence_tokens = self.counter.count_tokens(sentence)

            if current_tokens + sentence_tokens > target_tokens and current_chunk:
                chunks.append(". ".join(current_chunk) + ".")
                current_chunk = [sentence]
                current_tokens = sentence_tokens
            else:
                current_chunk.append(sentence)
                current_tokens += sentence_tokens

        if current_chunk:
            chunks.append(". ".join(current_chunk) + ".")

        return chunks
```

**Tests**:
```python
# tests/core/compression/test_summarizer.py

import pytest
from unittest.mock import AsyncMock, patch
from kagura.core.compression import TokenCounter, ContextSummarizer

@pytest.fixture
def summarizer():
    counter = TokenCounter(model="gpt-4o-mini")
    return ContextSummarizer(counter)

@pytest.mark.asyncio
@patch("kagura.core.compression.summarizer.call_llm", new_callable=AsyncMock)
async def test_summarize_recursive_basic(mock_call_llm, summarizer):
    """Test basic recursive summarization"""
    mock_call_llm.return_value = "This is a brief summary."

    messages = [
        {"role": "user", "content": "Long message " * 100},
        {"role": "assistant", "content": "Long response " * 100},
    ]

    summary = await summarizer.summarize_recursive(messages, target_tokens=50)

    assert "summary" in summary.lower()
    assert len(summary) < 200

@pytest.mark.asyncio
@patch("kagura.core.compression.summarizer.call_llm", new_callable=AsyncMock)
async def test_summarize_recursive_already_short(mock_call_llm, summarizer):
    """Test when content is already under target"""
    messages = [{"role": "user", "content": "Short message"}]

    summary = await summarizer.summarize_recursive(messages, target_tokens=1000)

    # Should not call LLM
    mock_call_llm.assert_not_called()
    assert "Short message" in summary
```

---

#### Day 3-4: Hierarchical Summarization
**Goal**: 3段階の要約生成

**Tasks**:
1. `summarize_hierarchical()`実装
2. brief（10%）、detailed（30%）、full（70%）の要約生成
3. テスト追加（5 tests）

**Code**:
```python
async def summarize_hierarchical(
    self,
    messages: list[dict[str, Any]],
    levels: int = 3
) -> dict[str, str]:
    """Create hierarchical summary at multiple levels

    Returns:
        Dict with keys: "brief", "detailed", "full"
    """
    conversation = self._messages_to_text(messages)
    current_tokens = self.counter.count_tokens(conversation)

    summaries = {}

    # Level 1: Brief (10% of original)
    target_brief = max(int(current_tokens * 0.1), 100)
    summaries["brief"] = await self.summarize_recursive(messages, target_brief)

    # Level 2: Detailed (30% of original)
    target_detailed = max(int(current_tokens * 0.3), 300)
    summaries["detailed"] = await self.summarize_recursive(messages, target_detailed)

    # Level 3: Full (original or 70% if too long)
    if current_tokens > 5000:
        target_full = int(current_tokens * 0.7)
        summaries["full"] = await self.summarize_recursive(messages, target_full)
    else:
        summaries["full"] = conversation

    return summaries
```

**Tests**:
```python
@pytest.mark.asyncio
@patch("kagura.core.compression.summarizer.call_llm", new_callable=AsyncMock)
async def test_summarize_hierarchical(mock_call_llm, summarizer):
    """Test hierarchical summarization"""
    mock_call_llm.return_value = "Summary text"

    messages = [
        {"role": "user", "content": "Message " * 100}
    ] * 10

    summaries = await summarizer.summarize_hierarchical(messages, levels=3)

    assert "brief" in summaries
    assert "detailed" in summaries
    assert "full" in summaries

    # Brief should be shortest
    assert len(summaries["brief"]) < len(summaries["detailed"])
```

---

#### Day 5-7: Event-Preserving Compression
**Goal**: 重要イベント保持型圧縮

**Tasks**:
1. `compress_preserve_events()`実装
2. `_is_key_event()`キーワード検出実装
3. イベント保持テスト（8 tests）

**Code**:
```python
async def compress_preserve_events(
    self,
    messages: list[dict[str, Any]],
    target_tokens: int
) -> list[dict[str, Any]]:
    """Compress while preserving key events

    Strategy:
    1. Identify key events (decisions, errors, preferences)
    2. Summarize routine messages
    3. Keep key events verbatim
    """
    # Separate key events from routine messages
    key_events = []
    routine = []

    for msg in messages:
        if self._is_key_event(msg):
            key_events.append(msg)
        else:
            routine.append(msg)

    # Calculate token budget
    key_event_tokens = self.counter.count_tokens_messages(key_events)
    remaining_tokens = target_tokens - key_event_tokens

    if remaining_tokens < 100:
        # Not enough space, must summarize everything
        summary = await self.summarize_recursive(messages, target_tokens)
        return [{"role": "system", "content": f"[Summary] {summary}"}]

    # Summarize routine messages
    if routine:
        routine_summary = await self.summarize_recursive(routine, remaining_tokens)
        summary_msg = {
            "role": "system",
            "content": f"[Previous conversation summary] {routine_summary}"
        }
    else:
        summary_msg = None

    # Reconstruct message list
    compressed = []
    if summary_msg:
        compressed.append(summary_msg)
    compressed.extend(key_events)

    return compressed

def _is_key_event(self, msg: dict[str, Any]) -> bool:
    """Check if message is a key event"""
    content = msg.get("content", "").lower()

    key_indicators = [
        "error", "exception", "failed",
        "important", "critical", "urgent",
        "decided", "agreed", "confirmed",
        "preference", "setting", "config",
        "remember", "note", "save"
    ]

    return any(indicator in content for indicator in key_indicators)
```

**Tests**:
```python
@pytest.mark.asyncio
@patch("kagura.core.compression.summarizer.call_llm", new_callable=AsyncMock)
async def test_compress_preserve_events(mock_call_llm, summarizer):
    """Test event-preserving compression"""
    mock_call_llm.return_value = "Routine summary"

    messages = [
        {"role": "user", "content": "Normal message 1"},
        {"role": "user", "content": "IMPORTANT: User decided to use dark mode"},
        {"role": "user", "content": "Normal message 2"},
        {"role": "user", "content": "ERROR: Connection failed"},
        {"role": "user", "content": "Normal message 3"},
    ]

    compressed = await summarizer.compress_preserve_events(messages, target_tokens=200)

    # Should preserve key events
    contents = [m["content"] for m in compressed]
    assert any("IMPORTANT" in c for c in contents)
    assert any("ERROR" in c for c in contents)

def test_is_key_event(summarizer):
    """Test key event detection"""
    # Key events
    assert summarizer._is_key_event({"content": "IMPORTANT: user preference"})
    assert summarizer._is_key_event({"content": "ERROR: failed to connect"})
    assert summarizer._is_key_event({"content": "Decided to use API key auth"})

    # Not key events
    assert not summarizer._is_key_event({"content": "Hello, how are you?"})
    assert not summarizer._is_key_event({"content": "Thanks for the help"})
```

---

### Week 4: Testing & Documentation

#### Day 1-3: Comprehensive Testing
**Goal**: 25+ tests全パス

**Test Categories**:
1. **Basic Functionality** (5 tests)
   - Recursive summarization
   - Hierarchical summarization
   - Event-preserving compression

2. **Edge Cases** (8 tests)
   - Empty messages
   - Single message
   - Very long messages
   - No key events
   - All key events
   - Target tokens < actual tokens

3. **Integration** (7 tests)
   - With TokenCounter
   - With different LLM models
   - With async processing
   - Mock LLM responses

4. **Performance** (5 tests)
   - Large message lists (1000+)
   - Token reduction verification
   - LLM call count optimization

**Additional Tests**:
```python
@pytest.mark.asyncio
async def test_summarize_empty_messages(summarizer):
    """Test with empty message list"""
    messages = []
    summary = await summarizer.summarize_recursive(messages, target_tokens=100)
    assert summary == ""

@pytest.mark.asyncio
@patch("kagura.core.compression.summarizer.call_llm", new_callable=AsyncMock)
async def test_summarize_large_conversation(mock_call_llm, summarizer):
    """Test with large conversation (1000+ messages)"""
    mock_call_llm.return_value = "Summary"

    messages = [{"role": "user", "content": f"Message {i}"} for i in range(1000)]

    summary = await summarizer.summarize_recursive(messages, target_tokens=500)

    # Should significantly reduce tokens
    original_tokens = summarizer.counter.count_tokens_messages(messages)
    summary_tokens = summarizer.counter.count_tokens(summary)

    assert summary_tokens < original_tokens * 0.1  # 90%+ reduction

@pytest.mark.asyncio
@patch("kagura.core.compression.summarizer.call_llm", new_callable=AsyncMock)
async def test_compress_no_routine_messages(mock_call_llm, summarizer):
    """Test when all messages are key events"""
    messages = [
        {"role": "user", "content": "IMPORTANT: Event 1"},
        {"role": "user", "content": "ERROR: Event 2"},
        {"role": "user", "content": "CRITICAL: Event 3"},
    ]

    compressed = await summarizer.compress_preserve_events(messages, target_tokens=500)

    # Should not call LLM (no routine to summarize)
    mock_call_llm.assert_not_called()

    # Should keep all key events
    assert len(compressed) == len(messages)
```

---

#### Day 4-7: Documentation & PR

**Tasks**:
1. Update `__init__.py` exports
2. Update `ai_docs/NEXT_STEPS.md`
3. Create comprehensive docstrings
4. Write usage examples
5. Create Draft PR
6. CI verification

**Documentation**:
```markdown
## Usage Example

```python
from kagura.core.compression import TokenCounter, ContextSummarizer

counter = TokenCounter(model="gpt-4o-mini")
summarizer = ContextSummarizer(counter)

# Recursive summarization
messages = [
    {"role": "user", "content": "Long conversation..."},
    # ... many messages
]

summary = await summarizer.summarize_recursive(messages, target_tokens=500)
print(summary)

# Hierarchical summarization
summaries = await summarizer.summarize_hierarchical(messages)
print(summaries["brief"])     # 10% of original
print(summaries["detailed"])  # 30% of original
print(summaries["full"])      # 70% of original

# Event-preserving compression
compressed = await summarizer.compress_preserve_events(messages, target_tokens=1000)
# Key events are preserved verbatim, routine messages are summarized
```
```

---

## 🎯 Deliverables

### Code
- ✅ `src/kagura/core/compression/summarizer.py` (~250 lines)
- ✅ `tests/core/compression/test_summarizer.py` (~400 lines, 25+ tests)
- ✅ Updated `__init__.py` exports

### Tests
- ✅ 25+ tests全パス
- ✅ Pyright: 0 errors
- ✅ Ruff: All checks passed
- ✅ Coverage: 95%+

### Documentation
- ✅ Comprehensive docstrings
- ✅ Usage examples
- ✅ `ai_docs/NEXT_STEPS.md` updated

### PR
- ✅ Draft PR作成
- ✅ CI通過
- ✅ Ready for review

---

## 📊 Quality Metrics

### Functional
- Token reduction: 80%+ (summarization)
- Key event preservation: 95%+
- Async processing: Full support

### Performance
- Processing speed: <5s/1000 messages
- LLM cost: <$0.01/1000 messages

### Code Quality
- Pyright: 0 errors (strict mode)
- Ruff: All checks passed
- Test coverage: 95%+

---

## 🔗 Next Steps

After Phase 3:
- **Phase 4**: Integration & Policy
  - CompressionPolicy implementation
  - ContextManager統合
  - MemoryManager統合
  - @agentデコレータ統合

---

**Phase 3完了により、Kagura AIは高度なContext Compression機能を獲得します！**
