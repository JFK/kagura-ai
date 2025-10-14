"""Tests for ContextMonitor"""

import pytest

from kagura.core.compression import ContextMonitor, ContextUsage, TokenCounter


class TestContextMonitor:
    """Tests for ContextMonitor"""

    @pytest.fixture
    def counter(self):
        """Create TokenCounter instance"""
        return TokenCounter(model="gpt-4o-mini")

    @pytest.fixture
    def monitor(self, counter):
        """Create ContextMonitor instance"""
        return ContextMonitor(counter, max_tokens=10000)

    def test_init_with_max_tokens(self, counter):
        """Test initialization with explicit max_tokens"""
        monitor = ContextMonitor(counter, max_tokens=5000)
        assert monitor.max_tokens == 5000
        assert monitor.counter is counter

    def test_init_auto_detect_max_tokens(self, counter):
        """Test initialization with auto-detected max_tokens"""
        monitor = ContextMonitor(counter, max_tokens=None)
        # Should auto-detect from model (128k - 4k = 124k for gpt-4o-mini)
        assert monitor.max_tokens > 100_000
        assert monitor.max_tokens == 124_000  # 128k - 4k

    def test_check_usage_empty_messages(self, monitor):
        """Test checking usage with empty messages"""
        usage = monitor.check_usage([], system_prompt="")

        assert isinstance(usage, ContextUsage)
        assert usage.prompt_tokens >= 0
        assert usage.completion_tokens == 4000
        assert usage.total_tokens >= 0
        assert usage.max_tokens == 10000
        assert 0.0 <= usage.usage_ratio <= 1.0
        assert not usage.should_compress

    def test_check_usage_basic_messages(self, monitor):
        """Test checking usage with basic messages"""
        messages = [{"role": "user", "content": "Hello"}]

        usage = monitor.check_usage(messages, system_prompt="Be helpful.")

        assert usage.prompt_tokens > 0
        assert usage.total_tokens > usage.prompt_tokens
        assert usage.usage_ratio < 0.1  # Should be very low
        assert not usage.should_compress

    def test_check_usage_many_messages(self, monitor):
        """Test checking usage with many messages"""
        messages = [{"role": "user", "content": "Message " * 50} for _ in range(100)]

        usage = monitor.check_usage(messages, system_prompt="")

        assert usage.prompt_tokens > 1000
        assert usage.usage_ratio > 0.1
        # Should not compress yet (below 80% threshold)
        assert not usage.should_compress

    def test_check_usage_should_compress_false(self, monitor):
        """Test should_compress is False when usage is low"""
        messages = [{"role": "user", "content": "Hello"}]

        usage = monitor.check_usage(messages)

        assert not usage.should_compress
        assert usage.usage_ratio < 0.8

    def test_check_usage_should_compress_true(self):
        """Test should_compress is True when usage is high"""
        counter = TokenCounter(model="gpt-4o-mini")
        monitor = ContextMonitor(counter, max_tokens=1000)  # Small limit

        messages = [{"role": "user", "content": "Long message " * 100} for _ in range(10)]

        usage = monitor.check_usage(messages)

        assert usage.should_compress
        assert usage.usage_ratio > 0.8

    def test_check_usage_with_system_prompt(self, monitor):
        """Test checking usage with system prompt"""
        messages = [{"role": "user", "content": "Hello"}]
        system_prompt = "You are a helpful assistant. " * 10

        usage = monitor.check_usage(messages, system_prompt=system_prompt)

        # System prompt should add to token count
        usage_no_system = monitor.check_usage(messages, system_prompt="")
        assert usage.prompt_tokens > usage_no_system.prompt_tokens

    def test_get_max_tokens_calculation(self, counter):
        """Test _get_max_tokens calculation"""
        monitor = ContextMonitor(counter, max_tokens=None)

        # For gpt-4o-mini: 128k context - 4k reserved = 124k
        assert monitor.max_tokens == 124_000

    def test_different_models(self):
        """Test monitor with different models"""
        # GPT-4o-mini
        counter1 = TokenCounter(model="gpt-4o-mini")
        monitor1 = ContextMonitor(counter1, max_tokens=None)
        assert monitor1.max_tokens == 124_000

        # Claude
        counter2 = TokenCounter(model="claude-3-5-sonnet")
        monitor2 = ContextMonitor(counter2, max_tokens=None)
        assert monitor2.max_tokens == 196_000  # 200k - 4k

        # Gemini
        counter3 = TokenCounter(model="gemini-1.5-pro")
        monitor3 = ContextMonitor(counter3, max_tokens=None)
        assert monitor3.max_tokens == 1_996_000  # 2M - 4k


# Total: 10 tests for ContextMonitor
