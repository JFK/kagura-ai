"""Context memory for conversation history and session management."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Message:
    """A message in the conversation context.

    Attributes:
        role: Message role ("user", "assistant", "system")
        content: Message content
        timestamp: When message was created
        metadata: Optional metadata
    """

    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Optional[dict] = None

    def to_dict(self) -> dict:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


class ContextMemory:
    """Conversation history and session context.

    Manages message history with automatic pruning to stay within limits.
    """

    def __init__(self, max_messages: int = 100) -> None:
        """Initialize context memory.

        Args:
            max_messages: Maximum number of messages to keep
        """
        self._messages: list[Message] = []
        self._max_messages = max_messages
        self._session_id: Optional[str] = None

    def add_message(
        self,
        role: str,
        content: str,
        metadata: Optional[dict] = None,
    ) -> None:
        """Add message to context.

        Args:
            role: Message role ("user", "assistant", "system")
            content: Message content
            metadata: Optional metadata
        """
        msg = Message(
            role=role, content=content, timestamp=datetime.now(), metadata=metadata
        )
        self._messages.append(msg)

        # Prune old messages if exceeding limit
        if len(self._messages) > self._max_messages:
            self._messages = self._messages[-self._max_messages :]

    def get_messages(
        self, last_n: Optional[int] = None, role: Optional[str] = None
    ) -> list[Message]:
        """Retrieve messages.

        Args:
            last_n: Get last N messages only
            role: Filter by role

        Returns:
            List of messages
        """
        messages = self._messages

        # Filter by role
        if role:
            messages = [m for m in messages if m.role == role]

        # Get last N
        if last_n:
            messages = messages[-last_n:]

        return messages

    def get_last_message(self, role: Optional[str] = None) -> Optional[Message]:
        """Get the last message.

        Args:
            role: Filter by role

        Returns:
            Last message or None
        """
        messages = self.get_messages(last_n=1, role=role)
        return messages[0] if messages else None

    def clear(self) -> None:
        """Clear all messages."""
        self._messages.clear()

    def set_session_id(self, session_id: str) -> None:
        """Set session ID.

        Args:
            session_id: Session identifier
        """
        self._session_id = session_id

    def get_session_id(self) -> Optional[str]:
        """Get session ID.

        Returns:
            Session ID or None
        """
        return self._session_id

    def to_llm_format(self, last_n: Optional[int] = None) -> list[dict]:
        """Convert to LLM API format.

        Args:
            last_n: Get last N messages only

        Returns:
            List of message dictionaries
        """
        messages = self.get_messages(last_n=last_n)
        return [{"role": msg.role, "content": msg.content} for msg in messages]

    def to_dict(self) -> dict:
        """Export to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "session_id": self._session_id,
            "messages": [msg.to_dict() for msg in self._messages],
        }

    def __len__(self) -> int:
        """Get number of messages."""
        return len(self._messages)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ContextMemory(messages={len(self._messages)}, session={self._session_id})"
        )
