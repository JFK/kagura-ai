# Kagura AI 2.0 Examples

This directory contains example agents demonstrating various features of Kagura AI 2.0.

## 🎯 Quick Start Examples

### 1. [Simple Chat](agents/simple_chat/)

Basic conversational agent showing the simplest usage of the `@agent` decorator.

**Key Concepts:**
- @agent decorator
- Jinja2 templates
- String return types

**Run:**
```bash
cd agents/simple_chat
python agent.py
```

### 2. [Data Extractor](agents/data_extractor/)

Structured data extraction using Pydantic models and type-based parsing.

**Key Concepts:**
- Pydantic models
- Type-based parsing
- Nested structures
- List extraction

**Run:**
```bash
cd agents/data_extractor
python agent.py
```

### 3. [Code Generator](agents/code_generator/)

Safe Python code generation and execution using the built-in code executor.

**Key Concepts:**
- execute_code()
- Safe code execution
- Natural language → Code
- Error handling

**Run:**
```bash
cd agents/code_generator
python agent.py
```

### 4. [Workflow Example](agents/workflow_example/)

Multi-step workflow demonstrating agent composition and data flow.

**Key Concepts:**
- Agent composition
- Data flow between agents
- Jinja2 loops
- Plan → Execute → Review pattern

**Run:**
```bash
cd agents/workflow_example
python agent.py
```

## 📚 Learning Path

If you're new to Kagura AI 2.0, we recommend following this order:

1. **Start with Simple Chat** → Understand the basic `@agent` decorator
2. **Move to Data Extractor** → Learn structured output with Pydantic
3. **Try Code Generator** → Explore code execution capabilities
4. **Build Workflows** → Compose agents for complex tasks

## 🔧 Common Patterns

### Basic Agent

```python
from kagura import agent

@agent
async def my_agent(input: str) -> str:
    '''Process {{ input }}'''
    pass

result = await my_agent("Hello")
```

### Structured Output

```python
from kagura import agent
from pydantic import BaseModel

class Person(BaseModel):
    name: str
    age: int

@agent
async def extract_person(text: str) -> Person:
    '''Extract person from: {{ text }}'''
    pass
```

### Code Execution

```python
from kagura.agents import execute_code

result = await execute_code("Calculate the factorial of 10")
if result["success"]:
    print(result["result"])
```

### Agent Composition

```python
@agent
async def step1(input: str) -> str:
    '''Process {{ input }}'''
    pass

@agent
async def step2(input: str) -> str:
    '''Refine {{ input }}'''
    pass

# Compose
result1 = await step1("data")
result2 = await step2(result1)
```

## 🛠️ Running Examples

### Prerequisites

1. Install Kagura AI:
   ```bash
   pip install kagura-ai
   ```

2. Set your API key:
   ```bash
   export OPENAI_API_KEY="your-key-here"
   ```

### Run an Example

```bash
cd agents/<example-name>
python agent.py
```

### Run All Examples

```bash
# From the examples directory
for dir in agents/*/; do
    echo "Running $(basename $dir)..."
    cd "$dir"
    python agent.py
    cd ..
done
```

## 📖 Additional Resources

- [Full Documentation](https://www.kagura-ai.com/)
- [API Reference](https://www.kagura-ai.com/en/api/)
- [Quick Start Guide](../docs/en/quickstart.md)
- [Installation Guide](../docs/en/installation.md)

## 🏗️ Directory Structure

```
examples/
├── agents/
│   ├── simple_chat/          # Basic conversational agent
│   ├── data_extractor/       # Structured data extraction
│   ├── code_generator/       # Code execution
│   └── workflow_example/     # Multi-step workflows
└── README.md                 # This file
```

## 💡 Tips

### Debugging

Enable debug logging to see what's happening:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Custom LLM Models

Change the model by setting the model parameter:

```python
from kagura import agent

@agent(model="gpt-4")  # Use GPT-4 instead of default
async def my_agent(input: str) -> str:
    '''Process {{ input }}'''
    pass
```

### Error Handling

Wrap agent calls in try-except for production:

```python
try:
    result = await my_agent("input")
except Exception as e:
    print(f"Agent failed: {e}")
```

## 🤝 Contributing

Want to add more examples? See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

### Example Structure

Each example should have:
- `agent.py` - Working code with multiple use cases
- `README.md` - Documentation explaining concepts
- Clear comments and docstrings
- Runnable with `python agent.py`

## ❓ Common Questions

### Q: Can I use these examples in production?

A: These examples are for learning purposes. For production, add proper error handling, logging, and testing.

### Q: Which LLM providers are supported?

A: Kagura uses LiteLLM, supporting OpenAI, Anthropic, Google, Azure, Ollama, and 100+ other providers.

### Q: How do I customize prompts?

A: Modify the docstring template in the `@agent` decorator. Use Jinja2 syntax for dynamic values.

### Q: Can agents call other agents?

A: Yes! See the [workflow_example](agents/workflow_example/) for agent composition patterns.

### Q: How secure is code execution?

A: The code executor has security constraints (no file I/O, network, dangerous imports), but should still be used with caution. See [code_generator](agents/code_generator/) for details.

## 📝 License

Apache License 2.0 - see [LICENSE](../LICENSE)

---

Built with ❤️ by the Kagura AI community
