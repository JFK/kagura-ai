# RFC-005 Phase 1 Implementation Plan: Meta Agent Core (REVISED)

**Status**: In Progress (Design Review Complete)
**Issue**: #65
**Target Version**: v2.5.0
**Started**: 2025-10-13
**Revised**: 2025-10-13 (避免AgentBuilder命名重複)

---

## ⚠️ 重要な設計変更

### 既存コードとの衝突
- **既存**: `src/kagura/builder/agent_builder.py` (`AgentBuilder` - Fluent API配置ビルダー)
- **RFC-005**: コードジェネレーター（自然言語 → Pythonコード生成）

### 解決策
RFC-005のコンポーネントを以下に変更：
- ~~`AgentBuilder`~~ → **`MetaAgent`** (自然言語からコード生成API)
- モジュール名: `kagura.meta` (変更なし)
- CLI: `kagura build agent` (変更なし)

---

## Overview

Phase 1 implements **AI-powered Agent Code Generator**:
1. **Natural Language Parser** - 自然言語からエージェント仕様抽出
2. **Code Generator** - LLM使用してPythonコード生成
3. **Validator** - セキュリティ検証（AST解析）
4. **CLI Command** - `kagura build agent` インタラクティブコマンド

**核心**: 既存`@agent`を使ったコードを**生成**する（設定ではなく）

---

## Architecture

```
src/kagura/meta/
├── __init__.py              # Public API exports
├── meta_agent.py            # MetaAgent class (main code generator API)
├── spec.py                  # AgentSpec (構造化仕様)
├── parser.py                # NLSpecParser (natural language → AgentSpec)
├── generator.py             # CodeGenerator (AgentSpec → Python code)
├── validator.py             # CodeValidator (security + AST checks)
├── templates/               # Jinja2 code templates
│   ├── agent_base.py.j2     # Basic agent template
│   ├── agent_with_tools.py.j2  # Agent with tools
│   └── agent_with_memory.py.j2 # Agent with memory
└── cli/
    └── build_cmd.py         # CLI command implementation
```

### CLI Integration
```
src/kagura/cli/
├── main.py                  # Add 'build' command group
└── (no new files)           # build command imported from meta.cli
```

### 既存との関係
```
既存システム (v2.4.0):
  @agent decorator → AgentBuilder (設定) → 実行

RFC-005 (v2.5.0):
  自然言語 → MetaAgent (生成) → Pythonコード → @agent decorator
```

---

## Phase 1 Tasks Breakdown

### Task 1: Project Structure & Dependencies (0.5 days)

**Goal**: Set up meta agent module structure and add required dependencies

**Files to Create**:
- `src/kagura/meta/__init__.py`
- `src/kagura/meta/builder.py`
- `src/kagura/meta/parser.py`
- `src/kagura/meta/generator.py`
- `src/kagura/meta/validator.py`
- `src/kagura/meta/templates/` directory

**Dependencies to Add** (pyproject.toml):
```toml
[project.optional-dependencies]
meta = [
    "openai>=1.0.0",      # For GPT-4 based parsing
    "tiktoken>=0.5.0",    # Token counting
]
```

**Acceptance Criteria**:
- ✅ Module structure created
- ✅ Dependencies added to pyproject.toml
- ✅ Import `from kagura.meta import AgentBuilder` works

---

### Task 2: Natural Language Spec Parser (2 days)

**Goal**: Implement `NLSpecParser` using **existing LLM infrastructure** to extract agent specifications

**Files**:
- `src/kagura/meta/spec.py` - AgentSpec model
- `src/kagura/meta/parser.py` - NLSpecParser implementation

**Key Insight**: 既存の`call_llm`と`parse_response`を活用！

**Core Classes**:

