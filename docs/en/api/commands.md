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

By default, searches both project-local (`./.kagura/commands`) and global (`~/.kagura/commands`) directories. Local commands take priority over global commands with the same name.

### Constructor

```python
CommandLoader(commands_dir: Optional[Path] = None)
```

**Parameters:**

- `commands_dir`: Directory containing command files. If `None`, searches both:
  1. `~/.kagura/commands` (global commands)
  2. `./.kagura/commands` (project-local commands, takes priority)

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

Load all commands from configured directories.

Searches all directories in priority order. When multiple directories contain commands with the same name, later directories take priority (local overrides global).

**Returns:** Dictionary mapping command names to `Command` objects

**Raises:** `FileNotFoundError` if no commands directory exists

**Example:**

```python
# Default: searches both global and local directories
loader = CommandLoader()
commands = loader.load_all()

for name, command in commands.items():
    print(f"{name}: {command.description}")

# Custom single directory
loader = CommandLoader(Path("./my-commands"))
commands = loader.load_all()
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

# Default: searches both global and local directories
loader = CommandLoader()
# Searches:
#   1. ~/.kagura/commands (global)
#   2. ./.kagura/commands (local, takes priority)

# Custom single directory
loader = CommandLoader(Path("./my-commands"))

# Load all commands
commands = loader.load_all()
print(f"Loaded {len(commands)} commands")

# Get specific command
example = loader.get_command("example")
if example:
    print(f"Template: {example.template}")
```

### Multi-Directory Search

By default, `CommandLoader` searches both global and local directories:

```python
loader = CommandLoader()  # No argument

# Equivalent to:
# loader.commands_dirs = [
#     Path.home() / ".kagura" / "commands",  # Global
#     Path.cwd() / ".kagura" / "commands",   # Local (priority)
# ]

commands = loader.load_all()
```

**Priority**: Local commands override global commands with the same name.

**Example**:

```
~/.kagura/commands/deploy.md       ← Global version
./.kagura/commands/deploy.md       ← Local version (used)
```

When both exist, the local version is used.

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

## InlineCommandExecutor Class

Executes inline shell commands in templates using the `!`command`` syntax.

### Constructor

```python
InlineCommandExecutor(timeout: int = 10)
```

**Parameters:**

- `timeout`: Timeout in seconds for command execution (default: 10)

### Methods

#### execute

```python
executor.execute(template: str) -> str
```

Execute all inline commands in a template string.

**Parameters:**

- `template`: Template string containing inline commands in `!`command`` format

**Returns:** Template with inline commands replaced by their output

**Example:**

```python
from kagura.commands import InlineCommandExecutor

executor = InlineCommandExecutor()

# Simple command
result = executor.execute("Current user: !`whoami`")
print(result)  # "Current user: alice"

# Multiple commands
result = executor.execute("User: !`whoami`, PWD: !`pwd`")
print(result)  # "User: alice, PWD: /home/alice/project"

# Command with pipes
result = executor.execute("Files: !`ls | wc -l`")
print(result)  # "Files: 5"
```

### Inline Command Syntax

Inline commands use the format: `!`command``

**Examples:**

```markdown
Current directory: !`pwd`
Current user: !`whoami`
Git branch: !`git branch --show-current`
File count: !`ls | wc -l`
Date: !`date +%Y-%m-%d`
```

### Error Handling

Failed commands are replaced with error messages:

```python
executor = InlineCommandExecutor()

# Nonexistent command
result = executor.execute("Result: !`nonexistent_cmd`")
print(result)  # "Result: [Error: command not found]"

# Failed command
result = executor.execute("Result: !`false`")
print(result)  # "Result: [Error: ...]"
```

### Timeout

Commands that exceed the timeout are terminated:

```python
executor = InlineCommandExecutor(timeout=1)

# This will timeout
result = executor.execute("Result: !`sleep 5`")
print(result)  # "Result: [Error: Command timed out after 1s]"
```

## CommandExecutor Class

Executes custom commands with template rendering and inline command execution.

