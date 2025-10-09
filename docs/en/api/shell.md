# Shell API Reference

## Overview

The Shell module provides secure shell command execution with security controls including command whitelisting, blacklisting, and timeout management.

## Module: `kagura.core.shell`

### `class ShellExecutor`

Secure shell command executor with security controls.

**Constructor:**
```python
ShellExecutor(
    allowed_commands: Optional[list[str]] = None,
    blocked_commands: Optional[list[str]] = None,
    working_dir: Optional[Path] = None,
    timeout: int = 30,
    require_confirmation: bool = False
)
```

**Parameters:**
- `allowed_commands`: Whitelist of allowed commands (None = use defaults)
- `blocked_commands`: Blacklist of blocked commands (None = use defaults)
- `working_dir`: Working directory for command execution
- `timeout`: Command timeout in seconds (default: 30)
- `require_confirmation`: Whether to require user confirmation

**Methods:**

#### `async exec(command: str, env: Optional[dict[str, str]] = None, capture_output: bool = True) -> ShellResult`

Execute shell command securely.

**Parameters:**
- `command`: Shell command to execute
- `env`: Environment variables (optional)
- `capture_output`: Whether to capture stdout/stderr

**Returns:**
- `ShellResult` containing execution results

**Raises:**
- `SecurityError`: If command violates security policy
- `TimeoutError`: If command exceeds timeout
- `UserCancelledError`: If user cancels execution

**Example:**
```python
from kagura.core.shell import ShellExecutor
from pathlib import Path

executor = ShellExecutor(
    allowed_commands=["git", "npm"],
    timeout=60,
    working_dir=Path("./project")
)

result = await executor.exec("git status")
if result.success:
    print(result.stdout)
```

#### `validate_command(command: str) -> bool`

Validate command against security policies.

**Parameters:**
- `command`: Shell command to validate

**Returns:**
- `True` if command is valid

**Raises:**
- `SecurityError`: If command violates security policy

**Example:**
```python
executor = ShellExecutor(allowed_commands=["echo", "ls"])

# Will pass
executor.validate_command("echo hello")

# Will raise SecurityError
executor.validate_command("rm -rf /")
```

---

### `class ShellResult`

Result of shell command execution.

**Attributes:**
- `return_code: int` - Process exit code
- `stdout: str` - Standard output
- `stderr: str` - Standard error
- `command: str` - Executed command

**Properties:**

#### `success: bool`

Check if command executed successfully (return code == 0).

**Example:**
```python
result = await executor.exec("ls")
if result.success:
    print("Command succeeded")
```

---

### Exceptions

#### `SecurityError`

Raised when command violates security policy.

```python
from kagura.core.shell import SecurityError

try:
    await executor.exec("sudo rm -rf /")
except SecurityError as e:
    print(f"Command blocked: {e}")
```

#### `UserCancelledError`

Raised when user cancels command execution.

---

## Module: `kagura.builtin`

### Built-in Shell Functions

#### `async shell(command: str, working_dir: str = ".") -> str`

Execute a shell command safely.

**Parameters:**
- `command`: The shell command to execute
- `working_dir`: Working directory (default: current directory)

**Returns:**
- Command output (stdout if success, stderr if failed)

**Raises:**
- `RuntimeError`: If command execution fails
- `SecurityError`: If command violates security policy

**Example:**
```python
from kagura.builtin import shell

output = await shell("ls -la")
print(output)

output = await shell("pwd", working_dir="/tmp")
```

---

### Built-in Git Functions

#### `async git_commit(message: str, files: list[str] | None = None, all: bool = False) -> str`

Create a git commit.

**Parameters:**
- `message`: Commit message
- `files`: Specific files to commit (optional)
- `all`: Commit all changes (git commit -a)

**Returns:**
- Git commit output

**Example:**
```python
from kagura.builtin import git_commit

await git_commit("feat: add feature", files=["src/main.py"])
await git_commit("fix: bug fix", all=True)
```

#### `async git_push(remote: str = "origin", branch: str | None = None) -> str`

Push commits to remote repository.

**Parameters:**
- `remote`: Remote name (default: origin)
- `branch`: Branch name (default: current branch)

**Returns:**
- Git push output

**Example:**
```python
from kagura.builtin import git_push

await git_push()
await git_push(remote="origin", branch="main")
```

#### `async git_status() -> str`

Get git repository status.

**Returns:**
- Git status output

**Example:**
```python
from kagura.builtin import git_status

status = await git_status()
print(status)
```

#### `async git_create_pr(title: str, body: str, base: str = "main") -> str`

Create a pull request using GitHub CLI.

**Requires:** GitHub CLI (`gh`) installed and authenticated

**Parameters:**
- `title`: PR title
- `body`: PR description
- `base`: Base branch (default: main)

**Returns:**
- PR URL

**Example:**
```python
from kagura.builtin import git_create_pr

pr_url = await git_create_pr(
    title="feat: new feature",
    body="This PR adds a new feature"
)
```

---

### Built-in File Functions

#### `async file_search(pattern: str, directory: str = ".", file_type: str = "*") -> list[str]`

Search for files matching pattern.

**Parameters:**
- `pattern`: File name pattern to search for
- `directory`: Directory to search in (default: current directory)
- `file_type`: File extension filter (e.g., "*.py", "*.txt")

**Returns:**
- List of matching file paths

**Example:**
```python
from kagura.builtin import file_search

files = await file_search("test", directory="./tests", file_type="*.py")
print(f"Found {len(files)} test files")
```

#### `async grep_content(pattern: str, files: list[str]) -> dict[str, list[str]]`

Search for content in files.

**Parameters:**
- `pattern`: Text pattern to search for
- `files`: List of file paths to search in

**Returns:**
- Dictionary mapping file paths to matching lines

**Example:**
```python
from kagura.builtin import grep_content

results = await grep_content("TODO", ["src/main.py", "src/utils.py"])
for file, lines in results.items():
    print(f"{file}: {len(lines)} matches")
```

---

## Security Configuration

### Default Allowed Commands

```python
[
    # Git
    "git", "gh",
    # File operations
    "ls", "cat", "find", "grep", "mkdir", "rm", "cp", "mv", "pwd",
    # Package managers
    "npm", "pip", "uv", "poetry", "yarn", "pnpm",
    # Build tools
    "make", "cmake", "cargo", "go",
    # Testing
    "pytest", "jest", "vitest",
    # Others
    "echo", "which", "wc", "sort", "uniq"
]
```

### Default Blocked Commands

```python
[
    "sudo", "su", "passwd", "shutdown", "reboot",
    "dd", "mkfs", "fdisk", "parted",
    "eval", "exec", "source",
    "curl -s | sh", "wget -O - | sh", "rm -rf /"
]
```

---

## See Also

- [Shell Integration Tutorial](../tutorials/07-shell-integration.md)
- [Built-in Functions](../tutorials/07-shell-integration.md#built-in-functions)
