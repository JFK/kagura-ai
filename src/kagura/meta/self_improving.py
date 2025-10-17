"""Self-improving Meta Agent with automatic error recovery"""

import logging

from kagura.core.llm import LLMConfig
from kagura.meta.error_analyzer import ErrorAnalysis, ErrorAnalyzer
from kagura.meta.fixer import CodeFixer
from kagura.meta.meta_agent import MetaAgent

logger = logging.getLogger(__name__)


class SelfImprovingMetaAgent(MetaAgent):
    """Meta Agent with self-improving capabilities

    Extends MetaAgent to automatically fix errors in generated agents.
    When validation fails or execution errors occur, the agent analyzes
    the error and attempts to fix the code automatically.

    Example:
        >>> agent = SelfImprovingMetaAgent(max_retries=3)
        >>> code, errors = await agent.generate_with_retry(
        ...     "Analyze CSV file",
        ...     validate=True
        ... )
        >>> if errors:
        ...     print(f"Fixed {len(errors)} errors automatically")
    """

    def __init__(
        self,
        model: str = "gpt-5-mini",
        max_retries: int = 3,
    ):
        """Initialize self-improving meta agent

        Args:
            model: LLM model for code generation and error analysis
                   (default: gpt-4o-mini)
            max_retries: Maximum retry attempts for error fixing (default: 3)
        """
        super().__init__(model=model)

        # Create LLMConfig for error analyzer
        llm_config = LLMConfig(model=model, temperature=0.3)
        self.error_analyzer = ErrorAnalyzer(llm_config=llm_config)
        self.code_fixer = CodeFixer()
        self.max_retries = max_retries
        self._error_history: list[ErrorAnalysis] = []

    async def generate_with_retry(
        self,
        description: str,
        validate: bool = True,
    ) -> tuple[str, list[ErrorAnalysis]]:
        """Generate agent with automatic error fixing

        Generates agent code and validates it. If validation fails,
        automatically analyzes the error and attempts to fix the code,
        up to max_retries times.

        Args:
            description: Agent description in natural language
            validate: Whether to validate generated code (default: True)

        Returns:
            Tuple of (generated_code, error_history)
                - generated_code: Final code (possibly fixed)
                - error_history: List of errors encountered and fixed

        Example:
            >>> agent = SelfImprovingMetaAgent()
            >>> code, errors = await agent.generate_with_retry(
            ...     "Calculate fibonacci number",
            ...     validate=True
            ... )
            >>> print(f"Generated code with {len(errors)} fixes")
        """
        # Initial generation
        code = await self.generate(description)

        if not validate:
            return code, []

        # Validate and fix if needed
        attempts = 0
        errors: list[ErrorAnalysis] = []

        while attempts < self.max_retries:
            # Validate code
            if not self.validator:
                # No validator, return code as-is
                return code, errors

            is_valid = self.validator.validate(code)

            if is_valid:
                logger.info(f"Code validated successfully (attempt {attempts + 1})")
                return code, errors

            # Code has issues, analyze
            logger.warning(f"Validation failed (attempt {attempts + 1})")

            # For Phase 3, we create a synthetic validation error
            # Future: CodeValidator should return detailed validation errors
            analysis = ErrorAnalysis(
                error_type="ValidationError",
                error_message="Code validation failed",
                stack_trace="",
                root_cause="Generated code has syntax or type errors",
                suggested_fix="Review and fix code syntax/types",
                fix_code=None,
            )

            errors.append(analysis)

            # Try to fix (Phase 3: limited fixing capability)
            # In practice, validation failures are rare with good LLMs
            fixed_code = self.code_fixer.apply_fix(code, analysis)

            if not fixed_code:
                logger.error("Failed to apply fix, returning current code")
                break

            code = fixed_code
            attempts += 1

        # Max retries reached or fix failed
        if attempts >= self.max_retries:
            logger.error(f"Max retries ({self.max_retries}) reached")

        return code, errors

    def get_error_history(self) -> list[ErrorAnalysis]:
        """Get error history for learning

        Returns:
            Copy of error history list

        Example:
            >>> history = agent.get_error_history()
            >>> for error in history:
            ...     print(f"{error.error_type}: {error.suggested_fix}")
        """
        return self._error_history.copy()

    def clear_error_history(self) -> None:
        """Clear error history

        Useful for starting fresh or managing memory.

        Example:
            >>> agent.clear_error_history()
            >>> assert len(agent.get_error_history()) == 0
        """
        self._error_history.clear()


__all__ = ["SelfImprovingMetaAgent"]