Combines two rendering steps:
1. Execute inline commands (`!`command``)
2. Render Jinja2 template with parameters

### Constructor

```python
CommandExecutor(
    inline_timeout: int = 10,
    enable_inline: bool = True
)
```

**Parameters:**

- `inline_timeout`: Timeout for inline command execution (default: 10)
- `enable_inline`: Enable inline command execution (default: True)

### Methods

#### render

```python
executor.render(
    command: Command,
    parameters: Optional[dict[str, Any]] = None
) -> str
```

Render command template with parameters and inline commands.

**Parameters:**

- `command`: Command to render
- `parameters`: Template parameters (default: {})

**Returns:** Rendered template string

**Raises:** `ValueError` if required parameters are missing

**Example:**

```python
from kagura.commands import Command, CommandExecutor

# Command with inline commands
command = Command(
    name="status",
    description="Show status",
    template="User: {{ user }}, PWD: !`pwd`",
    parameters={"user": "string"}
)

executor = CommandExecutor()
result = executor.render(command, {"user": "Alice"})
print(result)  # "User: Alice, PWD: /home/alice"
```

#### execute

```python
executor.execute(
    command: Command,
    parameters: Optional[dict[str, Any]] = None
) -> str
```

Alias for `render()` for consistency with executor pattern.

### Rendering Order

1. **Inline commands first**: `!`pwd`` → `/home/user`
2. **Jinja2 second**: `{{ user }}` → `Alice`

**Example:**

```python
# Template
template = "{{ name }} is in !`pwd`"

# Step 1: Inline execution
# → "{{ name }} is in /home/alice"

# Step 2: Jinja2 rendering with {"name": "Alice"}
# → "Alice is in /home/alice"
```

### Disabling Inline Commands

```python
executor = CommandExecutor(enable_inline=False)
result = executor.render(command)
# Inline commands like !`pwd` are NOT executed
```

### Full Example

```python
from kagura.commands import Command, CommandExecutor

# Create command
command = Command(
    name="git-status",
    description="Show git status for user",
    template="""# Git Status Report

**User**: {{ username }}
**Branch**: !`git branch --show-current`
**Working Directory**: !`pwd`

## Changes

!`git status --short`

## Summary

You are currently on branch !`git branch --show-current` in directory !`pwd`.
""",
    parameters={"username": "string"}
)

# Execute
executor = CommandExecutor()
result = executor.render(command, {"username": "Alice"})

print(result)
# Output:
# # Git Status Report
#
# **User**: Alice
# **Branch**: main
# **Working Directory**: /home/alice/project
#
# ## Changes
#
# M src/main.py
# ?? new_file.py
#
# ## Summary
#
# You are currently on branch main in directory /home/alice/project.
```

## Hook Integration

CommandExecutor automatically applies hooks during execution. See [Hooks API](./hooks.md) for details.

### Using Hooks with CommandExecutor

```python
from kagura.commands import Command, CommandExecutor, hook, HookResult

# Define hook
@hook.pre_tool_use("bash")
def block_dangerous(tool_input):
    if "rm -rf /" in tool_input.get("command", ""):
        return HookResult.block("Dangerous command!")
    return HookResult.ok()

# Hooks automatically applied
command = Command(
    name="check",
    description="Check system",
    template="Files: !`ls`"
)

executor = CommandExecutor()
result = executor.render(command)  # Hook applied
```

### Custom Hook Registry

```python
from kagura.commands import CommandExecutor, HookRegistry

# Create custom registry
registry = HookRegistry()

# Register hooks to custom registry
# ... (register hooks)

# Use custom registry
executor = CommandExecutor(hook_registry=registry)
```

## See Also

- [Custom Commands Quick Start](../guides/commands-quickstart.md)
- [Hooks Guide](../guides/hooks-guide.md) - Hook system guide
- [Hooks API](./hooks.md) - Hooks API reference
- [CLI Commands Reference](./cli.md)
- [@agent Decorator API](./agent.md)
- [Memory Management API](./memory.md)
