"""Prompt template engine using Jinja2"""

import inspect
from typing import Any, Callable, Optional

from jinja2 import Environment, StrictUndefined, TemplateSyntaxError, UndefinedError


# Custom filters for prompt templates
def filter_truncate(text: Any, length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length."""
    text_str = str(text)
    if len(text_str) <= length:
        return text_str
    return text_str[:length] + suffix


def filter_format_code(code: str, language: str = "python") -> str:
    """Format code with language marker."""
    return f"```{language}\n{code}\n```"


def filter_list_items(items: list[Any], separator: str = ", ") -> str:
    """Format list items as string."""
    return separator.join(str(item) for item in items)


# Create Jinja2 environment with custom filters
def create_environment() -> Environment:
    """
    Create Jinja2 environment with custom filters and strict mode.

    Returns:
        Configured Jinja2 environment
    """
    env = Environment(
        undefined=StrictUndefined,  # Raise error on undefined variables
        trim_blocks=True,
        lstrip_blocks=True,
    )

    # Register custom filters
    env.filters["truncate"] = filter_truncate
    env.filters["format_code"] = filter_format_code
    env.filters["list_items"] = filter_list_items

    return env


# Global environment instance
_env = create_environment()


def extract_template(func: Callable[..., Any]) -> str:
    """
    Extract Jinja2 template from function docstring.

    Args:
        func: Function with docstring template

    Returns:
        Template string

    Raises:
        ValueError: If function has no docstring
    """
    docstring = inspect.getdoc(func)
    if not docstring:
        raise ValueError(f"Function {func.__name__} has no docstring")

    return docstring


def validate_template(template_str: str, **sample_vars: Any) -> Optional[str]:
    """
    Validate Jinja2 template syntax.

    Args:
        template_str: Template string to validate
        **sample_vars: Sample variables to test rendering

    Returns:
        None if valid, error message if invalid
    """
    try:
        template = _env.from_string(template_str)
        # Try rendering with sample vars to catch undefined variable errors
        if sample_vars:
            template.render(**sample_vars)
        return None
    except TemplateSyntaxError as e:
        return f"Template syntax error at line {e.lineno}: {e.message}"
    except UndefinedError as e:
        return f"Undefined variable: {e.message}"
    except Exception as e:
        return f"Template error: {str(e)}"


def render_prompt(template_str: str, **kwargs: Any) -> str:
    """
    Render Jinja2 template with variables.

    Args:
        template_str: Jinja2 template string
        **kwargs: Template variables

    Returns:
        Rendered prompt

    Raises:
        TemplateSyntaxError: If template has syntax errors
        UndefinedError: If template uses undefined variables
    """
    template = _env.from_string(template_str)
    return template.render(**kwargs)
