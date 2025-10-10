"""Safe Python code executor with AST validation"""

import ast
import asyncio
import io
import time
from contextlib import redirect_stderr, redirect_stdout
from typing import Any, Optional

from pydantic import BaseModel

# Security configuration
ALLOWED_IMPORTS = {
    "math",
    "datetime",
    "json",
    "itertools",
    "functools",
    "collections",
    "re",
    "random",
    "statistics",
    "decimal",
    "string",
    "typing",
    "dataclasses",
    "enum",
    "fractions",
    "time",
}

ALLOWED_BUILTINS = {
    "abs",
    "all",
    "any",
    "ascii",
    "bin",
    "bool",
    "bytearray",
    "bytes",
    "chr",
    "dict",
    "divmod",
    "enumerate",
    "filter",
    "float",
    "format",
    "frozenset",
    "hash",
    "hex",
    "int",
    "isinstance",
    "issubclass",
    "iter",
    "len",
    "list",
    "map",
    "max",
    "min",
    "next",
    "oct",
    "ord",
    "pow",
    "print",
    "range",
    "repr",
    "reversed",
    "round",
    "set",
    "slice",
    "sorted",
    "str",
    "sum",
    "tuple",
    "type",
    "zip",
}

DISALLOWED_NAMES = {
    "exec",
    "eval",
    "compile",
    "open",
    "input",
    "file",
    "quit",
    "exit",
    "help",
    "license",
    "copyright",
    "credits",
    "globals",
    "locals",
    "vars",
    "dir",
    "breakpoint",
}


class ExecutionResult(BaseModel):
    """Result of code execution"""

    success: bool
    result: Any = None
    error: Optional[str] = None
    stdout: str = ""
    stderr: str = ""
    execution_time: float = 0.0


class SecurityError(Exception):
    """Raised when code violates security constraints"""

    pass


class ASTValidator(ast.NodeVisitor):
    """Validates AST for security constraints"""

    def __init__(self, allowed_imports: set[str]):
        self.allowed_imports = allowed_imports
        self.errors: list[str] = []

    def visit_Import(self, node: ast.Import) -> None:
        """Check import statements"""
        for alias in node.names:
            module = alias.name.split(".")[0]
            if module not in self.allowed_imports:
                self.errors.append(f"Disallowed import: {module}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Check from...import statements"""
        if node.module:
            module = node.module.split(".")[0]
            if module not in self.allowed_imports:
                self.errors.append(f"Disallowed import: {module}")
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        """Check for disallowed names"""
        if node.id in DISALLOWED_NAMES:
            self.errors.append(f"Disallowed name: {node.id}")
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        """Check for dangerous attributes"""
        dangerous_attrs = {"__builtins__", "__globals__", "__code__", "__dict__"}
        if node.attr in dangerous_attrs:
            self.errors.append(f"Disallowed attribute access: {node.attr}")
        self.generic_visit(node)


class CodeExecutor:
    """Safe Python code executor with security constraints"""

    def __init__(
        self,
        timeout: float = 30.0,
        allowed_imports: Optional[set[str]] = None,
        memory_limit_mb: Optional[int] = None,
    ):
        """
        Initialize code executor.

        Args:
            timeout: Maximum execution time in seconds
            allowed_imports: Set of allowed import modules
            memory_limit_mb: Memory limit (not enforced on all platforms)
        """
        self.timeout = timeout
        self.allowed_imports = allowed_imports or ALLOWED_IMPORTS
        self.memory_limit_mb = memory_limit_mb

    def validate_code(self, code: str) -> None:
        """
        Validate code using AST analysis.

        Args:
            code: Python code to validate

        Raises:
            SecurityError: If code violates security constraints
            SyntaxError: If code has syntax errors
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            raise SyntaxError(f"Syntax error: {e}")

        # Run AST validation
        validator = ASTValidator(self.allowed_imports)
        validator.visit(tree)

        if validator.errors:
            raise SecurityError("; ".join(validator.errors))

    def create_safe_globals(self) -> dict[str, Any]:
        """
        Create restricted global namespace.

        Returns:
            Dictionary with safe built-ins only
        """
        safe_builtins = {
            name: __builtins__[name]  # type: ignore
            for name in ALLOWED_BUILTINS
            if name in __builtins__  # type: ignore
        }

        # Add restricted __import__ function
        def safe_import(name: str, *args: Any, **kwargs: Any) -> Any:
            """Restricted import that only allows whitelisted modules"""
            module_name = name.split(".")[0]
            if module_name not in self.allowed_imports:
                raise ImportError(f"Import of '{name}' is not allowed")
            return __builtins__["__import__"](name, *args, **kwargs)  # type: ignore

        safe_builtins["__import__"] = safe_import

        return {
            "__builtins__": safe_builtins,
            "__name__": "__main__",
            "__doc__": None,
        }

    async def execute(self, code: str) -> ExecutionResult:
        """
        Execute Python code safely.

        Args:
            code: Python code to execute

        Returns:
            ExecutionResult with success status and output
        """
        start_time = time.time()

        try:
            # Validate code first
            self.validate_code(code)

            # Prepare execution environment
            # Use same dict for globals and locals to allow function definitions
            execution_namespace = self.create_safe_globals()

            # Capture stdout and stderr
            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()

            # Execute with timeout
            try:
                with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                    # Run in executor to enable timeout
                    await asyncio.wait_for(
                        self._execute_in_thread(
                            code, execution_namespace, execution_namespace
                        ),
                        timeout=self.timeout,
                    )

                execution_time = time.time() - start_time

                # Get result variable if it exists
                result = execution_namespace.get("result", None)

                return ExecutionResult(
                    success=True,
                    result=result,
                    stdout=stdout_capture.getvalue(),
                    stderr=stderr_capture.getvalue(),
                    execution_time=execution_time,
                )

            except asyncio.TimeoutError:
                execution_time = time.time() - start_time
                return ExecutionResult(
                    success=False,
                    error=f"TimeoutError: Execution exceeded {self.timeout} seconds",
                    stdout=stdout_capture.getvalue(),
                    stderr=stderr_capture.getvalue(),
                    execution_time=execution_time,
                )

        except SecurityError as e:
            execution_time = time.time() - start_time
            return ExecutionResult(
                success=False,
                error=f"SecurityError: {str(e)}",
                execution_time=execution_time,
            )

        except SyntaxError as e:
            execution_time = time.time() - start_time
            return ExecutionResult(
                success=False,
                error=f"SyntaxError: {str(e)}",
                execution_time=execution_time,
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return ExecutionResult(
                success=False,
                error=f"{type(e).__name__}: {str(e)}",
                execution_time=execution_time,
            )

    async def _execute_in_thread(
        self, code: str, globals_dict: dict[str, Any], locals_dict: dict[str, Any]
    ) -> None:
        """
        Execute code in a thread to allow timeout.

        Args:
            code: Code to execute
            globals_dict: Global namespace
            locals_dict: Local namespace
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, exec, code, globals_dict, locals_dict)
