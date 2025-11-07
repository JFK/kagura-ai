"""Common utilities for MCP built-in tools.

Provides unified logging, caching, and directory management for all MCP tools.
"""

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def get_kagura_base_dir() -> Path:
    """Get Kagura's base directory in user's home.

    Creates $HOME/.kagura/ if it doesn't exist.

    Returns:
        Path to ~/.kagura/ directory

    Raises:
        OSError: If home directory is not accessible
    """
    home = Path.home()
    kagura_dir = home / ".kagura"
    kagura_dir.mkdir(parents=True, exist_ok=True)
    return kagura_dir


def get_kagura_logs_dir() -> Path:
    """Get Kagura's logs directory.

    Creates $HOME/.kagura/logs/ if it doesn't exist.
    Used for all MCP tool logs (brave_search, yt-dlp, etc.)

    Returns:
        Path to ~/.kagura/logs/ directory

    Raises:
        OSError: If directory cannot be created or is not writable
    """
    try:
        logs_dir = get_kagura_base_dir() / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)

        # Test write permission
        test_file = logs_dir / ".write_test"
        test_file.touch()
        test_file.unlink()

        return logs_dir

    except (OSError, PermissionError) as e:
        logger.error(f"Cannot create/access logs directory: {e}")
        raise


def get_kagura_cache_dir() -> Path:
    """Get Kagura's cache directory.

    Creates $HOME/.kagura/cache/ if it doesn't exist.
    Used for temporary data, API caches, etc.

    Returns:
        Path to ~/.kagura/cache/ directory

    Raises:
        OSError: If directory cannot be created or is not writable
    """
    try:
        cache_dir = get_kagura_base_dir() / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Test write permission
        test_file = cache_dir / ".write_test"
        test_file.touch()
        test_file.unlink()

        return cache_dir

    except (OSError, PermissionError) as e:
        logger.error(f"Cannot create/access cache directory: {e}")
        raise


def get_fallback_temp_dir(subdir: str = "kagura") -> Path:
    """Get fallback temporary directory when home is not writable.

    Args:
        subdir: Subdirectory name under temp (default: "kagura")

    Returns:
        Path to temporary directory
    """
    import tempfile

    temp_dir = Path(tempfile.gettempdir()) / subdir
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def setup_external_library_logging(
    library_name: str,
    env_var_name: str,
    filename: str,
) -> str | None:
    """Set up logging for external libraries with fallback handling.

    Configures an external library's log file location with proper fallbacks:
    1. $HOME/.kagura/logs/{filename} (preferred)
    2. /dev/null or NUL (if home not writable)
    3. None (if all else fails)

    Args:
        library_name: Name of the library (for logging)
        env_var_name: Environment variable name for log file path
        filename: Log filename (e.g., "brave_search.log")

    Returns:
        Path to log file as string, or None if setup failed

    Example:
        >>> log_path = setup_external_library_logging(
        ...     "brave_search_python_client",
        ...     "BRAVE_SEARCH_PYTHON_CLIENT_LOG_FILE_NAME",
        ...     "brave_search_python_client.log"
        ... )
    """
    # Don't override if already set
    if env_var_name in os.environ:
        logger.debug(f"{library_name}: Using existing log path from {env_var_name}")
        return os.environ[env_var_name]

    try:
        # Try to use Kagura logs directory
        logs_dir = get_kagura_logs_dir()
        log_file = logs_dir / filename

        os.environ[env_var_name] = str(log_file)
        logger.debug(f"{library_name}: Logs will be written to {log_file}")
        return str(log_file)

    except (OSError, PermissionError) as e:
        logger.warning(
            f"{library_name}: Cannot write logs to home directory: {e}. "
            f"Logs will be discarded."
        )

        # Fallback: disable logging with null device
        try:
            if os.name == "nt":  # Windows
                null_device = "NUL"
            else:  # Unix-like (Linux, macOS)
                null_device = "/dev/null"

            os.environ[env_var_name] = null_device
            logger.debug(f"{library_name}: Logging disabled (using null device)")
            return null_device

        except Exception as fallback_error:
            logger.error(
                f"{library_name}: Failed to configure logging: {fallback_error}"
            )
            return None


