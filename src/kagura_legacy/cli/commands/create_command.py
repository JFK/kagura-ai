from typing import Any, Dict, Optional, List, Protocol
from pathlib import Path
from textwrap import dedent

import yaml
import asyncio
import click

from ...core.agent import Agent
from ...core.utils.console import KaguraConsole
from ...core.config import ConfigBase


class DescriptionType(Protocol):
    language: str
    text: str


class FieldType(Protocol):
    name: str
    type: str
    description: List[Dict[str, str]]


class CustomModelType(Protocol):
    name: str
    fields: List[FieldType]


class AgentConfigType(Protocol):
    agent_name: str
    description: List[DescriptionType]
    input_fields: List[str]
    response_fields: List[str]
    custom_models: Optional[List[CustomModelType]]

    def model_dump(self) -> Dict[str, Any]: ...


class StateModelType(Protocol):
    agent_config: AgentConfigType
    state_model_config: Optional[Dict[str, Any]]
    custom_tool_code: Optional[str]

    def model_dump(self) -> Dict[str, Any]: ...


StateModel = StateModelType


class KaguraRepoGenerator:
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)

    def _format_yaml(self, data: Dict[str, Any]) -> str:
        class MyDumper(yaml.Dumper):
            def increase_indent(self, flow=False, indentless=False):
                return super(MyDumper, self).increase_indent(flow, indentless=False)

        yaml_str = yaml.dump(
            data,
            Dumper=MyDumper,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
            indent=2,
            width=1000,
            explicit_start=True,
        )
        if isinstance(yaml_str, str):
            return yaml_str
        return ""

    def _format_agent_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Format and structure agent configuration."""
        # Define the preferred order of fields
        field_order = [
            "type",
            "description",
            "instructions",
            "prompt",
            "llm",
            "input_fields",
            "response_fields",
            "custom_tool",
            "pre_custom_tool",
            "post_custom_tool",
            # Workflow specific fields
            "entry_point",
            "nodes",
            "edges",
            "state_field_bindings",
            "conditional_edges",
        ]

        # Create ordered dictionary based on field_order
        ordered_config = {}
        for field in field_order:
            if field in config:
                ordered_config[field] = config[field]

        # Add any remaining fields not in the order list
        for key, value in config.items():
            if key not in ordered_config:
                ordered_config[key] = value

        return ordered_config

    def _format_state_model(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Format and structure state model configuration."""
        if not config:
            return config

        formatted_config = {}

        # Format custom models if present
        if "custom_models" in config:
            formatted_config["custom_models"] = []
            for model in config["custom_models"]:
                formatted_model = {
                    "name": model["name"],
                    "fields": sorted(model["fields"], key=lambda x: x["name"]),
                }
                formatted_config["custom_models"].append(formatted_model)

        # Format state fields if present
        if "state_fields" in config:
            formatted_config["state_fields"] = sorted(
                config["state_fields"], key=lambda x: x["name"]
            )

        return formatted_config

    async def generate_repo(self, config: StateModel) -> None:
        """Generate repository structure with improved organization."""
        agent_config = config.agent_config
        repo_dir = self.output_dir / agent_config.agent_name

        # Create directory structure
        await self._create_directory_structure(repo_dir)

        # Generate configuration files
        await self._generate_files(repo_dir, config)

        # Generate example and test files
        await self._generate_examples(repo_dir, config)
        await self._generate_tests(repo_dir, config)

    async def _create_directory_structure(self, repo_dir: Path) -> None:
        """Create directory structure with proper organization."""
        directories = ["src", "tests", "examples", "docs"]
        for dir_path in directories:
            (repo_dir / dir_path).mkdir(parents=True, exist_ok=True)

    async def _generate_files(self, repo_dir: Path, config: StateModel) -> None:
        """Generate configuration and source files."""
        agent_dir = repo_dir / "src" / config.agent_config.agent_name
        agent_dir.mkdir(parents=True, exist_ok=True)

        # Generate agent.yml
        agent_config = self._format_agent_config(config.agent_config.model_dump())
        with open(agent_dir / "agent.yml", "w") as f:
            f.write(self._format_yaml(agent_config))

        # Generate state_model.yml if needed
        if hasattr(config, "state_model_config") and config.state_model_config:
            state_model = config.state_model_config
            if not isinstance(state_model, dict):
                state_model = state_model.model_dump()
            else:
                raise RuntimeError("Error generating state model configuration")

            formatted_state_model = self._format_state_model(state_model)
            with open(agent_dir / "state_model.yml", "w") as f:
                f.write(self._format_yaml(formatted_state_model))

        # Generate custom tool if needed
        if hasattr(config, "custom_tool_code") and config.custom_tool_code:
            with open(agent_dir / "tools.py", "w") as f:
                f.write(dedent(config.custom_tool_code))

        # Generate README.md
        readme_content = self._generate_readme(config)
        with open(repo_dir / "README.md", "w") as f:
            f.write(readme_content)

        # Generate pyproject.toml
        pyproject_content = self._generate_pyproject(config)
        with open(repo_dir / "pyproject.toml", "w") as f:
            f.write(pyproject_content)

    def _generate_readme(self, config: StateModel) -> str:
        """Generate comprehensive README with examples and documentation."""
        agent_config = config.agent_config
        description = ""
        for desc in agent_config.description:
            if desc.language == "en":
                description = desc.text
                break
            else:
                description = desc.text
                break

        return dedent(
            f"""\
            # {agent_config.agent_name}

            {description}

            ## Installation

            ```bash
            kagura install https://github.com/<username>/{agent_config.agent_name}.git
            ```

            ## Basic Usage

            ```python
            from kagura.core.agent import Agent

            async def main():
                agent = Agent.assigner("{agent_config.agent_name}")
                result = await agent.execute({{
                    # Add your input here
                }})
                print(result)

            if __name__ == "__main__":
                import asyncio
                asyncio.run(main())
            ```

            ## Configuration

            See `src/{agent_config.agent_name}/agent.yml` for detailed configuration options.

            ## Advanced Usage

            For more examples, check the `examples/` directory.

            ## Testing

            Run tests using pytest:
            ```bash
            uv run pytest
            ```

            ## License

            Apache License 2.0
            """
        )

    def _generate_pyproject(self, config: StateModel) -> str:
        """Generate pyproject.toml configuration."""
        return dedent(
            f"""\
            [project]
            name = "{config.agent_config.agent_name}"
            version = "0.1.0"
            description = "Kagura AI agent"

            [project.dependencies]
            kagura-ai = ">=0.0.9"

            [build-system]
            requires = ["setuptools>=42.0.0", "wheel"]
            build-backend = "setuptools.build_meta"

            [tool.pytest.ini_options]
            asyncio_mode = "auto"
            """
        )

    async def _generate_examples(self, repo_dir: Path, config: StateModel) -> None:
        """Generate comprehensive example files."""
        example_dir = repo_dir / "examples"
        agent_name = config.agent_config.agent_name.lower()

        example_code = dedent(
            f"""\
            from kagura.core.agent import Agent
            from kagura.core.utils.console import KaguraConsole

            async def run_example():
                # Initialize agent
                agent = Agent.assigner("{config.agent_config.agent_name}")

                # Example input based on your agent's configuration
                input_data = {{
                    # Add example input here based on your agent's input_fields
                }}

                # Execute agent
                result = await agent.execute(input_data)

                # Display results using KaguraConsole for better formatting
                console = KaguraConsole()
                console.print_data_table(result.model_dump())

            if __name__ == "__main__":
                import asyncio
                asyncio.run(run_example())
            """
        )

        with open(example_dir / f"{agent_name}_example.py", "w") as f:
            f.write(example_code)

    async def _generate_tests(self, repo_dir: Path, config: StateModel) -> None:
        """Generate comprehensive test files."""
        test_dir = repo_dir / "tests"
        agent_name = config.agent_config.agent_name

        test_code = dedent(
            f"""\
            import pytest
            from kagura.core.agent import Agent

            @pytest.mark.asyncio
            class Test{agent_name}:
                async def test_basic_execution(self):
                    agent = Agent.assigner("{agent_name}")
                    result = await agent.execute({{
                        # Add test input here
                    }})
                    assert result.SUCCESS
                    # Add more specific assertions based on your agent's output

                async def test_error_handling(self):
                    agent = Agent.assigner("{agent_name}")
                    result = await agent.execute({{
                        # Add invalid input for error testing
                    }})
                    assert not result.SUCCESS
                    assert result.ERROR_MESSAGE

                async def test_state_validation(self):
                    agent = Agent.assigner("{agent_name}")
                    # Add state validation tests here
                    pass

                async def test_custom_functionality(self):
                    # Add tests for custom functionality
                    pass
            """
        )

        with open(test_dir / f"test_{agent_name.lower()}.py", "w") as f:
            f.write(test_code)


