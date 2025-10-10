"""Decorator API for registering hooks.

Provides convenient decorators for defining hooks:
    @hook.pre_tool_use("bash")
    @hook.post_tool_use("git")
    @hook.validation("*")
"""

from typing import Any, Callable

from .hooks import Hook, HookRegistry, HookResult, HookType, get_registry


class HookDecorators:
    """Decorator API for hooks.

    Example:
        @hook.pre_tool_use("bash")
        def validate_bash(tool_input: dict) -> HookResult:
            if "rm -rf /" in tool_input.get("command", ""):
                return HookResult.block("Dangerous command!")
            return HookResult.ok()
    """

    def __init__(self, registry: HookRegistry | None = None) -> None:
        """Initialize hook decorators.

        Args:
            registry: Hook registry to use (default: global registry)
        """
        self.registry = registry or get_registry()

    def pre_tool_use(
        self, matcher: str = "*", name: str | None = None
    ) -> Callable[
        [Callable[[dict[str, Any]], HookResult]], Callable[[dict[str, Any]], HookResult]
    ]:
        """Decorator for PreToolUse hooks.

        Args:
            matcher: Tool name pattern to match (default: "*" for all)
            name: Optional hook name (default: function name)

        Returns:
            Decorator function

        Example:
            @hook.pre_tool_use("bash")
            def validate_bash(tool_input: dict) -> HookResult:
                if dangerous(tool_input["command"]):
                    return HookResult.block("Blocked!")
                return HookResult.ok()
        """

        def decorator(
            func: Callable[[dict[str, Any]], HookResult],
        ) -> Callable[[dict[str, Any]], HookResult]:
            hook_name = name or func.__name__
            hook = Hook(
                name=hook_name,
                hook_type=HookType.PRE_TOOL_USE,
                matcher=matcher,
                callback=func,
            )
            self.registry.register(hook)
            return func

        return decorator

    def post_tool_use(
        self, matcher: str = "*", name: str | None = None
    ) -> Callable[
        [Callable[[dict[str, Any]], HookResult]], Callable[[dict[str, Any]], HookResult]
    ]:
        """Decorator for PostToolUse hooks.

        Args:
            matcher: Tool name pattern to match (default: "*" for all)
            name: Optional hook name (default: function name)

        Returns:
            Decorator function

        Example:
            @hook.post_tool_use("git")
            def log_git_usage(tool_input: dict) -> HookResult:
                print(f"Git command executed: {tool_input}")
                return HookResult.ok()
        """

        def decorator(
            func: Callable[[dict[str, Any]], HookResult],
        ) -> Callable[[dict[str, Any]], HookResult]:
            hook_name = name or func.__name__
            hook = Hook(
                name=hook_name,
                hook_type=HookType.POST_TOOL_USE,
                matcher=matcher,
                callback=func,
            )
            self.registry.register(hook)
            return func

        return decorator

    def validation(
        self, matcher: str = "*", name: str | None = None
    ) -> Callable[
        [Callable[[dict[str, Any]], HookResult]], Callable[[dict[str, Any]], HookResult]
    ]:
        """Decorator for Validation hooks.

        Args:
            matcher: Tool name pattern to match (default: "*" for all)
            name: Optional hook name (default: function name)

        Returns:
            Decorator function

        Example:
            @hook.validation("*")
            def validate_parameters(tool_input: dict) -> HookResult:
                if not tool_input:
                    return HookResult.block("Empty input!")
                return HookResult.ok()
        """

        def decorator(
            func: Callable[[dict[str, Any]], HookResult],
        ) -> Callable[[dict[str, Any]], HookResult]:
            hook_name = name or func.__name__
            hook = Hook(
                name=hook_name,
                hook_type=HookType.VALIDATION,
                matcher=matcher,
                callback=func,
            )
            self.registry.register(hook)
            return func

        return decorator


# Global hook decorator instance
hook = HookDecorators()
