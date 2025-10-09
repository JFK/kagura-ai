"""Built-in agents for Kagura AI.

This module provides built-in agents for common tasks:
- shell: Execute shell commands securely
- git: Git operations (commit, push, status, PR)
- file: File operations (search, grep)
"""

from kagura.builtin.file import file_search, grep_content
from kagura.builtin.git import git_commit, git_create_pr, git_push, git_status
from kagura.builtin.shell import shell

__all__ = [
    "shell",
    "git_commit",
    "git_push",
    "git_status",
    "git_create_pr",
    "file_search",
    "grep_content",
]