```python
# src/kagura/meta/spec.py
from pydantic import BaseModel, Field

class AgentSpec(BaseModel):
    """Structured agent specification extracted from NL description"""
    name: str = Field(..., description="Agent name (snake_case)")
    description: str = Field(..., description="Agent purpose")
    input_type: str = Field(default="str", description="Input parameter type")
    output_type: str = Field(default="str", description="Output type")
    tools: list[str] = Field(default_factory=list, description="Required tools")
    has_memory: bool = Field(default=False, description="Needs memory context")
    system_prompt: str = Field(..., description="Agent system prompt")
    examples: list[dict[str, str]] = Field(default_factory=list)

# src/kagura/meta/parser.py
from kagura.core.llm import LLMConfig, call_llm
from kagura.core.parser import parse_response
from .spec import AgentSpec

class NLSpecParser:
    """Parse natural language agent descriptions into AgentSpec

    Uses existing Kagura LLM infrastructure (call_llm + parse_response)
    """

    def __init__(self, model: str = "gpt-4o-mini"):
        """Initialize parser with LLM model"""
        self.config = LLMConfig(model=model, temperature=0.3)

    async def parse(self, description: str) -> AgentSpec:
        """Parse natural language description into AgentSpec

        Args:
            description: Natural language agent description

        Returns:
            Structured AgentSpec
        """
        prompt = self._build_prompt(description)

        # Use existing call_llm + parse_response
        response = await call_llm(prompt, self.config)
        spec = parse_response(response, AgentSpec)

        return spec

    def _build_prompt(self, description: str) -> str:
        """Build parsing prompt"""
        return f"""Extract structured agent specification from this description:

{description}

Return JSON with these fields:
- name: snake_case function name
- description: What the agent does (1-2 sentences)
- input_type: Parameter type (str, dict, list, etc.)
- output_type: Return type (str, dict, BaseModel, etc.)
- tools: Required tools (code_executor, web_search, memory, etc.)
- has_memory: Whether agent needs conversation memory
- system_prompt: Agent's system instructions
- examples: Example inputs/outputs (if any)
"""

    def detect_tools(self, description: str) -> list[str]:
        """Detect required tools from description using pattern matching"""
        TOOL_PATTERNS = {{
            "code_executor": ["execute code", "run python", "code execution"],
            "web_search": ["search web", "google", "find online"],
            "memory": ["remember", "recall", "memory", "history"],
            "file_ops": ["read file", "write file", "file operations"],
        }}

        detected = []
        desc_lower = description.lower()

        for tool, patterns in TOOL_PATTERNS.items():
            if any(pattern in desc_lower for pattern in patterns):
                detected.append(tool)

        return detected
```

**LLM Prompt Template** (`prompts/parse_agent.j2`):
```
You are an AI agent specification parser. Extract structured information from the user's natural language description of an agent.

User Description:
{{ description }}

Extract the following:
1. Agent name (snake_case function name)
2. Purpose/description (1-2 sentences)
3. Input parameter type (str, dict, list, etc.)
4. Output type (str, dict, BaseModel, etc.)
5. Required tools (code_executor, web_search, memory, etc.)
6. System prompt for the agent
7. Example inputs/outputs (if mentioned)

Respond with JSON matching this schema:
{
  "name": "agent_name",
  "description": "What the agent does",
  "input_type": "str",
  "output_type": "str",
  "tools": ["tool1", "tool2"],
  "has_memory": false,
  "system_prompt": "You are...",
  "examples": [{"input": "...", "output": "..."}]
}
```

**Tool Detection Patterns**:
```python
TOOL_PATTERNS = {
    "code_executor": ["execute code", "run python", "code execution"],
    "web_search": ["search web", "google", "find information online"],
    "memory": ["remember", "recall", "memory", "conversation history"],
    "file_ops": ["read file", "write file", "file operations"],
}
```

**Acceptance Criteria**:
- ✅ `NLParser.parse()` returns valid `AgentSpec`
- ✅ Tool detection works for common patterns
- ✅ Unit tests: 10+ test cases covering various descriptions
- ✅ Type checking passes (pyright --strict)

