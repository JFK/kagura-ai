# Commands API

Custom commands allow you to define reusable AI tasks in Markdown files with YAML frontmatter.

## Overview

Commands are Markdown files with two parts:
1. **Frontmatter** (YAML metadata): Command configuration
2. **Body** (Markdown content): Command template

## Command Class

Represents a custom command loaded from a Markdown file.

### Constructor

```python
Command(
    name: str,
    description: str,
    template: str,
    allowed_tools: list[str] = [],
    model: str = "gpt-4o-mini",
    parameters: dict[str, Any] = {},
    metadata: dict[str, Any] = {}
)
```

**Parameters:**

- `name`: Command name (used to invoke the command)
- `description`: Human-readable description
- `template`: Markdown template body
- `allowed_tools`: List of allowed tool names (empty = all allowed)
- `model`: LLM model to use (default: `gpt-4o-mini`)
- `parameters`: Parameter definitions
- `metadata`: Additional metadata from frontmatter

### Methods

#### validate_parameters

```python
command.validate_parameters(provided: dict[str, Any]) -> None
```

Validate provided parameters against parameter definitions.

**Raises:** `ValueError` if required parameters are missing.

**Example:**

```python
command = Command(
    name="test",
    description="Test",
    template="Content",
    parameters={"file": "string", "count": "int"}
)

# Valid
command.validate_parameters({"file": "test.txt", "count": 5})

# Invalid - raises ValueError
command.validate_parameters({"file": "test.txt"})  # Missing 'count'
```

## CommandLoader Class

Loads custom commands from Markdown files.

### Constructor

```python
CommandLoader(commands_dir: Optional[Path] = None)
```

**Parameters:**

- `commands_dir`: Directory containing command files (default: `~/.kagura/commands`)

### Methods

#### load_command

```python
loader.load_command(path: Path) -> Command
```

Load a single command from a Markdown file.

**Returns:** `Command` object

**Raises:**
- `FileNotFoundError`: If file doesn't exist
- `ValueError`: If frontmatter is invalid

**Example:**

```python
from pathlib import Path
from kagura.commands import CommandLoader

loader = CommandLoader()
command = loader.load_command(Path("~/.kagura/commands/example.md"))
print(command.name)  # "example"
```

#### load_all

```python
loader.load_all() -> dict[str, Command]
```

Load all commands from the commands directory.

**Returns:** Dictionary mapping command names to `Command` objects

**Raises:** `FileNotFoundError` if commands directory doesn't exist

**Example:**

```python
loader = CommandLoader()
commands = loader.load_all()

for name, command in commands.items():
    print(f"{name}: {command.description}")
```

#### get_command

```python
loader.get_command(name: str) -> Optional[Command]
```

Get a loaded command by name.

**Returns:** `Command` object if found, `None` otherwise

**Example:**

```python
loader = CommandLoader()
loader.load_all()

command = loader.get_command("example")
if command:
    print(command.description)
```

#### list_commands

```python
loader.list_commands() -> list[str]
```

List all loaded command names.

**Returns:** List of command names

**Example:**

```python
loader = CommandLoader()
loader.load_all()

commands = loader.list_commands()
print(f"Available commands: {', '.join(commands)}")
```

## Command File Format

Commands are defined in Markdown files with YAML frontmatter.

### Basic Example

`~/.kagura/commands/example.md`:

```markdown
---
name: example
description: Example command
---

# Task

Execute an example task.
```

### Full Example

`~/.kagura/commands/full-example.md`:

```markdown
---
name: full-example
description: Full example with all fields
allowed_tools: [git, gh, bash]
model: gpt-4o
parameters:
  file: string
  count: int
author: Your Name
version: 1.0
---

# Context

Processing file: {{ file }}

# Task

Execute task {{ count }} times.
```

### Frontmatter Fields

**Required:**
- None (all fields are optional)

**Standard Fields:**
- `name`: Command name (defaults to filename if not specified)
- `description`: Command description
- `allowed_tools`: List of allowed tools (e.g., `[git, bash]`)
- `model`: LLM model name (default: `gpt-4o-mini`)
- `parameters`: Parameter definitions

**Custom Fields:**
- Any additional YAML fields are stored in `command.metadata`

### Parameter Definitions

#### Simple Type

```yaml
parameters:
  file: string
  count: int
  enabled: bool
```

#### With Required Flag

```yaml
parameters:
  file:
    type: string
    required: true
  count:
    type: int
    required: false
```

## Usage Examples

### Loading Commands

```python
from pathlib import Path
from kagura.commands import CommandLoader

# Default directory (~/.kagura/commands)
loader = CommandLoader()

# Custom directory
loader = CommandLoader(Path("./my-commands"))

# Load all commands
commands = loader.load_all()
print(f"Loaded {len(commands)} commands")

# Get specific command
example = loader.get_command("example")
if example:
    print(f"Template: {example.template}")
```

### Creating Commands Programmatically

```python
from kagura.commands import Command

command = Command(
    name="my-command",
    description="My custom command",
    template="# Task\nDo something",
    allowed_tools=["bash"],
    model="gpt-4o-mini"
)

# Validate parameters
command.validate_parameters({})  # OK if no required params
```

### Command with Parameters

Create `~/.kagura/commands/greet.md`:

```markdown
---
name: greet
description: Greet a person
parameters:
  name: string
  formal: bool
---

# Task

Greet {{ name }} in a {% if formal %}formal{% else %}casual{% endif %} manner.
```

Load and use:

```python
loader = CommandLoader()
loader.load_all()

greet = loader.get_command("greet")

# Validate parameters
greet.validate_parameters({"name": "Alice", "formal": True})  # OK
greet.validate_parameters({"name": "Bob"})  # Error: missing 'formal'
```

## Error Handling

### Missing Command File

```python
from pathlib import Path
from kagura.commands import CommandLoader

loader = CommandLoader()

try:
    cmd = loader.load_command(Path("nonexistent.md"))
except FileNotFoundError as e:
    print(f"Command file not found: {e}")
```

### Invalid Frontmatter

If a command file has invalid YAML frontmatter, `load_command` will raise a `ValueError`.

### Missing Directory

```python
from pathlib import Path
from kagura.commands import CommandLoader

loader = CommandLoader(Path("/nonexistent"))

try:
    loader.load_all()
except FileNotFoundError as e:
    print(f"Commands directory not found: {e}")
```

### Skipping Invalid Files

`load_all()` skips invalid files and prints warnings:

```python
loader = CommandLoader()
commands = loader.load_all()
# Prints: "Warning: Failed to load invalid.md: ..."
# But continues loading other commands
```

## Best Practices

### 1. Use Descriptive Names

```yaml
---
name: git-commit-push-pr
description: Create commit, push, and open PR
---
```

### 2. Specify Allowed Tools

```yaml
---
allowed_tools: [git, gh]  # Only allow git and GitHub CLI
---
```

### 3. Add Metadata

```yaml
---
author: Your Name
version: 1.0
tags: [git, workflow]
---
```

### 4. Organize by Purpose

```
~/.kagura/commands/
├── git/
│   ├── commit-pr.md
│   └── sync-fork.md
├── docs/
│   ├── generate-readme.md
│   └── update-changelog.md
└── analysis/
    ├── analyze-logs.md
    └── report-metrics.md
```

## See Also

- [Custom Commands Tutorial](../tutorials/09-custom-commands.md) (coming soon)
- [@agent Decorator API](./agent.md)
- [Memory Management API](./memory.md)
