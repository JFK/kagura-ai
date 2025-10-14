"""Full-Featured Agent - All Kagura features combined

This example demonstrates:
- Memory (working + persistent)
- Routing (semantic)
- Tools (custom functions)
- Pydantic models
- Caching
- All features in one agent
"""

import asyncio
from pathlib import Path
from pydantic import BaseModel, Field
from kagura import agent, tool, LLMConfig
from kagura.core.memory import MemoryManager, WorkingMemory


# Pydantic models for structured outputs
class TaskAnalysis(BaseModel):
    """Analysis of a user task"""
    task_type: str = Field(description="Type: question, command, or request")
    complexity: str = Field(description="Simple, moderate, or complex")
    requires_tools: bool = Field(description="Whether tools are needed")
    estimated_steps: int = Field(description="Number of steps needed")


# Custom tools
@tool
async def calculate(expression: str) -> str:
    """Safely evaluate mathematical expressions"""
    try:
        # In production, use a safe eval library
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"


@tool
async def save_note(content: str, filename: str) -> str:
    """Save a note to a file"""
    try:
        Path("./notes").mkdir(exist_ok=True)
        filepath = Path("./notes") / filename
        filepath.write_text(content)
        return f"Note saved to {filepath}"
    except Exception as e:
        return f"Error saving note: {str(e)}"


@tool
async def search_notes(keyword: str) -> str:
    """Search for notes containing a keyword"""
    notes_dir = Path("./notes")
    if not notes_dir.exists():
        return "No notes directory found"

    matches = []
    for note_file in notes_dir.glob("*.txt"):
        content = note_file.read_text()
        if keyword.lower() in content.lower():
            matches.append(f"{note_file.name}: {content[:50]}...")

    return "\n".join(matches) if matches else "No matching notes found"


# Configure with caching
config = LLMConfig(
    model="gpt-4o-mini",
    temperature=0.7,
    enable_cache=True,
    cache_ttl=3600
)

# Memory manager
memory = MemoryManager(backend=WorkingMemory())


# Main agent with all features
@agent(
    config=config,
    enable_memory=True,
    tools=[calculate, save_note, search_notes]
)
async def super_assistant(
    user_input: str,
    memory_manager: MemoryManager
) -> str:
    """
    You are a super-powered assistant with:
    - Memory of our conversation
    - Calculator tool
    - Note-taking capabilities
    - Search functionality

    User: {{ user_input }}

    Use all available tools and context to help effectively.
    """
    pass


# Task analyzer (returns structured data)
@agent(config=config)
async def task_analyzer(task: str) -> TaskAnalysis:
    """
    Analyze this task: {{ task }}

    Return structured analysis with task_type, complexity,
    requires_tools, and estimated_steps.
    """
    pass


async def main():
    print("Full-Featured Agent Demo - All Kagura Capabilities")
    print("=" * 60)

    # Demo conversation showing all features
    interactions = [
        "Hi! I'm working on a math project.",
        "Calculate 45 * 23 + 17",
        "Save that result to a note called math_results.txt",
        "Now calculate the square root of 144",
        "Save that to math_results.txt too",
        "Search my notes for 'math'",
        "What calculations have we done so far?"  # Tests memory
    ]

    for user_input in interactions:
        print(f"\n{'─' * 60}")
        print(f"User: {user_input}")

        # Analyze task (structured output)
        analysis = await task_analyzer(user_input)
        print(f"[Analysis: {analysis.task_type}, "
              f"complexity={analysis.complexity}, "
              f"tools={analysis.requires_tools}]")

        # Get response with all features
        response = await super_assistant(user_input, memory_manager=memory)
        print(f"Assistant: {response}")

        # Store in memory
        await memory.store(
            content=f"User: {user_input}\nAssistant: {response}",
            metadata={"task_type": analysis.task_type}
        )

    # Show final stats
    print(f"\n{'=' * 60}")
    print("Session Statistics:")
    stats = await memory.stats()
    print(f"  Interactions: {stats.get('total_memories', 0)}")
    print(f"  Notes created: {len(list(Path('./notes').glob('*.txt'))) if Path('./notes').exists() else 0}")


if __name__ == "__main__":
    asyncio.run(main())
