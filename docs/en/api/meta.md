# Meta Agent API Reference

API reference for Kagura AI's Meta Agent - AI-powered agent code generator.

## Overview

The Meta Agent system allows you to generate complete Kagura agent code from natural language descriptions. It uses a multi-stage pipeline:

1. **Natural Language Parsing** → Extract structured specification
2. **Code Generation** → Generate Python code from templates
3. **Security Validation** → Ensure generated code is safe
4. **File Creation** → Save the agent to a file

## MetaAgent

Main class for AI-powered agent code generation.

### Class Definition

```python
from kagura.meta import MetaAgent

class MetaAgent:
    """AI-powered agent code generator

    Generate Kagura agent code from natural language descriptions.

    Args:
        model: LLM model for spec parsing (default: "gpt-4o-mini")
        template_dir: Custom template directory (optional)
        validate: Whether to validate generated code (default: True)

    Example:
        >>> meta = MetaAgent()
        >>> code = await meta.generate("Translate English to Japanese")
        >>> print(code)  # Complete Python agent code
    """
```

### Methods

#### `__init__(model="gpt-4o-mini", template_dir=None, validate=True)`

Initialize MetaAgent.

**Parameters:**
- `model` (str): LLM model for parsing descriptions (default: "gpt-4o-mini")
- `template_dir` (Path | None): Custom template directory (optional)
- `validate` (bool): Whether to validate generated code (default: True)

**Example:**
```python
meta = MetaAgent(model="gpt-4o-mini", validate=True)
```

#### `async generate(description: str) -> str`

Generate agent code from natural language description.

**Parameters:**
- `description` (str): Natural language agent description

**Returns:**
- `str`: Generated Python code

**Raises:**
- `ValidationError`: If generated code is invalid (when validate=True)

**Example:**
```python
meta = MetaAgent()
code = await meta.generate("Create a chatbot that remembers conversation history")
print(code)  # Complete Python agent code with @agent decorator
```

#### `async generate_from_spec(spec: AgentSpec) -> str`

Generate agent code from AgentSpec.

**Parameters:**
- `spec` (AgentSpec): Agent specification

**Returns:**
- `str`: Generated Python code

**Raises:**
- `ValidationError`: If generated code is invalid

**Example:**
```python
from kagura.meta.spec import AgentSpec

spec = AgentSpec(
    name="translator",
    description="Translate text",
    input_type="str",
    output_type="str",
    system_prompt="You are a professional translator."
)

meta = MetaAgent()
code = await meta.generate_from_spec(spec)
```

#### `async generate_and_save(description: str, output_path: Path) -> tuple[str, Path]`

Generate agent code and save to file.

**Parameters:**
- `description` (str): Natural language agent description
- `output_path` (Path): Output file path

**Returns:**
- `tuple[str, Path]`: (generated_code, output_path)

**Raises:**
- `ValidationError`: If generated code is invalid

**Example:**
```python
from pathlib import Path

meta = MetaAgent()
code, path = await meta.generate_and_save(
    "Create a translator agent",
    Path("agents/translator.py")
)
print(f"Saved to {path}")
```

---

## AgentSpec

Structured specification for an agent.

### Class Definition

```python
from kagura.meta.spec import AgentSpec
from pydantic import BaseModel

class AgentSpec(BaseModel):
    """Agent specification parsed from natural language

    Structured representation of agent requirements.

    Fields:
        name: Agent function name (snake_case)
        description: What the agent does (1-2 sentences)
        input_type: Parameter type (str, dict, list, etc.)
        output_type: Return type (str, dict, list, etc.)
        tools: List of required tools (optional)
        has_memory: Whether agent needs conversation memory
        system_prompt: Agent's system instructions
        examples: Example inputs/outputs (optional)
    """
```

### Fields

#### `name: str`

Agent function name in snake_case.

**Example:**
```python
spec = AgentSpec(
    name="translator",
    description="Translate text",
    system_prompt="You are a translator"
)
```

#### `description: str`

What the agent does (1-2 sentences).

**Example:**
```python
spec = AgentSpec(
    name="summarizer",
    description="Summarize articles in 3 bullet points",
    system_prompt="You are a summarizer"
)
```

