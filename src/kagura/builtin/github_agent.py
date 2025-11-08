"""GitHub CLI Agent with safety controls.

This module provides safe GitHub operations via the `gh` CLI,
with automatic safety analysis and confirmation prompts.

All operations use the CommandSafetyAnalyzer for protection against
dangerous commands.
"""

# All gh CLI tools have been removed.
# Users should use shell_exec for gh CLI commands directly.
# For remote access, use the API-based tools (*_api) in github_api.py.
