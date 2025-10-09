"""Custom commands system for Kagura AI.

Provides functionality to load and execute custom commands defined in
Markdown files with YAML frontmatter, plus hooks for intercepting execution.
"""

from .command import Command
from .executor import CommandExecutor, InlineCommandExecutor
from .hook_decorators import hook
from .hooks import Hook, HookAction, HookRegistry, HookResult, HookType, get_registry
from .loader import CommandLoader

__all__ = [
    "Command",
    "CommandLoader",
    "CommandExecutor",
    "InlineCommandExecutor",
    # Hooks
    "Hook",
    "HookType",
    "HookAction",
    "HookResult",
    "HookRegistry",
    "get_registry",
    "hook",
]
