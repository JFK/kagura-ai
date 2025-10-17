"""Chatbot Preset - Conversational agent with memory."""

from kagura.builder import AgentBuilder


class ChatbotPreset(AgentBuilder):
    """Preset configuration for conversational chatbots.

    Features:
    - Context memory for conversation history
    - Moderate temperature for natural responses
    - Optimized for multi-turn conversations

    Example:
        >>> from kagura.agents import ChatbotPreset
        >>> chatbot = (
        ...     ChatbotPreset("my_chatbot")
        ...     .with_model("gpt-5-mini")
        ...     .build()
        ... )
        >>> result = await chatbot("Hello!")
    """

    def __init__(self, name: str):
        """Initialize chatbot preset.

        Args:
            name: Agent name
        """
        super().__init__(name)

        # Configure for conversational use
        self.with_memory(
            type="context",
            max_messages=100,  # Keep conversation history
        ).with_context(
            temperature=0.8,  # Natural, varied responses
            max_tokens=1000,  # Reasonable response length
        )
