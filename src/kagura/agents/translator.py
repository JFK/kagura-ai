"""Translator Preset - Multi-language translation agent."""

from kagura.builder import AgentBuilder


class TranslatorPreset(AgentBuilder):
    """Preset configuration for translation agents.

    Features:
    - Optimized for accurate translations
    - Lower temperature for consistency
    - Multi-language support
    - Optional caching for repeated translations

    Example:
        >>> from kagura.agents import TranslatorPreset
        >>> translator = (
        ...     TranslatorPreset("translator")
        ...     .with_model("gpt-5-mini")
        ...     .build()
        ... )
        >>> result = await translator("Translate 'hello' to Japanese")
    """

    def __init__(self, name: str, enable_cache: bool = True):
        """Initialize translator preset.

        Args:
            name: Agent name
            enable_cache: Enable response caching (default: True)
        """
        super().__init__(name)

        # Configure for translation
        self.with_context(
            temperature=0.3,  # Low temperature for consistency
            max_tokens=500,  # Translations are usually concise
        )

        # Note: Caching is enabled by default in LLMConfig
        # Users can customize via: .with_model("gpt-5-mini")
        self._enable_cache = enable_cache
