# Tutorial 03: Type-Based Parsing

Learn how to use Python type hints to automatically parse LLM responses into structured data.

## What You'll Learn

- How type-based parsing works in Kagura
- Using Pydantic models for complex structures
- Handling lists, dicts, and nested objects
- Error handling and validation

## Prerequisites

- Completed [Tutorial 01: Basic Agent](01-basic-agent.md)
- Basic understanding of Python type hints
- Familiarity with Pydantic (helpful but not required)

## Why Type-Based Parsing?

LLMs return unstructured text, but your application needs structured data. Kagura automatically converts LLM responses to Python types based on your return type annotation.

```python
# Without parsing: raw string
async def get_age(name: str) -> str:
    """What is {{ name }}'s age?"""
    pass

result = await get_age("Alice")
# result = "Alice is 25 years old."  ← Hard to use in code

# With parsing: structured data
async def get_age(name: str) -> int:
    """What is {{ name }}'s age? Return only the number."""
    pass

result = await get_age("Alice")
# result = 25  ← Easy to use!
```

## Basic Types

### Strings

```python
from kagura import agent

@agent
async def summarize(text: str) -> str:
    """Summarize this in one sentence: {{ text }}"""
    pass

result = await summarize("Long article...")
# result: str = "Article summary."
```

### Numbers

```python
@agent
async def count_words(text: str) -> int:
    """Count the words in: {{ text }}. Return only the number."""
    pass

result = await count_words("Hello world")
# result: int = 2

@agent
async def calculate_average(numbers: list[int]) -> float:
    """Calculate the average of {{ numbers }}. Return only the number."""
    pass

result = await calculate_average([1, 2, 3, 4, 5])
# result: float = 3.0
```

### Booleans

```python
@agent
async def is_positive(text: str) -> bool:
    """Is this text positive in sentiment? {{ text }}
    Return only 'true' or 'false'."""
    pass

result = await is_positive("I love this!")
# result: bool = True
```

## Collections

### Lists

```python
from typing import List

@agent
async def extract_keywords(text: str) -> List[str]:
    """Extract keywords from: {{ text }}
    Return as JSON array."""
    pass

result = await extract_keywords("Python is great for AI")
# result: List[str] = ["Python", "AI", "programming"]
```

**Supported List Types:**
- `List[str]`: List of strings
- `List[int]`: List of integers
- `List[float]`: List of floats
- `List[YourModel]`: List of Pydantic models

### Dictionaries

```python
from typing import Dict

@agent
async def extract_metadata(text: str) -> Dict[str, str]:
    """Extract metadata from: {{ text }}
    Return as JSON object."""
    pass

result = await extract_metadata("Title: Hello\nAuthor: Alice")
# result: Dict[str, str] = {"title": "Hello", "author": "Alice"}
```

## Pydantic Models

For complex structures, use Pydantic models:

```python
from pydantic import BaseModel, Field
from typing import List

class Person(BaseModel):
    name: str
    age: int
    email: str

@agent
async def extract_person(text: str) -> Person:
    """Extract person information from: {{ text }}
    Return as JSON object with fields: name, age, email."""
    pass

result = await extract_person("Alice (25) - alice@example.com")
# result: Person = Person(name="Alice", age=25, email="alice@example.com")
```

### Model Validation

Pydantic automatically validates the data:

```python
from pydantic import BaseModel, EmailStr, validator

class User(BaseModel):
    name: str
    email: EmailStr  # Validates email format
    age: int

    @validator('age')
    def age_must_be_positive(cls, v):
        if v < 0:
            raise ValueError('age must be positive')
        return v

@agent
async def extract_user(text: str) -> User:
    """Extract user info from: {{ text }}
    Return as JSON: {name, email, age}"""
    pass

# Valid input
result = await extract_user("Bob, bob@example.com, 30")
# result: User(name="Bob", email="bob@example.com", age=30)

# Invalid input (bad email)
# Will raise ValidationError
```

### Field Descriptions

Help the LLM understand fields:

```python
class Article(BaseModel):
    title: str = Field(description="The article title")
    summary: str = Field(description="Brief summary, max 100 words")
    tags: List[str] = Field(description="Relevant tags, 3-5 items")
    published: bool = Field(description="Whether article is published")

@agent
async def analyze_article(content: str) -> Article:
    """Analyze this article: {{ content }}
    Return as JSON with: title, summary, tags, published."""
    pass
```

