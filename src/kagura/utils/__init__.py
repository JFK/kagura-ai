"""Shared utilities for Kagura AI.

This package contains utility modules shared across CLI, MCP, and API layers:
- json_helpers: JSON encoding/decoding for ChromaDB compatibility
- metadata: Metadata extraction and manipulation
- db: Database query helpers
- memory: MemoryManager factory and caching
"""

from kagura.utils.db import MemoryDatabaseQuery, db_exists, get_db_path
from kagura.utils.json_helpers import (
    decode_chromadb_metadata,
    encode_chromadb_metadata,
    safe_json_loads,
)
from kagura.utils.metadata import (
    MemoryMetadata,
    build_full_metadata,
    extract_memory_fields,
    merge_metadata,
    prepare_for_chromadb,
    validate_importance,
)

__all__ = [
    # json_helpers
    "decode_chromadb_metadata",
    "encode_chromadb_metadata",
    "safe_json_loads",
    # metadata
    "MemoryMetadata",
    "build_full_metadata",
    "extract_memory_fields",
    "merge_metadata",
    "prepare_for_chromadb",
    "validate_importance",
    # db
    "MemoryDatabaseQuery",
    "db_exists",
    "get_db_path",
]
