# Tutorial 1: Creating Your First Agent

Learn how to create a basic AI agent using the `@agent` decorator.

## Prerequisites

- Python 3.11 or higher
- Kagura AI installed (`pip install kagura-ai`)
- OpenAI API key (or other LLM provider)

## Goal

By the end of this tutorial, you will:
- Understand the `@agent` decorator
- Create a simple conversational agent
- Run and test your agent
- Understand how prompts work

## Step 1: Set Up Your Environment

First, set your API key:

```bash
export OPENAI_API_KEY="your-key-here"
```

Create a new file called `hello_agent.py`:

```bash
touch hello_agent.py
```

## Step 2: Import Kagura

Open `hello_agent.py` and add the import:

```python
import asyncio
from kagura import agent
```

**Explanation:**
- `asyncio`: Python's built-in library for async operations
- `agent`: The core decorator from Kagura AI

## Step 3: Define Your First Agent

Add this agent definition:

```python
@agent
async def hello(name: str) -> str:
    '''Say hello to {{ name }}'''
    pass
```

**Let's break this down:**

1. `@agent` - The decorator that converts the function into an AI agent
2. `async def hello` - An async function (required for all agents)
3. `(name: str)` - Function parameter with type hint
4. `-> str` - Return type annotation (tells parser to expect a string)
5. `'''Say hello to {{ name }}'''` - The prompt template using Jinja2 syntax
6. `pass` - Function body (ignored, as decorator replaces it)

## Step 4: Create a Main Function

Add code to run the agent:

```python
async def main():
    # Call the agent
    result = await hello("World")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

## Step 5: Run Your Agent

Execute the script:

```bash
python hello_agent.py
```

**Expected output:**
```
Hello, World! How can I assist you today?
```

🎉 Congratulations! You've created your first AI agent.

## Complete Code

Here's the full `hello_agent.py`:

```python
import asyncio
from kagura import agent


@agent
async def hello(name: str) -> str:
    '''Say hello to {{ name }}'''
    pass


async def main():
    result = await hello("World")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
```

## Understanding What Happened

Let's trace the execution:

1. **You call**: `await hello("World")`
2. **Decorator extracts**: Parameter `name = "World"`
3. **Template renders**: `"Say hello to World"`
4. **LLM is called**: With the rendered prompt
5. **Response is parsed**: As a string (because `-> str`)
6. **Result returned**: `"Hello, World! How can I assist you today?"`

## Experiment: Different Names

Try calling with different names:

```python
async def main():
    print(await hello("Alice"))
    print(await hello("Bob"))
    print(await hello("神楽"))  # Japanese name
```

**Output:**
```
Hello, Alice! How can I help you?
Hello, Bob! Nice to meet you!
こんにちは、神楽さん！お手伝いできることはありますか？
```

Notice how the LLM adapts its response based on the input!

## Experiment: Multiple Parameters

Let's create an agent with multiple parameters:

```python
@agent
async def greet(name: str, time_of_day: str = "morning") -> str:
    '''Good {{ time_of_day }}, {{ name }}! How are you doing?'''
    pass


async def main():
    print(await greet("Alice"))
    print(await greet("Bob", "evening"))
```

**Output:**
```
Good morning, Alice! How are you doing?
I hope you're doing well!

Good evening, Bob! How are you doing?
I hope you had a great day!
```

## Experiment: Different Prompts

The prompt greatly affects the response. Try these variations:

### Formal Greeting

```python
@agent
async def formal_greet(name: str) -> str:
    '''Provide a formal business greeting to {{ name }}, a potential client.'''
    pass
```

### Casual Greeting

```python
@agent
async def casual_greet(name: str) -> str:
    '''Give a super casual, friendly greeting to {{ name }}, your best friend.'''
    pass
```

### Poetic Greeting

```python
@agent
async def poetic_greet(name: str) -> str:
    '''Write a short, poetic greeting to {{ name }} (2-3 lines).'''
    pass
```

## Key Concepts Learned

### 1. The @agent Decorator

Converts a function into an AI agent:
- Extracts function signature
- Uses docstring as prompt template
- Calls LLM automatically
- Parses response based on return type

### 2. Async/Await

All agents are async functions:
```python
result = await hello("World")  # ✓ Correct
result = hello("World")        # ✗ Wrong - missing await
```

### 3. Type Hints

Type hints tell the parser how to handle the response:
```python
async def hello(name: str) -> str:  # Returns string
    pass
```

### 4. Prompt Templates

Docstrings use Jinja2 syntax for dynamic prompts:
```python
'''Say hello to {{ name }}'''  # {{ }} injects variables
```

## Common Mistakes

### 1. Forgetting `async`/`await`

```python
# Wrong
@agent
def hello(name: str) -> str:  # Missing 'async'
    pass

result = hello("World")  # Missing 'await'

# Correct
@agent
async def hello(name: str) -> str:
    pass

result = await hello("World")
```

### 2. Missing Return Type

```python
# Less good
@agent
async def hello(name: str):  # No return type
    pass

# Better
@agent
async def hello(name: str) -> str:  # Explicit return type
    pass
```

### 3. Empty Docstring

```python
# Won't work well
@agent
async def hello(name: str) -> str:
    pass  # No docstring = no prompt!

# Correct
@agent
async def hello(name: str) -> str:
    '''Say hello to {{ name }}'''
    pass
```

## Next Steps

Now that you understand basic agents, you can:

1. **Learn about templates** - [Tutorial 2: Template Engine](02-templates.md)
2. **Explore type parsing** - [Tutorial 3: Type-Based Parsing](03-type-parsing.md)
3. **Try Interactive Chat** - Run `kagura chat` to experiment

## Practice Exercises

### Exercise 1: Sentiment Analysis

Create an agent that analyzes sentiment:

```python
@agent
async def analyze_sentiment(text: str) -> str:
    '''Analyze the sentiment (positive/negative/neutral) of: {{ text }}'''
    pass
```

Test it:
```python
print(await analyze_sentiment("I love this product!"))
print(await analyze_sentiment("This is terrible."))
print(await analyze_sentiment("It's okay."))
```

### Exercise 2: Language Translation

Create a translation agent:

```python
@agent
async def translate(text: str, target_language: str) -> str:
    '''Translate to {{ target_language }}: {{ text }}'''
    pass
```

Test it:
```python
print(await translate("Hello, world!", "Japanese"))
print(await translate("Hello, world!", "French"))
```

### Exercise 3: Question Answering

Create a Q&A agent:

```python
@agent
async def answer_question(question: str) -> str:
    '''Answer this question concisely: {{ question }}'''
    pass
```

Test it:
```python
print(await answer_question("What is Python?"))
print(await answer_question("How do I install Kagura AI?"))
```

## Summary

You learned:
- ✓ How to use the `@agent` decorator
- ✓ How to create async agent functions
- ✓ How to use type hints for return types
- ✓ How to write prompt templates with Jinja2
- ✓ How to call and test agents

Continue to [Tutorial 2: Template Engine](02-templates.md) to learn more advanced prompting techniques!