**Test Examples**:
```python
# tests/meta/test_parser.py

def test_simple_agent_parsing():
    parser = NLParser()
    spec = parser.parse(
        "Create an agent that translates English to Japanese. "
        "It should take a string and return translated text."
    )
    assert spec.name == "translate_agent"
    assert spec.input_type == "str"
    assert spec.output_type == "str"
    assert "translate" in spec.system_prompt.lower()

def test_code_execution_detection():
    parser = NLParser()
    spec = parser.parse(
        "Build an agent that can execute Python code and return results"
    )
    assert "code_executor" in spec.tools
```

---

### Task 3: Code Generator (2 days)

**Goal**: Generate Python agent code from `AgentSpec` using **既存のJinja2インフラ**

**File**: `src/kagura/meta/generator.py`

**Key Insight**: 既存の`render_prompt`と同じJinja2環境を使用可能！

**Core Classes**:

```python
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from .spec import AgentSpec

class CodeGenerator:
    """Generate agent Python code from AgentSpec

    Uses Jinja2 templates (similar to prompt templates in kagura.core.prompt)
    """

    def __init__(self, template_dir: Path | None = None):
        """Initialize with template directory"""
        if template_dir is None:
            template_dir = Path(__file__).parent / "templates"
        self.template_dir = template_dir
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )

    def generate(self, spec: AgentSpec) -> str:
        """Generate complete agent code

        Args:
            spec: Agent specification

        Returns:
            Python code as string
        """
        template_name = self._select_template(spec)
        template = self.env.get_template(template_name)

        # Add metadata for template
        context = {
            "spec": spec,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "kagura_version": "2.5.0",  # TODO: Get from version.py
            "tool_descriptions": self._get_tool_descriptions(),
        }

        return template.render(**context)

    def _select_template(self, spec: AgentSpec) -> str:
        """Select appropriate template based on spec"""
        if spec.has_memory:
            return "agent_with_memory.py.j2"
        elif spec.tools:
            return "agent_with_tools.py.j2"
        else:
            return "agent_base.py.j2"

    def _get_tool_descriptions(self) -> dict[str, str]:
        """Get tool descriptions for template"""
        return {
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
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(code, encoding="utf-8")
```

**Template**: `agent_base.py.j2`
```python
"""{{ spec.description }}

Auto-generated by Kagura Meta Agent
Created: {{ timestamp }}
"""

from kagura import agent

@agent(
    name="{{ spec.name }}",
    model="gpt-4o-mini",
    temperature=0.7,
)
def {{ spec.name }}(input_data: {{ spec.input_type }}) -> {{ spec.output_type }}:
    """{{ spec.description }}

    Args:
        input_data: {{ spec.input_type }} - Input data

    Returns:
        {{ spec.output_type }} - Generated result
    """
    system_prompt = """{{ spec.system_prompt }}"""

    # Agent implementation will be generated here
    pass

{% if spec.examples %}
# Example usage:
{% for example in spec.examples %}
# Input: {{ example.input }}
# Expected Output: {{ example.output }}
{% endfor %}
{% endif %}
```

**Template**: `agent_with_tools.py.j2`
```python
"""{{ spec.description }}

Auto-generated by Kagura Meta Agent
Created: {{ timestamp }}
"""

from kagura import agent
{% if "code_executor" in spec.tools %}
from kagura.core.executor import CodeExecutor
{% endif %}

@agent(
    name="{{ spec.name }}",
    model="gpt-4o-mini",
    temperature=0.7,
    {% if "code_executor" in spec.tools %}
    tools=[CodeExecutor()],
    {% endif %}
)
def {{ spec.name }}(input_data: {{ spec.input_type }}) -> {{ spec.output_type }}:
    """{{ spec.description }}

    Args:
        input_data: {{ spec.input_type }} - Input data

    Returns:
        {{ spec.output_type }} - Generated result

    Tools:
    {% for tool in spec.tools %}
    - {{ tool }}
    {% endfor %}
    """
    system_prompt = """{{ spec.system_prompt }}

    Available tools:
    {% for tool in spec.tools %}
    - {{ tool }}: {{ tool_descriptions[tool] }}
    {% endfor %}
    """

    pass
```

