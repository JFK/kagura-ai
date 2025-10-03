"""Prompt template engine using Jinja2"""
import inspect
from typing import Callable, Any
from jinja2 import Template


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


def render_prompt(template_str: str, **kwargs: Any) -> str:
    """
    Render Jinja2 template with variables.

    Args:
        template_str: Jinja2 template string
        **kwargs: Template variables

    Returns:
        Rendered prompt
    """
    template = Template(template_str)
    return template.render(**kwargs)