## Nested Structures

### Nested Models

```python
class Address(BaseModel):
    street: str
    city: str
    country: str

class Company(BaseModel):
    name: str
    address: Address
    employees: int

@agent
async def extract_company(text: str) -> Company:
    """Extract company information from: {{ text }}
    Return as JSON with nested address object."""
    pass

result = await extract_company("Acme Corp, 123 Main St, NYC, USA, 500 employees")
# result: Company(
#     name="Acme Corp",
#     address=Address(street="123 Main St", city="NYC", country="USA"),
#     employees=500
# )
```

### Lists of Models

```python
class Task(BaseModel):
    title: str
    priority: str
    estimated_hours: int

@agent
async def extract_tasks(text: str) -> List[Task]:
    """Extract tasks from: {{ text }}
    Return as JSON array of objects."""
    pass

result = await extract_tasks("""
    1. Fix bug - High priority - 3 hours
    2. Write docs - Low priority - 5 hours
""")
# result: List[Task] = [
#     Task(title="Fix bug", priority="High", estimated_hours=3),
#     Task(title="Write docs", priority="Low", estimated_hours=5)
# ]
```

## Advanced Patterns

### Optional Fields

```python
from typing import Optional

class Product(BaseModel):
    name: str
    price: float
    discount: Optional[float] = None
    description: Optional[str] = None

@agent
async def extract_product(text: str) -> Product:
    """Extract product info from: {{ text }}
    Return as JSON. discount and description are optional."""
    pass

result = await extract_product("Laptop $999")
# result: Product(name="Laptop", price=999.0, discount=None, description=None)
```

### Union Types

```python
from typing import Union

@agent
async def parse_value(text: str) -> Union[int, str]:
    """Parse the value from: {{ text }}
    Return as number if numeric, otherwise as string."""
    pass

result1 = await parse_value("42")        # returns int: 42
result2 = await parse_value("hello")     # returns str: "hello"
```

### Enums

```python
from enum import Enum

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class Issue(BaseModel):
    title: str
    priority: Priority

@agent
async def extract_issue(text: str) -> Issue:
    """Extract issue from: {{ text }}
    Priority must be: low, medium, or high."""
    pass

result = await extract_issue("Fix login bug - high priority")
# result: Issue(title="Fix login bug", priority=Priority.HIGH)
```

## Best Practices

### 1. Clear Return Format Instructions

```python
# ✅ Good: Explicit format
@agent
async def extract_data(text: str) -> Person:
    """Extract person from: {{ text }}
    Return as JSON: {"name": str, "age": int, "email": str}"""
    pass

# ❌ Bad: Unclear format
@agent
async def extract_data(text: str) -> Person:
    """Get person from: {{ text }}"""
    pass
```

### 2. Use Field Descriptions

```python
# ✅ Good: Descriptive fields
class Report(BaseModel):
    summary: str = Field(description="Executive summary, 2-3 sentences")
    findings: List[str] = Field(description="Key findings, bullet points")
    score: int = Field(description="Overall score 0-100")

# ❌ Bad: No descriptions
class Report(BaseModel):
    summary: str
    findings: List[str]
    score: int
```

### 3. Validate Constraints

```python
from pydantic import validator, Field

class Temperature(BaseModel):
    celsius: float = Field(ge=-273.15, description="Temperature in Celsius")

    @validator('celsius')
    def validate_temp(cls, v):
        if v < -273.15:
            raise ValueError('Temperature below absolute zero')
        return v
```

### 4. Handle Errors Gracefully

```python
from pydantic import ValidationError

@agent
async def extract_safe(text: str) -> Optional[Person]:
    """Extract person from: {{ text }}
    Return as JSON or null if not found."""
    pass

try:
    result = await extract_safe("No person here")
except ValidationError as e:
    print(f"Validation failed: {e}")
```

## Error Handling

### Validation Errors

