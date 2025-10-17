"""Meta Agent - Main API for agent code generation"""

from pathlib import Path
from typing import Optional

from .generator import CodeGenerator
from .parser import NLSpecParser
from .spec import AgentSpec
from .validator import CodeValidator


class MetaAgent:
    """AI-powered agent code generator

    Generate Kagura agent code from natural language descriptions.

    Example:
        >>> from kagura.meta import MetaAgent
        >>> meta = MetaAgent()
        >>> code = await meta.generate("Translate English to Japanese")
        >>> print(code)  # Complete Python agent code
    """

    def __init__(
        self,
        model: str = "gpt-5-mini",
        template_dir: Optional[Path] = None,
        validate: bool = True,
    ):
        """Initialize MetaAgent

        Args:
            model: LLM model for spec parsing (default: gpt-4o-mini)
            template_dir: Custom template directory (optional)
            validate: Whether to validate generated code (default: True)
        """
        self.parser = NLSpecParser(model=model)
        self.generator = CodeGenerator(template_dir=template_dir)
        self.validator = CodeValidator() if validate else None

    async def generate(self, description: str) -> str:
        """Generate agent code from natural language description

        Args:
            description: Natural language agent description

        Returns:
            Generated Python code

        Raises:
            ValidationError: If generated code is invalid (when validate=True)

        Example:
            >>> desc = "Create a chatbot that remembers conversation history"
            >>> code = await meta.generate(desc)
            >>> assert "@agent" in code
            >>> assert "memory" in code
        """
        # Step 1: Parse description into AgentSpec
        spec = await self.parser.parse(description)

        # Step 2: Generate code from spec
        code = self.generator.generate(spec)

        # Step 3: Validate code (if enabled)
        if self.validator:
            self.validator.validate(code)

        return code

    async def generate_from_spec(self, spec: AgentSpec) -> str:
        """Generate agent code from AgentSpec

        Args:
            spec: Agent specification

        Returns:
            Generated Python code

        Raises:
            ValidationError: If generated code is invalid

        Example:
            >>> spec = AgentSpec(
            ...     name="translator",
            ...     description="Translate text",
            ...     system_prompt="You are a translator."
            ... )
            >>> code = await meta.generate_from_spec(spec)
        """
        code = self.generator.generate(spec)

        if self.validator:
            self.validator.validate(code)

        return code

    async def generate_and_save(
        self,
        description: str,
        output_path: Path | None = None,
    ) -> tuple[str, Path]:
        """Generate agent code and save to file

        Args:
            description: Natural language agent description
            output_path: Output file path (default: ~/.kagura/agents/<name>.py)

        Returns:
            Tuple of (generated_code, output_path)

        Raises:
            ValidationError: If generated code is invalid

        Example:
            >>> # Default location
            >>> code, path = await meta.generate_and_save(
            ...     "Create a translator agent"
            ... )
            >>> print(path)  # ~/.kagura/agents/translator.py

            >>> # Custom location
            >>> code, path = await meta.generate_and_save(
            ...     "Create a translator agent",
            ...     Path("/custom/path/translator.py")
            ... )
        """
        # Generate code first to get AgentSpec for name
        code = await self.generate(description)

        # Default to ~/.kagura/agents/<name>.py if not specified
        if output_path is None:
            # Parse description again to get agent name
            spec = await self.parser.parse(description)
            agents_dir = Path.home() / ".kagura" / "agents"
            agents_dir.mkdir(parents=True, exist_ok=True)
            output_path = agents_dir / f"{spec.name}.py"

        self.generator.save(code, output_path)
        return code, output_path
