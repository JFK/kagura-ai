"""Shared utilities for Kagura AI.

This package contains utility modules shared across CLI, MCP, and API layers:
- json_helpers: JSON encoding/decoding for ChromaDB compatibility
- metadata: Metadata extraction and manipulation
- db: Database query helpers
- memory: MemoryManager factory and caching
"""

from kagura.utils.json_helpers import (
    decode_chromadb_metadata,
    encode_chromadb_metadata,
    safe_json_loads,
)

__all__ = [
    "decode_chromadb_metadata",
    "encode_chromadb_metadata",
    "safe_json_loads",
]
