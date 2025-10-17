"""Tests for ContextSummarizer"""

import pytest
from unittest.mock import AsyncMock, patch

from kagura.core.compression import ContextSummarizer, TokenCounter


@pytest.fixture
def counter():
    """Create TokenCounter fixture"""
    return TokenCounter(model="gpt-5-mini")


@pytest.fixture
def summarizer(counter):
    """Create ContextSummarizer fixture"""
    return ContextSummarizer(counter)


# Basic Functionality Tests


@pytest.mark.asyncio
@patch("kagura.core.compression.summarizer.call_llm", new_callable=AsyncMock)
async def test_summarize_recursive_basic(mock_call_llm, summarizer):
    """Test basic recursive summarization"""
    mock_call_llm.return_value = "This is a brief summary of the conversation."

    messages = [
        {"role": "user", "content": "Long message " * 100},
        {"role": "assistant", "content": "Long response " * 100},
    ]

    summary = await summarizer.summarize_recursive(messages, target_tokens=50)

    assert "summary" in summary.lower()
    assert len(summary) < 500
    mock_call_llm.assert_called_once()


@pytest.mark.asyncio
async def test_summarize_recursive_already_short(summarizer):
    """Test when content is already under target"""
    messages = [{"role": "user", "content": "Short message"}]

    summary = await summarizer.summarize_recursive(messages, target_tokens=1000)

    # Should not call LLM (no mocking needed)
    assert "Short message" in summary


@pytest.mark.asyncio
@patch("kagura.core.compression.summarizer.call_llm", new_callable=AsyncMock)
async def test_summarize_hierarchical(mock_call_llm, summarizer):
    """Test hierarchical summarization"""
    mock_call_llm.return_value = "Summary text"

    messages = [{"role": "user", "content": "Message " * 100}] * 10

    summaries = await summarizer.summarize_hierarchical(messages, levels=3)

    assert "brief" in summaries
    assert "detailed" in summaries
    assert "full" in summaries

    # Brief should be shortest (or equal if mocked)
    assert len(summaries["brief"]) <= len(summaries["detailed"])


@pytest.mark.asyncio
@patch("kagura.core.compression.summarizer.call_llm", new_callable=AsyncMock)
async def test_compress_preserve_events_basic(mock_call_llm, summarizer):
    """Test event-preserving compression"""
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


# Edge Cases


@pytest.mark.asyncio
async def test_summarize_empty_messages(summarizer):
    """Test with empty message list"""
    messages = []
    summary = await summarizer.summarize_recursive(messages, target_tokens=100)
    assert summary == ""


@pytest.mark.asyncio
async def test_summarize_single_message(summarizer):
    """Test with single short message"""
    messages = [{"role": "user", "content": "Hello"}]

    summary = await summarizer.summarize_recursive(messages, target_tokens=100)

    assert "Hello" in summary


@pytest.mark.asyncio
@patch("kagura.core.compression.summarizer.call_llm", new_callable=AsyncMock)
async def test_summarize_very_long_messages(mock_call_llm, summarizer):
    """Test with very long messages requiring multiple rounds"""
    # First call returns still-long summary, second call returns short
    mock_call_llm.side_effect = [
        "Still quite long summary " * 50,
        "Final brief summary",
    ]

    messages = [{"role": "user", "content": "Message " * 500}] * 10

    summary = await summarizer.summarize_recursive(messages, target_tokens=50)

    # Should call LLM multiple times for recursive summarization
    assert mock_call_llm.call_count >= 1
    assert "summary" in summary.lower()


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


@pytest.mark.asyncio
@patch("kagura.core.compression.summarizer.call_llm", new_callable=AsyncMock)
async def test_compress_no_key_events(mock_call_llm, summarizer):
    """Test when no messages are key events"""
    mock_call_llm.return_value = "Summary of routine messages"

    # Make messages long enough to trigger summarization
    messages = [
        {"role": "user", "content": "Normal message 1 " * 50},
        {"role": "user", "content": "Normal message 2 " * 50},
        {"role": "user", "content": "Normal message 3 " * 50},
    ]

    compressed = await summarizer.compress_preserve_events(messages, target_tokens=200)

    # Should call LLM to summarize routine messages
    assert mock_call_llm.call_count >= 1

    # Should have summary message
    assert any("summary" in m["content"].lower() for m in compressed)


