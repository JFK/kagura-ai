"""Memory management system for Kagura AI.

Provides three types of memory:
- Context Memory: Conversation history and session management
- Persistent Memory: Long-term storage using SQLite/PostgreSQL
- Memory RAG: Vector-based semantic search (requires chromadb/qdrant)
- Multimodal RAG: RAG with directory scanning (requires chromadb + gemini)

The MemoryManager provides a unified interface to all memory types.

Note: Working Memory was removed in v4.4.0 (Issue #683).
Client-side context management is now the recommended approach for ephemeral data.
"""

from .context import ContextMemory, Message
from .manager import MemoryManager
from .persistent import PersistentMemory
from .rag import MemoryRAG

__all__ = [
    "MemoryManager",
    "ContextMemory",
    "PersistentMemory",
    "MemoryRAG",
    "Message",
]

# Conditional import for MultimodalRAG (requires multimodal extra)
try:
    from .multimodal_rag import MultimodalRAG

    __all__.append("MultimodalRAG")
except ImportError:
    pass
