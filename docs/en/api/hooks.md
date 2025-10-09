# Hooks API

Hooks allow you to intercept and modify command execution flow.

## Overview

The hooks system provides three types of hooks:

1. **PreToolUse**: Execute before a tool is invoked
2. **PostToolUse**: Execute after a tool completes
3. **Validation**: Validate command parameters before execution

Hooks can:
- ✅ Block execution
- ✅ Modify inputs
- ✅ Suggest alternatives
- ✅ Log execution

## HookResult Class

Result from hook execution.

### Constructor

```python
HookResult(
    action: HookAction,
    message: Optional[str] = None,
    modified_input: Optional[dict[str, Any]] = None
)
```

### Factory Methods

#### ok

```python
HookResult.ok(message: Optional[str] = None) -> HookResult
```

Continue execution normally.

**Example:**

```python
@hook.pre_tool_use("bash")
def allow_command(tool_input):
    return HookResult.ok("Command allowed")
```

#### block

```python
HookResult.block(message: str) -> HookResult
```

Block execution with error message.

**Example:**

```python
@hook.pre_tool_use("bash")
def block_dangerous(tool_input):
    if "rm -rf /" in tool_input["command"]:
        return HookResult.block("Dangerous command blocked!")
    return HookResult.ok()
```

#### suggest

```python
HookResult.suggest(message: str) -> HookResult
```

