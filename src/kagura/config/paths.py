"""Platform-specific path management with XDG Base Directory compliance.

Provides functions to get cache, data, and config directories following
platform conventions:
- Linux/macOS: XDG Base Directory specification
- Windows: AppData directories
- Environment variable override support

Example:
    >>> from kagura.config.paths import get_cache_dir
    >>> cache_dir = get_cache_dir()
    >>> print(cache_dir)
    Path('/home/user/.cache/kagura')  # Linux
"""

import os
import platform
from pathlib import Path


def get_cache_dir() -> Path:
    """Get platform-specific cache directory.

    Returns cache directory following platform conventions:
    - Linux/macOS: $XDG_CACHE_HOME/kagura or ~/.cache/kagura
    - Windows: %LOCALAPPDATA%/kagura/cache
    - Override: $KAGURA_CACHE_DIR environment variable

    Returns:
        Path to cache directory

    Example:
        >>> cache_dir = get_cache_dir()
        >>> vector_db = cache_dir / "chromadb"
    """
    # Environment variable override
    if cache_dir := os.getenv("KAGURA_CACHE_DIR"):
        return Path(cache_dir)

    system = platform.system()

    if system == "Linux" or system == "Darwin":  # macOS
        # XDG Base Directory: $XDG_CACHE_HOME or ~/.cache
        xdg_cache = os.getenv("XDG_CACHE_HOME")
        base = Path(xdg_cache) if xdg_cache else Path.home() / ".cache"
        return base / "kagura"

    elif system == "Windows":
        # Windows: %LOCALAPPDATA%
        local_appdata = os.getenv("LOCALAPPDATA")
        if local_appdata:
            return Path(local_appdata) / "kagura" / "cache"
        return Path.home() / "AppData" / "Local" / "kagura" / "cache"

    else:
        # Fallback for unknown systems
        return Path.home() / ".kagura" / "cache"


def get_data_dir() -> Path:
    """Get platform-specific data directory (persistent storage).

    Returns data directory for persistent user data:
    - Linux/macOS: $XDG_DATA_HOME/kagura or ~/.local/share/kagura
    - Windows: %LOCALAPPDATA%/kagura/data
    - Override: $KAGURA_DATA_DIR environment variable

    Returns:
        Path to data directory

    Example:
        >>> data_dir = get_data_dir()
        >>> db_path = data_dir / "memory.db"
    """
    # Environment variable override
    if data_dir := os.getenv("KAGURA_DATA_DIR"):
        return Path(data_dir)

    system = platform.system()

    if system == "Linux" or system == "Darwin":
        # XDG Base Directory: $XDG_DATA_HOME or ~/.local/share
        xdg_data = os.getenv("XDG_DATA_HOME")
        base = Path(xdg_data) if xdg_data else Path.home() / ".local" / "share"
        return base / "kagura"

    elif system == "Windows":
        # Windows: %LOCALAPPDATA%
        local_appdata = os.getenv("LOCALAPPDATA")
        if local_appdata:
            return Path(local_appdata) / "kagura" / "data"
        return Path.home() / "AppData" / "Local" / "kagura" / "data"

    else:
        # Fallback
        return Path.home() / ".kagura" / "data"


def get_config_dir() -> Path:
    """Get platform-specific config directory (user-editable config files).

    Returns config directory for configuration files:
    - Linux/macOS: $XDG_CONFIG_HOME/kagura or ~/.config/kagura
    - Windows: %APPDATA%/kagura
    - Override: $KAGURA_CONFIG_DIR environment variable

    Returns:
        Path to config directory

    Example:
        >>> config_dir = get_config_dir()
        >>> config_file = config_dir / "config.json"
    """
    # Environment variable override
    if config_dir := os.getenv("KAGURA_CONFIG_DIR"):
        return Path(config_dir)

    system = platform.system()

    if system == "Linux" or system == "Darwin":
        # XDG Base Directory: $XDG_CONFIG_HOME or ~/.config
        xdg_config = os.getenv("XDG_CONFIG_HOME")
        base = Path(xdg_config) if xdg_config else Path.home() / ".config"
        return base / "kagura"

    elif system == "Windows":
        # Windows: %APPDATA%
        appdata = os.getenv("APPDATA")
        if appdata:
            return Path(appdata) / "kagura"
        return Path.home() / "AppData" / "Roaming" / "kagura"

    else:
        # Fallback
        return Path.home() / ".kagura"


def get_legacy_dir() -> Path:
    """Get legacy ~/.kagura directory for migration support.

    Returns:
        Path to legacy directory (~/.kagura)

    Example:
        >>> legacy = get_legacy_dir()
        >>> if legacy.exists():
        ...     # Migrate to new XDG paths
    """
    return Path.home() / ".kagura"


__all__ = ["get_cache_dir", "get_data_dir", "get_config_dir", "get_legacy_dir"]
