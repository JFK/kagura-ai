"""Memory management system for Kagura AI.

Provides four types of memory:
- Working Memory: Temporary data during agent execution
- Context Memory: Conversation history and session management
- Persistent Memory: Long-term storage using SQLite
- Memory RAG: Vector-based semantic search (requires chromadb)
- Multimodal RAG: RAG with directory scanning (requires chromadb + gemini)

The MemoryManager provides a unified interface to all memory types.
"""

from .context import ContextMemory, Message
from .manager import MemoryManager
from .persistent import PersistentMemory
from .rag import MemoryRAG
from .working import WorkingMemory

__all__ = [
    "MemoryManager",
    "WorkingMemory",
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