def get_library_cache_dir(library_name: str) -> str:
    """Get cache directory for a specific external library.

    Creates $HOME/.kagura/cache/{library_name}/ with fallback to temp.

    Args:
        library_name: Name of the library (e.g., "yt-dlp", "chromadb")

    Returns:
        Path to cache directory as string
    """
    try:
        cache_dir = get_kagura_cache_dir() / library_name
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Test write permission
        test_file = cache_dir / ".write_test"
        test_file.touch()
        test_file.unlink()

        logger.debug(f"{library_name}: Using cache directory {cache_dir}")
        return str(cache_dir)

    except (OSError, PermissionError) as e:
        logger.warning(
            f"{library_name}: Cannot write to home cache directory: {e}. "
            f"Using temporary directory."
        )

        # Fallback to temp
        temp_dir = get_fallback_temp_dir(f"kagura-{library_name}")
        return str(temp_dir)


# ==============================================================================
# MCP Tool Helpers (Phase 2: Issue #545)
# ==============================================================================


def parse_json_list(
    value: str | list | None,
    param_name: str = "parameter",
    default: list | None = None,
) -> list:
    """Parse JSON array from MCP parameter.

    MCP tools receive parameters as strings (LLMs send JSON as string).
    This helper safely parses list parameters with error handling.

    Args:
        value: Parameter value (string JSON or already-parsed list)
        param_name: Parameter name (for error messages)
        default: Default value if parsing fails (defaults to [])

    Returns:
        Parsed list or default

    Examples:
        >>> parse_json_list('["tag1", "tag2"]')
        ['tag1', 'tag2']

        >>> parse_json_list(['already', 'parsed'])
        ['already', 'parsed']

        >>> parse_json_list('invalid', default=['fallback'])
        ['fallback']

        >>> parse_json_list(None)
        []
    """
    import json

    if default is None:
        default = []

    if value is None:
        return default

    if isinstance(value, list):
        return value

    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return parsed
            logger.warning(
                f"{param_name}: Expected list but got {type(parsed).__name__}, "
                f"using default"
            )
            return default
        except json.JSONDecodeError as e:
            logger.warning(f"{param_name}: JSON decode error: {e}, using default")
            return default

    logger.warning(
        f"{param_name}: Unexpected type {type(value).__name__}, using default"
    )
    return default


def parse_json_dict(
    value: str | dict | None,
    param_name: str = "parameter",
    default: dict | None = None,
) -> dict:
    """Parse JSON object from MCP parameter.

    MCP tools receive parameters as strings (LLMs send JSON as string).
    This helper safely parses dict parameters with error handling.

    Args:
        value: Parameter value (string JSON or already-parsed dict)
        param_name: Parameter name (for error messages)
        default: Default value if parsing fails (defaults to {})

    Returns:
        Parsed dict or default

    Examples:
        >>> parse_json_dict('{"key": "value"}')
        {'key': 'value'}

        >>> parse_json_dict({'already': 'parsed'})
        {'already': 'parsed'}

        >>> parse_json_dict('invalid', default={'fallback': True})
        {'fallback': True}

        >>> parse_json_dict(None)
        {}
    """
    import json

    if default is None:
        default = {}

    if value is None:
        return default

    if isinstance(value, dict):
        return value

    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                return parsed
            logger.warning(
                f"{param_name}: Expected dict but got {type(parsed).__name__}, "
                f"using default"
            )
            return default
        except json.JSONDecodeError as e:
            logger.warning(f"{param_name}: JSON decode error: {e}, using default")
            return default

    logger.warning(
        f"{param_name}: Unexpected type {type(value).__name__}, using default"
    )
    return default


