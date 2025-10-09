# Shell Integration

## Overview

Kagura AI provides secure shell command execution through built-in functions and the `ShellExecutor` class. This enables automation of system tasks, Git operations, and file management.

## Built-in Functions

### Shell Commands

Execute shell commands securely:

```python
from kagura.builtin import shell

# Basic commands
output = await shell("ls -la")
print(output)

# With working directory
output = await shell("pwd", working_dir="/tmp")
```

### Git Operations

Automate Git workflows:

```python
from kagura.builtin import git_commit, git_push, git_status, git_create_pr

# Check status
status = await git_status()
print(status)

# Commit changes
await git_commit("feat: add new feature", files=["src/main.py"])

# Or commit all changes
await git_commit("fix: bug fix", all=True)

# Push to remote
await git_push()

# Create pull request (requires GitHub CLI)
pr_url = await git_create_pr(
    title="feat: implement shell integration",
    body="This PR adds shell execution capabilities"
)
```

### File Operations

Search and analyze files:

```python
from kagura.builtin import file_search, grep_content

# Search for Python test files
test_files = await file_search(
    pattern="test",
    directory="./tests",
    file_type="*.py"
)

# Search for TODOs in files
results = await grep_content("TODO", test_files)
for file, matches in results.items():
    print(f"{file}: {len(matches)} TODOs")
```

## Security

Shell execution is protected by:

1. **Whitelist**: Only approved commands are allowed
2. **Blacklist**: Dangerous commands are blocked
3. **Timeout**: Commands have 30-second timeout by default
4. **Working Directory**: Commands run in isolated directories

Default allowed commands:
- Git: `git`, `gh`
- File operations: `ls`, `cat`, `find`, `grep`, `mkdir`, `rm`, `cp`, `mv`
- Package managers: `npm`, `pip`, `uv`, `poetry`, `yarn`
- Build tools: `make`, `cargo`, `go`
- Testing: `pytest`, `jest`, `vitest`

## Advanced Usage

### Custom ShellExecutor

For more control, use `ShellExecutor` directly:

```python
from kagura.core.shell import ShellExecutor
from pathlib import Path

executor = ShellExecutor(
    allowed_commands=["git", "npm"],  # Restrict to specific commands
    timeout=60,  # Custom timeout
    working_dir=Path("./my-project")
)

result = await executor.exec("git status")
if result.success:
    print(result.stdout)
else:
    print(f"Error: {result.stderr}")
```

### Error Handling

```python
from kagura.builtin import shell
from kagura.core.shell import SecurityError

try:
    output = await shell("my-command")
except SecurityError as e:
    print(f"Command blocked: {e}")
except RuntimeError as e:
    print(f"Command failed: {e}")
except TimeoutError as e:
    print(f"Command timed out: {e}")
```

## Examples

### Automated Deployment

```python
from kagura.builtin import shell, git_commit, git_push

async def deploy(version: str):
    """Deploy application"""

    # Run tests
    test_result = await shell("pytest tests/")
    if "FAILED" in test_result:
        raise RuntimeError("Tests failed")

    # Build
    await shell("uv build")

    # Commit and push
    await git_commit(f"chore: release v{version}")
    await shell(f"git tag v{version}")
    await git_push()
    await shell("git push --tags")

    print(f"✓ Deployed v{version}")

# Usage
import asyncio
asyncio.run(deploy("2.1.0"))
```

### Code Quality Check

```python
from kagura.builtin import file_search, grep_content, shell

async def code_review():
    """Run automated code review"""
    issues = {}

    # Find Python files
    py_files = await file_search("*.py", directory="src/")

    # Check for TODOs
    todos = await grep_content("TODO", py_files)
    if todos:
        issues["todos"] = todos

    # Run linter
    ruff_output = await shell("ruff check src/")
    if ruff_output:
        issues["lint"] = ruff_output

    # Run type checker
    pyright_output = await shell("pyright src/")
    if "error" in pyright_output.lower():
        issues["types"] = pyright_output

    return issues

# Usage
import asyncio
results = asyncio.run(code_review())
print(f"Found {len(results)} issue types")
```

## See Also

- [Shell API Reference](../api/shell.md)
- [ShellExecutor Documentation](../api/shell.md#shellexecutor)
