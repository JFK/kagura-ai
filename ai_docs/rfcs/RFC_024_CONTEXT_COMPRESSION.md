# RFC-024: Context Compression System

**ステータス**: Draft
**作成日**: 2025-10-14
**優先度**: 🔥🔥🔥 Critical
**関連Issue**: #159
**依存RFC**: RFC-018 (Memory Management)

---

## 📋 概要

### 問題

現在のKagura AIには**Context Compression機能が一切ありません**。これにより：

1. **長い会話で必ずコンテキストリミットに達する**
   - GPT-4: 8K/32K/128K tokens
   - Claude: 200K tokens
   - 長時間会話では必ず限界に到達

2. **トークン管理機能がない**
   - 現在のトークン使用量が不明
   - コスト予測不可能
   - いつコンテキストリミットに達するか分からない

3. **Personal Assistant実装が不可能**
   - RFC-003実装時に破綻
   - 継続的な会話が成立しない

4. **Production環境で使用不可能**
   - ユーザーに「会話が長すぎる」エラー
   - 予期せぬ動作停止

### 解決策

LangChainのContext Engineering手法に基づき、以下を実装：

1. **Token Management**: トークン計測・監視
2. **Message Trimming**: 古いメッセージの削除
3. **Context Summarization**: 会話履歴の要約
4. **Smart Compression**: 重要情報保持型圧縮

---

## 🎯 目標

### 成功指標

1. **長時間会話対応**
   - ✅ 10,000メッセージの会話でもコンテキストリミット回避
   - ✅ 無制限の会話継続が可能

2. **トークン削減**
   - ✅ 圧縮時にトークン使用量90%削減
   - ✅ コスト削減

3. **情報保持**
   - ✅ 圧縮後も回答精度95%+維持
   - ✅ 重要な決定事項・イベントを保持

4. **自動化**
   - ✅ 自動圧縮トリガー（80%到達時）
   - ✅ ユーザー介入不要

---

## 🏗️ アーキテクチャ

### 全体像

```
┌─────────────────────────────────────────────────────────┐
│                    ContextManager                        │
│  (統合インターフェース - 4つの戦略を統合)                │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼────────┐  ┌───────▼────────┐  ┌──────▼──────┐
│ TokenCounter   │  │ MessageTrimmer │  │ Summarizer  │
│                │  │                │  │             │
│ - count_tokens │  │ - trim_last    │  │ - recursive │
│ - estimate     │  │ - trim_first   │  │ - hierarchi │
│ - should_      │  │ - trim_smart   │  │   cal       │
│   compress     │  │                │  │ - event_    │
└────────────────┘  └────────────────┘  │   preserve  │
                                        └─────────────┘
                            │
                ┌───────────▼───────────┐
                │  CompressionPolicy    │
                │  (戦略・設定)         │
                │                       │
                │ - strategy: "smart"   │
                │ - max_tokens: 4000    │
                │ - trigger: 0.8        │
                └───────────────────────┘
                            │
                ┌───────────▼───────────┐
                │   MemoryManager       │
                │   (既存システム)      │
                └───────────────────────┘
```

---

## 📦 Phase 1: Token Management (Week 1)

### 実装内容

#### 1.1 TokenCounter

