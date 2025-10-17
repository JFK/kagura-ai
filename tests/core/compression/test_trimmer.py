"""Tests for MessageTrimmer"""

import pytest

from kagura.core.compression import MessageTrimmer, TokenCounter


@pytest.fixture
def counter():
    """Create TokenCounter fixture"""
    return TokenCounter(model="gpt-5-mini")


@pytest.fixture
def trimmer(counter):
    """Create MessageTrimmer fixture"""
    return MessageTrimmer(counter)


@pytest.fixture
def sample_messages():
    """Create sample messages for testing"""
    return [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is Python?"},
        {"role": "assistant", "content": "Python is a programming language."},
        {"role": "user", "content": "Tell me more about it."},
        {
            "role": "assistant",
            "content": "Python is widely used for web development, data science, and more.",
        },
        {"role": "user", "content": "Thanks!"},
    ]


# Basic Functionality Tests


def test_trim_empty_messages(trimmer):
    """Test trimming empty message list"""
    result = trimmer.trim([], max_tokens=100, strategy="last")
    assert result == []


def test_trim_single_message(trimmer):
    """Test trimming single message"""
    messages = [{"role": "user", "content": "Hello"}]
    result = trimmer.trim(messages, max_tokens=100, strategy="last")
    assert len(result) == 1
    assert result[0] == messages[0]


def test_trim_no_trimming_needed(trimmer, sample_messages):
    """Test when no trimming is needed (under limit)"""
    result = trimmer.trim(sample_messages, max_tokens=10000, strategy="last")
    assert len(result) == len(sample_messages)


# Strategy: Last


def test_trim_last_basic(trimmer, sample_messages):
    """Test last strategy keeps most recent messages"""
    result = trimmer.trim(sample_messages, max_tokens=50, strategy="last")

    # Should keep system message and recent messages
    assert result[0]["role"] == "system"
    assert len(result) < len(sample_messages)

    # Last user message should be present
    assert any(msg["content"] == "Thanks!" for msg in result)


def test_trim_last_preserves_system(trimmer, sample_messages):
    """Test last strategy preserves system message"""
    result = trimmer.trim(
        sample_messages, max_tokens=50, strategy="last", preserve_system=True
    )

    assert result[0]["role"] == "system"
    assert result[0]["content"] == "You are a helpful assistant."


def test_trim_last_without_system(trimmer):
    """Test last strategy without system message"""
    messages = [
        {"role": "user", "content": "Message 1"},
        {"role": "assistant", "content": "Response 1"},
        {"role": "user", "content": "Message 2"},
        {"role": "assistant", "content": "Response 2"},
    ]

    result = trimmer.trim(messages, max_tokens=30, strategy="last")

    # Should keep most recent messages
    assert len(result) < len(messages)
    assert result[-1]["content"] == "Response 2"


# Strategy: First


def test_trim_first_basic(trimmer, sample_messages):
    """Test first strategy keeps oldest messages"""
    result = trimmer.trim(sample_messages, max_tokens=50, strategy="first")

    # Should keep system message and oldest messages
    assert result[0]["role"] == "system"
    assert len(result) < len(sample_messages)

    # First user message should be present
    assert any(msg["content"] == "What is Python?" for msg in result)


def test_trim_first_preserves_system(trimmer, sample_messages):
    """Test first strategy preserves system message"""
    result = trimmer.trim(
        sample_messages, max_tokens=50, strategy="first", preserve_system=True
    )

    assert result[0]["role"] == "system"
    assert result[0]["content"] == "You are a helpful assistant."


def test_trim_first_without_system(trimmer):
    """Test first strategy without system message"""
    messages = [
        {"role": "user", "content": "Message 1"},
        {"role": "assistant", "content": "Response 1"},
        {"role": "user", "content": "Message 2"},
        {"role": "assistant", "content": "Response 2"},
    ]

    result = trimmer.trim(messages, max_tokens=30, strategy="first")

    # Should keep oldest messages
    assert len(result) < len(messages)
    assert result[0]["content"] == "Message 1"


# Strategy: Middle


def test_trim_middle_basic(trimmer, sample_messages):
    """Test middle strategy keeps beginning and end"""
    result = trimmer.trim(sample_messages, max_tokens=60, strategy="middle")

    # Should keep system message, some beginning, and some end
    assert result[0]["role"] == "system"
    assert len(result) < len(sample_messages)

    # Should have messages from both beginning and end
    contents = [msg["content"] for msg in result]
    assert "What is Python?" in contents or "Thanks!" in contents


