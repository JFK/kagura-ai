import asyncio
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import click
import yaml
from rich.panel import Panel

from kagura.core.agent import Agent
from kagura.core.memory import MessageHistory
from kagura.core.utils.logger import get_logger

from ..ui import ConsoleManager
from . import CommandRegistry

logger = get_logger(__name__)


class AgentCreator:
    def __init__(self, output_dir: Optional[str] = None):
        self.console_manager = ConsoleManager()
        self.console = self.console_manager.console
        self.message_history = None
        self.command_registry = None
        self.default_output_dir = output_dir or os.getcwd()
        self.generator = Agent.assigner("agent_generator")

    async def initialize(self):
        """Initialize the agent creator with message history"""
        self.message_history = await MessageHistory.factory(
            system_prompt=self.generator.instructions
        )
        self.command_registry = CommandRegistry(
            self.console_manager, self.message_history
        )

    async def create_agent_files(
        self, config: Dict[str, Any], output_dir: Path
    ) -> Path:
        """Create agent files from configuration"""
        agent_name = config["agent_config"]["name"]
        agent_dir = output_dir / agent_name

        # Create directory structure
        agent_dir.mkdir(parents=True, exist_ok=True)
        (agent_dir / "tools").mkdir(exist_ok=True)

        # Create agent.yml
        with open(agent_dir / "agent.yml", "w", encoding="utf-8") as f:
            yaml.safe_dump(
                config["agent_config"],
                f,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
            )

        # Create state_model.yml
        with open(agent_dir / "state_model.yml", "w", encoding="utf-8") as f:
            yaml.safe_dump(
                config["state_model_config"],
                f,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
            )

        # Create custom tool if provided
        if custom_tool_code := config.get("custom_tool_code"):
            tools_init = agent_dir / "tools" / "__init__.py"
            tools_init.touch()

            tool_path = agent_dir / "tools" / "process.py"
            with open(tool_path, "w", encoding="utf-8") as f:
                f.write(custom_tool_code)

        return agent_dir

    def get_agent_type_prompt(self) -> str:
        """Generate and return the agent type selection prompt"""
        return """
[bold cyan]Select the type of agent to create:[/bold cyan]

1. [green]Atomic Agent[/green]
   - LLM-powered with state management
   - Best for: NLP tasks, content generation, analysis

2. [blue]Function Agent[/blue]
   - Custom tool integration without LLM
   - Best for: Data processing, API integration, transformations

3. [magenta]Orchestrator Agent[/magenta]
   - Multi-agent workflow coordination
   - Best for: Complex pipelines, multi-step processes

Enter your choice (1-3): """

    async def get_output_location(self) -> Path:
        """Get and validate the output location"""
        while True:
            default_path = self.default_output_dir
            output_path = await self.console_manager.console.input_async(
                f"\nOutput directory [{default_path}]: "
            )

            output_path = output_path.strip() or default_path
            path = Path(output_path).resolve()

            try:
                path.mkdir(parents=True, exist_ok=True)
                return path
            except Exception as e:
                self.console.print(f"[red]Error creating directory: {str(e)}[/red]")
                retry = await self.console_manager.console.input_async(
                    "Try another location? [y/N]: "
                )
                if retry.lower() != "y":
                    raise click.Abort()

    async def generate_agent(self, agent_type: str, purpose: str) -> Dict[str, Any]:
        """Generate agent configuration using the agent_generator"""
        state = {"agent_type": agent_type, "purpose": purpose}
        try:
            result = await self.generator.execute(state)
            if not result.SUCCESS:
                raise Exception(f"Agent generation failed: {result.ERROR_MESSAGE}")

            return result.model_dump()
        except Exception as e:
            import traceback

            logger.error(traceback.format_exc())
            logger.error(f"Error generating agent: {e}")
            raise

    async def confirm_creation(self, config: Dict[str, Any]) -> bool:
        """Display config summary and get user confirmation"""
        agent_config = config["agent_config"]
        summary = f"""
[bold]Agent Configuration Summary:[/bold]

Name: {agent_config['name']}
Type: {agent_config.get('agent_type', 'Not specified')}
Description: {agent_config.get('description', {}).get('en', 'Not specified')}

Custom Models: {len(config.get('state_model_config', {}).get('custom_models', []))}
State Fields: {len(config.get('state_model_config', {}).get('state_fields', []))}
Has Custom Tool: {'Yes' if config.get("custom_tool_code") else 'No'}
        """

        self.console.print(Panel(summary, title="Configuration Preview"))

        confirm = await self.console_manager.console.input_async(
            "\nCreate agent with this configuration? [y/N]: "
        )
        return confirm.lower() == "y"

    async def arun(self) -> None:
        """Main execution flow"""
        await self.initialize()

        # Display welcome message
        self.console.print(
            Panel(
                "[bold green]Welcome to Kagura AI Agent Creator![/bold green]\n"
                "This tool will help you create a new Kagura agent.",
                title="[bold blue]Kagura Agent Creator[/bold blue]",
            )
        )

        try:
            # Get agent type
            self.console.print(self.get_agent_type_prompt())
            agent_type_map = {"1": "atomic", "2": "function", "3": "orchestrator"}
            while True:
                choice = (await self.console_manager.console.input_async("")).strip()
                agent_type = agent_type_map.get(choice)
                if agent_type:
                    break
                self.console.print(
                    "[red]Invalid choice. Please enter 1, 2, or 3.[/red]"
                )

            # Get purpose
            purpose = await self.console_manager.console.input_async(
                "\n[cyan]Describe the purpose of your agent.[/cyan]\n"
                "Be specific about what you want it to do: "
            )

            # Generate configuration
            self.console.print("\n[bold]Generating agent configuration...[/bold]")
            config = await self.generate_agent(agent_type, purpose)

            # Confirm and create
            if await self.confirm_creation(config):
                output_dir = await self.get_output_location()
                agent_dir = await self.create_agent_files(config, output_dir)

                self.console.print(
                    f"\n[green]Successfully created agent in: {agent_dir}[/green]"
                )
                self.console.print(
                    "\nNext steps:"
                    "\n1. Review the generated configuration files"
                    "\n2. Customize the agent as needed"
                    "\n3. Test your agent using the Kagura CLI"
                )
            else:
                self.console.print("\n[yellow]Agent creation cancelled[/yellow]")

        except Exception as e:
            logger.error(f"Error in agent creation: {e}")
            self.console.print(f"[red]Error: {str(e)}[/red]")
        finally:
            await self.cleanup()

    async def cleanup(self):
        """Cleanup resources"""
        if self.message_history:
            await self.message_history.close()


@click.command()
@click.option(
    "--output-dir",
    "-o",
    help="Output directory for the agent files",
    default=None,
    type=click.Path(),
)
def create(output_dir: Optional[str] = None):
    """Create a new Kagura agent interactively"""
    creator = None
    try:
        creator = AgentCreator(output_dir)
        asyncio.run(creator.arun())
    except KeyboardInterrupt:
        print("\nAgent creation cancelled")
        sys.exit(0)
    except click.Abort:
        print("\nOperation aborted")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error in create command: {e}")
        print(f"Error: {str(e)}")
        sys.exit(1)
    finally:
        if creator and creator.message_history:
            asyncio.run(creator.cleanup())


if __name__ == "__main__":
    create()
