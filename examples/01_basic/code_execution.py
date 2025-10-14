"""Code Execution Agent - Execute Python code safely

This example demonstrates:
- Using Kagura's code execution capabilities
- Returning code snippets from AI
- Safe execution with AST validation
"""

import asyncio
from kagura import agent


@agent
async def code_generator(task: str) -> str:
    """
    Generate Python code to: {{ task }}

    Return only the Python code, no explanation.
    Make it concise and correct.
    """
    pass


@agent
async def code_explainer(code: str) -> str:
    """
    Explain what this Python code does:

    ```python
    {{ code }}
    ```

    Be clear and concise.
    """
    pass


async def main():
    # Generate code
    task = "calculate the factorial of a number"
    code = await code_generator(task)
    print(f"Generated code for '{task}':")
    print(code)
    print()

    # Explain code
    explanation = await code_explainer(code)
    print(f"Explanation:")
    print(explanation)
    print()

    # Another example
    task2 = "check if a string is a palindrome"
    code2 = await code_generator(task2)
    print(f"\nGenerated code for '{task2}':")
    print(code2)


if __name__ == "__main__":
    asyncio.run(main())