**Acceptance Criteria**:
- ✅ `CodeGenerator.generate()` produces valid Python code
- ✅ Generated code passes syntax check (`ast.parse()`)
- ✅ All templates render correctly
- ✅ Unit tests: 8+ test cases for different agent types
- ✅ Type checking passes

**Test Examples**:
```python
# tests/meta/test_generator.py

def test_generate_basic_agent():
    spec = AgentSpec(
        name="summarizer",
        description="Summarize text",
        input_type="str",
        output_type="str",
        system_prompt="You are a text summarizer."
    )
    generator = CodeGenerator()
    code = generator.generate(spec)

    # Verify code is valid Python
    import ast
    ast.parse(code)

    # Verify @agent decorator present
    assert "@agent" in code
    assert "def summarizer(" in code
```

---

### Task 4: Code Validator (1 day)

**Goal**: Validate generated agent code - **既存CodeExecutor検証ロジックを再利用**

**File**: `src/kagura/meta/validator.py`

**Key Insight**: `CodeExecutor`のAST検証（ASTValidator）を再利用可能！

**Core Classes**:

```python
import ast
from typing import Optional
from kagura.core.executor import ASTValidator, DISALLOWED_NAMES

class ValidationError(Exception):
    """Agent validation failed"""
    pass

class CodeValidator:
    """Validate generated agent code

    Reuses security checks from kagura.core.executor.ASTValidator
    """

    # Extend allowed imports for agent code (not execution sandbox)
    AGENT_ALLOWED_IMPORTS = {
        "kagura",
        "kagura.core",
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
        """
        self._check_syntax(code)
        self._check_security(code)
        self._check_decorator(code)
        return True

    def _check_syntax(self, code: str) -> None:
        """Check Python syntax"""
        try:
            ast.parse(code)
        except SyntaxError as e:
            raise ValidationError(f"Syntax error: {e}")

    def _check_security(self, code: str) -> None:
        """Check security using ASTValidator"""
        tree = ast.parse(code)
        self.ast_validator.visit(tree)

        if self.ast_validator.errors:
            raise ValidationError("; ".join(self.ast_validator.errors))

    def _check_decorator(self, code: str) -> None:
        """Verify @agent decorator is present"""
        tree = ast.parse(code)
        has_agent_decorator = False

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for decorator in node.decorator_list:
                    # Check for @agent or @agent(...)
                    if isinstance(decorator, ast.Name) and decorator.id == "agent":
                        has_agent_decorator = True
                    elif isinstance(decorator, ast.Call):
                        if isinstance(decorator.func, ast.Name) and decorator.func.id == "agent":
                            has_agent_decorator = True

        if not has_agent_decorator:
            raise ValidationError("Missing @agent decorator")
```

**Acceptance Criteria**:
- ✅ Validator catches syntax errors
- ✅ Validator blocks dangerous imports
- ✅ Validator blocks dangerous function calls
- ✅ Validator ensures @agent decorator present
- ✅ Unit tests: 10+ test cases
- ✅ Type checking passes

**Test Examples**:
```python
# tests/meta/test_validator.py

def test_valid_agent_passes():
    validator = AgentValidator()
    code = '''
from kagura import agent

@agent(name="test")
def test_agent(x: str) -> str:
    return x
'''
    assert validator.validate(code) is True

def test_dangerous_import_blocked():
    validator = AgentValidator()
    code = '''
import subprocess
from kagura import agent

@agent(name="test")
def test_agent(x: str) -> str:
    subprocess.run(["ls"])
'''
    with pytest.raises(ValidationError, match="Forbidden import"):
        validator.validate(code)
```