```python
from pydantic import ValidationError

@agent
async def parse_age(text: str) -> int:
    """Extract age from: {{ text }}. Return only the number."""
    pass

try:
    result = await parse_age("Alice is twenty-five")
    # LLM returns "twenty-five" instead of 25
except ValidationError as e:
    print(f"Failed to parse: {e}")
    # Handle error: retry, use default, etc.
```

### Missing Fields

```python
class Contact(BaseModel):
    name: str
    email: str
    phone: str  # Required

@agent
async def extract_contact(text: str) -> Contact:
    """Extract contact from: {{ text }}
    Return JSON with: name, email, phone."""
    pass

# If LLM omits phone, ValidationError is raised
try:
    result = await extract_contact("John, john@example.com")
except ValidationError as e:
    print("Missing required field:", e)
```

### Type Mismatches

```python
@agent
async def get_count(text: str) -> int:
    """Count items in: {{ text }}. Return only the number."""
    pass

# If LLM returns "five" instead of 5
try:
    result = await get_count("five items")
except ValidationError:
    # Retry with more explicit instructions
    @agent
    async def get_count_strict(text: str) -> int:
        """Count items in: {{ text }}.
        Return ONLY a numeric digit, no words."""
        pass
```

## Common Patterns

### Progressive Extraction

```python
# Step 1: Extract basic info
@agent
async def extract_basic(text: str) -> Dict[str, str]:
    """Extract key-value pairs from: {{ text }}"""
    pass

# Step 2: Parse into model
basic = await extract_basic(text)
person = Person(**basic)
```

### Fallback Values

```python
class Config(BaseModel):
    timeout: int = 30  # Default value
    retries: int = 3
    debug: bool = False

@agent
async def parse_config(text: str) -> Config:
    """Parse config from: {{ text }}
    Use defaults for missing values."""
    pass
```

### Multi-Step Validation

```python
class ValidatedData(BaseModel):
    data: str

    @validator('data')
    def clean_data(cls, v):
        # Clean and validate
        return v.strip().lower()

@agent
async def extract_and_validate(text: str) -> ValidatedData:
    """Extract data from: {{ text }}"""
    pass
```

## Practice Exercises

### Exercise 1: Contact Extractor

Create a model for contact information:

```python
class Contact(BaseModel):
    # TODO: Add fields for name, email, phone, company
    pass

@agent
async def extract_contact(text: str) -> Contact:
    """# TODO: Write prompt to extract contact info"""
    pass
```

### Exercise 2: Product List Parser

Parse a list of products:

```python
class Product(BaseModel):
    # TODO: Add fields for name, price, stock
    pass

@agent
async def parse_products(text: str) -> List[Product]:
    """# TODO: Write prompt to parse product list"""
    pass
```

### Exercise 3: Nested Organization

Create a nested structure:

```python
class Employee(BaseModel):
    # TODO: name, role, salary
    pass

class Department(BaseModel):
    # TODO: name, employees list, budget
    pass

@agent
async def parse_org(text: str) -> Department:
    """# TODO: Write prompt to parse organization"""
    pass
```

## Troubleshooting

### LLM Returns Wrong Format

```python
# Problem: LLM returns "The age is 25" instead of just "25"

# Solution: Be more explicit
@agent
async def get_age(name: str) -> int:
    """What is {{ name }}'s age?
    IMPORTANT: Return ONLY the numeric age, nothing else.
    Example: 25"""
    pass
```

### Validation Fails Repeatedly

```python
# Problem: LLM returns data that fails validation

# Solution: Relax constraints or provide examples
class Person(BaseModel):
    age: int = Field(ge=0, le=150, description="Age between 0-150")

@agent
async def extract_person(text: str) -> Person:
    """Extract person from: {{ text }}
    Return JSON: {"name": "string", "age": number between 0-150}
    Example: {"name": "Alice", "age": 25}"""
    pass
```

## Next Steps

- [Tutorial 04: Code Execution](04-code-execution.md) - Execute Python code with AI
- [API Reference: Type Parsing](../api/agent.md#type-parsing) - Complete parsing documentation
- [Pydantic Documentation](https://docs.pydantic.dev/) - Learn more about Pydantic

## Additional Resources

- [Type Hints Cheat Sheet](https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html)
- [Pydantic Field Types](https://docs.pydantic.dev/latest/usage/types/)