```python
# src/kagura/core/compression/token_counter.py

import tiktoken
from typing import Any

class TokenCounter:
    """Count tokens for various LLM models"""

    def __init__(self, model: str = "gpt-4o-mini"):
        """Initialize with specific model tokenizer

        Args:
            model: LLM model name (e.g., "gpt-4o-mini", "claude-3-5-sonnet")
        """
        self.model = model
        self._encoder = self._get_encoder(model)

    def _get_encoder(self, model: str) -> tiktoken.Encoding:
        """Get tiktoken encoder for model"""
        try:
            # OpenAI models
            if "gpt" in model.lower():
                return tiktoken.encoding_for_model(model)
            # Claude models (use cl100k_base)
            elif "claude" in model.lower():
                return tiktoken.get_encoding("cl100k_base")
            # Gemini models (use cl100k_base approximation)
            elif "gemini" in model.lower():
                return tiktoken.get_encoding("cl100k_base")
            else:
                # Default to cl100k_base
                return tiktoken.get_encoding("cl100k_base")
        except Exception:
            # Fallback to cl100k_base
            return tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """Count tokens in text

        Args:
            text: Text to count

        Returns:
            Number of tokens
        """
        if not text:
            return 0
        return len(self._encoder.encode(text))

    def count_tokens_messages(self, messages: list[dict[str, Any]]) -> int:
        """Count tokens in message list (OpenAI format)

        Args:
            messages: List of messages with role/content

        Returns:
            Total token count including overhead
        """
        # OpenAI message format overhead
        # Every message: 3 tokens for role/name/content
        # Every reply: 3 tokens (assistant priming)
        tokens = 3  # Reply priming

        for message in messages:
            tokens += 3  # Message overhead
            tokens += self.count_tokens(message.get("role", ""))
            tokens += self.count_tokens(message.get("content", ""))
            if "name" in message:
                tokens += self.count_tokens(message["name"])
                tokens -= 1  # Name adjustment

        return tokens

    def estimate_context_size(
        self,
        messages: list[dict[str, Any]],
        system_prompt: str = "",
        max_tokens: int = 1000
    ) -> dict[str, int]:
        """Estimate total context window usage

        Args:
            messages: Conversation history
            system_prompt: System prompt
            max_tokens: Max completion tokens

        Returns:
            Dict with prompt_tokens, completion_tokens, total_tokens
        """
        prompt_tokens = self.count_tokens(system_prompt)
        prompt_tokens += self.count_tokens_messages(messages)

        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": max_tokens,
            "total_tokens": prompt_tokens + max_tokens
        }

    def should_compress(
        self,
        current_tokens: int,
        max_tokens: int,
        threshold: float = 0.8
    ) -> bool:
        """Decide if compression is needed

        Args:
            current_tokens: Current token count
            max_tokens: Maximum allowed tokens
            threshold: Trigger compression at this ratio (default: 0.8 = 80%)

        Returns:
            True if compression should be triggered
        """
        return current_tokens >= (max_tokens * threshold)

    def get_model_limits(self, model: str) -> dict[str, int]:
        """Get token limits for specific model

        Args:
            model: Model name

        Returns:
            Dict with context_window, max_completion_tokens
        """
        # Model limits (as of 2025)
        limits = {
            "gpt-4o-mini": {"context_window": 128_000, "max_completion": 16_384},
            "gpt-4o": {"context_window": 128_000, "max_completion": 16_384},
            "gpt-4-turbo": {"context_window": 128_000, "max_completion": 4_096},
            "gpt-3.5-turbo": {"context_window": 16_385, "max_completion": 4_096},
            "claude-3-5-sonnet": {"context_window": 200_000, "max_completion": 8_192},
            "claude-3-opus": {"context_window": 200_000, "max_completion": 4_096},
            "gemini-1.5-pro": {"context_window": 2_000_000, "max_completion": 8_192},
            "gemini-1.5-flash": {"context_window": 1_000_000, "max_completion": 8_192},
        }

        # Default for unknown models
        default = {"context_window": 8_000, "max_completion": 2_000}

        return limits.get(model, default)
```

#### 1.2 Context Monitoring

```python
# src/kagura/core/compression/monitor.py

from dataclasses import dataclass
from typing import Optional

@dataclass
class ContextUsage:
    """Context usage statistics"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    max_tokens: int
    usage_ratio: float  # 0.0 - 1.0
    should_compress: bool

class ContextMonitor:
    """Monitor context window usage"""

    def __init__(self, token_counter: TokenCounter, max_tokens: Optional[int] = None):
        """Initialize monitor

        Args:
            token_counter: TokenCounter instance
            max_tokens: Max context window (if None, auto-detect from model)
        """
        self.counter = token_counter
        self.max_tokens = max_tokens or self._get_max_tokens()

    def _get_max_tokens(self) -> int:
        """Get max tokens for current model"""
        limits = self.counter.get_model_limits(self.counter.model)
        # Reserve space for completion (e.g., 4000 tokens)
        return limits["context_window"] - 4000

    def check_usage(
        self,
        messages: list[dict[str, Any]],
        system_prompt: str = ""
    ) -> ContextUsage:
        """Check current context usage

        Args:
            messages: Message history
            system_prompt: System prompt

        Returns:
            ContextUsage statistics
        """
        estimate = self.counter.estimate_context_size(
            messages,
            system_prompt,
            max_tokens=4000  # Reserve for completion
        )

        usage_ratio = estimate["total_tokens"] / self.max_tokens
        should_compress = self.counter.should_compress(
            estimate["total_tokens"],
            self.max_tokens
        )

        return ContextUsage(
            prompt_tokens=estimate["prompt_tokens"],
            completion_tokens=estimate["completion_tokens"],
            total_tokens=estimate["total_tokens"],
            max_tokens=self.max_tokens,
            usage_ratio=usage_ratio,
            should_compress=should_compress
        )
```