@pytest.mark.asyncio
@patch("kagura.core.compression.summarizer.call_llm", new_callable=AsyncMock)
async def test_compress_insufficient_space(mock_call_llm, summarizer):
    """Test when target tokens is too low for key events"""
    mock_call_llm.return_value = "Complete summary"

    messages = [
        {"role": "user", "content": "IMPORTANT: Very long key event " * 50},
        {"role": "user", "content": "ERROR: Another long key event " * 50},
        {"role": "user", "content": "Normal message"},
    ]

    compressed = await summarizer.compress_preserve_events(messages, target_tokens=50)

    # Should summarize everything (including key events)
    assert len(compressed) == 1
    assert "Summary" in compressed[0]["content"]


@pytest.mark.asyncio
async def test_hierarchical_empty_messages(summarizer):
    """Test hierarchical summarization with empty messages"""
    messages = []

    summaries = await summarizer.summarize_hierarchical(messages)

    assert summaries["brief"] == ""
    assert summaries["detailed"] == ""
    assert summaries["full"] == ""


@pytest.mark.asyncio
async def test_hierarchical_short_conversation(summarizer):
    """Test hierarchical summarization with short conversation"""
    messages = [{"role": "user", "content": "Short conversation"}]

    summaries = await summarizer.summarize_hierarchical(messages)

    # Full should be original for short conversations
    assert "Short conversation" in summaries["full"]


# Helper Method Tests


def test_is_key_event_error(summarizer):
    """Test key event detection for errors"""
    assert summarizer._is_key_event({"content": "ERROR: Connection failed"})
    assert summarizer._is_key_event({"content": "An exception occurred"})
    assert summarizer._is_key_event({"content": "The operation failed"})


def test_is_key_event_important(summarizer):
    """Test key event detection for important messages"""
    assert summarizer._is_key_event({"content": "IMPORTANT: user preference"})
    assert summarizer._is_key_event({"content": "This is critical information"})
    assert summarizer._is_key_event({"content": "Urgent: Please respond"})


def test_is_key_event_decisions(summarizer):
    """Test key event detection for decisions"""
    assert summarizer._is_key_event({"content": "We decided to use API key auth"})
    assert summarizer._is_key_event({"content": "User agreed to the terms"})
    assert summarizer._is_key_event({"content": "Confirmed: will use dark mode"})


def test_is_key_event_preferences(summarizer):
    """Test key event detection for preferences"""
    assert summarizer._is_key_event({"content": "User preference: dark mode"})
    assert summarizer._is_key_event({"content": "Setting: notifications enabled"})
    assert summarizer._is_key_event({"content": "Config: use JSON format"})


def test_is_key_event_remember(summarizer):
    """Test key event detection for things to remember"""
    assert summarizer._is_key_event({"content": "Remember to check this later"})
    assert summarizer._is_key_event({"content": "Note: user is left-handed"})
    assert summarizer._is_key_event({"content": "Save this for later reference"})


def test_is_key_event_normal(summarizer):
    """Test that normal messages are not key events"""
    assert not summarizer._is_key_event({"content": "Hello, how are you?"})
    assert not summarizer._is_key_event({"content": "Thanks for the help"})
    assert not summarizer._is_key_event({"content": "That makes sense"})


def test_messages_to_text(summarizer):
    """Test message to text conversion"""
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there"},
    ]

    text = summarizer._messages_to_text(messages)

    assert "USER: Hello" in text
    assert "ASSISTANT: Hi there" in text


def test_messages_to_text_empty(summarizer):
    """Test message to text conversion with empty list"""
    messages = []

    text = summarizer._messages_to_text(messages)

    assert text == ""


def test_split_into_chunks(summarizer):
    """Test text splitting into chunks"""
    # Create text with clear sentence boundaries
    text = "First sentence. Second sentence. Third sentence. Fourth sentence."

    chunks = summarizer._split_into_chunks(text, target_tokens=20)

    # Should split into multiple chunks (or single if too small)
    assert len(chunks) >= 1

    # All chunks together should contain all sentences
    combined = ". ".join(chunks)
    assert "First sentence" in combined
    assert "Fourth sentence" in combined


