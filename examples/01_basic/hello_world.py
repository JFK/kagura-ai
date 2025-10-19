"""Hello World - Simplest Kagura AI agent

This example demonstrates the most basic usage of Kagura AI:
- @agent decorator to convert a function into an AI agent
- Jinja2 template in docstring for prompt
- Simple string return type
"""

import asyncio

from kagura import agent


@agent
async def hello(name: str) -> str:
    """Say hello to {{ name }} in a friendly way."""
    pass  # Implementation replaced by AI


async def main():
    # Call the AI agent
    result = await hello("World")
    print(result)

    # Try with different names
    result2 = await hello("Alice")
    print(result2)


if __name__ == "__main__":
    asyncio.run(main())