### テスト

```python
# tests/core/compression/test_token_counter.py

import pytest
from kagura.core.compression import TokenCounter

def test_count_tokens_basic():
    counter = TokenCounter(model="gpt-4o-mini")

    text = "Hello, world!"
    tokens = counter.count_tokens(text)
    assert tokens > 0
    assert tokens < 10  # Should be ~3 tokens

def test_count_tokens_messages():
    counter = TokenCounter(model="gpt-4o-mini")

    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"},
        {"role": "assistant", "content": "Hi there!"}
    ]

    tokens = counter.count_tokens_messages(messages)
    assert tokens > 20  # Includes overhead

def test_should_compress():
    counter = TokenCounter(model="gpt-4o-mini")

    # Below threshold
    assert not counter.should_compress(1000, 10000, threshold=0.8)

    # Above threshold
    assert counter.should_compress(9000, 10000, threshold=0.8)

def test_get_model_limits():
    counter = TokenCounter(model="gpt-4o-mini")

    limits = counter.get_model_limits("gpt-4o-mini")
    assert limits["context_window"] == 128_000
    assert limits["max_completion"] == 16_384

# 10+ more tests...
```

---

## 📦 Phase 2: Message Trimming (Week 2)

### 実装内容

#### 2.1 MessageTrimmer

