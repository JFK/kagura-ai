# src/kagura/cli/commands/install_command.py
import asyncio

import click

from ...core.utils.install import KaguraAgentInstaller


@click.command()
@click.argument("repo_url")
@click.option("--branch", default="main", help="Git branch to install from")
def install(repo_url: str, branch: str):
    """Install Kagura AI agents from a GitHub repository"""
    asyncio.run(KaguraAgentInstaller().install_from_github(repo_url, branch))
