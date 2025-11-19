"""MCP utilities (moved from builtin/).

Common utilities for MCP tools:
- cache.py: Search result caching
- common.py: Helper functions, logging, directory management
"""

from kagura.mcp.utils.cache import SearchCache, SearchCacheEntry
from kagura.mcp.utils.common import (
    format_error,
    format_success,
    get_kagura_base_dir,
    get_kagura_cache_dir,
    get_kagura_logs_dir,
    get_library_cache_dir,
    handle_import_error,
    infer_category,
    parse_json_dict,
    parse_json_list,
    require_api_key,
    setup_external_library_logging,
    to_bool,
    to_float_clamped,
    to_int,
)

__all__ = [
    # cache.py
    "SearchCache",
    "SearchCacheEntry",
    # common.py
    "format_error",
    "format_success",
    "get_kagura_base_dir",
    "get_kagura_cache_dir",
    "get_kagura_logs_dir",
    "get_library_cache_dir",
    "handle_import_error",
    "infer_category",
    "parse_json_dict",
    "parse_json_list",
    "require_api_key",
    "setup_external_library_logging",
    "to_bool",
    "to_float_clamped",
    "to_int",
]
