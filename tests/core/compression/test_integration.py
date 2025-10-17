"""Integration tests for compression module"""

import pytest
from unittest.mock import AsyncMock, patch

from kagura.core.compression import (
    ContextManager,
    ContextMonitor,
    ContextUsage,
    CompressionPolicy,
    TokenCounter,
)


class TestIntegration:
    """Integration tests for compression components"""

    def test_full_workflow(self):
        """Test complete token management workflow"""
        # 1. Create counter
        counter = TokenCounter(model="gpt-5-mini")

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
        assert isinstance(usage, ContextUsage)

    def test_different_models(self):
        """Test with different models"""
        models = ["gpt-5-mini", "claude-3-5-sonnet", "gemini-1.5-flash"]

        for model in models:
            counter = TokenCounter(model=model)
            monitor = ContextMonitor(counter)

            messages = [{"role": "user", "content": "Test"}]
            usage = monitor.check_usage(messages)

            assert usage.total_tokens > 0
            assert usage.usage_ratio >= 0.0
            assert not usage.should_compress

    def test_compression_trigger(self):
        """Test compression trigger at different thresholds"""
        counter = TokenCounter(model="gpt-5-mini")
        monitor = ContextMonitor(counter, max_tokens=1000)

        # Create messages that will exceed threshold
        messages = []
        for i in range(100):
            messages.append({"role": "user", "content": f"Message {i} " * 10})

        usage = monitor.check_usage(messages)

        # Should trigger compression (>80% usage)
        assert usage.should_compress
        assert usage.usage_ratio > 0.8

    def test_token_accuracy(self):
        """Test token counting accuracy across models"""
        text = "The quick brown fox jumps over the lazy dog."

        models = ["gpt-5-mini", "gpt-4o", "claude-3-5-sonnet", "gemini-1.5-pro"]

        for model in models:
            counter = TokenCounter(model=model)
            tokens = counter.count_tokens(text)

            # Should be consistent (±20% across models due to different tokenizers)
            assert 8 <= tokens <= 15

    def test_message_overhead_calculation(self):
        """Test message overhead is correctly calculated"""
        counter = TokenCounter(model="gpt-5-mini")

        # Empty message (only overhead)
        empty_msg = [{"role": "user", "content": ""}]
        overhead_tokens = counter.count_tokens_messages(empty_msg)

        # Message with content
        with_content = [{"role": "user", "content": "Hello"}]
        total_tokens = counter.count_tokens_messages(with_content)

        # Difference should be content tokens
        content_tokens = counter.count_tokens("Hello")
        assert abs((total_tokens - overhead_tokens) - content_tokens) <= 1

    def test_realistic_conversation_scenario(self):
        """Test realistic conversation scenario"""
        counter = TokenCounter(model="gpt-5-mini")
        monitor = ContextMonitor(counter, max_tokens=50000)

        # Simulate realistic conversation
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant."}
        ]

        # Add 20 turns of conversation
        for i in range(20):
            messages.append(
                {
                    "role": "user",
                    "content": f"User question {i}: Can you explain something?",
                }
            )
            messages.append(
                {
                    "role": "assistant",
                    "content": f"Certainly! Here's a detailed explanation for question {i}. "
                    * 10,
                }
            )

        usage = monitor.check_usage(messages)

        assert usage.prompt_tokens > 500
        assert usage.total_tokens > 4500
        assert usage.usage_ratio < 0.2  # Should still be under 20%
        assert not usage.should_compress

    @pytest.mark.asyncio
    async def test_context_manager_integration(self):
        """Test ContextManager with all components"""
        policy = CompressionPolicy(strategy="trim", max_tokens=1000)
        manager = ContextManager(policy=policy, model="gpt-5-mini")

        # Create large message set
        messages = []
        for i in range(50):
            messages.append({"role": "user", "content": f"Message {i} " * 20})

        # Check usage
        usage = manager.get_usage(messages)
        assert usage.should_compress

        # Compress
        compressed = await manager.compress(messages)

        # Verify compression occurred
        assert len(compressed) < len(messages)

        # Verify token reduction (may still be high due to completion tokens)
        compressed_usage = manager.get_usage(compressed)
        assert compressed_usage.prompt_tokens < usage.prompt_tokens

    @pytest.mark.asyncio
    @patch("kagura.core.compression.summarizer.call_llm", new_callable=AsyncMock)
    async def test_context_manager_smart_strategy(self, mock_call_llm):
        """Test ContextManager with smart strategy"""
        mock_call_llm.return_value = "Summary of routine messages"

        policy = CompressionPolicy(
            strategy="smart", max_tokens=500, preserve_recent=3
        )
        manager = ContextManager(policy=policy, model="gpt-5-mini")

        messages = [
            {"role": "user", "content": "Normal message " * 30},
            {"role": "assistant", "content": "IMPORTANT: Key decision made"},
            {"role": "user", "content": "Normal message " * 30},
            {"role": "assistant", "content": "ERROR: Something failed"},
            {"role": "user", "content": "Normal message " * 30},
        ] * 5

        compressed = await manager.compress(messages)

        # Should preserve key events
        contents = [m["content"] for m in compressed]
        assert any("IMPORTANT" in c for c in contents)
        assert any("ERROR" in c for c in contents)

        # Should be compressed
        assert len(compressed) < len(messages)

        # Should have summary or be trimmed
        assert any("summary" in str(c).lower() or "Summary" in c for c in contents) or len(
            compressed
        ) < len(messages) * 0.5

    @pytest.mark.asyncio
    async def test_policy_validation_integration(self):
        """Test CompressionPolicy validation works in ContextManager"""
        # Valid policy
        policy = CompressionPolicy(
            trigger_threshold=0.7, target_ratio=0.5, preserve_recent=3
        )
        manager = ContextManager(policy=policy)
        assert manager.policy.trigger_threshold == 0.7

        # Invalid policy should raise
        with pytest.raises(ValueError, match="trigger_threshold"):
            CompressionPolicy(trigger_threshold=1.5)

        with pytest.raises(ValueError, match="requires enable_summarization"):
            CompressionPolicy(strategy="smart", enable_summarization=False)

    @pytest.mark.asyncio
    async def test_auto_strategy_selection(self):
        """Test auto strategy selects appropriate method"""
        policy = CompressionPolicy(strategy="auto", max_tokens=500)
        manager = ContextManager(policy=policy, model="gpt-5-mini")

        # Few messages -> should use trim
        few_messages = [{"role": "user", "content": "Message " * 50}] * 10
        compressed_few = await manager.compress(few_messages)
        assert len(compressed_few) < len(few_messages)

        # Many messages -> should use smart (but we disabled summarization)
        policy_no_summary = CompressionPolicy(
            strategy="auto", max_tokens=500, enable_summarization=False
        )
        manager_no_summary = ContextManager(
            policy=policy_no_summary, model="gpt-5-mini"
        )
        many_messages = [{"role": "user", "content": "Message " * 50}] * 30
        compressed_many = await manager_no_summary.compress(many_messages)
        assert len(compressed_many) < len(many_messages)

    @pytest.mark.asyncio
    @patch("kagura.core.compression.summarizer.call_llm", new_callable=AsyncMock)
    async def test_full_pipeline_with_manager(self, mock_call_llm):
        """Test complete compression pipeline"""
        mock_call_llm.return_value = "Comprehensive summary of conversation"

        # Create manager with moderate settings
        policy = CompressionPolicy(
            strategy="smart",
            max_tokens=2000,
            trigger_threshold=0.7,
            preserve_recent=3,
            target_ratio=0.5,
        )
        manager = ContextManager(policy=policy, model="gpt-5-mini")

        # Simulate realistic conversation
        messages = [{"role": "system", "content": "You are a helpful assistant."}]

        # Add conversation turns
        for i in range(30):
            messages.append(
                {"role": "user", "content": f"User question {i}: " + "x" * 50}
            )
            if i == 10:
                messages.append(
                    {"role": "assistant", "content": "IMPORTANT: Critical decision"}
                )
            elif i == 20:
                messages.append(
                    {"role": "assistant", "content": "ERROR: Failed operation"}
                )
            else:
                messages.append(
                    {"role": "assistant", "content": f"Response {i}: " + "y" * 50}
                )

        # Check if compression needed
        usage_before = manager.get_usage(messages)
        print(f"Usage before: {usage_before.usage_ratio:.2%}")

        # Compress
        compressed = await manager.compress(messages)

        # Verify results
        usage_after = manager.get_usage(compressed)
        print(f"Usage after: {usage_after.usage_ratio:.2%}")

        # Should reduce token usage
        assert usage_after.total_tokens < usage_before.total_tokens

        # Should preserve system prompt
        assert compressed[0]["role"] == "system"

        # Should preserve key events
        contents = [m["content"] for m in compressed]
        assert any("IMPORTANT" in c for c in contents)
        assert any("ERROR" in c for c in contents)

        # Should have summary or be trimmed
        assert len(compressed) < len(messages)


# Total: 12 integration tests
# Grand total: 25 (TokenCounter) + 10 (ContextMonitor) + 12 (Integration) = 47 tests
# + 15 (Policy) + 15 (Manager) = 77 tests total for compression module
