# Quick Start - Kagura AI

Get started with Kagura AI in 5 minutes.

---

## Installation

```bash
pip install kagura-ai[full]
```

## Setup API Key

```bash
export OPENAI_API_KEY=sk-...
```

---

## Your First Agent (30 seconds)

```python
from kagura import agent

@agent
async def translator(text: str, lang: str = "ja") -> str:
    '''Translate to {{ lang }}: {{ text }}'''

# Use it
result = await translator("Hello World", lang="ja")
print(result)  # "こんにちは世界"
```

---

## Type-Safe Output

```python
from kagura import agent
from pydantic import BaseModel

class Person(BaseModel):
    name: str
    age: int
    occupation: str

@agent
async def extract_person(text: str) -> Person:
    '''Extract person info from: {{ text }}'''

person = await extract_person("Alice is 30 and works as an engineer")
print(person.name)  # "Alice" - fully typed!
```

---

## With Built-in Tools

```python
@agent(tools=["web_search"])
async def researcher(topic: str) -> str:
    '''Research {{ topic }} using web_search(query) tool.'''

result = await researcher("Latest Python frameworks")
# Uses Brave Search automatically
```

---

## Try Interactive Chat

```bash
kagura chat
```

Then try:
```
[You] > Read report.pdf and summarize
[AI] > (analyzes PDF, provides summary)

[You] > Search for similar reports
[AI] > (searches web, finds content)
```

All features work automatically.

---

## Next Steps

- [SDK Guide](sdk-guide.md) - Learn @agent, @tool, memory
- [Examples](../examples/) - 30+ code examples
- [Chat Guide](chat-guide.md) - Interactive chat features