#### `input_type: str = "str"`

Parameter type annotation.

**Default:** `"str"`

**Common types:** `"str"`, `"dict"`, `"list"`, `"int"`, `"float"`

**Example:**
```python
spec = AgentSpec(
    name="calculator",
    description="Calculate math",
    input_type="str",
    output_type="float",
    system_prompt="Calculate the result"
)
```

#### `output_type: str = "str"`

Return type annotation.

**Default:** `"str"`

#### `tools: list[str] = []`

List of required tools.

**Available tools:**
- `"code_executor"`: Execute Python code
- `"web_search"`: Search the web
- `"memory"`: Conversation memory
- `"file_ops"`: File operations

**Default:** `[]`

**Example:**
```python
spec = AgentSpec(
    name="math_solver",
    description="Solve math problems",
    tools=["code_executor"],
    system_prompt="Solve math problems by executing Python code"
)
```

#### `has_memory: bool = False`

Whether agent needs conversation memory.

**Default:** `False`

**Example:**
```python
spec = AgentSpec(
    name="chatbot",
    description="Conversational chatbot",
    has_memory=True,
    system_prompt="You are a friendly chatbot"
)
```

#### `system_prompt: str`

Agent's system instructions.

**Required field**

**Example:**
```python
spec = AgentSpec(
    name="translator",
    description="Translate text",
    system_prompt="You are a professional translator. Translate text accurately while preserving meaning and tone."
)
```

#### `examples: list[dict[str, str]] = []`

Example inputs/outputs (optional).

**Default:** `[]`

**Format:** `[{"input": "...", "output": "..."}]`

**Example:**
```python
spec = AgentSpec(
    name="translator",
    description="Translate text",
    system_prompt="You are a translator",
    examples=[
        {"input": "Hello", "output": "こんにちは"},
        {"input": "Thank you", "output": "ありがとう"}
    ]
)
```

---

## NLSpecParser

Parse natural language descriptions into structured AgentSpec.

### Class Definition

```python
from kagura.meta.parser import NLSpecParser

class NLSpecParser:
    """Parse natural language agent descriptions into AgentSpec

    Uses LLM to extract structured information from user descriptions.

    Args:
        model: LLM model to use for parsing (default: "gpt-4o-mini")

    Example:
        >>> parser = NLSpecParser()
        >>> desc = "Create an agent that translates English to Japanese"
        >>> spec = await parser.parse(desc)
        >>> print(spec.name)  # "translator"
    """
```

### Methods

#### `__init__(model="gpt-4o-mini")`

Initialize parser with LLM model.

**Parameters:**
- `model` (str): LLM model for parsing (default: "gpt-4o-mini")

**Example:**
```python
parser = NLSpecParser(model="gpt-4o-mini")
```

#### `async parse(description: str) -> AgentSpec`

Parse natural language description into AgentSpec.

**Parameters:**
- `description` (str): Natural language agent description

**Returns:**
- `AgentSpec`: Structured specification

**Example:**
```python
parser = NLSpecParser()
spec = await parser.parse("Summarize articles in 3 bullet points")
print(spec.name)  # "article_summarizer"
print(spec.output_type)  # "str"
```

#### `detect_tools(description: str) -> list[str]`

Detect required tools from description using pattern matching.

**Parameters:**
- `description` (str): Natural language description

**Returns:**
- `list[str]`: List of detected tool names

**Example:**
```python
parser = NLSpecParser()

# Code execution detection
tools = parser.detect_tools("Execute Python code to solve math problems")
print(tools)  # ["code_executor"]

# Web search detection
tools = parser.detect_tools("Search the web for information")
print(tools)  # ["web_search"]

# Memory detection
tools = parser.detect_tools("Remember user preferences in conversation")
print(tools)  # ["memory"]
```

**Tool patterns:**
- **code_executor**: "execute code", "run python", "calculate"
- **web_search**: "search", "google", "find online", "web"
- **memory**: "remember", "conversation", "history"
- **file_ops**: "read file", "write file"

---

## CodeGenerator

Generate Python agent code from AgentSpec using Jinja2 templates.

### Class Definition

