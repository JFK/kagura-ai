"""Tests for ContextMemory."""

import pytest

from kagura.core.memory.context import ContextMemory, Message


def test_context_memory_add_message():
    """Test adding messages."""
    memory = ContextMemory()

    memory.add_message("user", "Hello")
    assert len(memory) == 1

    memory.add_message("assistant", "Hi there!")
    assert len(memory) == 2


def test_context_memory_get_messages():
    """Test retrieving messages."""
    memory = ContextMemory()

    memory.add_message("user", "Hello")
    memory.add_message("assistant", "Hi there!")

    messages = memory.get_messages()
    assert len(messages) == 2
    assert messages[0].role == "user"
    assert messages[0].content == "Hello"
    assert messages[1].role == "assistant"
    assert messages[1].content == "Hi there!"


def test_context_memory_get_last_n():
    """Test getting last N messages."""
    memory = ContextMemory()

    memory.add_message("user", "Message 1")
    memory.add_message("assistant", "Message 2")
    memory.add_message("user", "Message 3")

    last_2 = memory.get_messages(last_n=2)
    assert len(last_2) == 2
    assert last_2[0].content == "Message 2"
    assert last_2[1].content == "Message 3"


def test_context_memory_filter_by_role():
    """Test filtering messages by role."""
    memory = ContextMemory()

    memory.add_message("user", "User 1")
    memory.add_message("assistant", "Assistant 1")
    memory.add_message("user", "User 2")

    user_msgs = memory.get_messages(role="user")
    assert len(user_msgs) == 2
    assert all(m.role == "user" for m in user_msgs)


def test_context_memory_get_last_message():
    """Test getting last message."""
    memory = ContextMemory()

    memory.add_message("user", "Message 1")
    memory.add_message("assistant", "Message 2")

    last_msg = memory.get_last_message()
    assert last_msg is not None
    assert last_msg.content == "Message 2"


def test_context_memory_get_last_message_by_role():
    """Test getting last message by role."""
    memory = ContextMemory()

    memory.add_message("user", "User 1")
    memory.add_message("assistant", "Assistant 1")
    memory.add_message("user", "User 2")

    last_user = memory.get_last_message(role="user")
    assert last_user is not None
    assert last_user.content == "User 2"


def test_context_memory_clear():
    """Test clearing messages."""
    memory = ContextMemory()

    memory.add_message("user", "Hello")
    memory.add_message("assistant", "Hi")
    assert len(memory) == 2

    memory.clear()
    assert len(memory) == 0


def test_context_memory_auto_pruning():
    """Test automatic pruning when exceeding max_messages."""
    memory = ContextMemory(max_messages=3)

    memory.add_message("user", "Message 1")
    memory.add_message("assistant", "Message 2")
    memory.add_message("user", "Message 3")
    assert len(memory) == 3

    # Adding 4th message should prune the 1st
    memory.add_message("assistant", "Message 4")
    assert len(memory) == 3

    messages = memory.get_messages()
    assert messages[0].content == "Message 2"
    assert messages[-1].content == "Message 4"


def test_context_memory_session_id():
    """Test session ID management."""
    memory = ContextMemory()

    assert memory.get_session_id() is None

    memory.set_session_id("session-123")
    assert memory.get_session_id() == "session-123"


def test_context_memory_to_llm_format():
    """Test conversion to LLM API format."""
    memory = ContextMemory()

    memory.add_message("user", "Hello")
    memory.add_message("assistant", "Hi there!")

    llm_format = memory.to_llm_format()
    assert len(llm_format) == 2
    assert llm_format[0] == {"role": "user", "content": "Hello"}
    assert llm_format[1] == {"role": "assistant", "content": "Hi there!"}


def test_context_memory_to_llm_format_last_n():
    """Test LLM format with last_n."""
    memory = ContextMemory()

    memory.add_message("user", "Message 1")
    memory.add_message("assistant", "Message 2")
    memory.add_message("user", "Message 3")

    llm_format = memory.to_llm_format(last_n=2)
    assert len(llm_format) == 2
    assert llm_format[0]["content"] == "Message 2"


def test_context_memory_to_dict():
    """Test export to dictionary."""
    memory = ContextMemory()
    memory.set_session_id("session-123")
    memory.add_message("user", "Hello")

    export = memory.to_dict()
    assert export["session_id"] == "session-123"
    assert len(export["messages"]) == 1
    assert export["messages"][0]["role"] == "user"
    assert export["messages"][0]["content"] == "Hello"


def test_context_memory_metadata():
    """Test message metadata."""
    memory = ContextMemory()

    metadata = {"source": "web", "user_id": 123}
    memory.add_message("user", "Hello", metadata=metadata)

    messages = memory.get_messages()
    assert messages[0].metadata == metadata


def test_message_to_dict():
    """Test Message.to_dict()."""
    msg = Message(role="user", content="Hello", metadata={"key": "value"})

    msg_dict = msg.to_dict()
    assert msg_dict["role"] == "user"
    assert msg_dict["content"] == "Hello"
    assert msg_dict["metadata"] == {"key": "value"}
    assert "timestamp" in msg_dict


def test_context_memory_repr():
    """Test string representation."""
    memory = ContextMemory()
    memory.set_session_id("session-123")
    memory.add_message("user", "Hello")

    repr_str = repr(memory)
    assert "ContextMemory" in repr_str
    assert "messages=1" in repr_str
    assert "session=session-123" in repr_str
