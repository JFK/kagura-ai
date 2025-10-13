"""Code generator for agent code

Generate Python agent code from AgentSpec using Jinja2 templates.
"""

from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from .spec import AgentSpec


class CodeGenerator:
    """Generate agent Python code from AgentSpec

    Uses Jinja2 templates (similar to prompt templates in kagura.core.prompt)
    to generate complete, runnable agent code.

    Example:
        >>> generator = CodeGenerator()
        >>> code = generator.generate(spec)
        >>> print(code)  # Complete Python code with @agent decorator
    """

    def __init__(self, template_dir: Path | None = None):
        """Initialize with template directory

        Args:
            template_dir: Directory containing Jinja2 templates
                         (default: kagura/meta/templates/)
        """
        if template_dir is None:
            template_dir = Path(__file__).parent / "templates"
        self.template_dir = template_dir
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def generate(self, spec: AgentSpec) -> str:
        """Generate complete agent code

        Args:
            spec: Agent specification

        Returns:
            Python code as string

        Example:
            >>> code = generator.generate(spec)
            >>> assert "@agent" in code
            >>> assert f"def {spec.name}" in code
        """
        # Phase 2: Auto-add execute_code tool if needed
        tools = spec.tools.copy()
        if spec.requires_code_execution and "execute_code" not in tools:
            tools.insert(0, "execute_code")  # Add at beginning for priority

        template_name = self._select_template(spec)
        template = self.env.get_template(template_name)

        # Add metadata for template
        context = {
            "spec": spec,
            "tools": tools,  # Use modified tools list
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "kagura_version": self._get_kagura_version(),
            "tool_descriptions": self._get_tool_descriptions(),
        }

        return template.render(**context)

    def _select_template(self, spec: AgentSpec) -> str:
        """Select appropriate template based on spec

        Args:
            spec: Agent specification

        Returns:
            Template filename
        """
        # Phase 2: Priority for code execution template
        if spec.requires_code_execution:
            return "agent_with_code_exec.py.j2"
        elif spec.has_memory:
            return "agent_with_memory.py.j2"
        elif spec.tools:
            return "agent_with_tools.py.j2"
        else:
            return "agent_base.py.j2"

    def _get_kagura_version(self) -> str:
        """Get Kagura version

        Returns:
            Version string
        """
        try:
            from kagura.version import __version__

            return __version__
        except ImportError:
            return "2.5.0"

    def _get_tool_descriptions(self) -> dict[str, str]:
        """Get tool descriptions for template

        Returns:
            Dictionary mapping tool names to descriptions
        """
        return {
            "execute_code": "Execute Python code safely with AST validation",
            "code_executor": "Execute Python code safely",
            "web_search": "Search the web for information",
            "memory": "Persistent conversation memory",
            "file_ops": "Read and write files",
        }

    def save(self, code: str, output_path: Path) -> None:
        """Save generated code to file

        Args:
            code: Generated Python code
            output_path: Output file path

        Example:
            >>> generator.save(code, Path("agents/my_agent.py"))
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(code, encoding="utf-8")
