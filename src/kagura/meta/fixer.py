"""Code fixing for self-improving agents"""

import ast
from typing import Optional

from kagura.meta.error_analyzer import ErrorAnalysis
from kagura.meta.validator import CodeValidator


class CodeFixer:
    """Fix errors in generated agent code

    Applies fixes suggested by ErrorAnalyzer to agent code.
    Uses simple string-based patching for Phase 3.

    Example:
        >>> fixer = CodeFixer()
        >>> fixed = fixer.apply_fix(original_code, error_analysis)
        >>> if fixed:
        ...     print("Fixed successfully!")
    """

    def __init__(self):
        """Initialize code fixer"""
        self.validator = CodeValidator()

    def apply_fix(
        self,
        original_code: str,
        error_analysis: ErrorAnalysis,
    ) -> Optional[str]:
        """Apply fix to code

        Args:
            original_code: Original agent code with error
            error_analysis: Error analysis with suggested fix

        Returns:
            Fixed code or None if fix failed

        Example:
            >>> analysis = ErrorAnalysis(
            ...     error_type="NameError",
            ...     error_message="y not defined",
            ...     stack_trace="",
            ...     root_cause="Variable undefined",
            ...     suggested_fix="Fix variable",
            ...     fix_code="x + x"
            ... )
            >>> fixed = fixer.apply_fix(code, analysis)
        """
        if not error_analysis.fix_code:
            # No code fix suggested
            return None

        try:
            # Attempt to apply fix
            fixed_code = self._apply_code_patch(original_code, error_analysis.fix_code)

            # Validate fixed code
            is_valid = self.validator.validate(fixed_code)
            if not is_valid:
                return None

            return fixed_code

        except Exception:
            # Fix application failed
            return None

    def _apply_code_patch(self, original: str, fix_snippet: str) -> str:
        """Apply code patch to original code

        For Phase 3, we use simple string-based patching.
        Future phases may use AST-based transformations (libcst).

        Strategy:
        1. If fix_snippet looks like complete code → use it directly
        2. If fix_snippet is a function → replace function in original
        3. Otherwise → return original (cannot patch)

        Args:
            original: Original code
            fix_snippet: Fix code snippet from LLM

        Returns:
            Patched code

        Raises:
            ValueError: If patch cannot be applied
        """
        try:
            # Try to parse fix snippet as complete code
            fix_ast = ast.parse(fix_snippet)

            # If fix snippet has imports, it's probably complete code
            has_imports = any(
                isinstance(node, (ast.Import, ast.ImportFrom))
                for node in ast.walk(fix_ast)
            )

            if has_imports:
                # Fix snippet is complete code, use it directly
                return fix_snippet

            # Check if fix contains a function definition
            for node in ast.walk(fix_ast):
                if isinstance(node, ast.FunctionDef):
                    # Fix is a function, replace it in original
                    return self._replace_function(original, node.name, fix_snippet)

        except SyntaxError:
            # Fix snippet is not valid Python
            pass

        # Fallback: Cannot apply patch, return original
        # Future: More sophisticated patching strategies
        return original

    def _replace_function(self, original: str, func_name: str, new_func: str) -> str:
        """Replace function definition in code

        Args:
            original: Original code
            func_name: Name of function to replace
            new_func: New function code

        Returns:
            Code with replaced function
        """
        try:
            tree = ast.parse(original)

            # Find function definition
            for node in tree.body:
                if isinstance(node, ast.FunctionDef) and node.name == func_name:
                    # Found the function to replace
                    start_line = node.lineno - 1
                    end_line = node.end_lineno if node.end_lineno else start_line + 1

                    lines = original.split("\n")

                    # Replace function
                    new_lines = lines[:start_line] + [new_func] + lines[end_line:]

                    return "\n".join(new_lines)

        except Exception:
            pass

        # Fallback: return original if replacement failed
        return original


__all__ = ["CodeFixer"]