```python
from kagura.meta.generator import CodeGenerator
from pathlib import Path

class CodeGenerator:
    """Generate agent Python code from AgentSpec

    Uses Jinja2 templates to generate complete, runnable agent code.

    Args:
        template_dir: Directory containing Jinja2 templates
                     (default: kagura/meta/templates/)

    Example:
        >>> generator = CodeGenerator()
        >>> code = generator.generate(spec)
        >>> print(code)  # Complete Python code with @agent decorator
    """
```

### Methods

#### `__init__(template_dir=None)`

Initialize with template directory.

**Parameters:**
- `template_dir` (Path | None): Directory containing Jinja2 templates (optional)

**Example:**
```python
generator = CodeGenerator()
```

#### `generate(spec: AgentSpec) -> str`

Generate complete agent code.

**Parameters:**
- `spec` (AgentSpec): Agent specification

**Returns:**
- `str`: Python code as string

**Example:**
```python
from kagura.meta.spec import AgentSpec

spec = AgentSpec(
    name="translator",
    description="Translate text",
    system_prompt="You are a translator"
)

generator = CodeGenerator()
code = generator.generate(spec)

assert "@agent" in code
assert "async def translator" in code
```

#### `save(code: str, output_path: Path) -> None`

Save generated code to file.

**Parameters:**
- `code` (str): Generated Python code
- `output_path` (Path): Output file path

**Example:**
```python
from pathlib import Path

generator = CodeGenerator()
code = generator.generate(spec)
generator.save(code, Path("agents/my_agent.py"))
```

---

## CodeValidator

Validate generated agent code for security and correctness.

### Class Definition

```python
from kagura.meta.validator import CodeValidator

class CodeValidator:
    """Validate generated agent code

    Reuses security checks from kagura.core.executor.ASTValidator
    to ensure generated code is safe and correct.

    Args:
        allowed_imports: Set of allowed import modules (optional)

    Example:
        >>> validator = CodeValidator()
        >>> try:
        ...     validator.validate(code)
        ...     print("Code is valid")
        ... except ValidationError as e:
        ...     print(f"Validation failed: {e}")
    """
```

### Methods

#### `__init__(allowed_imports=None)`

Initialize validator.

**Parameters:**
- `allowed_imports` (set[str] | None): Set of allowed import modules (optional)

**Default allowed imports:**
- `kagura`
- `kagura.core`
- `kagura.core.executor`
- `kagura.core.memory`
- `pydantic`
- `typing`
- `datetime`
- `pathlib`
- `asyncio`

**Example:**
```python
validator = CodeValidator()
```

#### `validate(code: str) -> bool`

Validate agent code (raises ValidationError if invalid).

**Parameters:**
- `code` (str): Python code to validate

**Returns:**
- `bool`: True if valid

**Raises:**
- `ValidationError`: If code is invalid or insecure

**Checks performed:**
1. ✅ Syntax checking
2. ✅ Security validation (disallowed imports, dangerous functions)
3. ✅ @agent decorator verification

**Example:**
```python
validator = CodeValidator()

# Valid code
code = """
from kagura import agent

@agent(name="test")
async def test_agent(x: str) -> str:
    return x
"""
validator.validate(code)  # Returns True

# Invalid code (missing decorator)
bad_code = """
from kagura import agent

async def test_agent(x: str) -> str:
    return x
"""
try:
    validator.validate(bad_code)
except ValidationError as e:
    print(e)  # "Missing @agent decorator"
```

---

## ValidationError

Exception raised when agent code validation fails.

### Class Definition

```python
from kagura.meta.validator import ValidationError

class ValidationError(Exception):
    """Agent validation failed"""
```

### Common Validation Errors

#### Missing @agent decorator

**Error:** `ValidationError: Missing @agent decorator`

**Cause:** Generated code doesn't include `@agent` decorator

**Solution:** Report as bug

#### Disallowed import

**Error:** `ValidationError: Disallowed import: subprocess`

**Cause:** Generated code includes dangerous imports

**Example:**
```python
try:
    validator.validate(code_with_subprocess)
except ValidationError as e:
    print(e)  # "Disallowed import: subprocess"
```

#### Disallowed name

**Error:** `ValidationError: Disallowed name: eval`