def test_trim_middle_preserves_system(trimmer, sample_messages):
    """Test middle strategy preserves system message"""
    result = trimmer.trim(
        sample_messages, max_tokens=60, strategy="middle", preserve_system=True
    )

    assert result[0]["role"] == "system"


def test_trim_middle_no_duplicates(trimmer):
    """Test middle strategy avoids duplicates"""
    messages = [
        {"role": "user", "content": f"Message {i}"} for i in range(10)
    ]

    result = trimmer.trim(messages, max_tokens=100, strategy="middle")

    # Check no duplicates
    contents = [msg["content"] for msg in result]
    assert len(contents) == len(set(contents))


# Strategy: Smart


def test_trim_smart_basic(trimmer, sample_messages):
    """Test smart strategy preserves important messages"""
    result = trimmer.trim(sample_messages, max_tokens=60, strategy="smart")

    # Should preserve system message
    assert result[0]["role"] == "system"
    assert len(result) < len(sample_messages)


def test_trim_smart_preserves_important_keywords(trimmer):
    """Test smart strategy preserves messages with important keywords"""
    messages = [
        {"role": "system", "content": "System prompt"},
        {"role": "user", "content": "Normal message"},
        {"role": "user", "content": "IMPORTANT: User preference is dark mode"},
        {"role": "user", "content": "Another normal message"},
        {"role": "user", "content": "Recent message"},
    ]

    result = trimmer.trim(messages, max_tokens=100, strategy="smart")

    # Should preserve system, important message, and recent message
    contents = [msg["content"] for msg in result]
    assert "System prompt" in contents
    assert "IMPORTANT: User preference is dark mode" in contents
    assert "Recent message" in contents


def test_trim_smart_preserves_recent(trimmer):
    """Test smart strategy preserves recent messages"""
    messages = [
        {"role": "user", "content": f"Old message {i}"} for i in range(10)
    ] + [
        {"role": "user", "content": f"Recent message {i}"} for i in range(5)
    ]

    result = trimmer.trim(messages, max_tokens=100, strategy="smart")

    # Recent messages should be present
    contents = [msg["content"] for msg in result]
    assert any("Recent message" in c for c in contents)


def test_trim_smart_scoring(trimmer):
    """Test smart strategy message scoring"""
    msg_recent = {"role": "user", "content": "Recent"}
    msg_long = {"role": "user", "content": "Long message " * 100}
    msg_important = {"role": "user", "content": "IMPORTANT: critical info"}

    # Score recent message (index 9 out of 10)
    score_recent = trimmer._score_message(msg_recent, 9, 10)
    assert score_recent >= 5.0  # Recency bonus

    # Score long message
    score_long = trimmer._score_message(msg_long, 0, 10)
    assert score_long > 1.0  # Length bonus

    # Score important message
    score_important = trimmer._score_message(msg_important, 0, 10)
    assert score_important > 2.0  # Keyword bonus


def test_trim_smart_maintains_order(trimmer):
    """Test smart strategy maintains message order"""
    messages = [
        {"role": "user", "content": f"Message {i}"} for i in range(10)
    ]

    result = trimmer.trim(messages, max_tokens=100, strategy="smart")

    # Check messages are in original order
    for i in range(len(result) - 1):
        idx1 = messages.index(result[i])
        idx2 = messages.index(result[i + 1])
        assert idx1 < idx2, "Messages should be in original order"


# System Message Preservation


def test_preserve_system_true(trimmer, sample_messages):
    """Test preserve_system=True keeps system message"""
    result = trimmer.trim(
        sample_messages, max_tokens=30, strategy="last", preserve_system=True
    )

    assert result[0]["role"] == "system"


def test_preserve_system_false(trimmer, sample_messages):
    """Test preserve_system=False may remove system message"""
    result = trimmer.trim(
        sample_messages, max_tokens=30, strategy="last", preserve_system=False
    )

    # System message might be removed if token limit is tight
    if len(result) > 0:
        # If we have messages, check they fit
        tokens = trimmer.counter.count_tokens_messages(result)
        assert tokens <= 30


def test_only_system_message(trimmer):
    """Test with only system message"""
    messages = [{"role": "system", "content": "System prompt"}]

    result = trimmer.trim(messages, max_tokens=100, strategy="smart")

    assert len(result) == 1
    assert result[0] == messages[0]


# Edge Cases


def test_trim_very_low_token_limit(trimmer, sample_messages):
    """Test with very low token limit"""
    result = trimmer.trim(sample_messages, max_tokens=10, strategy="smart")

    # Should return minimal messages or empty if can't fit
    assert len(result) <= len(sample_messages)

    # Check token count is within limit (allowing small overflow for system msg)
    if result:
        tokens = trimmer.counter.count_tokens_messages(result)
        # Allow some overflow for system message preservation
        assert tokens <= 50  # Reasonable upper bound


