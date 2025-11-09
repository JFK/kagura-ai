"""API connectivity check utilities.

Provides unified API connectivity testing for all supported providers
(OpenAI, Anthropic, Google AI, Brave Search).

Consolidates duplicate logic from doctor.py and config_cli.py.
Related: Issue #538
"""

from __future__ import annotations

from typing import Literal


async def check_llm_api(
    provider: Literal["openai", "anthropic", "google"],
    api_key: str,
    model: str,
    timeout: int = 10,
) -> tuple[bool, str]:
    """Test LLM API connectivity.

    Args:
        provider: API provider name
        api_key: API key to test
        model: Model name to use for test
        timeout: Request timeout in seconds

    Returns:
        Tuple of (success: bool, message: str)

    Example:
        >>> success, msg = await check_llm_api("openai", "sk-...", "gpt-4o-mini")
        >>> print(f"OpenAI: {msg}")
    """
    try:
        from litellm import acompletion
    except ImportError:
        return False, "litellm not installed (optional dependency)"

    try:
        await acompletion(
            model=model,
            messages=[{"role": "user", "content": "hi"}],
            api_key=api_key,
            max_tokens=10,
            timeout=timeout,
        )
        return True, "Connection successful"

    except Exception as e:
        error_msg = str(e).lower()

        # Common error patterns across providers
        if any(
            pattern in error_msg
            for pattern in [
                "authentication",
                "invalid api key",
                "invalid x-api-key",
                "api key not valid",
                "invalid key",
            ]
        ):
            return False, "Invalid API key (check format and validity)"

        elif any(
            pattern in error_msg for pattern in ["rate_limit", "quota", "overloaded"]
        ):
            return False, "Rate limit exceeded or API overloaded (try again later)"

        # Max tokens errors from reasoning models = successful connection
        elif any(pattern in error_msg for pattern in ["max_tokens", "output limit"]):
            suffix = " (reasoning model)" if provider == "openai" else ""
            return True, f"Connection successful{suffix}"

        else:
            # Truncate long error messages
            return False, f"Connection failed: {str(e)[:200]}"


async def check_brave_search_api(
    api_key: str,
    timeout: int = 10,
) -> tuple[bool, str]:
    """Test Brave Search API connectivity.

    Args:
        api_key: Brave Search API key
        timeout: Request timeout in seconds

    Returns:
        Tuple of (success: bool, message: str)

    Example:
        >>> success, msg = await check_brave_search_api("BSA...")
        >>> print(f"Brave Search: {msg}")
    """
    try:
        import httpx
    except ImportError:
        return False, "httpx not installed (optional dependency)"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.search.brave.com/res/v1/web/search",
                params={"q": "test", "count": 1},
                headers={"X-Subscription-Token": api_key},
                timeout=timeout,
            )

            if response.status_code == 200:
                return True, "Connection successful"
            elif response.status_code == 401:
                return False, "Invalid API key"
            elif response.status_code == 429:
                return False, "Rate limit exceeded"
            else:
                return False, f"HTTP {response.status_code}: {response.text[:100]}"

    except Exception as e:
        return False, f"Connection failed: {str(e)[:200]}"


async def check_github_api(
    api_token: str,
    timeout: int = 10,
) -> tuple[bool, str]:
    """Test GitHub API connectivity.

    Args:
        api_token: GitHub API token
        timeout: Request timeout in seconds

    Returns:
        Tuple of (success: bool, message: str)

    Example:
        >>> success, msg = await check_github_api("ghp_...")
        >>> print(f"GitHub: {msg}")
    """
    try:
        import httpx
    except ImportError:
        return False, "httpx not installed (optional dependency)"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {api_token}",
                    "Accept": "application/vnd.github.v3+json",
                },
                timeout=timeout,
            )

            if response.status_code == 200:
                user_data = response.json()
                username = user_data.get("login", "unknown")
                return True, f"Connected as {username}"
            elif response.status_code == 401:
                return False, "Invalid token (check GITHUB_TOKEN)"
            elif response.status_code == 403:
                return False, "Token lacks permissions or rate limited"
            else:
                return False, f"HTTP {response.status_code}: {response.text[:100]}"

    except Exception as e:
        return False, f"Connection failed: {str(e)[:200]}"


async def check_api_configuration() -> list[tuple[str, str, str]]:
    """Check all API providers configuration and connectivity.

    Tests connectivity for configured API providers:
    - Anthropic (required)
    - OpenAI (optional)
    - Google AI (optional)
    - GitHub (optional)
    - Brave Search (optional)

    Returns:
        List of (provider_name, status, message) tuples
        Status: "ok" | "warning" | "error" | "info"

    Example:
        >>> results = await check_api_configuration()
        >>> for provider, status, msg in results:
        >>>     print(f"{provider}: [{status}] {msg}")
    """
    from kagura.config.env import (
        get_anthropic_api_key,
        get_anthropic_default_model,
        get_brave_search_api_key,
        get_github_token,
        get_google_ai_default_model,
        get_google_api_key,
        get_openai_api_key,
        get_openai_default_model,
    )

    results = []

    # Anthropic (required)
    anthropic_key = get_anthropic_api_key()
    if not anthropic_key:
        results.append(("Anthropic", "warning", "Not configured"))
    else:
        success, message = await check_llm_api(
            "anthropic", anthropic_key, get_anthropic_default_model()
        )
        status = "ok" if success else "error"
        results.append(("Anthropic", status, message))

    # OpenAI (optional)
    openai_key = get_openai_api_key()
    if not openai_key:
        results.append(("OpenAI", "info", "Not configured (optional)"))
    else:
        success, message = await check_llm_api(
            "openai", openai_key, get_openai_default_model()
        )
        status = "ok" if success else "warning"
        results.append(("OpenAI", status, message))

    # Google AI (optional)
    google_key = get_google_api_key()
    if not google_key:
        results.append(("Google AI", "info", "Not configured (optional)"))
    else:
        success, message = await check_llm_api(
            "google", google_key, get_google_ai_default_model()
        )
        status = "ok" if success else "warning"
        results.append(("Google AI", status, message))

    # GitHub (optional)
    github_token = get_github_token()
    if not github_token:
        results.append(("GitHub", "info", "Not configured (optional)"))
    else:
        success, message = await check_github_api(github_token)
        status = "ok" if success else "warning"
        results.append(("GitHub", status, message))

    # Brave Search (optional)
    brave_key = get_brave_search_api_key()
    if not brave_key:
        results.append(("Brave Search", "info", "Not configured (optional)"))
    else:
        success, message = await check_brave_search_api(brave_key)
        status = "ok" if success else "warning"
        results.append(("Brave Search", status, message))

    return results