def to_int(
    value: str | int | None,
    default: int = 0,
    min_val: int | None = None,
    max_val: int | None = None,
    param_name: str = "parameter",
) -> int:
    """Convert MCP parameter to int with validation.

    Args:
        value: Parameter value (string or int)
        default: Default value if conversion fails
        min_val: Minimum allowed value (inclusive)
        max_val: Maximum allowed value (inclusive)
        param_name: Parameter name (for error messages)

    Returns:
        Validated integer

    Examples:
        >>> to_int("42")
        42

        >>> to_int(42)
        42

        >>> to_int("invalid", default=10)
        10

        >>> to_int("100", min_val=0, max_val=50)
        50  # Clamped to max

        >>> to_int("-10", min_val=0, max_val=100)
        0  # Clamped to min
    """
    if value is None:
        return default

    try:
        result = int(value)
    except (TypeError, ValueError):
        logger.warning(
            f"{param_name}: Cannot convert '{value}' to int, using default {default}"
        )
        return default

    # Apply min/max clamping
    if min_val is not None and result < min_val:
        logger.debug(f"{param_name}: Value {result} < min {min_val}, clamping")
        result = min_val

    if max_val is not None and result > max_val:
        logger.debug(f"{param_name}: Value {result} > max {max_val}, clamping")
        result = max_val

    return result


def to_float_clamped(
    value: str | float | None,
    min_val: float = 0.0,
    max_val: float = 1.0,
    default: float = 0.5,
    param_name: str = "parameter",
) -> float:
    """Convert MCP parameter to float and clamp to range.

    Commonly used for importance, confidence, and other ratio parameters.

    Args:
        value: Parameter value (string or float)
        min_val: Minimum value (default: 0.0)
        max_val: Maximum value (default: 1.0)
        default: Default if conversion fails (default: 0.5)
        param_name: Parameter name (for error messages)

    Returns:
        Clamped float value

    Examples:
        >>> to_float_clamped("0.8")
        0.8

        >>> to_float_clamped("1.5")  # Clamped
        1.0

        >>> to_float_clamped("-0.5")  # Clamped
        0.0

        >>> to_float_clamped("invalid", default=0.7)
        0.7
    """
    if value is None:
        return default

    try:
        result = float(value)
    except (TypeError, ValueError):
        logger.warning(
            f"{param_name}: Cannot convert '{value}' to float, using default {default}"
        )
        return default

    # Clamp to range
    result = max(min_val, min(max_val, result))
    return result


def to_bool(value: str | bool | None, default: bool = False) -> bool:
    """Convert MCP parameter to bool.

    Handles common string representations: "true", "false", "1", "0", etc.

    Args:
        value: Parameter value (string or bool)
        default: Default if conversion fails

    Returns:
        Boolean value

    Examples:
        >>> to_bool("true")
        True

        >>> to_bool("false")
        False

        >>> to_bool("1")
        True

        >>> to_bool("0")
        False

        >>> to_bool(True)
        True

        >>> to_bool("invalid", default=True)
        True
    """
    if value is None:
        return default

    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        value_lower = value.lower().strip()
        if value_lower in ("true", "1", "yes", "on"):
            return True
        if value_lower in ("false", "0", "no", "off"):
            return False

    return default


def format_success(data: dict | str | None = None, message: str | None = None) -> str:
    """Format standard MCP success response as JSON string.

    Args:
        data: Response data (dict or string)
        message: Optional success message

    Returns:
        JSON string with status=success

    Examples:
        >>> format_success({"key": "value"}, "Operation completed")
        '{"status": "success", "message": "Operation completed", "data": {"key": "value"}}'

        >>> format_success(message="Deleted successfully")
        '{"status": "success", "message": "Deleted successfully"}'
    """
    import json

    response: dict = {"status": "success"}

    if message:
        response["message"] = message

    if data is not None:
        if isinstance(data, str):
            response["result"] = data
        else:
            response.update(data)

    return json.dumps(response, ensure_ascii=False, indent=2)


