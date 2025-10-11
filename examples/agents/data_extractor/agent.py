"""Data Extractor Agent Example

This example demonstrates structured data extraction using Pydantic models
with Kagura AI 2.0's type-based parsing.
"""

import asyncio
from typing import List

from pydantic import BaseModel

from kagura import agent


class Person(BaseModel):
    """Represents a person with basic information."""

    name: str
    age: int
    occupation: str


class Task(BaseModel):
    """Represents a task with title and priority."""

    task: str  # Task description
    priority: str  # Priority level: high, medium, low
    completed: bool = False


class TaskList(BaseModel):
    """Represents a list of tasks."""

    tasks: List[Task]


@agent
async def extract_person(text: str) -> Person:
    """Extract person information from: {{ text }}"""
    pass


@agent
async def extract_tasks(text: str) -> TaskList:
    """Extract tasks from: {{ text }}"""
    pass


@agent
async def extract_keywords(text: str) -> list[str]:
    """Extract keywords from: {{ text }}"""
    pass


async def main():
    """Run the data extractor agent with example queries."""
    print("=== Data Extractor Agent Example ===\n")

    # Example 1: Extract person information
    print("1. Extract Person Information")
    person_text = "Alice is 30 years old and works as a software engineer"
    person = await extract_person(person_text)
    print(f"Input: {person_text}")
    print(f"Output: {person.model_dump()}")
    print(f"  Name: {person.name}")
    print(f"  Age: {person.age}")
    print(f"  Occupation: {person.occupation}\n")

    # Example 2: Extract task list
    print("2. Extract Task List")
    task_text = "1. Fix bug (high priority), 2. Write docs (low priority), 3. Review PR (medium priority)"
    task_list = await extract_tasks(task_text)
    print(f"Input: {task_text}")
    print(f"Output: Found {len(task_list.tasks)} tasks")
    for t in task_list.tasks:
        status = "✓" if t.completed else "○"
        print(f"  {status} [{t.priority}] {t.task}")
    print()

    # Example 3: Extract keywords
    print("3. Extract Keywords")
    keyword_text = "Python is a programming language used for AI and web development"
    keywords = await extract_keywords(keyword_text)
    print(f"Input: {keyword_text}")
    print(f"Output: {keywords}\n")


if __name__ == "__main__":
    asyncio.run(main())