---

### Task 5: CLI Command Implementation (1.5 days)

**Goal**: Implement `kagura build agent` command

**Files**:
- `src/kagura/cli/build.py` (new)
- `src/kagura/cli/main.py` (modify to add 'build' command group)

**CLI Interface**:

```bash
# Interactive mode
kagura build agent

# Non-interactive mode
kagura build agent --description "Agent that summarizes text" --output agents/summarizer.py

# From file
kagura build agent --spec agent_spec.yaml --output agents/custom.py
```

**Implementation**: `src/kagura/cli/build.py`

```python
"""CLI commands for building agents"""

import click
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.syntax import Syntax

from kagura.meta.parser import NLParser
from kagura.meta.generator import CodeGenerator
from kagura.meta.validator import AgentValidator

console = Console()

@click.command()
@click.option(
    "--description", "-d",
    help="Natural language agent description"
)
@click.option(
    "--output", "-o",
    type=click.Path(path_type=Path),
    help="Output file path (default: agents/<name>.py)"
)
@click.option(
    "--model",
    default="gpt-4o-mini",
    help="LLM model for parsing (default: gpt-4o-mini)"
)
@click.option(
    "--interactive/--no-interactive",
    default=True,
    help="Interactive mode (default: True)"
)
def agent(
    description: str | None,
    output: Path | None,
    model: str,
    interactive: bool
):
    """Build an AI agent from natural language description

    Examples:
        # Interactive mode
        kagura build agent

        # Direct mode
        kagura build agent -d "Translate English to Japanese" -o translator.py
    """

    # Interactive mode
    if interactive and not description:
        console.print(Panel.fit(
            "[bold cyan]🤖 Kagura Agent Builder[/bold cyan]\n"
            "Describe your agent in natural language",
            border_style="cyan"
        ))

        description = Prompt.ask(
            "\n[bold]What should your agent do?[/bold]",
            default="Summarize text in 3 bullet points"
        )

    if not description:
        console.print("[red]Error: Description required[/red]")
        raise click.Abort()

    # Parse description
    console.print("\n[cyan]🔍 Parsing agent specification...[/cyan]")
    parser = NLParser(model=model)

    try:
        spec = parser.parse(description)
    except Exception as e:
        console.print(f"[red]❌ Parsing failed: {e}[/red]")
        raise click.Abort()

    # Show parsed spec
    console.print(Panel(
        f"[bold]Name:[/bold] {spec.name}\n"
        f"[bold]Description:[/bold] {spec.description}\n"
        f"[bold]Input:[/bold] {spec.input_type}\n"
        f"[bold]Output:[/bold] {spec.output_type}\n"
        f"[bold]Tools:[/bold] {', '.join(spec.tools) if spec.tools else 'None'}\n"
        f"[bold]Memory:[/bold] {'Yes' if spec.has_memory else 'No'}",
        title="📋 Agent Specification",
        border_style="green"
    ))

    # Confirm
    if interactive:
        if not Confirm.ask("\n[bold]Generate agent code?[/bold]", default=True):
            console.print("[yellow]Cancelled[/yellow]")
            return

    # Generate code
    console.print("\n[cyan]⚙️  Generating agent code...[/cyan]")
    generator = CodeGenerator()
    code = generator.generate(spec)

    # Validate
    console.print("[cyan]🔒 Validating code security...[/cyan]")
    validator = AgentValidator()

    try:
        validator.validate(code)
    except Exception as e:
        console.print(f"[red]❌ Validation failed: {e}[/red]")
        raise click.Abort()

    console.print("[green]✅ Code validated[/green]")

    # Preview code
    if interactive:
        console.print("\n[bold]Generated Code Preview:[/bold]")
        syntax = Syntax(code, "python", theme="monokai", line_numbers=True)
        console.print(syntax)

    # Determine output path
    if not output:
        output = Path("agents") / f"{spec.name}.py"

    # Save
    if interactive:
        output_str = Prompt.ask(
            "\n[bold]Save to[/bold]",
            default=str(output)
        )
        output = Path(output_str)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(code)

    console.print(f"\n[bold green]✅ Agent created: {output}[/bold green]")
    console.print(f"\n[dim]Run with: python {output}[/dim]")
```