Suggest an alternative (doesn't block execution).

**Example:**

```python
@hook.pre_tool_use("bash")
def suggest_alternative(tool_input):
    if "grep" in tool_input["command"]:
        return HookResult.suggest("Consider using 'rg' instead")
    return HookResult.ok()
```

#### modify

```python
HookResult.modify(
    modified_input: dict[str, Any],
    message: Optional[str] = None
) -> HookResult
```

Modify input before execution.

**Example:**

```python
@hook.pre_tool_use("bash")
def add_safety_flag(tool_input):
    cmd = tool_input["command"]
    if cmd.startswith("rm "):
        modified = {"command": f"{cmd} --interactive"}
        return HookResult.modify(modified, "Added --interactive flag")
    return HookResult.ok()
```

### Methods

#### is_ok

```python
result.is_ok() -> bool
```

Check if result allows execution.

#### is_blocked

```python
result.is_blocked() -> bool
```

Check if result blocks execution.

## Hook Class

Base hook class.

### Constructor

```python
Hook(
    name: str,
    hook_type: HookType,
    matcher: str,
    callback: Callable[[dict[str, Any]], HookResult],
    enabled: bool = True
)
```

**Parameters:**

- `name`: Hook name (unique identifier)
- `hook_type`: Type of hook (PRE_TOOL_USE, POST_TOOL_USE, VALIDATION)
- `matcher`: Tool name pattern (`"bash"`, `"git"`, `"*"` for all)
- `callback`: Function to call when hook is triggered
- `enabled`: Whether hook is active

**Example:**

```python
from kagura.commands import Hook, HookType, HookResult

def validate_bash(tool_input):
    if dangerous(tool_input["command"]):
        return HookResult.block("Blocked!")
    return HookResult.ok()

hook = Hook(
    name="bash-validator",
    hook_type=HookType.PRE_TOOL_USE,
    matcher="bash",
    callback=validate_bash
)
```

### Methods

#### matches

```python
hook.matches(tool_name: str) -> bool
```

Check if hook applies to the given tool.

**Example:**

```python
bash_hook = Hook(..., matcher="bash", ...)
bash_hook.matches("bash")  # True
bash_hook.matches("git")   # False

all_hook = Hook(..., matcher="*", ...)
all_hook.matches("bash")  # True
all_hook.matches("git")   # True
```

#### execute

```python
hook.execute(tool_input: dict[str, Any]) -> HookResult
```

Execute hook callback.

**Parameters:**

- `tool_input`: Input dictionary containing tool information

**Returns:** HookResult

## HookRegistry Class

Registry for managing hooks.

### Constructor

```python
HookRegistry()
```

Creates a new hook registry.

### Methods

#### register

```python
registry.register(hook: Hook) -> None
```

Register a hook.

**Example:**

```python
from kagura.commands import HookRegistry, Hook, HookType, HookResult

registry = HookRegistry()

def callback(tool_input):
    return HookResult.ok()

hook = Hook(
    name="my-hook",
    hook_type=HookType.PRE_TOOL_USE,
    matcher="bash",
    callback=callback
)

registry.register(hook)
```

#### unregister

```python
registry.unregister(
    hook_name: str,
    hook_type: Optional[HookType] = None
) -> bool
```

Unregister a hook by name.

**Returns:** `True` if removed, `False` if not found

**Example:**

```python
removed = registry.unregister("my-hook")
if removed:
    print("Hook removed")
```

#### get_hooks

```python
registry.get_hooks(hook_type: HookType, tool_name: str) -> list[Hook]
```

Get all hooks matching the given type and tool.

**Example:**

```python
# Get all pre-tool-use hooks for bash
hooks = registry.get_hooks(HookType.PRE_TOOL_USE, "bash")
```

#### execute_hooks

```python
registry.execute_hooks(
    hook_type: HookType,
    tool_name: str,
    tool_input: dict[str, Any]
) -> list[HookResult]
```

Execute all matching hooks.

**Returns:** List of HookResult (stops on first block)

**Example:**

```python
results = registry.execute_hooks(
    HookType.PRE_TOOL_USE,
    "bash",
    {"command": "ls"}
)

for result in results:
    if result.is_blocked():
        print(f"Blocked: {result.message}")
```

#### clear

```python
registry.clear(hook_type: Optional[HookType] = None) -> None
```

Clear hooks. If `hook_type` is None, clears all hooks.

**Example:**

```python
# Clear only pre-tool-use hooks
registry.clear(HookType.PRE_TOOL_USE)

# Clear all hooks
registry.clear()
```

#### count

```python
registry.count(hook_type: Optional[HookType] = None) -> int
```

Count registered hooks.

**Example:**

```python
# Count all hooks
total = registry.count()

# Count specific type
pre_hooks = registry.count(HookType.PRE_TOOL_USE)
```

## Decorator API

Convenient decorators for registering hooks.

### @hook.pre_tool_use

```python
@hook.pre_tool_use(matcher: str = "*", name: str | None = None)
```

Decorator for PreToolUse hooks.

**Parameters:**

- `matcher`: Tool name pattern (default: `"*"` for all)
- `name`: Optional hook name (default: function name)

**Example:**

```python
from kagura.commands import hook, HookResult

@hook.pre_tool_use("bash")
def validate_bash(tool_input):
    cmd = tool_input.get("command", "")
    if "rm -rf /" in cmd:
        return HookResult.block("Dangerous command!")
    return HookResult.ok()

@hook.pre_tool_use("*")  # All tools
def log_all(tool_input):
    print(f"Tool: {tool_input}")
    return HookResult.ok()
```

### @hook.post_tool_use

```python
@hook.post_tool_use(matcher: str = "*", name: str | None = None)
```

Decorator for PostToolUse hooks.

**Parameters:**

- `matcher`: Tool name pattern
- `name`: Optional hook name

**Example:**

```python
@hook.post_tool_use("git")
def log_git_usage(tool_input):
    cmd = tool_input.get("command", "")
    output = tool_input.get("output", "")
    print(f"Git command '{cmd}' executed")
    print(f"Output: {output}")
    return HookResult.ok()
```

### @hook.validation

```python
@hook.validation(matcher: str = "*", name: str | None = None)
```

Decorator for Validation hooks.

**Parameters:**

- `matcher`: Command name pattern
- `name`: Optional hook name

**Example:**

```python
@hook.validation("*")
def validate_parameters(tool_input):
    params = tool_input.get("parameters", {})
    if not params:
        return HookResult.block("Parameters required!")
    return HookResult.ok()
```

## Global Registry

```python
from kagura.commands import get_registry

registry = get_registry()
```

Get the global hook registry used by CommandExecutor.

**Example:**

```python
from kagura.commands import get_registry, Hook, HookType, HookResult

# Get global registry
registry = get_registry()

# Register hook directly
def callback(tool_input):
    return HookResult.ok()

hook = Hook(
    name="custom",
    hook_type=HookType.PRE_TOOL_USE,
    matcher="bash",
    callback=callback
)
registry.register(hook)

# Or use decorator (automatically uses global registry)
from kagura.commands import hook

@hook.pre_tool_use("bash")
def validate(tool_input):
    return HookResult.ok()
```

## Complete Example

```python
from kagura.commands import (
    Command,
    CommandExecutor,
    hook,
    HookResult,
    get_registry
)

# Define hooks using decorators
@hook.pre_tool_use("bash")
def block_dangerous(tool_input):
    """Block dangerous bash commands."""
    cmd = tool_input.get("command", "")

    dangerous_patterns = ["rm -rf /", ":(){ :|:& };:"]
    for pattern in dangerous_patterns:
        if pattern in cmd:
            return HookResult.block(
                f"Dangerous command blocked: {pattern}"
            )

    return HookResult.ok()

@hook.pre_tool_use("bash")
def suggest_safer(tool_input):
    """Suggest safer alternatives."""
    cmd = tool_input.get("command", "")

    if cmd.startswith("rm ") and "--interactive" not in cmd:
        return HookResult.suggest(
            "Consider using 'rm --interactive' for safety"
        )

    return HookResult.ok()

@hook.post_tool_use("*")
def log_execution(tool_input):
    """Log all tool executions."""
    tool = tool_input.get("tool", "unknown")
    cmd = tool_input.get("command", "")
    print(f"[LOG] {tool}: {cmd}")
    return HookResult.ok()

@hook.validation("*")
def ensure_parameters(tool_input):
    """Ensure required parameters are provided."""
    params = tool_input.get("parameters", {})
    cmd_name = tool_input.get("command_name", "")

    if cmd_name == "deploy" and "environment" not in params:
        return HookResult.block(
            "Deployment requires 'environment' parameter"
        )

    return HookResult.ok()

# Create command
command = Command(
    name="deploy",
    description="Deploy application",
    template="Deploying to {{ environment }}: !`git rev-parse HEAD`",
    parameters={"environment": "string"}
)

# Execute (hooks are automatically applied)
executor = CommandExecutor()

try:
    result = executor.render(command, {"environment": "production"})
    print(result)
except ValueError as e:
    print(f"Validation failed: {e}")
```

## Hook Execution Order

1. **Validation Hooks**: Run before parameter validation
2. **Parameter Validation**: Built-in validation (if hook didn't block)
3. **PreToolUse Hooks**: Run before each inline command execution
4. **Tool Execution**: Execute the actual command
5. **PostToolUse Hooks**: Run after tool completes

## See Also

- [Hooks Guide](../guides/hooks-guide.md) - Usage guide with examples
- [Commands API](./commands.md) - Command system API
- [CLI Reference](./cli.md) - CLI commands
