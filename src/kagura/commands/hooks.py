"""Hook system for command execution.

Provides hooks for intercepting and modifying command execution flow.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional


class HookType(Enum):
    """Type of hook."""

    PRE_TOOL_USE = "pre_tool_use"  # Before tool execution
    POST_TOOL_USE = "post_tool_use"  # After tool execution
    VALIDATION = "validation"  # Parameter validation


class HookAction(Enum):
    """Action to take based on hook result."""

    OK = "ok"  # Continue normally
    BLOCK = "block"  # Block execution
    SUGGEST = "suggest"  # Suggest alternative
    MODIFY = "modify"  # Modify input


@dataclass
class HookResult:
    """Result from hook execution.

    Attributes:
        action: Action to take (ok, block, suggest, modify)
        message: Optional message to display
        modified_input: Modified input if action is MODIFY
    """

    action: HookAction
    message: Optional[str] = None
    modified_input: Optional[dict[str, Any]] = None

    @classmethod
    def ok(cls, message: Optional[str] = None) -> "HookResult":
        """Create OK result (continue execution).

        Args:
            message: Optional informational message

        Returns:
            HookResult with OK action
        """
        return cls(action=HookAction.OK, message=message)

    @classmethod
    def block(cls, message: str) -> "HookResult":
        """Create BLOCK result (prevent execution).

        Args:
            message: Reason for blocking

        Returns:
            HookResult with BLOCK action
        """
        return cls(action=HookAction.BLOCK, message=message)

    @classmethod
    def suggest(cls, message: str) -> "HookResult":
        """Create SUGGEST result (recommend alternative).

        Args:
            message: Suggestion message

        Returns:
            HookResult with SUGGEST action
        """
        return cls(action=HookAction.SUGGEST, message=message)

    @classmethod
    def modify(
        cls, modified_input: dict[str, Any], message: Optional[str] = None
    ) -> "HookResult":
        """Create MODIFY result (modify input before execution).

        Args:
            modified_input: Modified input dictionary
            message: Optional explanation of modification

        Returns:
            HookResult with MODIFY action
        """
        return cls(
            action=HookAction.MODIFY, message=message, modified_input=modified_input
        )

    def is_ok(self) -> bool:
        """Check if result is OK."""
        return self.action == HookAction.OK

    def is_blocked(self) -> bool:
        """Check if result is BLOCK."""
        return self.action == HookAction.BLOCK


@dataclass
class Hook:
    """Base hook class.

    Attributes:
        name: Hook name
        hook_type: Type of hook (pre/post/validation)
        matcher: Tool name pattern to match (e.g., "bash", "git", "*")
        callback: Function to call when hook is triggered
        enabled: Whether hook is enabled
    """

    name: str
    hook_type: HookType
    matcher: str  # Tool name pattern (* = all tools)
    callback: Callable[[dict[str, Any]], HookResult]
    enabled: bool = True

    def matches(self, tool_name: str) -> bool:
        """Check if hook matches the given tool name.

        Args:
            tool_name: Name of tool being executed

        Returns:
            True if hook should be applied to this tool
        """
        if self.matcher == "*":
            return True
        return self.matcher.lower() == tool_name.lower()

    def execute(self, tool_input: dict[str, Any]) -> HookResult:
        """Execute hook callback.

        Args:
            tool_input: Input to the tool

        Returns:
            HookResult indicating how to proceed
        """
        if not self.enabled:
            return HookResult.ok()

        try:
            return self.callback(tool_input)
        except Exception as e:
            # If hook fails, don't block execution
            return HookResult.ok(message=f"Hook '{self.name}' failed: {e}")


class HookRegistry:
    """Registry for managing hooks.

    Allows registering, removing, and executing hooks for different
    tool execution points.
    """

    def __init__(self) -> None:
        """Initialize hook registry."""
        self._hooks: dict[HookType, list[Hook]] = {
            HookType.PRE_TOOL_USE: [],
            HookType.POST_TOOL_USE: [],
            HookType.VALIDATION: [],
        }

    def register(self, hook: Hook) -> None:
        """Register a hook.

        Args:
            hook: Hook to register
        """
        self._hooks[hook.hook_type].append(hook)

    def unregister(self, hook_name: str, hook_type: Optional[HookType] = None) -> bool:
        """Unregister a hook by name.

        Args:
            hook_name: Name of hook to remove
            hook_type: Optional hook type to narrow search

        Returns:
            True if hook was removed, False if not found
        """
        types_to_search = [hook_type] if hook_type else list(HookType)

        for htype in types_to_search:
            hooks = self._hooks[htype]
            for i, hook in enumerate(hooks):
                if hook.name == hook_name:
                    hooks.pop(i)
                    return True

        return False

    def get_hooks(self, hook_type: HookType, tool_name: str) -> list[Hook]:
        """Get all hooks matching the given type and tool.

        Args:
            hook_type: Type of hook to retrieve
            tool_name: Name of tool being executed

        Returns:
            List of matching hooks
        """
        return [
            hook
            for hook in self._hooks[hook_type]
            if hook.enabled and hook.matches(tool_name)
        ]

    def execute_hooks(
        self, hook_type: HookType, tool_name: str, tool_input: dict[str, Any]
    ) -> list[HookResult]:
        """Execute all matching hooks.

        Args:
            hook_type: Type of hooks to execute
            tool_name: Name of tool being executed
            tool_input: Input to the tool

        Returns:
            List of hook results
        """
        hooks = self.get_hooks(hook_type, tool_name)
        results = []

        for hook in hooks:
            result = hook.execute(tool_input)
            results.append(result)

            # Stop on first block
            if result.is_blocked():
                break

        return results

    def clear(self, hook_type: Optional[HookType] = None) -> None:
        """Clear all hooks of given type, or all hooks if type is None.

        Args:
            hook_type: Optional type of hooks to clear
        """
        if hook_type:
            self._hooks[hook_type].clear()
        else:
            for htype in HookType:
                self._hooks[htype].clear()

    def count(self, hook_type: Optional[HookType] = None) -> int:
        """Count registered hooks.

        Args:
            hook_type: Optional type to count, or all if None

        Returns:
            Number of registered hooks
        """
        if hook_type:
            return len(self._hooks[hook_type])
        return sum(len(hooks) for hooks in self._hooks.values())


# Global hook registry
_global_registry = HookRegistry()


def get_registry() -> HookRegistry:
    """Get the global hook registry.

    Returns:
        Global HookRegistry instance
    """
    return _global_registry
