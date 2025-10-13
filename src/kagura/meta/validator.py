"""Code validator for generated agent code

Validate generated code for security and correctness.
"""

import ast
from typing import Optional

from kagura.core.executor import ASTValidator


class ValidationError(Exception):
    """Agent validation failed"""

    pass


class CodeValidator:
    """Validate generated agent code

    Reuses security checks from kagura.core.executor.ASTValidator
    to ensure generated code is safe and correct.

    Example:
        >>> validator = CodeValidator()
        >>> try:
        ...     validator.validate(code)
        ...     print("Code is valid")
        ... except ValidationError as e:
        ...     print(f"Validation failed: {e}")
    """

    # Extend allowed imports for agent code (not execution sandbox)
    AGENT_ALLOWED_IMPORTS = {
        "kagura",
        "kagura.core",
        "kagura.core.executor",
        "kagura.core.memory",
        "pydantic",
        "typing",
        "datetime",
        "pathlib",
        "asyncio",
    }

    def __init__(self, allowed_imports: Optional[set[str]] = None):
        """Initialize validator

        Args:
            allowed_imports: Set of allowed import modules
                           (default: AGENT_ALLOWED_IMPORTS)
        """
        self.allowed_imports = allowed_imports or self.AGENT_ALLOWED_IMPORTS
        # Reuse CodeExecutor's ASTValidator
        self.ast_validator = ASTValidator(self.allowed_imports)

    def validate(self, code: str) -> bool:
        """Validate agent code (raises ValidationError if invalid)

        Args:
            code: Python code to validate

        Returns:
            True if valid

        Raises:
            ValidationError: If code is invalid or insecure

        Example:
            >>> code = "from kagura import agent\\n@agent\\nasync def test(): pass"
            >>> validator.validate(code)
            True
        """
        self._check_syntax(code)
        self._check_security(code)
        self._check_decorator(code)
        return True

    def _check_syntax(self, code: str) -> None:
        """Check Python syntax

        Args:
            code: Python code

        Raises:
            ValidationError: If syntax is invalid
        """
        try:
            ast.parse(code)
        except SyntaxError as e:
            raise ValidationError(f"Syntax error: {e}")

    def _check_security(self, code: str) -> None:
        """Check security using ASTValidator

        Args:
            code: Python code

        Raises:
            ValidationError: If code contains security issues
        """
        tree = ast.parse(code)
        self.ast_validator.visit(tree)

        if self.ast_validator.errors:
            raise ValidationError("; ".join(self.ast_validator.errors))

    def _check_decorator(self, code: str) -> None:
        """Verify @agent decorator is present

        Args:
            code: Python code

        Raises:
            ValidationError: If @agent decorator is missing
        """
        tree = ast.parse(code)
        has_agent_decorator = False

        for node in ast.walk(tree):
            # Check both sync and async function definitions
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for decorator in node.decorator_list:
                    # Check for @agent or @agent(...)
                    if isinstance(decorator, ast.Name) and decorator.id == "agent":
                        has_agent_decorator = True
                    elif isinstance(decorator, ast.Call):
                        if (
                            isinstance(decorator.func, ast.Name)
                            and decorator.func.id == "agent"
                        ):
                            has_agent_decorator = True

        if not has_agent_decorator:
            raise ValidationError("Missing @agent decorator")