```python
# src/kagura/core/compression/trimmer.py

from typing import Any, Literal

TrimStrategy = Literal["last", "first", "middle", "smart"]

class MessageTrimmer:
    """Trim messages to fit within token limits"""

    def __init__(self, token_counter: TokenCounter):
        """Initialize trimmer

        Args:
            token_counter: TokenCounter instance
        """
        self.counter = token_counter

    def trim(
        self,
        messages: list[dict[str, Any]],
        max_tokens: int,
        strategy: TrimStrategy = "smart",
        preserve_system: bool = True
    ) -> list[dict[str, Any]]:
        """Trim messages to fit within token limit

        Args:
            messages: Message list
            max_tokens: Maximum tokens
            strategy: Trimming strategy
            preserve_system: Always keep system message

        Returns:
            Trimmed message list
        """
        if strategy == "last":
            return self._trim_last(messages, max_tokens, preserve_system)
        elif strategy == "first":
            return self._trim_first(messages, max_tokens, preserve_system)
        elif strategy == "middle":
            return self._trim_middle(messages, max_tokens, preserve_system)
        elif strategy == "smart":
            return self._trim_smart(messages, max_tokens, preserve_system)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")

    def _trim_last(
        self,
        messages: list[dict[str, Any]],
        max_tokens: int,
        preserve_system: bool
    ) -> list[dict[str, Any]]:
        """Keep most recent messages (FIFO)"""
        system_msg = None
        if preserve_system and messages and messages[0].get("role") == "system":
            system_msg = messages[0]
            messages = messages[1:]

        # Start from end, accumulate until limit
        trimmed = []
        current_tokens = 0

        for msg in reversed(messages):
            msg_tokens = self.counter.count_tokens_messages([msg])
            if current_tokens + msg_tokens > max_tokens:
                break
            trimmed.insert(0, msg)
            current_tokens += msg_tokens

        # Re-add system message
        if system_msg:
            trimmed.insert(0, system_msg)

        return trimmed

    def _trim_first(
        self,
        messages: list[dict[str, Any]],
        max_tokens: int,
        preserve_system: bool
    ) -> list[dict[str, Any]]:
        """Keep oldest messages (LIFO)"""
        system_msg = None
        if preserve_system and messages and messages[0].get("role") == "system":
            system_msg = messages[0]
            messages = messages[1:]

        # Start from beginning, accumulate until limit
        trimmed = []
        current_tokens = 0

        for msg in messages:
            msg_tokens = self.counter.count_tokens_messages([msg])
            if current_tokens + msg_tokens > max_tokens:
                break
            trimmed.append(msg)
            current_tokens += msg_tokens

        # Re-add system message
        if system_msg:
            trimmed.insert(0, system_msg)

        return trimmed

    def _trim_middle(
        self,
        messages: list[dict[str, Any]],
        max_tokens: int,
        preserve_system: bool
    ) -> list[dict[str, Any]]:
        """Keep beginning and end, remove middle"""
        system_msg = None
        if preserve_system and messages and messages[0].get("role") == "system":
            system_msg = messages[0]
            messages = messages[1:]

        if not messages:
            return [system_msg] if system_msg else []

        # Allocate half tokens to beginning, half to end
        half_tokens = max_tokens // 2

        # Get beginning messages
        beginning = []
        current_tokens = 0
        for msg in messages:
            msg_tokens = self.counter.count_tokens_messages([msg])
            if current_tokens + msg_tokens > half_tokens:
                break
            beginning.append(msg)
            current_tokens += msg_tokens

        # Get ending messages
        ending = []
        current_tokens = 0
        for msg in reversed(messages):
            msg_tokens = self.counter.count_tokens_messages([msg])
            if current_tokens + msg_tokens > half_tokens:
                break
            ending.insert(0, msg)
            current_tokens += msg_tokens

        # Combine (avoid duplicates)
        trimmed = beginning.copy()
        for msg in ending:
            if msg not in trimmed:
                trimmed.append(msg)

        # Re-add system message
        if system_msg:
            trimmed.insert(0, system_msg)

        return trimmed

    def _trim_smart(
        self,
        messages: list[dict[str, Any]],
        max_tokens: int,
        preserve_system: bool
    ) -> list[dict[str, Any]]:
        """Smart trimming: preserve important messages

        Priority:
        1. System message (always)
        2. Recent messages (last 5)
        3. Messages with important keywords
        4. Longer messages (likely more important)
        """
        system_msg = None
        if preserve_system and messages and messages[0].get("role") == "system":
            system_msg = messages[0]
            messages = messages[1:]

        if not messages:
            return [system_msg] if system_msg else []

        # Score messages by importance
        scored = []
        for i, msg in enumerate(messages):
            score = self._score_message(msg, i, len(messages))
            scored.append((score, msg))

        # Sort by score (descending)
        scored.sort(key=lambda x: x[0], reverse=True)

        # Accumulate until token limit
        trimmed = []
        current_tokens = 0

        for score, msg in scored:
            msg_tokens = self.counter.count_tokens_messages([msg])
            if current_tokens + msg_tokens > max_tokens:
                continue
            trimmed.append(msg)
            current_tokens += msg_tokens

        # Re-sort by original order
        trimmed.sort(key=lambda m: messages.index(m))

        # Re-add system message
        if system_msg:
            trimmed.insert(0, system_msg)

        return trimmed

    def _score_message(self, msg: dict[str, Any], index: int, total: int) -> float:
        """Score message importance

        Args:
            msg: Message to score
            index: Message index
            total: Total number of messages

        Returns:
            Importance score (0.0 - 10.0)
        """
        score = 0.0

        # Recency score (last 5 messages get bonus)
        if index >= total - 5:
            score += 5.0

        # Length score (longer = more important, up to 2.0)
        content = msg.get("content", "")
        score += min(len(content) / 500, 2.0)

        # Important keywords
        important_keywords = [
            "error", "important", "critical", "remember", "note",
            "user preference", "setting", "config", "decided", "agreed"
        ]
        content_lower = content.lower()
        for keyword in important_keywords:
            if keyword in content_lower:
                score += 1.0

        # Role bonus (user/assistant more important than function)
        if msg.get("role") in ["user", "assistant"]:
            score += 1.0

        return score
```

### テスト

```python
# tests/core/compression/test_trimmer.py

import pytest
from kagura.core.compression import TokenCounter, MessageTrimmer

@pytest.fixture
def trimmer():
    counter = TokenCounter(model="gpt-4o-mini")
    return MessageTrimmer(counter)

def test_trim_last(trimmer):
    messages = [
        {"role": "system", "content": "System prompt"},
        {"role": "user", "content": "Message 1"},
        {"role": "assistant", "content": "Response 1"},
        {"role": "user", "content": "Message 2"},
        {"role": "assistant", "content": "Response 2"},
    ]

    trimmed = trimmer.trim(messages, max_tokens=50, strategy="last")

    # Should keep system + recent messages
    assert trimmed[0]["role"] == "system"
    assert len(trimmed) < len(messages)

def test_trim_smart_preserves_important(trimmer):
    messages = [
        {"role": "system", "content": "System prompt"},
        {"role": "user", "content": "Normal message"},
        {"role": "user", "content": "IMPORTANT: User preference is dark mode"},
        {"role": "user", "content": "Another normal message"},
        {"role": "user", "content": "Recent message"},
    ]

    trimmed = trimmer.trim(messages, max_tokens=100, strategy="smart")

    # Should preserve system, important message, and recent message
    contents = [m["content"] for m in trimmed]
    assert "System prompt" in contents
    assert "IMPORTANT: User preference is dark mode" in contents
    assert "Recent message" in contents

# 15+ more tests...
```

