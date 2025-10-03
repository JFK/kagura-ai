# Frequently Asked Questions

Common questions about Kagura AI 2.0.

## General

### What is Kagura AI 2.0?

Kagura AI 2.0 is a Python-first AI agent framework that lets you convert any async function into an AI agent with a single `@agent` decorator. It features type-based response parsing, Jinja2 templates, and safe code execution.

### What's the difference between Kagura AI 1.x and 2.0?

**1.x** used YAML configuration files and a complex multi-agent orchestration system:
```yaml
# agent.yml
type: atomic
llm:
  model: gpt-4
prompt:
  - language: en
    template: "You are helpful"
```

**2.0** is Python-first with a simple decorator:
```python
@agent
async def assistant(query: str) -> str:
    '''You are helpful. Answer: {{ query }}'''
    pass
```

**Key changes:**
- No more YAML configuration
- Simple `@agent` decorator instead of `Agent.assigner()`
- `kagura repl` instead of `kagura chat`
- Built-in code execution
- Type-based parsing with Pydantic

See the [Migration Guide](../../ai_docs/migration_guide.md) for details.

### Which LLM providers are supported?

Kagura AI uses [LiteLLM](https://docs.litellm.ai/docs/providers), supporting 100+ providers:

- **OpenAI**: `gpt-4o`, `gpt-4o-mini`, `gpt-3.5-turbo`
- **Anthropic**: `claude-3-5-sonnet-20241022`, `claude-3-haiku-20240307`
- **Google**: `gemini/gemini-pro`, `gemini/gemini-1.5-flash`
- **Azure OpenAI**: `azure/gpt-4`
- **Ollama**: `ollama/llama3.2`, `ollama/gemma2`
- **Cohere**: `command-r-plus`, `command-r`
- **Groq**: `groq/llama3-70b`, `groq/mixtral-8x7b`
- And many more...

### What Python version is required?

Python 3.11 or higher.

### How do I install Kagura AI?

```bash
pip install kagura-ai
```

Or with uv:
```bash
uv add kagura-ai
```

See [Installation Guide](installation.md) for details.

## Usage

### How do I set my API key?

Set the appropriate environment variable before running your code:

```bash
# OpenAI
export OPENAI_API_KEY="your-key-here"

# Anthropic
export ANTHROPIC_API_KEY="your-key-here"

# Google
export GOOGLE_API_KEY="your-key-here"
```

Or in Python:
```python
import os
os.environ["OPENAI_API_KEY"] = "your-key-here"
```

### How do I handle errors in agents?

Wrap agent calls in try-except:

```python
from litellm import APIError
from pydantic import ValidationError

try:
    result = await my_agent("input")
except APIError as e:
    # LLM API error (auth, rate limit, etc.)
    print(f"API error: {e}")
except ValidationError as e:
    # Pydantic parsing error
    print(f"Validation error: {e}")
except Exception as e:
    # Other errors
    print(f"Error: {e}")
```

### Can I use custom Pydantic validators?

Yes! All Pydantic features work:

```python
from pydantic import BaseModel, Field, field_validator

class Person(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    age: int = Field(ge=0, le=150)
    email: str

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('Invalid email')
        return v

@agent
async def extract_person(text: str) -> Person:
    '''Extract person from: {{ text }}'''
    pass
```

### How do I use different models for different agents?

Specify the model parameter:

```python
@agent(model="gpt-4o-mini")  # Fast, cheap
async def simple_task(x: str) -> str:
    '''{{ x }}'''
    pass

@agent(model="gpt-4o")  # Powerful, expensive
async def complex_task(x: str) -> str:
    '''{{ x }}'''
    pass

@agent(model="claude-3-5-sonnet-20241022")  # Long context
async def long_context_task(x: str) -> str:
    '''{{ x }}'''
    pass
```

### Can agents call other agents?

Yes! Agents are just async functions:

```python
@agent
async def summarize(text: str) -> str:
    '''Summarize: {{ text }}'''
    pass

@agent
async def translate(text: str, lang: str) -> str:
    '''Translate to {{ lang }}: {{ text }}'''
    pass

# Compose
text = "Long article..."
summary = await summarize(text)
japanese = await translate(summary, "Japanese")
```

### How do I pass complex objects to agents?

Use Jinja2 templates to access object properties:

```python
from pydantic import BaseModel

class Document(BaseModel):
    title: str
    content: str
    author: str

@agent
async def analyze(doc: Document) -> str:
    '''Analyze this document:
    Title: {{ doc.title }}
    Author: {{ doc.author }}
    Content: {{ doc.content }}
    '''
    pass

doc = Document(title="...", content="...", author="...")
result = await analyze(doc)
```

## Templates

### What templating language is used?

[Jinja2](https://jinja.palletsprojects.com/) - a powerful Python template engine.

Basic syntax:
- Variables: `{{ variable }}`
- Conditionals: `{% if condition %} ... {% endif %}`
- Loops: `{% for item in items %} ... {% endfor %}`
- Filters: `{{ text|upper }}`

### How do I use conditionals in prompts?

```python
@agent
async def respond(query: str, formal: bool = False) -> str:
    '''
    {% if formal %}
    Provide a formal, professional response to: {{ query }}
    {% else %}
    Respond casually to: {{ query }}
    {% endif %}
    '''
    pass
```

### How do I loop over lists in prompts?

```python
@agent
async def process_items(items: list[str]) -> str:
    '''Process these items:
    {% for item in items %}
    - {{ item }}
    {% endfor %}
    '''
    pass
```

## Code Execution

### How does code execution work?

The `execute_code()` function:
1. Takes a natural language task
2. Uses LLM to generate Python code
3. Validates code with AST analysis
4. Executes in a sandboxed environment
5. Returns the result

```python
from kagura.agents import execute_code

result = await execute_code("Calculate fibonacci(10)")
# Returns: {"success": True, "code": "...", "result": 55}
```

### How secure is code execution?

Code executor has multiple security layers:

1. **Forbidden imports**: Blocks `os`, `sys`, `subprocess`, etc.
2. **AST validation**: Analyzes code before execution
3. **Timeout**: Default 30 seconds
4. **Resource limits**: Memory constraints
5. **No file I/O**: Cannot read/write files
6. **No network**: Cannot make HTTP requests

**However**, still use caution:
- Don't execute untrusted user code without review
- Set appropriate timeouts
- Monitor execution logs
- Consider additional sandboxing for production

### What libraries can I use in code execution?

Safe libraries allowed by default:
- `math`, `statistics`, `random`
- `datetime`, `json`, `re`
- `collections`, `itertools`, `functools`
- `typing`

Forbidden:
- `os`, `sys`, `subprocess`
- `socket`, `urllib`, `requests`
- `open` (built-in)
- `eval`, `exec`, `compile`

### Can I add custom allowed imports?

Yes, use `CodeExecutor` directly:

```python
from kagura.core.executor import CodeExecutor

executor = CodeExecutor(
    allowed_imports={"math", "numpy", "pandas"}
)

result = await executor.execute("""
import numpy as np
result = np.array([1, 2, 3]).mean()
""")
```

## Type Parsing

### What types are supported?

| Type | Example |
|------|---------|
| `str` | `-> str` |
| `int` | `-> int` |
| `float` | `-> float` |
| `bool` | `-> bool` |
| `list[T]` | `-> list[str]` |
| `dict[K, V]` | `-> dict[str, int]` |
| `Pydantic Model` | `-> Person` |
| `Optional[T]` | `-> Optional[str]` |

### How do I return lists?

```python
@agent
async def extract_keywords(text: str) -> list[str]:
    '''Extract keywords from: {{ text }}'''
    pass

# Returns: ['Python', 'AI', 'framework']
```

### How do I return nested structures?

Use Pydantic models:

```python
class Address(BaseModel):
    street: str
    city: str

class Person(BaseModel):
    name: str
    address: Address

@agent
async def extract(text: str) -> Person:
    '''Extract person with address from: {{ text }}'''
    pass
```

### What if the LLM returns invalid JSON?

The parser will raise a `ValidationError`:

```python
try:
    result = await my_agent("input")
except ValidationError as e:
    print(f"Failed to parse: {e}")
    # Handle error - maybe retry with more explicit instructions
```

## Performance

### How do I reduce latency?

1. **Use faster models**:
   ```python
   @agent(model="gpt-4o-mini")  # Fast
   async def quick_task(x: str) -> str:
       pass
   ```

2. **Shorter prompts**:
   ```python
   # Better
   '''Summarize in 1 sentence: {{ text }}'''

   # Slower
   '''Provide a comprehensive summary...'''
   ```

3. **Parallel execution**:
   ```python
   import asyncio

   results = await asyncio.gather(
       agent1("task1"),
       agent2("task2"),
       agent3("task3"),
   )
   ```

### How do I reduce costs?

1. Use cheaper models (`gpt-4o-mini` instead of `gpt-4o`)
2. Shorter prompts and responses
3. Cache results for repeated queries
4. Use local models (Ollama) when possible

### Can I use local models?

Yes, via Ollama:

```bash
# Install Ollama and pull a model
ollama pull llama3.2
```

```python
@agent(model="ollama/llama3.2")
async def local_agent(query: str) -> str:
    '''Answer: {{ query }}'''
    pass
```

## Debugging

### How do I see the actual prompt sent to the LLM?

Currently, prompts are not exposed directly, but you can:

1. Use logging:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. Test templates manually:
   ```python
   from jinja2 import Template

   template = Template('''Say hello to {{ name }}''')
   print(template.render(name="World"))
   ```

### How do I debug parsing errors?

```python
from pydantic import ValidationError

try:
    result = await my_agent("input")
except ValidationError as e:
    print("Validation error:")
    print(e.errors())
    # Shows which fields failed validation
```

### Why is my agent not working?

Common issues:

1. **No API key**:
   ```
   AuthenticationError: API key not found
   ```
   Solution: Set `OPENAI_API_KEY`

2. **Missing return type**:
   ```python
   # Won't parse correctly
   async def my_agent(x: str):
       pass

   # Better
   async def my_agent(x: str) -> str:
       pass
   ```

3. **Missing await**:
   ```python
   result = my_agent("x")  # Wrong
   result = await my_agent("x")  # Correct
   ```

4. **Empty docstring**:
   ```python
   @agent
   async def my_agent(x: str) -> str:
       pass  # No prompt!
   ```

## Advanced

### Can I stream responses?

Not yet in v2.0.0-alpha.1. Streaming support is planned for a future release.

### Can I use function calling / tools?

Not directly in v2.0.0-alpha.1, but you can implement it:

```python
from kagura import agent

tools = {
    "calculator": lambda x, y: x + y,
    "search": lambda q: f"Results for {q}",
}

@agent
async def use_tool(task: str) -> str:
    '''Determine which tool to use and what arguments for: {{ task }}

    Available tools:
    - calculator(x, y): Add two numbers
    - search(query): Search for information
    '''
    pass

# Parse response and call tool
response = await use_tool("What is 5 + 3?")
```

### How do I implement retry logic?

```python
async def agent_with_retry(task: str, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            result = await my_agent(task)
            return result
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            print(f"Attempt {attempt + 1} failed: {e}")
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

### Can I customize the LLM parameters?

Yes, pass any LiteLLM parameter:

```python
@agent(
    model="gpt-4o",
    temperature=0.5,
    max_tokens=1000,
    top_p=0.9,
    frequency_penalty=0.5
)
async def my_agent(query: str) -> str:
    '''Answer: {{ query }}'''
    pass
```

## Troubleshooting

### Module not found error

```
ModuleNotFoundError: No module named 'kagura'
```

**Solution**:
1. Ensure installed: `pip list | grep kagura`
2. Check Python version: `python --version` (must be 3.11+)
3. Reinstall: `pip install kagura-ai`

### Import error with Pydantic

```
ImportError: cannot import name 'BaseModel'
```

**Solution**: Ensure Pydantic v2:
```bash
pip install "pydantic>=2.10"
```

### REPL not starting

```
kagura: command not found
```

**Solution**:
1. Ensure installed: `pip install kagura-ai`
2. Check PATH: `which kagura`
3. Try full path: `python -m kagura.cli repl`

## Getting Help

- **Documentation**: [https://www.kagura-ai.com/](https://www.kagura-ai.com/)
- **GitHub Issues**: [https://github.com/JFK/kagura-ai/issues](https://github.com/JFK/kagura-ai/issues)
- **Discussions**: [https://github.com/JFK/kagura-ai/discussions](https://github.com/JFK/kagura-ai/discussions)

## Related

- [Quick Start](quickstart.md)
- [API Reference](api/agent.md)
- [Tutorials](tutorials/01-basic-agent.md)
- [Examples](../examples/)
