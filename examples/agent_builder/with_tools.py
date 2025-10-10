"""AgentBuilder with Tools Example

This example demonstrates how to create agents with tool integration
using AgentBuilder's fluent API.
"""

import asyncio
from datetime import datetime
from kagura import AgentBuilder


# Define example tools
def get_current_time() -> str:
    """Get the current time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def calculate(expression: str) -> float:
    """Safely evaluate a mathematical expression.

    Args:
        expression: Mathematical expression (e.g., "2 + 2", "10 * 5")

    Returns:
        Result of the calculation
    """
    try:
        # Only allow basic math operations for safety
        allowed_chars = set("0123456789+-*/(). ")
        if not all(c in allowed_chars for c in expression):
            raise ValueError("Invalid characters in expression")
        return float(eval(expression))
    except Exception as e:
        return f"Error: {str(e)}"


def search_database(query: str) -> list[dict]:
    """Search a mock database.

    Args:
        query: Search query

    Returns:
        List of matching results
    """
    # Mock database
    database = [
        {"id": 1, "name": "Python", "category": "programming"},
        {"id": 2, "name": "JavaScript", "category": "programming"},
        {"id": 3, "name": "Docker", "category": "devops"},
        {"id": 4, "name": "Kubernetes", "category": "devops"},
    ]

    # Simple search
    results = [
        item for item in database
        if query.lower() in item["name"].lower() or query.lower() in item["category"].lower()
    ]
    return results


async def main():
    """Demonstrate AgentBuilder with tool integration."""
    print("=== AgentBuilder with Tools ===\n")

    # Example 1: Single tool
    print("1. Agent with Single Tool")
    time_agent = (
        AgentBuilder("time_assistant")
        .with_model("gpt-4o-mini")
        .with_tools([get_current_time])
        .build()
    )

    response = await time_agent("What time is it?")
    print(f"Agent: {response}\n")

    # Example 2: Multiple tools
    print("2. Agent with Multiple Tools")
    multi_tool_agent = (
        AgentBuilder("assistant")
        .with_model("gpt-4o-mini")
        .with_tools([
            get_current_time,
            calculate,
            search_database
        ])
        .build()
    )

    response = await multi_tool_agent("What's 25 * 4?")
    print(f"Agent: {response}")

    response = await multi_tool_agent("Search for programming languages")
    print(f"Agent: {response}\n")

    # Example 3: Tools with memory
    print("3. Agent with Tools and Memory")
    tool_memory_agent = (
        AgentBuilder("smart_assistant")
        .with_model("gpt-4o-mini")
        .with_memory(type="context", max_messages=50)
        .with_tools([calculate])
        .build()
    )

    response1 = await tool_memory_agent("Calculate 100 + 50")
    print(f"Agent: {response1}")

    response2 = await tool_memory_agent("Now multiply that result by 2")
    print(f"Agent: {response2}\n")

    # Example 4: Tool-enabled workflow agent
    print("4. Workflow Agent with Tools")
    workflow_agent = (
        AgentBuilder("workflow_assistant")
        .with_model("gpt-4o-mini")
        .with_tools([get_current_time, calculate, search_database])
        .with_memory(type="persistent", max_messages=100)
        .with_context(
            temperature=0.3,  # More deterministic for calculations
            max_tokens=1000
        )
        .build()
    )

    response = await workflow_agent(
        "What time is it? Then search for devops tools and calculate how many results there are."
    )
    print(f"Agent: {response}\n")

    # Example 5: Custom tool configuration
    print("5. Agent with Custom Tool Setup")

    # Custom tools with specific configurations
    def weather_api(location: str) -> dict:
        """Mock weather API."""
        return {
            "location": location,
            "temperature": 22,
            "condition": "Sunny",
            "humidity": 65
        }

    weather_agent = (
        AgentBuilder("weather_assistant")
        .with_model("gpt-4o-mini")
        .with_tools([weather_api])
        .with_context(temperature=0.5)
        .build()
    )

    response = await weather_agent("What's the weather in Tokyo?")
    print(f"Agent: {response}\n")


if __name__ == "__main__":
    asyncio.run(main())
