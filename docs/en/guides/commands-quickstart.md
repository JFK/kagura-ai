# Custom Commands Quick Start

Learn how to create and use custom commands in Kagura AI.

## What are Custom Commands?

Custom commands are reusable AI tasks defined in simple Markdown files. They allow you to:

- Define common workflows once, use them repeatedly
- Share commands with your team via Git
- Build a library of AI-powered automation
- Use global commands across all projects
- Override global commands with project-specific versions

## Creating Your First Command

### Step 1: Create Commands Directory

**Option A: Global Commands** (available in all projects)

```bash
mkdir -p ~/.kagura/commands
```

**Option B: Local Commands** (project-specific)

```bash
mkdir -p .kagura/commands
```

**Recommended**: Use local commands for project-specific workflows, and global commands for general-purpose tasks.

By default, Kagura searches both directories:
1. `~/.kagura/commands` - Global commands
2. `./.kagura/commands` - Local commands (takes priority)

### Step 2: Create a Command File

Create `~/.kagura/commands/hello.md`:

```markdown
---
name: hello
description: Say hello to someone
---

# Task

Say hello to the user in a friendly way!
```

### Step 3: Load and Use the Command

```python
from kagura.commands import CommandLoader

# Load commands
loader = CommandLoader()
commands = loader.load_all()

# Get your command
hello = commands["hello"]

print(f"Command: {hello.name}")
print(f"Description: {hello.description}")
print(f"Template:\n{hello.template}")
```

## Command Structure

Every command file has two parts:

### 1. Frontmatter (YAML Metadata)

```yaml
---
name: my-command          # Command name
description: What it does # Description
model: gpt-4o-mini       # LLM model (optional)
allowed_tools: [git]      # Allowed tools (optional)
---
```

### 2. Body (Markdown Template)

```markdown
# Context

Current working directory...

# Task

Do something amazing!
```

## Example Commands

### Git Workflow

`~/.kagura/commands/git-workflow.md`:

```markdown
---
name: git-workflow
description: Complete git workflow (commit, push, PR)
allowed_tools: [git, gh]
model: gpt-4o-mini
---

# Task

Execute the following git workflow:

1. Create a feature branch (if on main)
2. Stage and commit all changes
3. Push to origin
4. Create a pull request

Use conventional commit format for the commit message.
```

### Code Review

`~/.kagura/commands/code-review.md`:

```markdown
---
name: code-review
description: Review code changes
model: gpt-4o
---

# Task

Review the recent code changes and provide feedback on:

1. **Code Quality**
   - Naming conventions
   - Code organization
   - Complexity

2. **Best Practices**
   - Error handling
   - Type hints
   - Documentation

3. **Potential Issues**
   - Security concerns
   - Performance problems
   - Edge cases

Provide specific, actionable feedback.
```

### Data Analysis

`~/.kagura/commands/analyze-csv.md`:

```markdown
---
name: analyze-csv
description: Analyze CSV data file
parameters:
  file: string
---

# Context

Analyzing file: {{ file }}

# Task

Perform a comprehensive analysis:

1. Data summary (rows, columns, types)
2. Missing values analysis
3. Statistical summary
4. Key insights and patterns
5. Recommendations

Present findings in a clear, structured format.
```

## Using Commands

### Load All Commands

```python
from kagura.commands import CommandLoader

loader = CommandLoader()
commands = loader.load_all()

print(f"Loaded {len(commands)} commands:")
for name in loader.list_commands():
    cmd = commands[name]
    print(f"  - {name}: {cmd.description}")
```

### Load Single Command

```python
from pathlib import Path
from kagura.commands import CommandLoader

loader = CommandLoader()
command = loader.load_command(
    Path("~/.kagura/commands/hello.md").expanduser()
)

print(command.name)
print(command.template)
```

### Get Command by Name

```python
loader = CommandLoader()
loader.load_all()

# Get specific command
cmd = loader.get_command("git-workflow")
if cmd:
    print(f"Found: {cmd.description}")
else:
    print("Command not found")
```

## Command Features

### Allowed Tools

Restrict which tools a command can use:

```yaml
---
allowed_tools: [git, gh, bash]
---
```

### Custom Model

Use a different LLM model:

```yaml
---
model: gpt-4o  # Use more powerful model
---
```

### Parameters

Define parameters for your command:

```yaml
---
parameters:
  filename: string
  count: int
  verbose: bool
---

Processing {{ filename }} with count={{ count }}
```

Validate parameters:

```python
command = loader.get_command("my-cmd")
command.validate_parameters({
    "filename": "data.csv",
    "count": 10,
    "verbose": True
})
```

### Custom Metadata

Add any custom fields:

```yaml
---
author: Your Name
version: 1.0
tags: [git, automation]
category: workflow
---
```

