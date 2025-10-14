"""Integration tests for compression module Phase 1"""

import pytest

from kagura.core.compression import ContextMonitor, ContextUsage, TokenCounter


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
        assert isinstance(usage, ContextUsage)

    def test_different_models(self):
        """Test with different models"""
        models = ["gpt-4o-mini", "claude-3-5-sonnet", "gemini-1.5-flash"]

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
        counter = TokenCounter(model="gpt-4o-mini")
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

        models = ["gpt-4o-mini", "gpt-4o", "claude-3-5-sonnet", "gemini-1.5-pro"]

        for model in models:
            counter = TokenCounter(model=model)
            tokens = counter.count_tokens(text)

            # Should be consistent (±20% across models due to different tokenizers)
            assert 8 <= tokens <= 15

    def test_message_overhead_calculation(self):
        """Test message overhead is correctly calculated"""
        counter = TokenCounter(model="gpt-4o-mini")

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
        counter = TokenCounter(model="gpt-4o-mini")
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


# Total: 7 integration tests
# Grand total: 25 (TokenCounter) + 10 (ContextMonitor) + 7 (Integration) = 42 tests
