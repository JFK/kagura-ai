"""Multi-step Workflow Example

This example demonstrates how to compose multiple agents together
to create complex multi-step workflows with Kagura AI 2.0.
"""

import asyncio
from typing import List

from pydantic import BaseModel

from kagura import agent


class Step(BaseModel):
    """Represents a single step in a plan."""

    title: str
    description: str
    order: int


class Plan(BaseModel):
    """Represents a complete plan with multiple steps."""

    goal: str
    steps: List[Step]


@agent
async def create_plan(goal: str) -> Plan:
    """Create a detailed plan to achieve this goal: {{ goal }}

    Break it down into concrete, actionable steps with clear descriptions.
    """
    pass


@agent
async def execute_step(step_title: str, step_description: str) -> str:
    """Execute this step:
    Title: {{ step_title }}
    Description: {{ step_description }}

    Provide a brief summary of how to accomplish this step.
    """
    pass


@agent
async def review_results(goal: str, results: list[str]) -> str:
    """Review the results of executing a plan:

    Goal: {{ goal }}

    Step Results:
    {% for result in results %}
    - {{ result }}
    {% endfor %}

    Provide a summary of whether the goal was achieved and any next steps.
    """
    pass


async def run_workflow(goal: str):
    """Execute a complete workflow: plan → execute → review."""
    print(f"🎯 Goal: {goal}\n")

    # Step 1: Create the plan
    print("📋 Step 1: Creating plan...")
    plan = await create_plan(goal)
    print(f"   Created plan with {len(plan.steps)} steps\n")

    # Display the plan
    print("📝 Plan:")
    for step in plan.steps:
        print(f"   {step.order}. {step.title}")
        print(f"      {step.description}")
    print()

    # Step 2: Execute each step
    print("⚙️  Step 2: Executing plan...")
    results = []
    for step in plan.steps:
        print(f"   Executing: {step.title}")
        result = await execute_step(step.title, step.description)
        results.append(f"{step.title}: {result}")
        print(f"   ✓ {result[:100]}...")
    print()

    # Step 3: Review results
    print("🔍 Step 3: Reviewing results...")
    review = await review_results(goal, results)
    print(f"   {review}\n")

    return plan, results, review


async def main():
    """Run workflow examples."""
    print("=== Multi-step Workflow Example ===\n")

    # Example 1: Build a web application
    print("Example 1: Web Application Development")
    print("=" * 60)
    await run_workflow("Build a simple web application with user authentication")
    print()

    # Example 2: Learn a new skill
    print("\nExample 2: Learning Plan")
    print("=" * 60)
    await run_workflow("Learn Python programming in 30 days")
    print()


if __name__ == "__main__":
    asyncio.run(main())