Access metadata:

```python
command = loader.get_command("my-cmd")
print(command.metadata["author"])  # "Your Name"
print(command.metadata["tags"])    # ["git", "automation"]
```

## Directory Structure

### Global vs Local Commands

**Global commands** (`~/.kagura/commands/`):
- Available in all projects
- General-purpose workflows
- Shared across your system

**Local commands** (`./.kagura/commands/`):
- Project-specific workflows
- Can be committed to Git
- Override global commands with same name

### Example Structure

**Global commands**:
```
~/.kagura/commands/
├── git-commit-pr.md         # Generic git workflow
├── code-review.md           # General code review
└── translate.md             # Generic translation
```

**Local commands** (in project directory):
```
.kagura/commands/
├── deploy.md                # Project-specific deployment
├── test-suite.md            # Project-specific tests
└── git-commit-pr.md         # Overrides global version
```

When both exist, **local takes priority**:
```
~/.kagura/commands/deploy.md      ← Not used (global)
./.kagura/commands/deploy.md      ← Used (local)
```

### Organizing Commands

You can organize commands by category:

```
.kagura/commands/
├── git-commit.md
├── git-pr.md
├── docs-readme.md
├── docs-changelog.md
├── code-review.md
└── data-analyze.md
```

**Note:** Subdirectory support will be added in a future release. Currently, only top-level `.md` files are loaded.

## Best Practices

### 1. Use Local Commands for Projects

**Commit local commands to Git** for team collaboration:

```bash
# Add to Git
git add .kagura/commands/
git commit -m "Add project commands"
```

This allows your team to:
- Use the same workflows
- Override with their own local changes
- Keep project-specific automation in version control

### 2. Clear, Descriptive Names

✅ Good:
```yaml
name: git-commit-push-pr
```

❌ Bad:
```yaml
name: cmd1
```

### 3. Detailed Descriptions

✅ Good:
```yaml
description: Create commit, push to origin, and open pull request
```

❌ Bad:
```yaml
description: Git stuff
```

### 4. Specific Task Instructions

✅ Good:
```markdown
# Task

1. Create feature branch from main
2. Stage all changes with `git add .`
3. Create commit with conventional format
4. Push to origin with `-u` flag
5. Create PR using `gh pr create`
```

❌ Bad:
```markdown
# Task

Do git things
```

### 5. Use Allowed Tools

Restrict tools for security:

```yaml
---
allowed_tools: [git, gh]  # Only git and GitHub CLI
---
```

### 6. Add Metadata

Help others understand your command:

```yaml
---
author: Team Name
version: 2.0
updated: 2025-01-15
category: workflow
---
```

## Troubleshooting

### Command Not Found

```python
loader = CommandLoader()
loader.load_all()

if not loader.get_command("my-cmd"):
    print("Command not found!")
    print("Available commands:", loader.list_commands())
```

### Invalid Frontmatter

If you see warnings about invalid files, check your YAML syntax:

```yaml
---
name: my-command
description: My command  # Make sure quotes are balanced
allowed_tools: [git]     # Make sure brackets match
---
```

### Directory Doesn't Exist

Create the commands directory if it doesn't exist:

```bash
mkdir -p ~/.kagura/commands
```

## Inline Command Execution

### What are Inline Commands?

Inline commands allow you to embed shell commands directly in your templates using the `!`command`` syntax. They are executed before the template is rendered.

### Basic Syntax

```markdown
Current directory: !`pwd`
Current user: !`whoami`
Git branch: !`git branch --show-current`
```

### Example Command with Inline Execution

Create `~/.kagura/commands/system-info.md`:

```markdown
---
name: system-info
description: Show system information
---

# System Information

**Current User**: !`whoami`
**Working Directory**: !`pwd`
**Git Branch**: !`git branch --show-current`
**Current Date**: !`date +%Y-%m-%d`

## Task

Analyze the current development environment.
```

### Using Inline Commands Programmatically

```python
from kagura.commands import InlineCommandExecutor

executor = InlineCommandExecutor()

# Simple command
result = executor.execute("User: !`whoami`")
print(result)  # "User: alice"

# Multiple commands
template = """
Current directory: !`pwd`
Current user: !`whoami`
Git branch: !`git branch --show-current`
"""
result = executor.execute(template)
print(result)
```

### Inline Commands with Parameters

Combine Jinja2 parameters with inline commands:

```markdown
---
name: git-info
description: Show git information
parameters:
  project: string
---

# Git Information for {{ project }}

**Branch**: !`git branch --show-current`
**Status**: !`git status --short`
**Last Commit**: !`git log -1 --oneline`

Project {{ project }} is on branch !`git branch --show-current`.
```

