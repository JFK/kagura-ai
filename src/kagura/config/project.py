"""Project configuration and auto-detection.

Provides automatic project name detection from:
- Git repository (remote URL or directory name)
- pyproject.toml [tool.kagura] section
- Environment variables
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Any, Optional

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # type: ignore  # Fallback for older Python


def detect_git_repo_name() -> Optional[str]:
    """Detect git repository name from remote URL or directory.

    Returns:
        Repository name or None if not in a git repository

    Example:
        >>> # In /path/to/kagura-ai with remote git@github.com:JFK/kagura-ai.git
        >>> detect_git_repo_name()
        'kagura-ai'
    """
    try:
        # Method 1: Parse remote URL
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            timeout=1,
            check=False,
        )

        if result.returncode == 0:
            url = result.stdout.strip()
            # Extract repo name from URL
            # git@github.com:JFK/kagura-ai.git -> kagura-ai
            # https://github.com/JFK/kagura-ai.git -> kagura-ai
            # https://github.com/JFK/kagura-ai -> kagura-ai
            match = re.search(r'/([^/]+?)(?:\.git)?$', url)
            if match:
                return match.group(1)

            # SSH format: git@host:user/repo.git
            match = re.search(r':([^/]+/)?([^/]+?)(?:\.git)?$', url)
            if match:
                return match.group(2)

        # Method 2: Use git toplevel directory name
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=1,
            check=False,
        )

        if result.returncode == 0:
            return Path(result.stdout.strip()).name

    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    return None


def load_pyproject_config() -> dict[str, Any]:
    """Load Kagura configuration from pyproject.toml.

    Returns:
        Configuration dict from [tool.kagura] section, or empty dict

    Example pyproject.toml:
        [tool.kagura]
        project = "kagura-ai"
        user = "kiyota"
        enable_reranking = true
    """
    pyproject_path = Path.cwd() / "pyproject.toml"

    if not pyproject_path.exists():
        return {}

    try:
        content = pyproject_path.read_text(encoding="utf-8")
        data = tomllib.loads(content)
        return data.get("tool", {}).get("kagura", {})
    except Exception:
        # Ignore parse errors - pyproject.toml might be invalid
        return {}


def get_default_project() -> Optional[str]:
    """Get default project name with priority cascade.

    Priority order:
    1. Environment variable: $KAGURA_DEFAULT_PROJECT (explicit override)
    2. pyproject.toml: [tool.kagura] project = "name"
    3. Git repository: Auto-detected from remote URL
    4. Git directory: Top-level directory name
    5. None (no default available)

    Returns:
        Project name or None

    Example:
        >>> # In kagura-ai repo with pyproject.toml
        >>> get_default_project()
        'kagura-ai'
    """
    # Priority 1: Environment variable (explicit override)
    if project := os.getenv("KAGURA_DEFAULT_PROJECT"):
        return project.strip()

    # Priority 2: pyproject.toml [tool.kagura] section
    pyproject_config = load_pyproject_config()
    if project := pyproject_config.get("project"):
        return str(project).strip()

    # Priority 3 & 4: Git auto-detection
    if project := detect_git_repo_name():
        return project.strip()

    return None


def get_default_user() -> Optional[str]:
    """Get default user ID from configuration.

    Priority order:
    1. Environment variable: $KAGURA_DEFAULT_USER
    2. pyproject.toml: [tool.kagura] user = "name"
    3. Git user.name
    4. None

    Returns:
        User ID or None
    """
    # Priority 1: Environment variable
    if user := os.getenv("KAGURA_DEFAULT_USER"):
        return user.strip()

    # Priority 2: pyproject.toml
    pyproject_config = load_pyproject_config()
    if user := pyproject_config.get("user"):
        return str(user).strip()

    # Priority 3: Git user.name
    try:
        result = subprocess.run(
            ["git", "config", "user.name"],
            capture_output=True,
            text=True,
            timeout=1,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    return None


def is_reranking_model_cached() -> bool:
    """Check if reranking model is already downloaded/cached.

    Returns:
        True if model is cached and ready to use
    """
    try:
        from kagura.config.paths import get_data_dir

        # Check standard cache locations for sentence-transformers
        cache_dir = get_data_dir() / "models"
        model_path = cache_dir / "cross-encoder_ms-marco-MiniLM-L-6-v2"

        if model_path.exists():
            return True

        # Also check HuggingFace cache directory
        hf_cache = Path.home() / ".cache" / "huggingface" / "hub"
        if hf_cache.exists():
            # Look for model files
            for item in hf_cache.iterdir():
                if "cross-encoder" in item.name.lower() and "marco" in item.name.lower():
                    return True

    except Exception:
        pass

    return False


def get_reranking_enabled() -> bool:
    """Get reranking enabled flag from configuration.

    Priority order:
    1. Environment variable: $KAGURA_ENABLE_RERANKING (explicit override)
    2. pyproject.toml: [tool.kagura] enable_reranking = true
    3. Auto-enable if model is cached (ready to use)
    4. False (default for first-time users)

    Returns:
        True if reranking should be enabled

    Note:
        Auto-enables when model is already downloaded to improve UX.
        First-time users get reranking disabled (offline-friendly).
    """
    # Priority 1: Environment variable (explicit override)
    env_value = os.getenv("KAGURA_ENABLE_RERANKING", "").lower()
    if env_value in ("true", "1", "yes", "on"):
        return True
    elif env_value in ("false", "0", "no", "off"):
        return False

    # Priority 2: pyproject.toml
    pyproject_config = load_pyproject_config()
    if "enable_reranking" in pyproject_config:
        return bool(pyproject_config["enable_reranking"])

    # Priority 3: Auto-enable if model is cached (smart default)
    if is_reranking_model_cached():
        return True

    # Default: False (conservative for first-time users, offline-friendly)
    return False