---

## 📦 Phase 3: Context Summarization (Week 3-4)

### 実装内容

#### 3.1 ContextSummarizer

```python
# src/kagura/core/compression/summarizer.py

from typing import Any, Optional
from kagura.core.llm import call_llm, LLMConfig

class ContextSummarizer:
    """Summarize conversation history to reduce tokens"""

    def __init__(
        self,
        token_counter: TokenCounter,
        llm_config: Optional[LLMConfig] = None
    ):
        """Initialize summarizer

        Args:
            token_counter: TokenCounter instance
            llm_config: LLM configuration for summarization
        """
        self.counter = token_counter
        self.llm_config = llm_config or LLMConfig(
            model="gpt-4o-mini",  # Fast, cheap model for summarization
            temperature=0.3
        )

    async def summarize_recursive(
        self,
        messages: list[dict[str, Any]],
        target_tokens: int
    ) -> str:
        """Recursively summarize conversation history

        Args:
            messages: Message history
            target_tokens: Target token count

        Returns:
            Summary text
        """
        # Convert messages to text
        conversation = self._messages_to_text(messages)

        # If already under target, return as-is
        current_tokens = self.counter.count_tokens(conversation)
        if current_tokens <= target_tokens:
            return conversation

        # Summarize
        summary_prompt = f"""Summarize the following conversation concisely while preserving all important information, decisions, user preferences, and context:

{conversation}

Summary:"""

        summary = await call_llm(summary_prompt, self.llm_config)

        # Check if summary is small enough
        summary_tokens = self.counter.count_tokens(summary)
        if summary_tokens <= target_tokens:
            return summary

        # If still too large, recursively summarize
        # Split into chunks and summarize each
        chunks = self._split_into_chunks(conversation, target_tokens)
        chunk_summaries = []

        for chunk in chunks:
            chunk_summary = await self._summarize_chunk(chunk)
            chunk_summaries.append(chunk_summary)

        # Combine chunk summaries
        combined = "\n\n".join(chunk_summaries)

        # Final summary
        return await self.summarize_recursive(
            [{"role": "user", "content": combined}],
            target_tokens
        )

    async def summarize_hierarchical(
        self,
        messages: list[dict[str, Any]],
        levels: int = 3
    ) -> dict[str, str]:
        """Create hierarchical summary at multiple levels

        Args:
            messages: Message history
            levels: Number of summary levels (default: 3)

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

        Args:
            messages: Message history
            target_tokens: Target token count

        Returns:
            Compressed message list
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
            # Not enough space, must summarize key events too
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
        # Simple split by sentences
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

### テスト

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
async def test_summarize_recursive(mock_call_llm, summarizer):
    mock_call_llm.return_value = "This is a brief summary of the conversation."

    messages = [
        {"role": "user", "content": "Long message " * 100},
        {"role": "assistant", "content": "Long response " * 100},
    ]

    summary = await summarizer.summarize_recursive(messages, target_tokens=50)

    assert "summary" in summary.lower()
    assert len(summary) < 200

@pytest.mark.asyncio
@patch("kagura.core.compression.summarizer.call_llm", new_callable=AsyncMock)
async def test_summarize_hierarchical(mock_call_llm, summarizer):
    mock_call_llm.return_value = "Summary text"

    messages = [
        {"role": "user", "content": "Message " * 100},
    ]

    summaries = await summarizer.summarize_hierarchical(messages, levels=3)

    assert "brief" in summaries
    assert "detailed" in summaries
    assert "full" in summaries

@pytest.mark.asyncio
@patch("kagura.core.compression.summarizer.call_llm", new_callable=AsyncMock)
async def test_compress_preserve_events(mock_call_llm, summarizer):
    mock_call_llm.return_value = "Routine summary"

    messages = [
        {"role": "user", "content": "Normal message"},
        {"role": "user", "content": "IMPORTANT: User decided to use dark mode"},
        {"role": "user", "content": "Another normal message"},
    ]

    compressed = await summarizer.compress_preserve_events(messages, target_tokens=200)

    # Should preserve key event
    contents = [m["content"] for m in compressed]
    assert any("IMPORTANT" in c for c in contents)

# 20+ more tests...
```

