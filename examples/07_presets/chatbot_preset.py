"""ChatbotPreset - Conversational AI with personality

This example demonstrates:
- Using ChatbotPreset for conversations
- Customizing personality and style
- Memory-enabled chatbot
"""

import asyncio
from kagura.presets import ChatbotPreset


async def main():
    print("ChatbotPreset Demo")
    print("-" * 50)

    # Create chatbot with custom personality
    chatbot = (
        ChatbotPreset("friendly_assistant")
        .with_model("gpt-4o-mini")
        .with_context(
            personality="friendly and enthusiastic",
            style="casual but professional"
        )
        .build()
    )

    # Conversation
    conversations = [
        "Hi! What can you help me with?",
        "I'm learning Python programming",
        "Can you recommend some good resources?",
        "What topics should I focus on first?",
        "Thanks for the advice!"
    ]

    for message in conversations:
        response = await chatbot(message)
        print(f"\nUser: {message}")
        print(f"Bot: {response}")

    print("\n" + "=" * 50)
    print("ChatbotPreset Features:")
    print("- Conversational tone")
    print("- Context awareness")
    print("- Personality customization")
    print("- Memory support")


if __name__ == "__main__":
    asyncio.run(main())
