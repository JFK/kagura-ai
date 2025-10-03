"""
Main CLI entry point

Stub implementation.
"""
import click
from ..version import __version__


@click.group()
@click.version_option(version=__version__)
def cli():
    """Kagura AI - Python-First AI Agent Framework"""
    pass


@cli.command()
def version():
    """Show version"""
    click.echo(f"Kagura AI v{__version__}")


if __name__ == "__main__":
    cli()