**Update**: `src/kagura/cli/main.py`

```python
import click
from . import build  # Add this import

@click.group()
def cli():
    """Kagura AI - Python-First AI Agent Framework"""
    pass

# Add build command group
@cli.group()
def build_group():
    """Build agents, tools, and workflows"""
    pass

# Register 'agent' command under 'build'
build_group.add_command(build.agent, name="agent")

# Register build group as 'build'
cli.add_command(build_group, name="build")
```

**Acceptance Criteria**:
- ✅ `kagura build agent` interactive mode works
- ✅ `kagura build agent -d "..." -o "..."` non-interactive mode works
- ✅ Rich UI displays correctly (panels, syntax highlighting)
- ✅ Generated code is saved to specified path
- ✅ Integration tests: 5+ test cases
- ✅ Type checking passes

---

### Task 6: Integration Tests (1 day)

**Goal**: End-to-end tests for the full agent building pipeline

**File**: `tests/meta/test_integration.py`

**Test Cases**:

```python
# tests/meta/test_integration.py

import pytest
from pathlib import Path
from kagura.meta.parser import NLParser
from kagura.meta.generator import CodeGenerator
from kagura.meta.validator import AgentValidator
from kagura.core.decorators import agent  # To verify generated code works

class TestMetaAgentIntegration:
    """Integration tests for Meta Agent pipeline"""

    def test_end_to_end_basic_agent(self, tmp_path):
        """Test complete pipeline: parse → generate → validate → execute"""
        # 1. Parse
        parser = NLParser()
        spec = parser.parse("Create an agent that counts words in text")

        assert spec.name == "word_counter"

        # 2. Generate
        generator = CodeGenerator()
        code = generator.generate(spec)

        # 3. Validate
        validator = AgentValidator()
        assert validator.validate(code) is True

        # 4. Save and import
        agent_file = tmp_path / "word_counter.py"
        agent_file.write_text(code)

        # 5. Verify importable (basic check)
        import ast
        tree = ast.parse(code)
        func_defs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
        assert len(func_defs) == 1
        assert func_defs[0].name == "word_counter"

    def test_agent_with_code_executor(self, tmp_path):
        """Test agent generation with code execution tool"""
        parser = NLParser()
        spec = parser.parse(
            "Build an agent that can execute Python code to solve math problems"
        )

        assert "code_executor" in spec.tools

        generator = CodeGenerator()
        code = generator.generate(spec)

        # Verify CodeExecutor import present
        assert "from kagura.core.executor import CodeExecutor" in code
        assert "tools=[CodeExecutor()]" in code

        validator = AgentValidator()
        assert validator.validate(code) is True

    def test_cli_command_simulation(self, tmp_path):
        """Simulate CLI command flow"""
        from click.testing import CliRunner
        from kagura.cli.build import agent as build_agent_cmd

        runner = CliRunner()

        # Non-interactive mode
        result = runner.invoke(build_agent_cmd, [
            "--description", "Translate English to Japanese",
            "--output", str(tmp_path / "translator.py"),
            "--no-interactive"
        ])

        assert result.exit_code == 0
        assert (tmp_path / "translator.py").exists()

        # Verify generated file is valid Python
        code = (tmp_path / "translator.py").read_text()
        import ast
        ast.parse(code)  # Should not raise
```

