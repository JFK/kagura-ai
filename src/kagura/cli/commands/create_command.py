# src/kagura/cli/commands/create_command.py
import click

from ...core.utils.create import KaguraAgentTemplateCreator


@click.command()
@click.option("--name", prompt="Agent name", help="Name of the agent")
@click.option(
    "--description", prompt="Agent description", help="Description of the agent"
)
def create(name: str, description: str):
    """Create a new Kagura agent template"""
    creator = KaguraAgentTemplateCreator()
    creator.create_template(name, description)
