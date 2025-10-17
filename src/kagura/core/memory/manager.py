"""Memory manager for unified memory access.

Provides a unified interface to all memory types (working, context, persistent).
"""

from pathlib import Path
from typing import Any, Optional

from kagura.core.compression import CompressionPolicy, ContextManager

from .context import ContextMemory, Message
from .persistent import PersistentMemory
from .rag import MemoryRAG
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
        enable_rag: bool = False,
        enable_compression: bool = True,
        compression_policy: Optional[CompressionPolicy] = None,
        model: str = "gpt-5-mini",
    ) -> None:
        """Initialize memory manager.

        Args:
            agent_name: Optional agent name for scoping
            persist_dir: Directory for persistent storage
            max_messages: Maximum messages in context
            enable_rag: Enable RAG (vector-based semantic search)
            enable_compression: Enable automatic context compression
            compression_policy: Compression configuration
            model: LLM model name for compression
        """
        self.agent_name = agent_name

        # Initialize memory types
        self.working = WorkingMemory()
        self.context = ContextMemory(max_messages=max_messages)

        db_path = None
        if persist_dir:
            db_path = persist_dir / "memory.db"

        self.persistent = PersistentMemory(db_path=db_path)

        # Optional: RAG
        self.rag: Optional[MemoryRAG] = None
        if enable_rag:
            collection_name = f"kagura_{agent_name}" if agent_name else "kagura_memory"
            vector_dir = persist_dir / "vector_db" if persist_dir else None
            self.rag = MemoryRAG(
                collection_name=collection_name, persist_dir=vector_dir
            )

        # Optional: Compression
        self.enable_compression = enable_compression
        self.context_manager: Optional[ContextManager] = None
        if enable_compression:
            self.context_manager = ContextManager(
                policy=compression_policy or CompressionPolicy(), model=model
            )

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

    async def get_llm_context(
        self, last_n: Optional[int] = None, compress: bool = True
    ) -> list[dict]:
        """Get context in LLM API format with optional compression.

        Args:
            last_n: Get last N messages only
            compress: Whether to apply compression (default: True)

        Returns:
            List of message dictionaries (compressed if enabled)

        Example:
            >>> context = await memory.get_llm_context(compress=True)
        """
        messages = self.context.to_llm_format(last_n=last_n)

        if compress and self.context_manager:
            # Apply compression
            messages = await self.context_manager.compress(messages)

        return messages

    def get_usage_stats(self) -> dict[str, Any]:
        """Get context usage statistics.

        Returns:
            Dict with compression stats

        Example:
            >>> stats = memory.get_usage_stats()
            >>> print(f"Usage: {stats['usage_ratio']:.1%}")
        """
        if not self.context_manager:
            return {"compression_enabled": False}

        messages = self.context.to_llm_format()
        usage = self.context_manager.get_usage(messages)

        return {
            "compression_enabled": True,
            "total_tokens": usage.total_tokens,
            "max_tokens": usage.max_tokens,
            "usage_ratio": usage.usage_ratio,
            "should_compress": usage.should_compress,
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
        }

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

    # RAG Memory
    def store_semantic(self, content: str, metadata: Optional[dict] = None) -> str:
        """Store content for semantic search.

        Args:
            content: Content to store
            metadata: Optional metadata

        Returns:
            Content hash (unique ID)

        Raises:
            ValueError: If RAG is not enabled
        """
        if not self.rag:
            raise ValueError("RAG not enabled. Set enable_rag=True")
        return self.rag.store(content, metadata, self.agent_name)

    def recall_semantic(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Semantic search for relevant memories.

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            List of memory dictionaries with content, distance, and metadata

        Raises:
            ValueError: If RAG is not enabled
        """
        if not self.rag:
            raise ValueError("RAG not enabled. Set enable_rag=True")
        return self.rag.recall(query, top_k, self.agent_name)

    def clear_all(self) -> None:
        """Clear all memory (working and context).

        Note: Does not clear persistent memory or RAG memory.
        """
        self.working.clear()
        self.context.clear()

    def __repr__(self) -> str:
        """String representation."""
        rag_count = self.rag.count(self.agent_name) if self.rag else 0
        return (
            f"MemoryManager("
            f"agent={self.agent_name}, "
            f"working={len(self.working)}, "
            f"context={len(self.context)}, "
            f"persistent={self.persistent.count(self.agent_name)}, "
            f"rag={rag_count})"
        )