---

## 📦 Phase 4: Integration & Policy (Week 5)

### 実装内容

#### 4.1 CompressionPolicy

```python
# src/kagura/core/compression/policy.py

from dataclasses import dataclass
from typing import Literal

CompressionStrategy = Literal["auto", "trim", "summarize", "smart", "off"]

@dataclass
class CompressionPolicy:
    """Context compression configuration"""

    strategy: CompressionStrategy = "smart"
    """Compression strategy:
    - auto: Automatically choose best strategy
    - trim: Simple message trimming
    - summarize: Summarize old messages
    - smart: Preserve events + summarize routine
    - off: No compression
    """

    max_tokens: int = 4000
    """Maximum context tokens (excluding completion)"""

    trigger_threshold: float = 0.8
    """Trigger compression at this ratio (0.0 - 1.0)"""

    preserve_recent: int = 5
    """Always preserve this many recent messages"""

    preserve_system: bool = True
    """Always preserve system message"""

    target_ratio: float = 0.5
    """After compression, aim for this ratio (0.0 - 1.0)"""

    enable_summarization: bool = True
    """Allow LLM-based summarization"""

    summarization_model: str = "gpt-4o-mini"
    """Model for summarization (should be fast and cheap)"""
```

#### 4.2 ContextManager (統合インターフェース)

```python
# src/kagura/core/compression/manager.py

from typing import Any, Optional
from kagura.core.llm import LLMConfig

class ContextManager:
    """Unified context compression manager

    Integrates all compression strategies (Write, Select, Compress, Isolate)
    """

    def __init__(
        self,
        policy: Optional[CompressionPolicy] = None,
        model: str = "gpt-4o-mini"
    ):
        """Initialize context manager

        Args:
            policy: Compression policy
            model: LLM model name
        """
        self.policy = policy or CompressionPolicy()
        self.counter = TokenCounter(model=model)
        self.monitor = ContextMonitor(self.counter, max_tokens=self.policy.max_tokens)
        self.trimmer = MessageTrimmer(self.counter)
        self.summarizer = ContextSummarizer(
            self.counter,
            llm_config=LLMConfig(
                model=self.policy.summarization_model,
                temperature=0.3
            )
        ) if self.policy.enable_summarization else None

    async def compress(
        self,
        messages: list[dict[str, Any]],
        system_prompt: str = ""
    ) -> list[dict[str, Any]]:
        """Compress messages if needed

        Args:
            messages: Message history
            system_prompt: System prompt

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
        """Trim-based compression"""
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
        recent = messages[-self.policy.preserve_recent:]
        to_summarize = messages[:-self.policy.preserve_recent]

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
        """Get current context usage"""
        return self.monitor.check_usage(messages, system_prompt)
```

#### 4.3 MemoryManager統合

```python
# src/kagura/core/memory/manager.py (既存ファイルを拡張)

from kagura.core.compression import ContextManager, CompressionPolicy

class MemoryManager:
    def __init__(
        self,
        agent_name: str,
        compression_policy: Optional[CompressionPolicy] = None,
        enable_compression: bool = True
    ):
        # ... existing code ...

        # Compression
        self.enable_compression = enable_compression
        if enable_compression:
            self.context_manager = ContextManager(
                policy=compression_policy,
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
        """Get context usage statistics"""
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

#### 4.4 @agent デコレータ統合

```python
# src/kagura/core/decorators.py (既存ファイルを拡張)

from kagura.core.compression import CompressionPolicy

def agent(
    model: str = "gpt-4o-mini",
    # ... existing parameters ...
    enable_compression: bool = True,
    compression_policy: Optional[CompressionPolicy] = None,
):
    """Agent decorator with compression support

    Args:
        enable_compression: Enable automatic context compression
        compression_policy: Compression configuration
    """
    def decorator(func):
        # ... existing code ...

        # Setup compression
        if enable_memory and enable_compression:
            memory.enable_compression = True
            memory.context_manager = ContextManager(
                policy=compression_policy,
                model=model
            )

        # ... existing code ...

    return decorator
```

### テスト

```python
# tests/core/compression/test_manager.py

import pytest
from unittest.mock import AsyncMock, patch
from kagura.core.compression import ContextManager, CompressionPolicy

