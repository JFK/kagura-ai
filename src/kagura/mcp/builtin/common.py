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
