# Hooks Guide

Learn how to use hooks to intercept and control command execution.

## What are Hooks?

Hooks allow you to:

- 🛡️ Block dangerous commands
- ✏️ Modify inputs before execution
- 📊 Log and monitor tool usage
- ✅ Validate parameters
- 💡 Suggest better alternatives

## Hook Types

### 1. PreToolUse Hooks

Execute **before** a tool is invoked.

**Use cases:**
- Security validation
- Input modification
- Command blocking

**Example:**

```python
from kagura.commands import hook, HookResult

@hook.pre_tool_use("bash")
def block_dangerous(tool_input):
    cmd = tool_input.get("command", "")
    if "rm -rf /" in cmd:
        return HookResult.block("Dangerous command blocked!")
    return HookResult.ok()
```

### 2. PostToolUse Hooks

Execute **after** a tool completes.

**Use cases:**
- Logging
- Metrics collection
- Output processing

**Example:**

```python
@hook.post_tool_use("git")
def log_git(tool_input):
    cmd = tool_input["command"]
    output = tool_input["output"]
    print(f"Git: {cmd} -> {output}")
    return HookResult.ok()
```

### 3. Validation Hooks

Execute **before** parameter validation.

**Use cases:**
- Custom validation rules
- Parameter transformation
- Environment checks

**Example:**

```python
@hook.validation("deploy")
def require_environment(tool_input):
    params = tool_input.get("parameters", {})
    if "environment" not in params:
        return HookResult.block("Missing 'environment' parameter")
    return HookResult.ok()
```

## Quick Start

### Step 1: Define a Hook

```python
from kagura.commands import hook, HookResult

@hook.pre_tool_use("bash")
def safety_check(tool_input):
    """Block dangerous bash commands."""
    cmd = tool_input.get("command", "")

    # Block dangerous commands
    if any(pattern in cmd for pattern in ["rm -rf /", "dd if="]):
        return HookResult.block("Dangerous command blocked!")

    return HookResult.ok()
```

### Step 2: Use Commands

Hooks are **automatically applied** when executing commands:

```python
from kagura.commands import Command, CommandExecutor

command = Command(
    name="check-files",
    description="Check files",
    template="Files: !`ls`"
)

executor = CommandExecutor()
result = executor.render(command)  # Hook automatically applied
print(result)
```

### Step 3: Blocked Execution

If a hook blocks execution:

```markdown
Files: [Blocked: Dangerous command blocked!]
```

## Common Use Cases

### Security: Block Dangerous Commands

```python
from kagura.commands import hook, HookResult

# Block specific commands
@hook.pre_tool_use("bash")
def block_dangerous(tool_input):
    cmd = tool_input.get("command", "")

    dangerous = [
        "rm -rf /",
        ":(){ :|:& };:",  # Fork bomb
        "mkfs.",  # Format filesystem
        "> /dev/sda",  # Overwrite disk
    ]

    for pattern in dangerous:
        if pattern in cmd:
            return HookResult.block(f"Blocked: {pattern}")

    return HookResult.ok()
```

### Safety: Add Interactive Flags

```python
@hook.pre_tool_use("bash")
def add_interactive(tool_input):
    """Add --interactive flag to rm commands."""
    cmd = tool_input.get("command", "")

    if cmd.startswith("rm ") and "--interactive" not in cmd:
        # Modify command
        modified = {"command": f"{cmd} --interactive"}
        return HookResult.modify(modified, "Added --interactive")

    return HookResult.ok()
```

### Logging: Track Tool Usage

```python
import logging

@hook.post_tool_use("*")  # All tools
def log_execution(tool_input):
    """Log all tool executions."""
    tool = tool_input.get("tool", "unknown")
    cmd = tool_input.get("command", "")
    returncode = tool_input.get("returncode", 0)

    if returncode == 0:
        logging.info(f"{tool}: {cmd} - SUCCESS")
    else:
        logging.error(f"{tool}: {cmd} - FAILED ({returncode})")

    return HookResult.ok()
```

### Suggestions: Recommend Better Tools

```python
@hook.pre_tool_use("bash")
def suggest_modern_tools(tool_input):
    """Suggest modern alternatives."""
    cmd = tool_input.get("command", "")

    suggestions = {
        "grep": "rg (ripgrep)",
        "find": "fd",
        "cat": "bat",
        "ls": "exa",
    }

    for old_tool, new_tool in suggestions.items():
        if cmd.startswith(old_tool):
            return HookResult.suggest(f"Consider using '{new_tool}'")

    return HookResult.ok()
```