@pytest.mark.asyncio
@patch("kagura.core.compression.summarizer.call_llm", new_callable=AsyncMock)
async def test_compress_auto(mock_call_llm):
    mock_call_llm.return_value = "Summary"

    policy = CompressionPolicy(strategy="auto", max_tokens=1000)
    manager = ContextManager(policy=policy)

    messages = [
        {"role": "user", "content": "Message " * 100}
    ] * 30  # 30 long messages

    compressed = await manager.compress(messages)

    # Should be compressed
    assert len(compressed) < len(messages)

@pytest.mark.asyncio
async def test_compression_disabled():
    policy = CompressionPolicy(strategy="off")
    manager = ContextManager(policy=policy)

    messages = [{"role": "user", "content": "Test"}] * 100

    compressed = await manager.compress(messages)

    # Should not compress
    assert compressed == messages

# Integration test with MemoryManager
@pytest.mark.asyncio
@patch("kagura.core.compression.summarizer.call_llm", new_callable=AsyncMock)
async def test_memory_manager_compression(mock_call_llm):
    from kagura.core.memory import MemoryManager

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

    # Check usage stats
    stats = memory.get_usage_stats()
    assert stats["compression_enabled"] is True
    assert "usage_ratio" in stats

# 30+ more tests...
```

---

## 📊 成功指標

### Phase 1完了時（Token Management）
- ✅ 全モデルのトークンカウント正確（誤差±5%以内）
- ✅ コンテキスト使用量をリアルタイム監視可能
- ✅ 15+ tests全パス

### Phase 2完了時（Message Trimming）
- ✅ 4つの戦略（last, first, middle, smart）動作
- ✅ トークン削減率: 50%+（trim時）
- ✅ 重要メッセージ保持率: 90%+（smart strategy）
- ✅ 20+ tests全パス

### Phase 3完了時（Summarization）
- ✅ 再帰的要約動作（10,000メッセージ→500トークン）
- ✅ 階層的要約生成（brief/detailed/full）
- ✅ キーイベント保持率: 95%+
- ✅ 要約品質: 人間評価で4/5以上
- ✅ 25+ tests全パス

### Phase 4完了時（Integration）
- ✅ MemoryManager統合完了
- ✅ @agentデコレータで自動圧縮
- ✅ 全既存テスト（900+ tests）パス
- ✅ ドキュメント完備

### 全体完了時
- ✅ **10,000メッセージの会話でもコンテキストリミット回避**
- ✅ **トークン使用量90%削減（圧縮時）**
- ✅ **圧縮後も回答精度95%+維持**
- ✅ **自動圧縮（ユーザー介入不要）**
- ✅ **100+ 新規テスト全パス**

---

## 📝 ドキュメント

### ユーザーガイド

```markdown
# docs/en/guides/context-compression.md

## Context Compression

Kagura AI automatically manages context window size through intelligent compression.

### Basic Usage

```python
from kagura import agent
from kagura.core.compression import CompressionPolicy

# Auto compression (recommended)
@agent(
    model="gpt-4o-mini",
    enable_compression=True  # Default
)
async def assistant(query: str) -> str:
    """Assistant with auto compression"""
    pass

# Custom policy
@agent(
    model="gpt-4o-mini",
    compression_policy=CompressionPolicy(
        strategy="smart",  # Preserve key events
        max_tokens=4000,
        trigger_threshold=0.8  # Compress at 80%
    )
)
async def custom_assistant(query: str) -> str:
    """Assistant with custom compression"""
    pass
```

### Compression Strategies

1. **auto**: Automatically choose best strategy (recommended)
2. **trim**: Simple message trimming (fast, no LLM calls)
3. **summarize**: LLM-based summarization (slower, better quality)
4. **smart**: Preserve key events + summarize routine (best)
5. **off**: Disable compression

### Monitoring Usage

```python
from kagura.core.memory import MemoryManager

memory = MemoryManager(agent_name="assistant")

# Check context usage
stats = memory.get_usage_stats()
print(f"Usage: {stats['usage_ratio']:.1%}")  # e.g., 85.0%
print(f"Tokens: {stats['total_tokens']} / {stats['max_tokens']}")
```

### Best Practices

1. **Use auto strategy** for most cases
2. **Monitor token usage** in production
3. **Adjust max_tokens** based on your needs
4. **Use trim strategy** for cost-sensitive applications (no LLM calls)
5. **Use smart strategy** for conversation quality

### Troubleshooting

**Q: My agent still hits context limits**
A: Lower `max_tokens` or use more aggressive compression

**Q: Compression affects response quality**
A: Use `smart` strategy to preserve key information

