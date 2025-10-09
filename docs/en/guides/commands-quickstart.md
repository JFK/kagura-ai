# Custom Commands Quick Start

Learn how to create and use custom commands in Kagura AI.

## What are Custom Commands?

Custom commands are reusable AI tasks defined in simple Markdown files. They allow you to:

- Define common workflows once, use them repeatedly
- Share commands with your team
- Build a library of AI-powered automation

## Creating Your First Command

### Step 1: Create Commands Directory

```bash
mkdir -p ~/.kagura/commands
```

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

Organize commands by category:

```
~/.kagura/commands/
├── git/
│   ├── commit-pr.md
│   ├── sync-fork.md
│   └── rebase-main.md
├── docs/
│   ├── generate-readme.md
│   ├── update-changelog.md
│   └── api-docs.md
├── code/
│   ├── review.md
│   ├── refactor.md
│   └── test-gen.md
└── data/
    ├── analyze-csv.md
    └── clean-data.md
```

**Note:** Currently, the loader only searches the top-level commands directory. Subdirectory support will be added in a future release.

## Best Practices

### 1. Clear, Descriptive Names

✅ Good:
```yaml
name: git-commit-push-pr
```

❌ Bad:
```yaml
name: cmd1
```

### 2. Detailed Descriptions

✅ Good:
```yaml
description: Create commit, push to origin, and open pull request
```

❌ Bad:
```yaml
description: Git stuff
```

### 3. Specific Task Instructions

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

### 4. Use Allowed Tools

Restrict tools for security:

```yaml
---
allowed_tools: [git, gh]  # Only git and GitHub CLI
---
```

### 5. Add Metadata

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

## Next Steps

- Read the [Commands API Reference](../api/commands.md)
- Learn about inline command execution (coming soon)
- Explore hooks and validation (coming soon)

## Examples

Check out example commands in the [examples/commands/](https://github.com/JFK/kagura-ai/tree/main/examples/commands) directory (coming soon).
