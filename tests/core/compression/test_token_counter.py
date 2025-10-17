"""Tests for TokenCounter"""

import pytest

from kagura.core.compression import TokenCountError, TokenCounter


class TestTokenCounter:
    """Tests for TokenCounter"""

    @pytest.fixture
    def counter(self):
        """Create TokenCounter instance"""
        return TokenCounter(model="gpt-5-mini")

    def test_init_default_model(self):
        """Test initialization with default model"""
        counter = TokenCounter()
        assert counter.model == "gpt-5-mini"
        assert counter._encoder is not None

    def test_init_custom_model(self):
        """Test initialization with custom model"""
        counter = TokenCounter(model="claude-3-5-sonnet")
        assert counter.model == "claude-3-5-sonnet"
        assert counter._encoder is not None

    def test_init_gpt4o_model(self):
        """Test initialization with GPT-4o model"""
        counter = TokenCounter(model="gpt-4o")
        assert counter.model == "gpt-4o"
        assert counter._encoder is not None

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
        text = "This is a longer text with multiple sentences. " * 20
        tokens = counter.count_tokens(text)
        assert tokens > 100
        assert tokens < 500

    def test_count_tokens_japanese(self, counter):
        """Test counting tokens in Japanese text"""
        text = "こんにちは、世界！"
        tokens = counter.count_tokens(text)
        assert tokens > 0

    def test_count_tokens_messages_empty(self, counter):
        """Test counting tokens in empty message list"""
        tokens = counter.count_tokens_messages([])
        assert tokens == 3  # Reply priming only

    def test_count_tokens_messages_basic(self, counter):
        """Test counting tokens in basic messages"""
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"},
            {"role": "assistant", "content": "Hi there!"},
        ]

        tokens = counter.count_tokens_messages(messages)
        assert tokens > 20  # Includes message overhead

    def test_count_tokens_messages_with_name(self, counter):
        """Test counting tokens in messages with name field"""
        messages = [
            {"role": "user", "name": "Alice", "content": "Hello!"},
        ]

        tokens = counter.count_tokens_messages(messages)
        assert tokens > 5

    def test_count_tokens_messages_many(self, counter):
        """Test counting tokens in many messages"""
        messages = [{"role": "user", "content": "Message"} for _ in range(100)]

        tokens = counter.count_tokens_messages(messages)
        assert tokens > 500  # At least 5 tokens per message

    def test_estimate_context_size_basic(self, counter):
        """Test estimating context size"""
        messages = [{"role": "user", "content": "Hello"}]

        estimate = counter.estimate_context_size(
            messages, system_prompt="You are helpful.", max_tokens=1000
        )

        assert "prompt_tokens" in estimate
        assert "completion_tokens" in estimate
        assert "total_tokens" in estimate
        assert estimate["completion_tokens"] == 1000
        assert estimate["total_tokens"] == estimate["prompt_tokens"] + 1000
        assert estimate["prompt_tokens"] > 0

    def test_estimate_context_size_no_system_prompt(self, counter):
        """Test estimating context size without system prompt"""
        messages = [{"role": "user", "content": "Hello"}]

        estimate = counter.estimate_context_size(messages, max_tokens=500)

        assert estimate["prompt_tokens"] > 0
        assert estimate["completion_tokens"] == 500

    def test_should_compress_below_threshold(self, counter):
        """Test should_compress when below threshold"""
        assert not counter.should_compress(
            current_tokens=1000, max_tokens=10000, threshold=0.8
        )

    def test_should_compress_above_threshold(self, counter):
        """Test should_compress when above threshold"""
        assert counter.should_compress(
            current_tokens=9000, max_tokens=10000, threshold=0.8
        )

    def test_should_compress_at_threshold(self, counter):
        """Test should_compress exactly at threshold"""
        assert counter.should_compress(
            current_tokens=8000, max_tokens=10000, threshold=0.8
        )

    def test_should_compress_different_threshold(self, counter):
        """Test should_compress with different threshold"""
        # 50% threshold
        assert not counter.should_compress(
            current_tokens=4000, max_tokens=10000, threshold=0.5
        )
        assert counter.should_compress(
            current_tokens=6000, max_tokens=10000, threshold=0.5
        )

    def test_should_compress_zero_max_tokens(self, counter):
        """Test should_compress with zero max_tokens"""
        assert not counter.should_compress(
            current_tokens=1000, max_tokens=0, threshold=0.8
        )

    def test_get_model_limits_gpt4o_mini(self, counter):
        """Test getting model limits for GPT-4o-mini"""
        limits = counter.get_model_limits("gpt-5-mini")
        assert limits["context_window"] == 128_000
        assert limits["max_completion"] == 16_384

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
        limits = counter.get_model_limits("unknown-model-xyz")
        assert limits["context_window"] == 8_000  # Default
        assert limits["max_completion"] == 2_000  # Default


# Total: 25 tests for TokenCounter