### Rendering Order

1. **Inline commands execute first**: `!`pwd`` → `/home/user`
2. **Jinja2 renders second**: `{{ project }}` → `my-project`

```python
from kagura.commands import Command, CommandExecutor

command = Command(
    name="example",
    description="Example",
    template="{{ name }} is in !`pwd`",
    parameters={"name": "string"}
)

executor = CommandExecutor()
result = executor.render(command, {"name": "Alice"})
# Result: "Alice is in /home/alice/project"
```

### Error Handling

Failed commands show error messages:

```markdown
Result: !`nonexistent_command`
```

Renders as:

```
Result: [Error: command not found]
```

### Disabling Inline Execution

```python
executor = CommandExecutor(enable_inline=False)
result = executor.render(command)
# Inline commands are NOT executed
```

## Using the CLI

### Installing

After installing Kagura AI, the `kagura run` command is available:

```bash
pip install kagura-ai
```

### Basic Usage

```bash
# Run a command
kagura run hello

# Run with parameters
kagura run greet --param name=Alice --param formal=true

# Use custom commands directory
kagura run my-cmd --commands-dir ./my-commands

# Disable inline command execution
kagura run my-cmd --no-inline
```

### CLI Options

```
kagura run COMMAND_NAME [OPTIONS]

Options:
  --param, -p KEY=VALUE    Command parameter (can be used multiple times)
  --commands-dir PATH      Custom commands directory
  --no-inline              Disable inline command execution
  --help                   Show help message
```

### Example: Git Workflow

Create `~/.kagura/commands/git-status.md`:

```markdown
---
name: git-status
description: Show detailed git status
parameters:
  username: string
---

# Git Status Report

**User**: {{ username }}
**Branch**: !`git branch --show-current`
**Working Directory**: !`pwd`

## Changes

!`git status --short`

## Task

Review the changes and create an appropriate commit message.
```

Run it:

```bash
kagura run git-status --param username=Alice
```

Output:

```
┏━━━━━━━━━━━━━━━━━━━━━━┓
┃ Executing Command    ┃
┗━━━━━━━━━━━━━━━━━━━━━━┛
git-status
Show detailed git status

Rendered Command:
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ # Git Status Report                ┃
┃                                     ┃
┃ **User**: Alice                    ┃
┃ **Branch**: main                   ┃
┃ **Working Directory**: /home/alice ┃
┃                                     ┃
┃ ## Changes                         ┃
┃                                     ┃
┃ M src/main.py                      ┃
┃ ?? new_file.py                     ┃
┃                                     ┃
┃ ## Task                            ┃
┃                                     ┃
┃ Review the changes and create an   ┃
┃ appropriate commit message.        ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

### Quiet Mode

Use global flags for quiet output:

```bash
kagura --quiet run my-cmd
```

This prints only the rendered result without decorations.

### Verbose Mode

Use verbose mode for debugging:

```bash
kagura --verbose run my-cmd
```

## Advanced Examples

### Command with Multiple Parameters

`~/.kagura/commands/analyze-file.md`:

```markdown
---
name: analyze-file
description: Analyze a file
parameters:
  file: string
  lines:
    type: int
    required: false
  verbose:
    type: bool
    required: false
---

# File Analysis: {{ file }}

**File Location**: !`realpath {{ file }}`
**File Size**: !`stat -c%s {{ file }}` bytes
**Line Count**: !`wc -l < {{ file }}`

{% if lines %}
**First {{ lines }} lines**:

!`head -n {{ lines }} {{ file }}`
{% endif %}

## Task

{% if verbose %}
Perform a detailed analysis of {{ file }}.
{% else %}
Provide a summary analysis of {{ file }}.
{% endif %}
```

Run it:

```bash
# Basic usage
kagura run analyze-file --param file=data.csv

# With optional parameters
kagura run analyze-file \
  --param file=data.csv \
  --param lines=10 \
  --param verbose=true
```

### Command with Pipes

`~/.kagura/commands/code-stats.md`:

```markdown
---
name: code-stats
description: Show code statistics
---

# Code Statistics

**Total Python Files**: !`find . -name "*.py" | wc -l`
**Total Lines of Code**: !`find . -name "*.py" -exec wc -l {} + | tail -1 | awk '{print $1}'`
**Most Recent Change**: !`git log -1 --format=%cr`

## Task

Review the code statistics and provide insights.
```

Run it:

```bash
kagura run code-stats
```

## Next Steps

- Read the [Commands API Reference](../api/commands.md)
- Learn about [CLI Commands](../api/cli.md)
- Explore hooks and validation (coming soon)

## Examples

Check out example commands in the [examples/commands/](https://github.com/JFK/kagura-ai/tree/main/examples/commands) directory (coming soon).
