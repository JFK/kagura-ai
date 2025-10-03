# Data Extractor Agent

Demonstrates structured data extraction using Pydantic models and type-based parsing.

## Overview

This example shows how Kagura AI 2.0 automatically parses LLM responses into structured Python objects:
- **Pydantic models**: Define data structure with validation
- **Type-based parsing**: Automatic conversion from LLM response to typed objects
- **Nested structures**: Support for complex data hierarchies
- **Lists**: Extract multiple items automatically

## Code

```python
from pydantic import BaseModel
from kagura import agent

class Person(BaseModel):
    name: str
    age: int
    occupation: str

@agent
async def extract_person(text: str) -> Person:
    """Extract person information from: {{ text }}"""
    pass
```

## How It Works

1. **Define Pydantic Model**: Create a class inheriting from `BaseModel`
2. **Use as Return Type**: Specify the model as the function's return type
3. **Automatic Parsing**: The @agent decorator:
   - Calls the LLM with the prompt
   - Receives JSON response
   - Validates against Pydantic model
   - Returns validated model instance
4. **Type Safety**: Full IDE support and type checking

## Examples

### 1. Single Object Extraction

```python
@agent
async def extract_person(text: str) -> Person:
    """Extract person information from: {{ text }}"""
    pass

person = await extract_person("Alice is 30 years old and works as a software engineer")
# Returns: Person(name='Alice', age=30, occupation='software engineer')
```

### 2. List Extraction

```python
@agent
async def extract_keywords(text: str) -> list[str]:
    """Extract keywords from: {{ text }}"""
    pass

keywords = await extract_keywords("Python is a programming language used for AI")
# Returns: ['Python', 'programming language', 'AI']
```

### 3. Nested Structures

```python
class TaskList(BaseModel):
    tasks: List[Task]

@agent
async def extract_tasks(text: str) -> TaskList:
    """Extract tasks from: {{ text }}"""
    pass
```

## Running the Example

```bash
python agent.py
```

## Expected Output

```
=== Data Extractor Agent Example ===

1. Extract Person Information
Input: Alice is 30 years old and works as a software engineer
Output: {'name': 'Alice', 'age': 30, 'occupation': 'software engineer'}
  Name: Alice
  Age: 30
  Occupation: software engineer

2. Extract Task List
Input: 1. Fix bug (high priority), 2. Write docs (low priority)
Output: Found 2 tasks
  ○ [3] Fix bug
  ○ [1] Write docs

3. Extract Keywords
Input: Python is a programming language used for AI and web development
Output: ['Python', 'programming language', 'AI', 'web development']
```

## Key Concepts

- **Pydantic models**: Structured data validation
- **Type-based parsing**: Automatic response conversion
- **Nested models**: Complex data structures
- **List extraction**: Multiple items in one response
- **Validation**: Automatic data validation by Pydantic

## Next Steps

- See [simple_chat](../simple_chat/) for basic agent usage
- See [code_generator](../code_generator/) for code execution
- See [workflow_example](../workflow_example/) for multi-step workflows