def format_error(
    error: str, details: dict | None = None, help_text: str | None = None
) -> str:
    """Format standard MCP error response as JSON string.

    Args:
        error: Error message
        details: Optional error details
        help_text: Optional help text for resolution

    Returns:
        JSON string with status=error

    Examples:
        >>> format_error("Key not found", {"key": "missing_key"})
        '{"status": "error", "error": "Key not found", "details": {"key": "missing_key"}}'

        >>> format_error("Invalid API key", help_text="Set BRAVE_API_KEY environment variable")
        '{"status": "error", "error": "Invalid API key", "help": "Set BRAVE_API_KEY..."}'
    """
    import json

    response: dict = {"status": "error", "error": error}

    if details:
        response["details"] = details

    if help_text:
        response["help"] = help_text

    return json.dumps(response, ensure_ascii=False, indent=2)


def require_api_key(api_key: str | None, service: str, env_var: str = "") -> str | None:
    """Validate API key and return error message if missing.

    Args:
        api_key: API key to validate
        service: Service name (for error message)
        env_var: Environment variable name (for help text)

    Returns:
        Error JSON string if invalid, None if valid

    Examples:
        >>> require_api_key(None, "Brave Search", "BRAVE_API_KEY")
        '{"status": "error", "error": "Brave Search API key required", ...}'

        >>> require_api_key("valid-key", "Brave Search")
        None  # Valid
    """
    if not api_key:
        help_text = f"Set {env_var} environment variable" if env_var else None
        return format_error(
            f"{service} API key required",
            help_text=help_text,
        )
    return None


def handle_import_error(package: str, install_cmd: str) -> str:
    """Generate standard import error response for missing dependencies.

    Args:
        package: Package name that's missing
        install_cmd: Installation command

    Returns:
        Error JSON string

    Examples:
        >>> handle_import_error("chromadb", "pip install chromadb")
        '{"status": "error", "error": "Missing dependency: chromadb", ...}'
    """
    return format_error(
        f"Missing dependency: {package}",
        details={"package": package},
        help_text=f"Install with: {install_cmd}",
    )


# ==============================================================================
# Category Inference (Issue #592)
# ==============================================================================


def infer_category(tool_name: str) -> str:
    """Infer category from tool name based on prefix.

    Maps tool names to functional categories for organization and filtering.

    Args:
        tool_name: MCP tool name (e.g., "memory_store", "coding_start_session")

    Returns:
        Category name (e.g., "memory", "coding", "github")

    Categories:
        - memory: Memory CRUD operations
        - coding: Coding session management
        - github: GitHub integration
        - brave_search: Brave Search API
        - youtube: YouTube tools
        - file: File operations
        - media: Media file handling
        - multimodal: Multimodal RAG
        - meta: Meta-agent tools
        - observability: Telemetry/monitoring
        - academic: Academic search (arXiv)
        - fact_check: Fact checking
        - routing: Query routing
        - web: Web scraping
        - shell: Shell execution

    Examples:
        >>> infer_category("memory_store")
        'memory'

        >>> infer_category("coding_start_session")
        'coding'

        >>> infer_category("brave_web_search")
        'brave_search'

        >>> infer_category("unknown_tool")
        'other'
    """
    # Strip kagura_tool_ prefix if present (from MCP tool names)
    if tool_name.startswith("kagura_tool_"):
        tool_name = tool_name.replace("kagura_tool_", "")

    # Prefix-based category mapping
    prefix_map = {
        "memory_": "memory",
        "coding_": "coding",
        "claude_code_": "coding",  # Claude Code integration
        "github_": "github",
        "gh_": "github",  # GitHub safe wrappers
        "brave_": "brave_search",
        "youtube_": "youtube",
        "get_youtube_": "youtube",
        "file_": "file",
        "dir_": "file",
        "shell_": "shell",
        "multimodal_": "multimodal",
        "arxiv_": "academic",
        "fact_check_": "fact_check",
        "media_": "media",
        "meta_": "meta",
        "telemetry_": "observability",
        "route_": "routing",
        "web_": "web",
    }

    for prefix, category in prefix_map.items():
        if tool_name.startswith(prefix):
            return category

    # Default category
    return "other"
