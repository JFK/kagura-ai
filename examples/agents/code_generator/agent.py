"""Code Generator Agent Example

This example demonstrates safe Python code generation and execution
using Kagura AI 2.0's built-in code executor.
"""

import asyncio

from kagura.agents import execute_code


async def main():
    """Run the code generator agent with example queries."""
    print("=== Code Generator Agent Example ===\n")

    # Example 1: Mathematical calculation
    print("1. Calculate Factorial")
    result = await execute_code("Calculate the factorial of 10")
    if result["success"]:
        print(f"Task: Calculate the factorial of 10")
        print(f"Generated Code:\n{result['code']}")
        print(f"Result: {result['result']}\n")
    else:
        print(f"Error: {result['error']}\n")

    # Example 2: String manipulation
    print("2. String Processing")
    result = await execute_code("Reverse the string 'Hello, World!' and convert it to uppercase")
    if result["success"]:
        print(f"Task: Reverse and uppercase string")
        print(f"Generated Code:\n{result['code']}")
        print(f"Result: {result['result']}\n")
    else:
        print(f"Error: {result['error']}\n")

    # Example 3: List operations
    print("3. List Operations")
    result = await execute_code("Create a list of squares of numbers from 1 to 10")
    if result["success"]:
        print(f"Task: Generate list of squares")
        print(f"Generated Code:\n{result['code']}")
        print(f"Result: {result['result']}\n")
    else:
        print(f"Error: {result['error']}\n")

    # Example 4: Data processing
    print("4. Data Analysis")
    result = await execute_code(
        "Calculate the mean and standard deviation of the list [10, 20, 30, 40, 50]"
    )
    if result["success"]:
        print(f"Task: Statistical analysis")
        print(f"Generated Code:\n{result['code']}")
        print(f"Result: {result['result']}\n")
    else:
        print(f"Error: {result['error']}\n")

    # Example 5: Error handling
    print("5. Error Handling Example")
    result = await execute_code("Divide 100 by 0")
    if result["success"]:
        print(f"Result: {result['result']}\n")
    else:
        print(f"Task: Divide by zero (expected to fail)")
        print(f"Error caught: {result['error']}\n")


if __name__ == "__main__":
    asyncio.run(main())
