# Tutorial 02: Template Engine

Learn how to use Jinja2 templates in your AI agents to create dynamic prompts.

## What You'll Learn

- How to use Jinja2 template syntax in agent docstrings
- Template variables and expressions
- Advanced template features (loops, conditionals)
- Best practices for prompt engineering

## Prerequisites

- Completed [Tutorial 01: Your First Agent](01-basic-agent.md)
- Basic understanding of Python f-strings

## Template Basics

Kagura uses [Jinja2](https://jinja.palletsprojects.com/) template syntax in agent docstrings. Templates are rendered before being sent to the LLM.

### Simple Variables

```python
from kagura import agent

@agent
async def greet(name: str) -> str:
    """Say hello to {{ name }}"""
    pass

# Template renders to: "Say hello to Alice"
result = await greet("Alice")
```

**Key Points:**
- Use `{{ variable }}` to insert values
- Variable names must match function parameters
- Values are automatically escaped

### Multiple Variables

```python
@agent
async def introduce(name: str, age: int, occupation: str) -> str:
    """
    Introduce yourself as {{ name }}, a {{ age }}-year-old {{ occupation }}.
    Be friendly and professional.
    """
    pass

result = await introduce("Bob", 30, "engineer")
# Template renders to: "Introduce yourself as Bob, a 30-year-old engineer..."
```

## Template Expressions

Jinja2 supports Python-like expressions:

```python
@agent
async def analyze(score: int) -> str:
    """
    The score is {{ score }}.
    {% if score >= 80 %}
    This is excellent performance!
    {% elif score >= 60 %}
    This is good performance.
    {% else %}
    This needs improvement.
    {% endif %}
    """
    pass
```

**Expressions You Can Use:**
- Arithmetic: `{{ price * 1.1 }}`
- Comparison: `{% if age > 18 %}`
- String methods: `{{ name.upper() }}`
- List access: `{{ items[0] }}`

## Loops

Process lists and dictionaries in templates:

```python
from typing import List

@agent
async def summarize_items(items: List[str]) -> str:
    """
    Summarize the following items:
    {% for item in items %}
    - {{ item }}
    {% endfor %}

    Provide a brief overview.
    """
    pass

result = await summarize_items(["apples", "oranges", "bananas"])
```

**Loop Features:**
- `{% for item in list %}`: Iterate over lists
- `{{ loop.index }}`: Current iteration (1-based)
- `{{ loop.first }}`: True on first iteration
- `{{ loop.last }}`: True on last iteration

## Filters

Transform values with filters:

```python
@agent
async def format_text(text: str) -> str:
    """
    Original: {{ text }}
    Uppercase: {{ text | upper }}
    Capitalized: {{ text | capitalize }}
    First 50 chars: {{ text[:50] }}
    """
    pass
```

**Common Filters:**
- `upper`, `lower`, `capitalize`: Text transformation
- `length`: Get length of string/list
- `default(value)`: Default value if undefined
- `join(separator)`: Join list items

## Complex Data Structures

Work with dictionaries and objects:

```python
from pydantic import BaseModel
from typing import Dict

class User(BaseModel):
    name: str
    email: str
    age: int

@agent
async def analyze_user(user: User) -> str:
    """
    Analyze user profile:
    - Name: {{ user.name }}
    - Email: {{ user.email }}
    - Age: {{ user.age }}

    Provide insights about this user.
    """
    pass

user = User(name="Alice", email="alice@example.com", age=25)
result = await analyze_user(user)
```

**Accessing Data:**
- Dictionary: `{{ data['key'] }}` or `{{ data.key }}`
- Object attributes: `{{ obj.attribute }}`
- Nested: `{{ user.address.city }}`

## Multiline Templates

For complex prompts, use multiline docstrings:

```python
@agent
async def write_email(
    recipient: str,
    subject: str,
    points: List[str],
    tone: str = "professional"
) -> str:
    """
    Write an email with the following specifications:

    To: {{ recipient }}
    Subject: {{ subject }}
    Tone: {{ tone }}

    Key points to cover:
    {% for point in points %}
    {{ loop.index }}. {{ point }}
    {% endfor %}

    Make it {{ tone }} and concise.
    """
    pass
```

## Best Practices

### 1. Clear Instructions

```python
# ✅ Good: Clear instructions
@agent
async def translate(text: str, target_lang: str) -> str:
    """
    Translate the following text to {{ target_lang }}:
    {{ text }}

    Return only the translated text, no explanations.
    """
    pass

# ❌ Bad: Vague instructions
@agent
async def translate(text: str, target_lang: str) -> str:
    """{{ text }} {{ target_lang }}"""
    pass
```

### 2. Structure Your Prompts

```python
@agent
async def analyze(data: str) -> str:
    """
    ## Task
    Analyze the following data.

    ## Data
    {{ data }}

    ## Requirements
    - Identify key trends
    - Provide insights
    - Be concise
    """
    pass
```

### 3. Use Conditionals Wisely

```python
@agent
async def respond(message: str, context: str = None) -> str:
    """
    {% if context %}
    Context: {{ context }}
    {% endif %}

    User message: {{ message }}

    Respond appropriately{{ " based on the context" if context else "" }}.
    """
    pass
```

### 4. Validate Input

```python
@agent
async def process(items: List[str]) -> str:
    """
    {% if items %}
    Process these items:
    {% for item in items %}
    - {{ item }}
    {% endfor %}
    {% else %}
    No items to process.
    {% endif %}
    """
    pass
```

## Common Patterns

### Chain of Thought

```python
@agent
async def solve_math(problem: str) -> str:
    """
    Solve this math problem: {{ problem }}

    Think step by step:
    1. First, identify the operation
    2. Then, calculate the result
    3. Finally, verify your answer
    """
    pass
```

### Few-Shot Learning

```python
@agent
async def classify(text: str) -> str:
    """
    Classify the sentiment of the text.

    Examples:
    Text: "I love this!" → Sentiment: positive
    Text: "This is terrible" → Sentiment: negative
    Text: "It's okay" → Sentiment: neutral

    Text: {{ text }} → Sentiment: ?
    """
    pass
```

### Role-Based Prompts

```python
@agent
async def code_review(code: str, language: str) -> str:
    """
    You are an expert {{ language }} developer.
    Review this code and provide suggestions:

    ```{{ language }}
    {{ code }}
    ```

    Focus on:
    - Code quality
    - Best practices
    - Potential bugs
    """
    pass
```

## Troubleshooting

### Template Syntax Errors

```python
# ❌ Wrong: Missing closing tag
"""
{% for item in items %}
{{ item }}
"""

# ✅ Correct: Proper closing
"""
{% for item in items %}
{{ item }}
{% endfor %}
"""
```

### Variable Not Found

```python
# ❌ Wrong: Variable doesn't match parameter
@agent
async def greet(name: str) -> str:
    """Hello {{ username }}"""  # username doesn't exist
    pass

# ✅ Correct: Variable matches parameter
@agent
async def greet(name: str) -> str:
    """Hello {{ name }}"""
    pass
```

### Escaping Special Characters

```python
# If you need literal {{ or }}
@agent
async def explain() -> str:
    """
    In Jinja2, use {% raw %}{{ variable }}{% endraw %} for templates.
    """
    pass
```

## Practice Exercises

### Exercise 1: User Profile Generator

Create an agent that generates user profiles:

```python
from typing import List

@agent
async def create_profile(
    name: str,
    skills: List[str],
    experience_years: int
) -> str:
    """
    # TODO: Write template that:
    # - Introduces the person
    # - Lists their skills
    # - Mentions experience level
    """
    pass
```

### Exercise 2: Conditional Email Writer

Create an agent with conditional formatting:

```python
@agent
async def write_email(
    recipient: str,
    is_urgent: bool,
    has_attachments: bool
) -> str:
    """
    # TODO: Write template that:
    # - Adds [URGENT] to subject if urgent
    # - Mentions attachments if present
    """
    pass
```

### Exercise 3: Data Analyzer

Create an agent that analyzes data with loops:

```python
from typing import Dict

@agent
async def analyze_metrics(metrics: Dict[str, float]) -> str:
    """
    # TODO: Write template that:
    # - Iterates over metrics
    # - Highlights values > 80
    # - Provides summary
    """
    pass
```

## Next Steps

- [Tutorial 03: Type-Based Parsing](03-type-parsing.md) - Learn how to parse structured responses
- [API Reference: Templates](../api/agent.md#templates) - Complete template documentation

## Additional Resources

- [Jinja2 Documentation](https://jinja.palletsprojects.com/)
- [Prompt Engineering Guide](https://www.promptingguide.ai/)