class AgentCreator:
    def __init__(self, output_dir: str = "./", agent_type: str = "atomic"):
        self.output_dir = Path(output_dir)
        self.agent_type = agent_type
        self.console = KaguraConsole()

    def _get_generator_name(self, agent_type: str) -> str:
        """Get appropriate generator name based on agent type"""
        type_mapping = {
            "atomic": "atomic_agent_generator",
            "tool": "tool_agent_generator",
            "workflow": "workflow_agent_generator",
        }
        return type_mapping[agent_type]

    async def create_agent(self, agent_name: str):
        """エージェントを生成"""
        try:
            # 1. エージェントタイプの選択（未指定の場合）
            agent_type = await self._select_agent_type()

            # 2. 目的の入力
            purpose = await self._get_agent_purpose()

            available_agents = Agent.list_agents() if agent_type == "workflow" else []

            generator_name = self._get_generator_name(agent_type)
            self.generator = Agent.assigner(generator_name)

            state = {
                "agent_name": agent_name,
                "agent_type": agent_type,
                "purpose": purpose,
                "available_agents": [],
            }

            if isinstance(available_agents, List) and len(available_agents) > 0:
                state["available_agents"] = available_agents

            async def _execute_generator():
                return await self.generator.execute(state)

            config = await self.console.display_spinner_with_task(
                _execute_generator, "Generating agent configuration"
            )

            if await self._confirm_configuration(config):
                repo_generator = KaguraRepoGenerator(self.output_dir)
                await repo_generator.generate_repo(config)

                self.console.print(
                    "\n[bold green]✓ Agent created successfully![/bold green]"
                )
                self.console.print(
                    f"\n[cyan]Next steps:[/cyan]\n"
                    f"1. Your agent has been created in: [bold]{self.output_dir / agent_name}[/bold]\n"
                    "2. Review the generated configuration files\n"
                    "3. Customize the agent as needed\n"
                )
            else:
                self.console.print("\n[yellow]Agent creation cancelled[/yellow]")

        except Exception as e:
            self.console.print(f"\n[bold red]Error creating agent: {str(e)}[/bold red]")
            raise

    async def _select_agent_type(self) -> str:
        """Select the type of agent to create"""
        if self.agent_type:
            return self.agent_type

        choices = {
            "1": ("Atomic Agent", "atomic", "LLM-powered with state management"),
            "2": ("Tool Agent", "tool", "Custom tool integration without LLM"),
            "3": ("Workflow Agent", "workflow", "Multi-agent workflow coordination"),
        }

        model_name = ConfigBase.get("llm").get("model")
        message = dedent(
            f"""
            [bold cyan]Select the type of agent to create:[/bold cyan]

            [bold cyan]{model_name}[/bold cyan] will be used for generating the agent.
            Better models can be used for better performance.
            """
        )
        self.console.panel(
            message,
            title="[bold blue]Agent Type Selection[/bold blue]",
            border_style="blue",
        )

        for key, (name, _, desc) in choices.items():
            self.console.print(f"[bold cyan]{key}.[/bold cyan] [green]{name}[/green]")
            self.console.print(f"   {desc}")

        while True:
            choice = await self.console.input_async("\nEnter choice (1-3): ")
            if choice in choices:
                self.agent_type = choices[choice][1]
                return self.agent_type
            self.console.print("[bold red]Invalid choice. Please try again.[/bold red]")

    async def _get_agent_purpose(self) -> str:
        """エージェントの目的を入力"""
        self.console.panel(
            "\n[bold cyan]Describe your agent's purpose:[/bold cyan]\n\n"
            "Tips:\n"
            "- Be specific about what you want it to do\n"
            "- Include expected inputs and outputs\n"
            "- Mention any external services or APIs\n",
            title="[bold blue]Agent Purpose[/bold blue]",
            border_style="blue",
        )

        return await self.console.multiline_input()

    async def _confirm_configuration(self, config: StateModel) -> bool:
        """生成された設定を表示し、確認を取る"""
        self.console.panel(
            "[bold cyan]Generated Configuration Preview:[/bold cyan]\n",
            title="[bold blue]Configuration Review[/bold blue]",
            border_style="blue",
        )

        # エージェントの基本情報を表示
        self.console.print("\n[bold cyan]Basic Information:[/bold cyan]")
        if hasattr(config, "agent_config"):
            agent_config = config.agent_config
            self.console.print(f"Name: {agent_config.agent_name}")
            self.console.print(f"Type: {self.agent_type}")

            # Display descriptions
            if hasattr(agent_config, "description"):
                self.console.print("\n[bold cyan]Description:[/bold cyan]")
                for desc in agent_config.description:
                    self.console.print(f"{desc.language}: {desc.text}")

            # Display input/response fields
            if hasattr(agent_config, "input_fields"):
                self.console.print("\n[bold cyan]Input Fields:[/bold cyan]")
                for field in agent_config.input_fields:
                    self.console.print(f"- {field}")

            if hasattr(agent_config, "response_fields"):
                self.console.print("\n[bold cyan]Response Fields:[/bold cyan]")
                for field in agent_config.response_fields:
                    self.console.print(f"- {field}")

            # Display custom models if present
            if hasattr(agent_config, "custom_models") and agent_config.custom_models:
                self.console.print("\n[bold cyan]Custom Models:[/bold cyan]")
                for model in agent_config.custom_models:
                    self.console.print(f"- {model.name}")
                    for field in model.fields:
                        desc = next((d for d in field.description if "en" in d), None)
                        if desc:
                            self.console.print(
                                f"  • {field.name} ({field.type}): {desc['text']}"
                            )
                        else:
                            self.console.print(f"  • {field.name} ({field.type})")

        # Display custom tool code if present
        if hasattr(config, "custom_tool_code") and config.custom_tool_code:
            self.console.print("\n[bold cyan]Custom Tool:[/bold cyan]")
            self.console.print("A custom tool will be generated")

        # Provide options for detailed review
        self.console.print("\n[bold cyan]Options:[/bold cyan]")
        self.console.print("Enter number to see details, or 'y' to proceed:")
        self.console.print("1. View full agent.yml")
        if hasattr(config, "state_model_config"):
            self.console.print("2. View full state_model.yml")
        if hasattr(config, "custom_tool_code") and config.custom_tool_code:
            self.console.print("3. View custom tool code")

        while True:
            choice = await self.console.input_async("Choice [y/N/1/2/3]: ")
            if choice.lower() == "y":
                return True
            elif choice.lower() == "n" or not choice:
                return False
            elif choice == "1":
                self.console.print("\n[bold cyan]Full agent.yml:[/bold cyan]")
                self.console.print_data_table({"agent.yml": agent_config.model_dump()})
            elif choice == "2" and hasattr(config, "state_model_config"):
                self.console.print("\n[bold cyan]Full state_model.yml:[/bold cyan]")
                self.console.print_data_table(
                    {"state_model.yml": config.state_model_config}
                )
            elif (
                choice == "3"
                and hasattr(config, "custom_tool_code")
                and config.custom_tool_code
            ):
                self.console.print("\n[bold cyan]Custom Tool Code:[/bold cyan]")
                self.console.print(config.custom_tool_code)


@click.command()
@click.argument("agent_name")
@click.option(
    "--output-dir",
    "-o",
    default="./",
    help="Output directory (defaults to ./<agent_name>)",
)
@click.option(
    "--type",
    "-t",
    type=click.Choice(["atomic", "tool", "workflow"]),
    help="Agent type (if not specified, will prompt interactively)",
)
def create(agent_name: str, output_dir: str, agent_type: str):
    """Create a new Kagura agent"""
    creator = AgentCreator(output_dir, agent_type=agent_type)
    asyncio.run(creator.create_agent(agent_name))