### Validation: Enforce Rules

```python
@hook.validation("deploy")
def validate_deploy(tool_input):
    """Validate deployment parameters."""
    params = tool_input.get("parameters", {})
    env = params.get("environment")

    # Require environment
    if not env:
        return HookResult.block("Missing 'environment' parameter")

    # Only allow specific environments
    allowed = ["development", "staging", "production"]
    if env not in allowed:
        return HookResult.block(
            f"Invalid environment '{env}'. Allowed: {allowed}"
        )

    # Production requires confirmation
    if env == "production" and not params.get("confirmed"):
        return HookResult.block(
            "Production deployment requires 'confirmed=true'"
        )

    return HookResult.ok()
```

## Advanced Patterns

### Conditional Modification

```python
@hook.pre_tool_use("bash")
def add_timeout(tool_input):
    """Add timeout to long-running commands."""
    cmd = tool_input.get("command", "")

    # Commands that might hang
    risky_commands = ["curl", "wget", "ssh"]

    for risky in risky_commands:
        if cmd.startswith(risky) and "timeout" not in cmd:
            modified = {"command": f"timeout 30 {cmd}"}
            return HookResult.modify(modified, "Added 30s timeout")

    return HookResult.ok()
```

### Environment-Specific Hooks

```python
import os

@hook.pre_tool_use("*")
def production_safety(tool_input):
    """Extra safety in production."""
    if os.getenv("ENVIRONMENT") != "production":
        return HookResult.ok()

    # In production, require confirmation for destructive operations
    cmd = tool_input.get("command", "")
    destructive = ["rm", "drop", "delete", "truncate"]

    if any(op in cmd.lower() for op in destructive):
        return HookResult.block(
            "Destructive operations require manual confirmation in production"
        )

    return HookResult.ok()
```

### Chaining Hooks

Multiple hooks can be registered for the same tool:

```python
@hook.pre_tool_use("bash")
def security_check(tool_input):
    """First check: security."""
    if "rm -rf /" in tool_input.get("command", ""):
        return HookResult.block("Security: Blocked")
    return HookResult.ok()

@hook.pre_tool_use("bash")
def add_safety_flags(tool_input):
    """Second check: add flags."""
    cmd = tool_input.get("command", "")
    if cmd.startswith("rm "):
        modified = {"command": f"{cmd} --interactive"}
        return HookResult.modify(modified)
    return HookResult.ok()

# Both hooks run in order
# If first blocks, second never runs
```

## Hook Management

### Disable a Hook

```python
from kagura.commands import get_registry, HookType

registry = get_registry()

# Find and disable
hooks = registry.get_hooks(HookType.PRE_TOOL_USE, "bash")
for h in hooks:
    if h.name == "security_check":
        h.enabled = False
```

### Remove a Hook

```python
from kagura.commands import get_registry

registry = get_registry()
registry.unregister("security_check")
```

### Clear All Hooks

```python
from kagura.commands import get_registry, HookType

registry = get_registry()

# Clear specific type
registry.clear(HookType.PRE_TOOL_USE)

# Clear all
registry.clear()
```

### Count Hooks

```python
from kagura.commands import get_registry, HookType

registry = get_registry()

print(f"Total hooks: {registry.count()}")
print(f"Pre-tool-use hooks: {registry.count(HookType.PRE_TOOL_USE)}")
print(f"Post-tool-use hooks: {registry.count(HookType.POST_TOOL_USE)}")
print(f"Validation hooks: {registry.count(HookType.VALIDATION)}")
```

## Best Practices

### 1. Fail Safe

Hooks should not break execution if they fail:

```python
@hook.pre_tool_use("*")
def safe_hook(tool_input):
    try:
        # Your logic here
        return HookResult.ok()
    except Exception as e:
        # Log error but don't block
        logging.error(f"Hook failed: {e}")
        return HookResult.ok()
```

### 2. Specific Matchers

Use specific matchers when possible:

```python
# ✅ Good: Specific
@hook.pre_tool_use("bash")
def validate_bash(tool_input):
    ...

# ⚠️ OK but slower: Catch-all
@hook.pre_tool_use("*")
def validate_all(tool_input):
    ...
```

### 3. Clear Error Messages

Provide helpful error messages when blocking:

```python
# ✅ Good: Clear and actionable
return HookResult.block(
    "Command 'rm -rf /' is not allowed. Use 'rm -rf ./directory' instead."
)

# ❌ Bad: Vague
return HookResult.block("Blocked")
```

### 4. Document Hooks

Add docstrings to explain hook purpose:

```python
@hook.pre_tool_use("bash")
def block_fork_bombs(tool_input):
    """Block fork bomb patterns.

    Prevents execution of commands containing fork bomb syntax:
    - :(){ :|:& };:
    - .(){.|.&};.

    These patterns can crash the system by consuming all resources.
    """
    ...
```

### 5. Test Hooks

Test your hooks to ensure they work correctly:

```python
def test_block_dangerous():
    """Test that dangerous commands are blocked."""
    from kagura.commands import InlineCommandExecutor, HookRegistry

    registry = HookRegistry()

    @hook.pre_tool_use("bash")
    def block_rm_rf(tool_input):
        if "rm -rf /" in tool_input.get("command", ""):
            return HookResult.block("Blocked")
        return HookResult.ok()

    executor = InlineCommandExecutor(hook_registry=registry)
    result = executor.execute("!`rm -rf /`")

    assert "[Blocked:" in result
```

## Troubleshooting

### Hook Not Firing

1. **Check matcher**: Ensure matcher matches the tool name
2. **Check enabled**: Verify `hook.enabled == True`
3. **Check registry**: Use correct registry instance

```python
from kagura.commands import get_registry, HookType

registry = get_registry()
hooks = registry.get_hooks(HookType.PRE_TOOL_USE, "bash")

for h in hooks:
    print(f"{h.name}: enabled={h.enabled}, matcher={h.matcher}")
```

### Hook Blocks Too Much

Refine your hook logic:

```python
# ❌ Too broad
@hook.pre_tool_use("bash")
def block_all_rm(tool_input):
    if "rm" in tool_input.get("command", ""):
        return HookResult.block("Blocked")
    return HookResult.ok()

# ✅ More specific
@hook.pre_tool_use("bash")
def block_dangerous_rm(tool_input):
    cmd = tool_input.get("command", "")
    if "rm -rf /" in cmd or "rm -rf ~" in cmd:
        return HookResult.block("Blocked")
    return HookResult.ok()
```

### Hook Exceptions

Hooks should handle their own exceptions:

```python
@hook.pre_tool_use("bash")
def safe_hook(tool_input):
    try:
        # Risky operation
        result = some_operation(tool_input)
        return HookResult.ok()
    except Exception as e:
        # Log and continue
        logging.error(f"Hook failed: {e}")
        return HookResult.ok()  # Don't block on error
```

## Examples

### Complete Security Setup

```python
from kagura.commands import hook, HookResult
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

@hook.pre_tool_use("bash")
def security_validator(tool_input):
    """Comprehensive security validation."""
    cmd = tool_input.get("command", "")

    # Block list
    dangerous = [
        "rm -rf /",
        "dd if=/dev/zero of=/dev/sda",
        "mkfs",
        ":(){ :|:& };:",
    ]

    for pattern in dangerous:
        if pattern in cmd:
            logging.warning(f"SECURITY: Blocked '{cmd}'")
            return HookResult.block(f"Security: '{pattern}' not allowed")

    return HookResult.ok()

@hook.pre_tool_use("bash")
def add_safety_nets(tool_input):
    """Add safety flags to destructive commands."""
    cmd = tool_input.get("command", "")

    if cmd.startswith("rm ") and "-i" not in cmd:
        modified = {"command": f"{cmd} -i"}
        return HookResult.modify(modified, "Added -i flag")

    return HookResult.ok()

@hook.post_tool_use("*")
def audit_log(tool_input):
    """Audit all command executions."""
    tool = tool_input.get("tool", "unknown")
    cmd = tool_input.get("command", "")
    returncode = tool_input.get("returncode", 0)

    logging.info(f"AUDIT: {tool} | {cmd} | exit={returncode}")
    return HookResult.ok()
```

## Next Steps

- Read the [Hooks API Reference](../api/hooks.md)
- Learn about [Custom Commands](./commands-quickstart.md)
- Explore [Advanced Patterns](#advanced-patterns)

## See Also

- [Hooks API](../api/hooks.md) - Complete API reference
- [Commands Guide](./commands-quickstart.md) - Custom commands
- [CLI Reference](../api/cli.md) - Command-line interface
