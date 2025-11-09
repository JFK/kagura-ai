"""Jinja2 template loader for Kagura prompts.

Loads prompt templates from templates/prompts/ directory with support
for user overrides in ~/.kagura/prompts/.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from jinja2 import (
    Environment,
    FileSystemLoader,
    TemplateNotFound,
    select_autoescape,
)

from kagura.config.paths import get_config_dir

logger = logging.getLogger(__name__)

# Template directories (in priority order: user overrides > package defaults)
_PACKAGE_TEMPLATE_DIR = Path(__file__).parent.parent / "templates" / "prompts"
_USER_TEMPLATE_DIR = get_config_dir() / "prompts"


def _get_template_loader() -> FileSystemLoader:
    """Create Jinja2 file system loader with user override support.

    Searches for templates in:
    1. ~/.kagura/prompts/ (user overrides, highest priority)
    2. src/kagura/templates/prompts/ (package defaults)

    Returns:
        FileSystemLoader with both search paths
    """
    search_paths = []

    # User overrides (if exists)
    if _USER_TEMPLATE_DIR.exists():
        search_paths.append(str(_USER_TEMPLATE_DIR))
        logger.debug(f"User template directory found: {_USER_TEMPLATE_DIR}")

    # Package defaults
    if _PACKAGE_TEMPLATE_DIR.exists():
        search_paths.append(str(_PACKAGE_TEMPLATE_DIR))
    else:
        logger.warning(f"Package template directory not found: {_PACKAGE_TEMPLATE_DIR}")

    return FileSystemLoader(search_paths)


# Global Jinja2 environment (cached)
_jinja_env: Environment | None = None


def get_jinja_env() -> Environment:
    """Get or create cached Jinja2 environment.

    Returns:
        Configured Jinja2 Environment with template loader
    """
    global _jinja_env

    if _jinja_env is None:
        _jinja_env = Environment(
            loader=_get_template_loader(),
            autoescape=select_autoescape(enabled_extensions=()),  # No autoescaping
            trim_blocks=True,
            lstrip_blocks=True,
        )
        logger.debug("Jinja2 environment initialized")

    return _jinja_env


def load_template(template_name: str) -> str:
    """Load a prompt template by name.

    Args:
        template_name: Template name relative to prompts/ directory
                      (e.g., "coding/session_summary_system.j2")

    Returns:
        Template content as string (unrendered)

    Raises:
        TemplateNotFound: If template doesn't exist in any search path

    Example:
        >>> template = load_template("coding/session_summary_system.j2")
        >>> print(template[:50])
    """
    try:
        # Try user directory first
        if _USER_TEMPLATE_DIR.exists():
            user_template_path = _USER_TEMPLATE_DIR / template_name
            if user_template_path.exists():
                return user_template_path.read_text(encoding="utf-8")

        # Fall back to package template
        package_template_path = _PACKAGE_TEMPLATE_DIR / template_name
        if package_template_path.exists():
            return package_template_path.read_text(encoding="utf-8")

        raise TemplateNotFound(template_name)

    except TemplateNotFound as e:
        logger.error(f"Template not found: {template_name}")
        raise FileNotFoundError(
            f"Template '{template_name}' not found in:\n"
            f"  - {_USER_TEMPLATE_DIR}\n"
            f"  - {_PACKAGE_TEMPLATE_DIR}"
        ) from e


def render_template(template_name: str, **kwargs: Any) -> str:
    """Load and render a prompt template with variables.

    Args:
        template_name: Template name relative to prompts/ directory
        **kwargs: Template variables to render

    Returns:
        Rendered prompt string

    Raises:
        TemplateNotFound: If template doesn't exist
        jinja2.TemplateSyntaxError: If template has syntax errors
        jinja2.UndefinedError: If required variable is missing

    Example:
        >>> prompt = render_template(
        ...     "coding/session_summary_user.j2",
        ...     duration_minutes=45.5,
        ...     project_id="my-project",
        ...     files_list="- file1.py\n- file2.py"
        ... )
    """
    env = get_jinja_env()

    try:
        template = env.get_template(template_name)
        return template.render(**kwargs)
    except TemplateNotFound as e:
        logger.error(f"Template not found: {template_name}")
        raise FileNotFoundError(
            f"Template '{template_name}' not found in:\n"
            f"  - {_USER_TEMPLATE_DIR}\n"
            f"  - {_PACKAGE_TEMPLATE_DIR}"
        ) from e


def list_available_templates() -> list[str]:
    """List all available prompt templates.

    Returns:
        List of template names relative to prompts/ directory

    Example:
        >>> templates = list_available_templates()
        >>> print(templates)
        ['coding/session_summary_system.j2', 'coding/session_summary_user.j2', ...]
    """
    env = get_jinja_env()
    return env.list_templates()


__all__ = [
    "load_template",
    "render_template",
    "list_available_templates",
    "get_jinja_env",
]
