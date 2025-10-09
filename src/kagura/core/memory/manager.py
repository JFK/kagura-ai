"""Memory manager for unified memory access.

Provides a unified interface to all memory types (working, context, persistent).
"""

from pathlib import Path
from typing import Any, Optional

from .context import ContextMemory, Message
from .persistent import PersistentMemory
from .working import WorkingMemory


class MemoryManager:
    """Unified memory management interface.

    Combines working, context, and persistent memory into a single API.
    """

    def __init__(
        self,
        agent_name: Optional[str] = None,
        persist_dir: Optional[Path] = None,
        max_messages: int = 100,
    ) -> None:
        """Initialize memory manager.

        Args:
            agent_name: Optional agent name for scoping
            persist_dir: Directory for persistent storage
            max_messages: Maximum messages in context
        """
        self.agent_name = agent_name

        # Initialize memory types
        self.working = WorkingMemory()
        self.context = ContextMemory(max_messages=max_messages)

        db_path = None
        if persist_dir:
            db_path = persist_dir / "memory.db"

        self.persistent = PersistentMemory(db_path=db_path)

    # Working Memory
    def set_temp(self, key: str, value: Any) -> None:
        """Store temporary data.

        Args:
            key: Key to store data under
            value: Value to store
        """
        self.working.set(key, value)

    def get_temp(self, key: str, default: Any = None) -> Any:
        """Get temporary data.

        Args:
            key: Key to retrieve
            default: Default value if key not found

        Returns:
            Stored value or default
        """
        return self.working.get(key, default)

    def has_temp(self, key: str) -> bool:
        """Check if temporary key exists.

        Args:
            key: Key to check

        Returns:
            True if key exists
        """
        return self.working.has(key)

    def delete_temp(self, key: str) -> None:
        """Delete temporary data.

        Args:
            key: Key to delete
        """
        self.working.delete(key)

    # Context Memory
    def add_message(
        self, role: str, content: str, metadata: Optional[dict] = None
    ) -> None:
        """Add message to context.

        Args:
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Optional metadata
        """
        self.context.add_message(role, content, metadata)

    def get_context(self, last_n: Optional[int] = None) -> list[Message]:
        """Get conversation context.

        Args:
            last_n: Get last N messages only

        Returns:
            List of messages
        """
        return self.context.get_messages(last_n=last_n)

    def get_llm_context(self, last_n: Optional[int] = None) -> list[dict]:
        """Get context in LLM API format.

        Args:
            last_n: Get last N messages only

        Returns:
            List of message dictionaries
        """
        return self.context.to_llm_format(last_n=last_n)

    def get_last_message(self, role: Optional[str] = None) -> Optional[Message]:
        """Get the last message.

        Args:
            role: Filter by role

        Returns:
            Last message or None
        """
        return self.context.get_last_message(role=role)

    def set_session_id(self, session_id: str) -> None:
        """Set session ID.

        Args:
            session_id: Session identifier
        """
        self.context.set_session_id(session_id)

    def get_session_id(self) -> Optional[str]:
        """Get session ID.

        Returns:
            Session ID or None
        """
        return self.context.get_session_id()

    # Persistent Memory
    def remember(self, key: str, value: Any, metadata: Optional[dict] = None) -> None:
        """Store persistent memory.

        Args:
            key: Memory key
            value: Value to store
            metadata: Optional metadata
        """
        self.persistent.store(key, value, self.agent_name, metadata)

    def recall(self, key: str) -> Optional[Any]:
        """Recall persistent memory.

        Args:
            key: Memory key

        Returns:
            Stored value or None
        """
        return self.persistent.recall(key, self.agent_name)

    def search_memory(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search persistent memory.

        Args:
            query: Search pattern (SQL LIKE pattern)
            limit: Maximum results

        Returns:
            List of memory dictionaries
        """
        return self.persistent.search(query, self.agent_name, limit)

    def forget(self, key: str) -> None:
        """Delete persistent memory.

        Args:
            key: Memory key to delete
        """
        self.persistent.forget(key, self.agent_name)

    def prune_old(self, older_than_days: int = 90) -> int:
        """Remove old memories.

        Args:
            older_than_days: Delete memories older than this many days

        Returns:
            Number of deleted memories
        """
        return self.persistent.prune(older_than_days, self.agent_name)

    # Session Management
    def save_session(self, session_name: str) -> None:
        """Save current session.

        Args:
            session_name: Name to save session under
        """
        session_data = {
            "working": self.working.to_dict(),
            "context": self.context.to_dict(),
        }
        self.persistent.store(
            key=f"session:{session_name}",
            value=session_data,
            agent_name=self.agent_name,
            metadata={"type": "session"},
        )

    def load_session(self, session_name: str) -> bool:
        """Load saved session.

        Args:
            session_name: Name of session to load

        Returns:
            True if session was loaded successfully
        """
        session_data = self.persistent.recall(
            key=f"session:{session_name}", agent_name=self.agent_name
        )

        if not session_data:
            return False

        # Restore context
        self.context.clear()
        context_data = session_data.get("context", {})
        if context_data.get("session_id"):
            self.context.set_session_id(context_data["session_id"])

        for msg_data in context_data.get("messages", []):
            self.context.add_message(
                role=msg_data["role"],
                content=msg_data["content"],
                metadata=msg_data.get("metadata"),
            )

        return True

    def clear_all(self) -> None:
        """Clear all memory (working and context).

        Note: Does not clear persistent memory.
        """
        self.working.clear()
        self.context.clear()

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"MemoryManager("
            f"agent={self.agent_name}, "
            f"working={len(self.working)}, "
            f"context={len(self.context)}, "
            f"persistent={self.persistent.count(self.agent_name)})"
        )
