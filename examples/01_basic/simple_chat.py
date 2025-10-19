"""Simple Chatbot - Basic conversational agent

This example demonstrates:
- Creating a simple chatbot with @agent
- Handling user input in a loop
- Basic conversation management
"""

import asyncio

from kagura import agent


@agent
async def chatbot(message: str) -> str:
    """
    You are a helpful and friendly assistant.

    User: {{ message }}

    Respond naturally and helpfully.
    """
    pass


async def main():
    print("Simple Chatbot (type 'exit' to quit)")
    print("-" * 40)

    while True:
        # Get user input
        user_input = input("You: ")

        if user_input.lower() in ["exit", "quit", "bye"]:
            print("Chatbot: Goodbye! Have a great day!")
            break

        # Get AI response
        response = await chatbot(user_input)
        print(f"Chatbot: {response}\n")


if __name__ == "__main__":
    asyncio.run(main())
