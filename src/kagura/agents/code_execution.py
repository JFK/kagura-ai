"""Code execution agent that generates and executes Python code"""

from typing import Any, Optional

from pydantic import BaseModel

from kagura import agent
from kagura.core.executor import CodeExecutor


class CodeResult(BaseModel):
    """Result of code generation and execution"""

    task: str
    code: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    stdout: str = ""
    stderr: str = ""
    execution_time: float = 0.0


class CodeExecutionAgent:
    """Agent that generates and executes Python code for tasks"""

    def __init__(
        self,
        model: str = "gpt-4o",
        temperature: float = 0.3,
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        """
        Initialize code execution agent.

        Args:
            model: LLM model to use for code generation
            temperature: Temperature for code generation
            timeout: Timeout for code execution
            max_retries: Maximum number of retry attempts on errors
        """
        self.model = model
        self.temperature = temperature
        self.timeout = timeout
        self.max_retries = max_retries
        self.executor = CodeExecutor(timeout=timeout)

    async def execute(self, task: str) -> CodeResult:
        """
        Generate and execute code for the given task.

        Args:
            task: Natural language description of the task

        Returns:
            CodeResult with generated code and execution result
        """
        # Generate code using LLM
        code = await self._generate_code(task)

        # Execute the generated code
        exec_result = await self.executor.execute(code)

        return CodeResult(
            task=task,
            code=code,
            success=exec_result.success,
            result=exec_result.result,
            error=exec_result.error,
            stdout=exec_result.stdout,
            stderr=exec_result.stderr,
            execution_time=exec_result.execution_time,
        )

    async def execute_with_retry(self, task: str) -> CodeResult:
        """
        Execute task with automatic retry on errors.

        Args:
            task: Natural language description of the task

        Returns:
            CodeResult with final attempt result
        """
        last_error = None

        for attempt in range(self.max_retries):
            if attempt == 0:
                # First attempt
                result = await self.execute(task)
            else:
                # Retry with error feedback
                retry_task = f"""{task}

Previous attempt {attempt} failed with error: {last_error}

Please fix the code to address this error."""
                result = await self.execute(retry_task)

            if result.success:
                return result

            last_error = result.error

        # Return last failed result
        return result

    async def _generate_code(
        self, task: str, error_feedback: Optional[str] = None
    ) -> str:
        """
        Generate Python code for the task using LLM.

        Args:
            task: Task description
            error_feedback: Optional error feedback for retry

        Returns:
            Generated Python code
        """

        @agent(model=self.model, temperature=self.temperature)
        async def code_generator(task_desc: str, feedback: str = "") -> str:  # type: ignore
            """
            Generate Python code to solve this task:

            Task: {{ task_desc }}

            {% if feedback %}
            Previous Error: {{ feedback }}
            Please fix the code to address this error.
            {% endif %}

            Requirements:
            - Write clean, efficient Python code
            - Use only these allowed imports: math, datetime, json, itertools,
              functools, collections, re, random, statistics, decimal, string,
              typing, dataclasses, enum, fractions, time
            - Store the final result in a variable named "result"
            - Do not use print statements unless specifically requested
            - Return ONLY the Python code, no explanations or markdown

            Example:
            Task: Calculate fibonacci(10)
            Code:
            def fibonacci(n):
                if n <= 1:
                    return n
                return fibonacci(n-1) + fibonacci(n-2)

            result = fibonacci(10)
            """
            pass  # type: ignore

        code = await code_generator(task, error_feedback or "")  # type: ignore

        # Clean up code (remove markdown code blocks if present)
        code = self._clean_code(code)

        return code

    def _clean_code(self, code: str) -> str:
        """
        Clean generated code by removing markdown formatting.

        Args:
            code: Raw code from LLM

        Returns:
            Cleaned Python code
        """
        lines = code.strip().split("\n")

        # Remove markdown code blocks
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]

        return "\n".join(lines).strip()


# Convenience function
async def execute_code(task: str, max_retries: int = 3) -> dict[str, Any]:
    """
    Convenience function to execute code for a task.

    Args:
        task: Natural language description of the task
        max_retries: Maximum number of retry attempts

    Returns:
        Dictionary with code, success, result, and error
    """
    agent = CodeExecutionAgent(max_retries=max_retries)
    result = await agent.execute_with_retry(task)

    return {
        "code": result.code,
        "success": result.success,
        "result": result.result,
        "error": result.error,
    }
