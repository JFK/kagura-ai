"""Simple Chat Agent Example

This example demonstrates the most basic usage of Kagura AI 2.0's @agent decorator
to create a conversational AI agent.
"""

import asyncio

from kagura import agent


@agent
async def chat(message: str) -> str:
    """You are a friendly AI assistant. Respond to: {{ message }}"""
    pass


async def main():
    """Run the simple chat agent with example queries."""
    print("=== Simple Chat Agent Example ===\n")

    # Example 1: Simple greeting
    response = await chat("Hello! How are you?")
    print(f"User: Hello! How are you?")
    print(f"Agent: {response}\n")

    # Example 2: Ask a question
    response = await chat("What is the meaning of life?")
    print(f"User: What is the meaning of life?")
    print(f"Agent: {response}\n")

    # Example 3: Request help
    response = await chat("Can you help me understand Python decorators?")
    print(f"User: Can you help me understand Python decorators?")
    print(f"Agent: {response}\n")


if __name__ == "__main__":
    asyncio.run(main())