**Q: Compression is too slow**
A: Use `trim` strategy (no LLM calls)
```

### APIリファレンス

```markdown
# docs/en/api/compression.md

## Context Compression API

### TokenCounter

Count tokens for various models.

### MessageTrimmer

Trim messages using different strategies.

### ContextSummarizer

Summarize conversation history.

### ContextManager

Unified compression interface.

### CompressionPolicy

Configuration for compression behavior.
```

---

## 🔄 Migration Guide

### 既存コードへの影響

**Good news**: 既存コードは変更不要！

Compression機能はデフォルトで有効ですが、既存の動作を変更しません：

```python
# 既存コード（変更不要）
@agent(model="gpt-4o-mini")
async def my_agent(query: str) -> str:
    pass

# Compressionは自動で有効だが、
# コンテキストが小さいうちは圧縮されない
# → 既存の動作を保持
```

### オプトアウト（圧縮を無効化）

```python
@agent(
    model="gpt-4o-mini",
    enable_compression=False  # Disable compression
)
async def my_agent(query: str) -> str:
    pass
```

---

## 🚀 実装順序

### Week 1: Token Management
1. Day 1-2: TokenCounter実装
2. Day 3-4: ContextMonitor実装
3. Day 5: テスト（15+ tests）
4. Day 6-7: ドキュメント、PR作成

### Week 2: Message Trimming
1. Day 1-2: MessageTrimmer基本実装
2. Day 3: Smart trimming実装
3. Day 4-5: テスト（20+ tests）
4. Day 6-7: ドキュメント、PR作成

### Week 3-4: Summarization
1. Week 3 Day 1-2: Recursive summarization
2. Week 3 Day 3-4: Hierarchical summarization
3. Week 3 Day 5-7: Event-preserving compression
4. Week 4 Day 1-3: テスト（25+ tests）
5. Week 4 Day 4-7: ドキュメント、PR作成

### Week 5: Integration
1. Day 1-2: CompressionPolicy & ContextManager
2. Day 3-4: MemoryManager統合
3. Day 5: @agentデコレータ統合
4. Day 6: 統合テスト（30+ tests）
5. Day 7: 最終ドキュメント、PR作成

---

## 📋 チェックリスト

### Phase 1 完了条件
- [ ] TokenCounter実装（tiktoken統合）
- [ ] ContextMonitor実装
- [ ] 全モデル対応（OpenAI, Claude, Gemini）
- [ ] 15+ tests全パス
- [ ] ドキュメント完成
- [ ] PR作成・レビュー

### Phase 2 完了条件
- [ ] MessageTrimmer実装（4戦略）
- [ ] Smart trimming実装
- [ ] 20+ tests全パス
- [ ] ドキュメント完成
- [ ] PR作成・レビュー

### Phase 3 完了条件
- [ ] ContextSummarizer実装
- [ ] Recursive/Hierarchical/Event-preserving
- [ ] 25+ tests全パス
- [ ] 要約品質検証（人間評価）
- [ ] ドキュメント完成
- [ ] PR作成・レビュー

### Phase 4 完了条件
- [ ] CompressionPolicy実装
- [ ] ContextManager実装
- [ ] MemoryManager統合
- [ ] @agentデコレータ統合
- [ ] 30+ tests全パス
- [ ] 全既存テスト（900+）パス
- [ ] ユーザーガイド完成
- [ ] APIリファレンス完成
- [ ] PR作成・レビュー

### v2.5.0リリース条件
- [ ] 全Phase完了
- [ ] 100+ 新規テスト全パス
- [ ] Pyright 0 errors
- [ ] Ruff linting全パス
- [ ] CI全テストパス
- [ ] ドキュメント完備
- [ ] リリースノート作成
- [ ] GitHub Release作成

---

## 🎓 学びと参考資料

### LangChain References
- [Context Engineering for Agents](https://blog.langchain.com/context-engineering-for-agents/)
- [How to trim messages](https://python.langchain.com/docs/how_to/chatbots_memory/)
- [LangGraph Memory Management](https://langchain-ai.github.io/langgraph/concepts/memory/)

### Token Counting
- [tiktoken](https://github.com/openai/tiktoken) - OpenAI's tokenizer
- [Token counting best practices](https://platform.openai.com/docs/guides/token-counting)

### Summarization Techniques
- Recursive summarization (map-reduce)
- Hierarchical summarization (multi-level)
- Event-preserving compression

---

**このRFCにより、Kagura AIは長時間会話対応のProduction-readyフレームワークになります！**