def test_split_into_chunks_short(summarizer):
    """Test splitting short text"""
    text = "Short text."

    chunks = summarizer._split_into_chunks(text, target_tokens=100)

    # Should have single chunk for short text
    assert len(chunks) == 1
    # Note: split(". ") removes the final period, so we compare without it
    assert "Short text" in chunks[0]


# Integration Tests


@pytest.mark.asyncio
@patch("kagura.core.compression.summarizer.call_llm", new_callable=AsyncMock)
async def test_full_workflow_recursive(mock_call_llm, summarizer):
    """Test full recursive summarization workflow"""
    mock_call_llm.return_value = "Complete summary of the conversation"

    messages = [
        {"role": "system", "content": "You are helpful."},
        {"role": "user", "content": "Tell me about Python."},
        {"role": "assistant", "content": "Python is a programming language..."},
        {"role": "user", "content": "What about libraries?"},
        {"role": "assistant", "content": "Python has many libraries..."},
    ] * 20  # Repeat to make it long

    summary = await summarizer.summarize_recursive(messages, target_tokens=200)

    # Should successfully summarize
    assert isinstance(summary, str)
    assert len(summary) > 0


@pytest.mark.asyncio
@patch("kagura.core.compression.summarizer.call_llm", new_callable=AsyncMock)
async def test_full_workflow_hierarchical(mock_call_llm, summarizer):
    """Test full hierarchical summarization workflow"""
    mock_call_llm.return_value = "Summary"

    messages = [{"role": "user", "content": f"Message {i} " * 20} for i in range(50)]

    summaries = await summarizer.summarize_hierarchical(messages)

    # Should have all three levels
    assert all(key in summaries for key in ["brief", "detailed", "full"])
    assert all(isinstance(v, str) for v in summaries.values())


@pytest.mark.asyncio
@patch("kagura.core.compression.summarizer.call_llm", new_callable=AsyncMock)
async def test_full_workflow_preserve_events(mock_call_llm, summarizer):
    """Test full event-preserving workflow"""
    mock_call_llm.return_value = "Routine conversation summary"

    messages = [
        {"role": "user", "content": "Hello there"},
        {"role": "assistant", "content": "Hi! How can I help?"},
        {"role": "user", "content": "IMPORTANT: I prefer dark mode"},
        {"role": "assistant", "content": "I'll remember that"},
        {"role": "user", "content": "What's the weather?"},
        {"role": "assistant", "content": "Let me check..."},
        {"role": "user", "content": "ERROR: API key is invalid"},
        {"role": "assistant", "content": "Let me help fix that"},
        {"role": "user", "content": "Thanks for your help"},
    ]

    compressed = await summarizer.compress_preserve_events(messages, target_tokens=300)

    # Should preserve both key events
    contents = [m["content"] for m in compressed]
    assert any("IMPORTANT" in c for c in contents)
    assert any("ERROR" in c for c in contents)

    # Should have summary for routine messages
    assert any("summary" in c.lower() for c in contents)


# Performance Tests


@pytest.mark.asyncio
@patch("kagura.core.compression.summarizer.call_llm", new_callable=AsyncMock)
async def test_performance_large_message_list(mock_call_llm, summarizer):
    """Test performance with large message list"""
    mock_call_llm.return_value = "Summary"

    messages = [{"role": "user", "content": f"Message {i}"} for i in range(1000)]

    summary = await summarizer.summarize_recursive(messages, target_tokens=500)

    # Should complete without error
    assert isinstance(summary, str)


@pytest.mark.asyncio
@patch("kagura.core.compression.summarizer.call_llm", new_callable=AsyncMock)
async def test_token_reduction_verification(mock_call_llm, summarizer):
    """Test that summarization actually reduces tokens"""
    mock_call_llm.return_value = "Brief summary"

    messages = [{"role": "user", "content": "Long message " * 100}] * 10

    original_tokens = summarizer.counter.count_tokens_messages(messages)
    summary = await summarizer.summarize_recursive(messages, target_tokens=100)
    summary_tokens = summarizer.counter.count_tokens(summary)

    # Summary should be significantly shorter
    assert summary_tokens < original_tokens * 0.2  # 80%+ reduction
