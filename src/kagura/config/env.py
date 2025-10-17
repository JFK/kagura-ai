"""
Centralized environment variable management for Kagura AI.

All environment variables used by Kagura should be documented and
accessed through this module. This provides:
- Single source of truth for environment variables
- Type safety through typed getters
- Backward compatibility with deprecation warnings
- Better discoverability for users

Example:
    >>> from kagura.config.env import get_openai_api_key
    >>> api_key = get_openai_api_key()
"""

import os
import warnings
from typing import Optional

# ============================================
# LLM Provider API Keys (via LiteLLM)
# ============================================


def get_openai_api_key() -> Optional[str]:
    """
    Get OpenAI API key from environment.

    Environment variable: OPENAI_API_KEY

    Returns:
        API key if set, None otherwise

    Example:
        >>> api_key = get_openai_api_key()
        >>> if api_key:
        ...     # Use OpenAI API
        ...     pass

    See: https://platform.openai.com/api-keys
    """
    return os.getenv("OPENAI_API_KEY")


def get_anthropic_api_key() -> Optional[str]:
    """
    Get Anthropic API key from environment.

    Environment variable: ANTHROPIC_API_KEY

    Returns:
        API key if set, None otherwise

    Example:
        >>> api_key = get_anthropic_api_key()
        >>> if api_key:
        ...     # Use Anthropic API
        ...     pass

    See: https://console.anthropic.com/
    """
    return os.getenv("ANTHROPIC_API_KEY")


def get_google_api_key() -> Optional[str]:
    """
    Get Google AI API key from environment.

    Environment variable: GOOGLE_API_KEY

    Used for:
    - Google Gemini API (multimodal features)
    - Image, video, audio, PDF analysis

    Returns:
        API key if set, None otherwise

    Example:
        >>> api_key = get_google_api_key()
        >>> if api_key:
        ...     # Use Gemini API
        ...     pass

    See: https://aistudio.google.com/app/apikey
    """
    return os.getenv("GOOGLE_API_KEY")


# ============================================
# Web Search API Keys
# ============================================


def get_brave_search_api_key() -> Optional[str]:
    """
    Get Brave Search API key from environment.

    Environment variable: BRAVE_SEARCH_API_KEY

    Returns:
        API key if set, None otherwise

    Example:
        >>> api_key = get_brave_search_api_key()
        >>> if api_key:
        ...     # Use Brave Search API
        ...     pass

    See: https://brave.com/search/api/
    """
    return os.getenv("BRAVE_SEARCH_API_KEY")


# ============================================
# Default Settings
# ============================================


def get_default_model() -> str:
    """
    Get default LLM model from environment.

    Environment variable: DEFAULT_MODEL

    Returns:
        Model name (default: "gpt-5-mini")

    Example:
        >>> model = get_default_model()
        >>> print(model)
        'gpt-4o-mini'

    Supported models:
    - OpenAI: gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-3.5-turbo
    - Anthropic: claude-3-5-sonnet-20241022, claude-3-opus, claude-3-haiku
    - Google: gemini-1.5-pro, gemini-1.5-flash, gemini-pro

    See: https://docs.litellm.ai/docs/providers for full list
    """
    return os.getenv("DEFAULT_MODEL", "gpt-5-mini")


def get_default_temperature() -> float:
    """
    Get default LLM temperature from environment.

    Environment variable: DEFAULT_TEMPERATURE

    Returns:
        Temperature value (default: 0.7)

    Valid range: 0.0 to 2.0
    - 0.0: Deterministic, focused
    - 0.7: Balanced (default)
    - 2.0: Creative, random

    Example:
        >>> temp = get_default_temperature()
        >>> print(temp)
        0.7
    """
    try:
        return float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))
    except ValueError:
        warnings.warn(
            f"Invalid DEFAULT_TEMPERATURE value: {os.getenv('DEFAULT_TEMPERATURE')}. "
            f"Using default: 0.7",
            UserWarning,
            stacklevel=2,
        )
        return 0.7


# ============================================
# Utility Functions
# ============================================


def list_env_vars() -> dict[str, Optional[str]]:
    """
    List all Kagura environment variables and their values.

    Returns:
        Dictionary mapping variable names to their values (or None if not set)

    Example:
        >>> env_vars = list_env_vars()
        >>> for name, value in env_vars.items():
        ...     status = "✓ Set" if value else "✗ Not set"
        ...     print(f"{name}: {status}")

    Note:
        API keys are not returned in plain text for security.
        Only their presence/absence is indicated.
    """
    return {
        "OPENAI_API_KEY": "***" if get_openai_api_key() else None,
        "ANTHROPIC_API_KEY": "***" if get_anthropic_api_key() else None,
        "GOOGLE_API_KEY": "***" if get_google_api_key() else None,
        "BRAVE_SEARCH_API_KEY": "***" if get_brave_search_api_key() else None,
        "DEFAULT_MODEL": get_default_model(),
        "DEFAULT_TEMPERATURE": str(get_default_temperature()),
    }


def check_required_env_vars() -> list[str]:
    """
    Check for required environment variables.

    Returns:
        List of missing required variables (empty if all set)

    Example:
        >>> missing = check_required_env_vars()
        >>> if missing:
        ...     print(f"Missing: {', '.join(missing)}")

    Note:
        At least one LLM provider API key is required:
        - OPENAI_API_KEY, ANTHROPIC_API_KEY, or GOOGLE_API_KEY
    """
    missing = []

    # At least one LLM provider key is required
    if not any(
        [
            get_openai_api_key(),
            get_anthropic_api_key(),
            get_google_api_key(),
        ]
    ):
        missing.append(
            "At least one of: OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY"
        )

    return missing
