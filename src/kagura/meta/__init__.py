"""Meta Agent - AI-powered agent code generator

This module provides tools to generate Kagura agent code from
natural language descriptions.

Example:
    >>> from kagura.meta import MetaAgent
    >>> meta = MetaAgent()
    >>> description = "Create an agent that translates English to Japanese"
    >>> code = await meta.generate(description)
    >>> print(code)  # Generated Python code with @agent decorator
"""

from .generator import CodeGenerator
from .meta_agent import MetaAgent
from .parser import NLSpecParser
from .spec import AgentSpec
from .validator import CodeValidator, ValidationError

__all__ = [
    "MetaAgent",
    "AgentSpec",
    "NLSpecParser",
    "CodeGenerator",
    "CodeValidator",
    "ValidationError",
]
