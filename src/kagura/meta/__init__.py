"""Meta Agent - AI-powered agent code generator

This module provides tools to generate Kagura agent code from
natural language descriptions.

Example:
    >>> from kagura.meta import MetaAgent
    >>> meta = MetaAgent()
    >>> description = "Create an agent that translates English to Japanese"
    >>> code = await meta.generate(description)
    >>> print(code)  # Generated Python code with @agent decorator

Self-Improving Example:
    >>> from kagura.meta import SelfImprovingMetaAgent
    >>> meta = SelfImprovingMetaAgent(max_retries=3)
    >>> code, errors = await meta.generate_with_retry(description, validate=True)
    >>> if errors:
    ...     print(f"Fixed {len(errors)} errors automatically")
"""

from .error_analyzer import ErrorAnalysis, ErrorAnalyzer
from .fixer import CodeFixer
from .generator import CodeGenerator
from .meta_agent import MetaAgent
from .parser import NLSpecParser
from .self_improving import SelfImprovingMetaAgent
from .spec import AgentSpec
from .validator import CodeValidator, ValidationError

__all__ = [
    "MetaAgent",
    "SelfImprovingMetaAgent",
    "AgentSpec",
    "NLSpecParser",
    "CodeGenerator",
    "CodeValidator",
    "ValidationError",
    "ErrorAnalyzer",
    "ErrorAnalysis",
    "CodeFixer",
]
