"""Tests for ContextManager"""

import pytest
from unittest.mock import AsyncMock, patch

from kagura.core.compression import (
    ContextManager,
    CompressionPolicy,
)


@pytest.mark.asyncio
async def test_manager_init_default():
    """Test manager initialization with defaults"""
    manager = ContextManager()

    assert manager.policy.strategy == "smart"
    assert manager.counter is not None
    assert manager.monitor is not None
    assert manager.trimmer is not None
    assert manager.summarizer is not None


@pytest.mark.asyncio
async def test_manager_init_custom_policy():
    """Test manager initialization with custom policy"""
    policy = CompressionPolicy(strategy="trim", enable_summarization=False)
    manager = ContextManager(policy=policy)

    assert manager.policy.strategy == "trim"
    assert manager.summarizer is None  # Disabled


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
async def test_compress_summarize_strategy(mock_call_llm):
    """Test summarize strategy"""
    mock_call_llm.return_value = "Summary"

    policy = CompressionPolicy(strategy="summarize", max_tokens=500)
    manager = ContextManager(policy=policy)

    messages = [{"role": "user", "content": "Message " * 20}] * 20

    compressed = await manager.compress(messages)

    # Should be compressed
    assert len(compressed) < len(messages)

    # Should have summary message
    assert any("summary" in str(m["content"]).lower() for m in compressed)


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


@pytest.mark.asyncio
@patch("kagura.core.compression.summarizer.call_llm", new_callable=AsyncMock)
async def test_compress_auto_strategy_many_messages(mock_call_llm):
    """Test auto strategy with many messages (uses smart)"""
    mock_call_llm.return_value = "Summary"

    policy = CompressionPolicy(strategy="auto", max_tokens=500)
    manager = ContextManager(policy=policy)

    # More than 20 messages -> should use smart
    messages = [{"role": "user", "content": "Message " * 20}] * 30

    compressed = await manager.compress(messages)

    # Should be compressed
    assert len(compressed) < len(messages)


@pytest.mark.asyncio
async def test_compress_auto_strategy_few_messages():
    """Test auto strategy with few messages (uses trim)"""
    policy = CompressionPolicy(strategy="auto", max_tokens=500)
    manager = ContextManager(policy=policy)

    # 15 messages -> should use trim
    messages = [{"role": "user", "content": "Message " * 50}] * 15

    compressed = await manager.compress(messages)

    # Should be compressed
    assert len(compressed) < len(messages)


def test_get_usage():
    """Test usage statistics"""
    manager = ContextManager()

    messages = [{"role": "user", "content": "Test"}] * 10

    usage = manager.get_usage(messages)

    assert usage.total_tokens > 0
    assert usage.max_tokens > 0
    assert usage.usage_ratio >= 0.0  # Can exceed 1.0 if over limit
    assert isinstance(usage.should_compress, bool)


@pytest.mark.asyncio
async def test_compress_with_system_prompt():
    """Test compression with system prompt"""
    # Use trim strategy to avoid LLM calls
    policy = CompressionPolicy(strategy="trim", max_tokens=500)
    manager = ContextManager(policy=policy)

    messages = [{"role": "user", "content": "Message " * 50}] * 20
    system_prompt = "You are a helpful assistant."

    compressed = await manager.compress(messages, system_prompt)

    # Should be compressed
    assert len(compressed) < len(messages)


@pytest.mark.asyncio
async def test_trim_fallback_when_summarizer_disabled():
    """Test fallback to trim when summarizer is disabled"""
    policy = CompressionPolicy(
        strategy="summarize", enable_summarization=True, max_tokens=500
    )
    manager = ContextManager(policy=policy)

    # Disable summarizer manually to test fallback
    manager.summarizer = None

    messages = [{"role": "user", "content": "Message " * 50}] * 20

    compressed = await manager.compress(messages)

    # Should still work (fallback to trim)
    assert len(compressed) < len(messages)


@pytest.mark.asyncio
@patch("kagura.core.compression.summarizer.call_llm", new_callable=AsyncMock)
async def test_compress_preserve_recent(mock_call_llm):
    """Test that recent messages are preserved in summarize strategy"""
    mock_call_llm.return_value = "Summary of old messages"

    policy = CompressionPolicy(
        strategy="summarize", max_tokens=500, preserve_recent=3
    )
    manager = ContextManager(policy=policy)

    messages = [
        {"role": "user", "content": f"Old message {i} " * 20} for i in range(10)
    ] + [
        {"role": "user", "content": f"Recent message {i}"} for i in range(3)
    ]

    compressed = await manager.compress(messages)

    # Should have summary + recent messages
    contents = [m["content"] for m in compressed]

    # Recent messages should be preserved
    assert any("Recent message 0" in c for c in contents)
    assert any("Recent message 1" in c for c in contents)
    assert any("Recent message 2" in c for c in contents)