**Cause:** Generated code uses dangerous functions like `eval()`, `exec()`

**Example:**
```python
try:
    validator.validate(code_with_eval)
except ValidationError as e:
    print(e)  # "Disallowed name: eval"
```

#### Syntax error

**Error:** `ValidationError: Syntax error: ...`

**Cause:** Generated code has invalid Python syntax

---

## CLI Commands

### kagura build agent

Generate agent code from natural language description.

**Usage:**
```bash
kagura build agent [OPTIONS]
```

**Options:**
- `-d, --description TEXT`: Natural language agent description
- `-o, --output PATH`: Output file path (default: `agents/<name>.py`)
- `--model TEXT`: LLM model for code generation (default: `gpt-4o-mini`)
- `--interactive / --no-interactive`: Interactive mode (default: `True`)
- `--no-validate`: Skip code validation

**Interactive Mode (default):**
```bash
kagura build agent
```

**Output:**
```
🤖 Kagura Agent Builder
Describe your agent in natural language and I'll generate the code.

What should your agent do? Translate English to Japanese

🔍 Parsing agent specification...

📋 Agent Specification
Name: translator
Description: Translate English to Japanese
Input: str
Output: str
Tools: None
Memory: No

⚙️  Generating agent code...
🔒 Validating code security...
✅ Code validated

✅ Agent created: agents/translator.py
```

**Non-Interactive Mode:**
```bash
kagura build agent \
  --description "Translate English to Japanese" \
  --output translator.py \
  --no-interactive
```

**Examples:**
```bash
# Interactive mode
kagura build agent

# Direct generation
kagura build agent -d "Summarize text in 3 bullet points" -o summarizer.py

# Use GPT-4
kagura build agent -d "Complex reasoning task" --model gpt-4o

# Skip validation (not recommended)
kagura build agent -d "Test agent" --no-validate
```

---

## Complete Example

Here's a complete example using the Meta Agent API:

```python
import asyncio
from pathlib import Path
from kagura.meta import MetaAgent
from kagura.meta.spec import AgentSpec
from kagura.meta.validator import ValidationError

async def main():
    # Method 1: Generate from natural language
    meta = MetaAgent(model="gpt-4o-mini", validate=True)

    try:
        code = await meta.generate("Create a chatbot that remembers conversation history")
        print("Generated code:")
        print(code)

        # Save to file
        output_path = Path("agents/chatbot.py")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(code)
        print(f"\nSaved to {output_path}")

    except ValidationError as e:
        print(f"Validation failed: {e}")

    # Method 2: Generate from AgentSpec
    spec = AgentSpec(
        name="translator",
        description="Translate text between languages",
        input_type="str",
        output_type="str",
        system_prompt="""You are a professional translator.
        Translate text accurately while preserving meaning and tone.""",
        examples=[
            {"input": "Hello", "output": "こんにちは"},
            {"input": "Thank you", "output": "ありがとう"}
        ]
    )

    code = await meta.generate_from_spec(spec)
    print("\nGenerated from spec:")
    print(code)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Template Customization

### Default Templates

Meta Agent includes three default templates:

1. **agent_base.py.j2**: Basic agent
2. **agent_with_tools.py.j2**: Agent with tools
3. **agent_with_memory.py.j2**: Agent with memory

### Custom Templates

You can provide custom templates:

```python
from pathlib import Path
from kagura.meta import MetaAgent

# Custom template directory
template_dir = Path("my_templates")

meta = MetaAgent(template_dir=template_dir)
code = await meta.generate("My agent description")
```

**Template variables:**
- `spec`: AgentSpec object
- `timestamp`: Generation timestamp
- `kagura_version`: Kagura version
- `tool_descriptions`: Tool descriptions dict

---

## Security Best Practices

1. **Always validate generated code** (default: `validate=True`)
2. **Review generated code** before running in production
3. **Use specific descriptions** to avoid unexpected behavior
4. **Test generated agents** thoroughly
5. **Keep Kagura up-to-date** for latest security fixes

---

## See Also

- [Meta Agent User Guide](../guides/meta-agent.md)
- [Agent API Reference](agent.md)
- [CLI Reference](cli.md)
- [Code Executor API](executor.md)