**Acceptance Criteria**:
- ✅ End-to-end pipeline works
- ✅ CLI command integration works
- ✅ All integration tests pass
- ✅ Coverage: 85%+ for meta module

---

## Deliverables

### Code Files (10 files)
1. `src/kagura/meta/__init__.py`
2. `src/kagura/meta/builder.py`
3. `src/kagura/meta/parser.py`
4. `src/kagura/meta/generator.py`
5. `src/kagura/meta/validator.py`
6. `src/kagura/meta/templates/agent_base.py.j2`
7. `src/kagura/meta/templates/agent_with_tools.py.j2`
8. `src/kagura/meta/cli/build.py`
9. `src/kagura/cli/main.py` (modified)
10. `pyproject.toml` (modified - add meta dependencies)

### Test Files (4 files)
1. `tests/meta/test_parser.py` (10+ tests)
2. `tests/meta/test_generator.py` (8+ tests)
3. `tests/meta/test_validator.py` (10+ tests)
4. `tests/meta/test_integration.py` (5+ tests)

### Documentation
1. User guide: `docs/guides/meta_agent.md`
2. API reference: `docs/api/meta.md`
3. CLI help text (in-code)

---

## Success Metrics

- ✅ **CLI Command**: `kagura build agent` works in both interactive and non-interactive modes
- ✅ **Code Quality**:
  - All tests pass (33+ tests)
  - Coverage: 85%+ for meta module
  - Type checking passes (pyright --strict)
  - No ruff warnings
- ✅ **Functionality**:
  - Parses 10+ different agent descriptions correctly
  - Generates valid Python code
  - Validates security correctly
  - Generated agents are importable

---

## Timeline

**Total**: 8 days

| Task | Duration | Dependencies |
|------|----------|--------------|
| Task 1: Project Structure | 0.5 days | None |
| Task 2: NL Parser | 2 days | Task 1 |
| Task 3: Code Generator | 2 days | Task 1, 2 |
| Task 4: Validator | 1 day | Task 1 |
| Task 5: CLI Command | 1.5 days | Task 1, 2, 3, 4 |
| Task 6: Integration Tests | 1 day | All tasks |

---

## Next Steps

After Phase 1 completion:
- **Phase 2**: Interactive Agent Builder API (`AgentBuilder` class)
- **Phase 3**: Advanced features (multi-agent, workflows)
- **Phase 4**: Web UI for agent building

---

## Summary of Changes from Original RFC-005

### ✅ 既存インフラの活用（設計改善）

| コンポーネント | 元の設計 | 修正後（既存活用） |
|--------------|---------|------------------|
| **NLParser** | OpenAI client直接使用 | **`call_llm` + `parse_response`** |
| **CodeGenerator** | 独自Jinja2実装 | **既存`render_prompt`と同じ方式** |
| **Validator** | 独自AST検証実装 | **`CodeExecutor.ASTValidator`再利用** |
| **CLI** | 独自Rich UI実装 | **既存CLIパターン踏襲** |

### ⚠️ 命名変更（重複回避）

| 元のRFC-005 | 修正後 | 理由 |
|------------|--------|------|
| `AgentBuilder` | **`MetaAgent`** | `builder.AgentBuilder`と重複 |
| `meta.AgentBuilder()` | **`meta.MetaAgent()`** | API命名統一 |

### ✨ 実装可能性の確認

**✅ 全て実装可能**:
- 既存の`@agent`, `LLMConfig`, `CodeExecutor`が完備
- Jinja2テンプレートエンジンも既存
- OAuth2認証も統合済み（v2.4.0）
- テストインフラ完備（pytest + pyright）

**追加必要な依存関係**: なし（既存で十分）

---

## Next Steps After Plan Approval

1. **ユーザー確認**: この修正案で良いか確認
2. **Issue #65更新**: RFC-005の設計変更を記録
3. **Task 1開始**: プロジェクト構造とスタブ作成

---

**Ready to start Task 1!** 🚀
