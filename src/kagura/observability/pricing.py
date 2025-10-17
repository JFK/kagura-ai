"""LLM API pricing and cost calculation

Provides cost calculation for various LLM models based on token usage.
"""

from __future__ import annotations


def calculate_cost(usage: dict[str, int], model: str) -> float:
    """Calculate LLM API cost based on token usage

    Args:
        usage: Dict with 'prompt_tokens' and 'completion_tokens'
        model: Model name (e.g., "gpt-5-mini", "claude-3-5-sonnet-20241022")

    Returns:
        Cost in USD

    Example:
        >>> usage = {"prompt_tokens": 100, "completion_tokens": 50}
        >>> cost = calculate_cost(usage, "gpt-5-mini")
        >>> print(f"${cost:.4f}")  # $0.0001
    """
    # Pricing as of October 2025 (per 1M tokens)
    # Source: OpenAI, Anthropic, Google pricing pages
    pricing = {
        # OpenAI models
        "gpt-5-mini": {"prompt": 0.15, "completion": 0.60},
        "gpt-4o": {"prompt": 2.50, "completion": 10.00},
        "gpt-4o-2024-11-20": {"prompt": 2.50, "completion": 10.00},
        "gpt-4-turbo": {"prompt": 10.00, "completion": 30.00},
        "gpt-4": {"prompt": 30.00, "completion": 60.00},
        "gpt-3.5-turbo": {"prompt": 0.50, "completion": 1.50},
        # Anthropic models
        "claude-3-5-sonnet-20241022": {"prompt": 3.00, "completion": 15.00},
        "claude-3-5-sonnet-20240620": {"prompt": 3.00, "completion": 15.00},
        "claude-3-opus-20240229": {"prompt": 15.00, "completion": 75.00},
        "claude-3-sonnet-20240229": {"prompt": 3.00, "completion": 15.00},
        "claude-3-haiku-20240307": {"prompt": 0.25, "completion": 1.25},
        # Google models
        "gemini-1.5-pro": {"prompt": 1.25, "completion": 5.00},
        "gemini-1.5-pro-002": {"prompt": 1.25, "completion": 5.00},
        "gemini-1.5-flash": {"prompt": 0.075, "completion": 0.30},
        "gemini-1.5-flash-002": {"prompt": 0.075, "completion": 0.30},
        "gemini-1.0-pro": {"prompt": 0.50, "completion": 1.50},
        # OpenAI o1 models
        "o1-preview": {"prompt": 15.00, "completion": 60.00},
        "o1-mini": {"prompt": 3.00, "completion": 12.00},
    }

    # Default pricing for unknown models (conservative estimate)
    default = {"prompt": 1.0, "completion": 3.0}

    model_pricing = pricing.get(model, default)

    prompt_tokens = usage.get("prompt_tokens", 0)
    completion_tokens = usage.get("completion_tokens", 0)

    prompt_cost = (prompt_tokens / 1_000_000) * model_pricing["prompt"]
    completion_cost = (completion_tokens / 1_000_000) * model_pricing["completion"]

    return prompt_cost + completion_cost


def get_model_pricing(model: str) -> dict[str, float]:
    """Get pricing info for a specific model

    Args:
        model: Model name

    Returns:
        Dict with 'prompt' and 'completion' prices (per 1M tokens)

    Example:
        >>> pricing = get_model_pricing("gpt-5-mini")
        >>> print(f"Prompt: ${pricing['prompt']}/1M tokens")
    """
    pricing = {
        "gpt-5-mini": {"prompt": 0.15, "completion": 0.60},
        "gpt-4o": {"prompt": 2.50, "completion": 10.00},
        "claude-3-5-sonnet-20241022": {"prompt": 3.00, "completion": 15.00},
        "gemini-1.5-pro": {"prompt": 1.25, "completion": 5.00},
        "gemini-1.5-flash": {"prompt": 0.075, "completion": 0.30},
    }

    return pricing.get(model, {"prompt": 1.0, "completion": 3.0})


__all__ = ["calculate_cost", "get_model_pricing"]
