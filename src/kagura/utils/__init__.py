"""Shared utilities for Kagura AI.

Reorganized in v4.3.0 for better modularity:
- cli/: CLI-specific utilities (progress, rich helpers, time formatters)
- memory/: Memory management utilities (MemoryManager factory)
- api/: API-related utilities (connectivity testing)
- common/: Shared utilities (JSON, errors, db, media, metadata)

This package re-exports commonly used utilities for backward compatibility.
"""

# Re-export submodules for backward compatibility (v4.3.0)
# Register in sys.modules to allow old-style imports like "from kagura.utils.db import X"
import sys

from kagura.utils.common import (  # noqa: F401
    db,
    errors,
    json_helpers,
    media_detector,
    metadata,
)

# Register submodules in sys.modules for backward compatibility
sys.modules["kagura.utils.db"] = db
sys.modules["kagura.utils.errors"] = errors
sys.modules["kagura.utils.json_helpers"] = json_helpers
sys.modules["kagura.utils.media_detector"] = media_detector
sys.modules["kagura.utils.metadata"] = metadata

# New organized imports (v4.3.0)
from kagura.utils.api.check import (
    check_api_configuration,
    check_brave_search_api,
    check_github_api,
    check_llm_api,
)
from kagura.utils.common.db import MemoryDatabaseQuery, db_exists, get_db_path
from kagura.utils.common.errors import *  # noqa: F403, F401
from kagura.utils.common.json_helpers import (
    decode_chromadb_metadata,
    encode_chromadb_metadata,
    safe_json_loads,
)
from kagura.utils.common.media_detector import *  # noqa: F403, F401
from kagura.utils.common.metadata import (
    MemoryMetadata,
    build_full_metadata,
    extract_memory_fields,
    merge_metadata,
    prepare_for_chromadb,
    validate_importance,
)
from kagura.utils.memory.factory import MemoryManagerFactory, get_memory_manager

__all__ = [
    # json_helpers (common)
    "decode_chromadb_metadata",
    "encode_chromadb_metadata",
    "safe_json_loads",
    # metadata (common)
    "MemoryMetadata",
    "build_full_metadata",
    "extract_memory_fields",
    "merge_metadata",
    "prepare_for_chromadb",
    "validate_importance",
    # db (common)
    "MemoryDatabaseQuery",
    "db_exists",
    "get_db_path",
    # memory
    "MemoryManagerFactory",
    "get_memory_manager",
    # api
    "check_llm_api",
    "check_brave_search_api",
    "check_github_api",
    "check_api_configuration",
]