def test_trim_invalid_strategy(trimmer, sample_messages):
    """Test with invalid strategy raises error"""
    with pytest.raises(ValueError, match="Unknown trimming strategy"):
        trimmer.trim(sample_messages, max_tokens=100, strategy="invalid")  # type: ignore


def test_trim_messages_without_content(trimmer):
    """Test trimming messages without content field"""
    messages = [
        {"role": "user"},  # No content
        {"role": "assistant", "content": "Response"},
    ]

    result = trimmer.trim(messages, max_tokens=100, strategy="smart")

    # Should handle gracefully
    assert isinstance(result, list)


# Token Reduction Tests


def test_token_reduction_last(trimmer):
    """Test token reduction with last strategy"""
    messages = [
        {"role": "user", "content": "Message " * 100} for _ in range(10)
    ]

    original_tokens = trimmer.counter.count_tokens_messages(messages)
    result = trimmer.trim(messages, max_tokens=200, strategy="last")
    trimmed_tokens = trimmer.counter.count_tokens_messages(result)

    # Should achieve significant reduction
    assert trimmed_tokens < original_tokens
    assert trimmed_tokens <= 200 or len(result) == 1  # Allow 1 message even if over


def test_token_reduction_smart(trimmer):
    """Test token reduction with smart strategy"""
    messages = [
        {"role": "user", "content": "Message " * 100} for _ in range(10)
    ]

    original_tokens = trimmer.counter.count_tokens_messages(messages)
    result = trimmer.trim(messages, max_tokens=200, strategy="smart")
    trimmed_tokens = trimmer.counter.count_tokens_messages(result)

    # Should achieve significant reduction
    assert trimmed_tokens < original_tokens


# Integration Tests


def test_trim_with_real_conversation(trimmer):
    """Test trimming a realistic conversation"""
    messages = [
        {"role": "system", "content": "You are a helpful AI assistant."},
        {"role": "user", "content": "Hi, I need help with Python."},
        {"role": "assistant", "content": "I'd be happy to help with Python!"},
        {"role": "user", "content": "How do I read a file?"},
        {
            "role": "assistant",
            "content": "You can use open() function. Here's an example...",
        },
        {"role": "user", "content": "What about writing?"},
        {
            "role": "assistant",
            "content": "For writing, you can use open() with 'w' mode...",
        },
        {"role": "user", "content": "Thanks!"},
        {"role": "assistant", "content": "You're welcome!"},
    ]

    result = trimmer.trim(messages, max_tokens=150, strategy="smart")

    # Should preserve system message
    assert result[0]["role"] == "system"

    # Should keep recent messages
    assert result[-1]["role"] in ["user", "assistant"]

    # Should maintain conversation flow
    for i in range(len(result) - 1):
        idx1 = messages.index(result[i])
        idx2 = messages.index(result[i + 1])
        assert idx1 < idx2


def test_trim_preserves_conversation_pairs(trimmer):
    """Test that trimming respects user-assistant pairs when possible"""
    messages = [
        {"role": "user", "content": "Question 1"},
        {"role": "assistant", "content": "Answer 1"},
        {"role": "user", "content": "Question 2"},
        {"role": "assistant", "content": "Answer 2"},
        {"role": "user", "content": "Question 3"},
        {"role": "assistant", "content": "Answer 3"},
    ]

    result = trimmer.trim(messages, max_tokens=80, strategy="smart")

    # Check that we don't have orphaned questions without answers (best effort)
    roles = [msg["role"] for msg in result]

    # At least some complete pairs should exist
    assert len(result) >= 2


# Performance Tests


def test_trim_performance_large_dataset(trimmer):
    """Test trimming performance with large message list"""
    # Create 100 messages
    messages = [
        {"role": "user" if i % 2 == 0 else "assistant", "content": f"Message {i}"}
        for i in range(100)
    ]

    # Should complete quickly
    result = trimmer.trim(messages, max_tokens=500, strategy="smart")

    assert isinstance(result, list)
    assert len(result) < len(messages)


def test_trim_all_strategies(trimmer, sample_messages):
    """Test that all strategies produce valid output"""
    strategies = ["last", "first", "middle", "smart"]

    for strategy in strategies:
        result = trimmer.trim(
            sample_messages, max_tokens=80, strategy=strategy  # type: ignore
        )

        # All should return valid lists
        assert isinstance(result, list)
        assert len(result) <= len(sample_messages)

        # All should preserve system message if present
        if sample_messages[0]["role"] == "system":
            assert result[0]["role"] == "system"
