# @agent Decorator

The `@agent` decorator is the core of Kagura AI, converting any async function into an AI agent with automatic LLM integration.

## Overview

The decorator:
1. Extracts function signature and parameters
2. Uses the docstring as a Jinja2 template
3. Calls the LLM with the rendered prompt
4. Parses the response based on return type hints
5. Returns a properly typed result

## Signature

```python
def agent(
    fn: Callable = None,
    *,
    model: str = "gpt-4o-mini",
    temperature: float = 0.7,
    max_tokens: int | None = None,
    **kwargs
) -> Callable
```

## Parameters

### Required Parameters

- **fn** (`Callable`): The async function to convert into an agent. When using `@agent` without parentheses, this is automatically passed.

### Optional Parameters

- **model** (`str`, default: `"gpt-4o-mini"`): The LLM model to use. Supports any model from [LiteLLM](https://docs.litellm.ai/docs/providers):
  - OpenAI: `"gpt-4o"`, `"gpt-4o-mini"`, `"gpt-3.5-turbo"`
  - Anthropic: `"claude-3-5-sonnet-20241022"`, `"claude-3-haiku-20240307"`
  - Google: `"gemini/gemini-pro"`, `"gemini/gemini-1.5-flash"`
  - Ollama: `"ollama/llama3.2"`, `"ollama/gemma2"`

- **temperature** (`float`, default: `0.7`): Sampling temperature (0.0 to 2.0). Lower values make output more focused and deterministic.

- **max_tokens** (`int | None`, default: `None`): Maximum tokens in the response. If not specified, uses the model's default.

- **kwargs**: Additional parameters passed to LiteLLM's `completion()` function.

## Return Value

Returns a wrapped async function with the same signature as the original, but with AI-powered behavior.

## Usage

### Basic Usage

```python
from kagura import agent

@agent
async def hello(name: str) -> str:
    '''Say hello to {{ name }}'''
    pass

result = await hello("World")
print(result)  # "Hello, World! How can I help you today?"
```

### With Custom Model

```python
@agent(model="gpt-4o")
async def analyze(text: str) -> str:
    '''Analyze the sentiment of: {{ text }}'''
    pass

result = await analyze("I love this product!")
print(result)  # "Positive sentiment..."
```

### With Temperature Control

```python
# More deterministic (lower temperature)
@agent(temperature=0.2)
async def translate(text: str, lang: str) -> str:
    '''Translate to {{ lang }}: {{ text }}'''
    pass

# More creative (higher temperature)
@agent(temperature=1.5)
async def creative_story(topic: str) -> str:
    '''Write a creative story about: {{ topic }}'''
    pass
```

### With Pydantic Models

```python
from pydantic import BaseModel

class Person(BaseModel):
    name: str
    age: int
    occupation: str

@agent
async def extract_person(text: str) -> Person:
    '''Extract person information from: {{ text }}'''
    pass

person = await extract_person("Alice is 30 years old and works as a software engineer")
print(f"{person.name}, {person.age}, {person.occupation}")
# Output: Alice, 30, software engineer
```

### With List Return Types

```python
@agent
async def extract_keywords(text: str) -> list[str]:
    '''Extract keywords from: {{ text }}'''
    pass

keywords = await extract_keywords("Python is a programming language for AI")
print(keywords)
# Output: ['Python', 'programming language', 'AI']
```

### Multiple Parameters

```python
@agent
async def summarize(text: str, max_words: int = 50) -> str:
    '''Summarize in {{ max_words }} words or less: {{ text }}'''
    pass

summary = await summarize("Long text here...", max_words=30)
```

## Docstring Templates

The docstring is treated as a Jinja2 template. All function parameters are available as template variables.

### Simple Variable Interpolation

```python
@agent
async def greet(name: str, greeting: str = "Hello") -> str:
    '''{{ greeting }}, {{ name }}! How are you?'''
    pass
```

### Conditional Logic

```python
@agent
async def format_response(query: str, formal: bool = False) -> str:
    '''
    {% if formal %}
    Respond formally to: {{ query }}
    {% else %}
    Respond casually to: {{ query }}
    {% endif %}
    '''
    pass
```

### Loops

```python
@agent
async def process_items(items: list[str]) -> str:
    '''
    Process the following items:
    {% for item in items %}
    - {{ item }}
    {% endfor %}
    '''
    pass
```

## Type-Based Response Parsing

The decorator automatically parses LLM responses based on the return type annotation:

| Return Type | Parsing Behavior |
|-------------|------------------|
| `str` | Returns raw response |
| `int` | Parses as integer |
| `float` | Parses as float |
| `bool` | Parses as boolean |
| `list[T]` | Parses as list of type T |
| `dict[K, V]` | Parses as dictionary |
| `Pydantic Model` | Validates and returns model instance |
| `Optional[T]` | Allows None values |

## Error Handling

### LLM API Errors

```python
from litellm import APIError

@agent
async def my_agent(query: str) -> str:
    '''Process: {{ query }}'''
    pass

try:
    result = await my_agent("test")
except APIError as e:
    print(f"LLM API error: {e}")
```

### Parsing Errors

```python
from pydantic import ValidationError

@agent
async def extract_data(text: str) -> Person:
    '''Extract person from: {{ text }}'''
    pass

try:
    result = await extract_data("invalid text")
except ValidationError as e:
    print(f"Failed to parse response: {e}")
```

## Advanced Features

### Accessing Agent Metadata

```python
@agent(model="gpt-4o", temperature=0.5)
async def my_agent(query: str) -> str:
    '''Answer: {{ query }}'''
    pass

# Check if function is an agent
print(hasattr(my_agent, '_is_agent'))  # True

# Access configuration
print(my_agent._model)  # "gpt-4o"
```

### Agent Composition

Agents can call other agents:

```python
@agent
async def extract_topic(text: str) -> str:
    '''Extract the main topic from: {{ text }}'''
    pass

@agent
async def elaborate(topic: str) -> str:
    '''Elaborate on: {{ topic }}'''
    pass

# Compose agents
text = "Quantum computing is revolutionary"
topic = await extract_topic(text)
elaboration = await elaborate(topic)
```

## Best Practices

1. **Clear Docstrings**: Write explicit instructions in the docstring
   ```python
   # Good
   '''Extract the person's name, age, and occupation from: {{ text }}'''

   # Less clear
   '''Process {{ text }}'''
   ```

2. **Appropriate Return Types**: Use the most specific type possible
   ```python
   # Good
   async def extract_person(text: str) -> Person:

   # Less good
   async def extract_person(text: str) -> dict:
   ```

3. **Temperature Selection**:
   - Use low temperature (0.0-0.3) for factual, deterministic tasks
   - Use medium temperature (0.7-1.0) for balanced responses
   - Use high temperature (1.0-2.0) for creative tasks

4. **Model Selection**:
   - Use `gpt-4o-mini` for simple tasks (faster, cheaper)
   - Use `gpt-4o` or `claude-3-5-sonnet` for complex reasoning
   - Use `claude-3-haiku` for fast, cost-effective responses

## Related

- [Template Engine](template.md) - Jinja2 templating details
- [Type Parser](parser.md) - Response parsing details
- [Quick Start](../quickstart.md) - Getting started guide
