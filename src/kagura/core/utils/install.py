# src/kagura/core/utils/install.py
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

import click
import pytest
from rich.console import Console
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn

from .validator import KaguraAgentValidator


class AgentValidationError(Exception):
    pass


class KaguraAgentInstaller:
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.config_dir = Path(os.path.expanduser("~")) / ".config" / "kagura"
        self.agents_dir = self.config_dir / "agents"

    async def install_from_github(self, repo_url: str, branch: str = "main"):
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("Installing agents...", total=None)

            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # Clone repository
                progress.update(task, description="Cloning repository...")
                subprocess.run(
                    ["git", "clone", "-b", branch, repo_url, temp_dir], check=True
                )

                # 構造の検証
                self.console.print("Validating repository structure...")
                try:
                    KaguraAgentValidator.validate_repository(temp_path)
                except AgentValidationError as e:
                    raise click.ClickException(f"Validation failed: {str(e)}")

                # Display repository README if exists
                repo_readme = temp_path / "README.md"
                if repo_readme.exists():
                    progress.stop()
                    self.console.print("\nRepository Information:")
                    self.console.print(Markdown(repo_readme.read_text()))
                    if not click.confirm("Continue with installation?"):
                        return
                    progress.start()

                # Install dependencies
                progress.update(task, description="Installing dependencies...")
                if (temp_path / "pyproject.toml").exists():
                    subprocess.run(["poetry", "install"], cwd=temp_dir, check=True)

                # Run tests
                progress.update(task, description="Running tests...")
                if not pytest.main([str(temp_path / "tests")]) == 0:
                    raise click.ClickException("Tests failed. Installation aborted.")

                # Process each agent
                agents_src = temp_path / "agents"
                for agent_dir in agents_src.iterdir():
                    if agent_dir.is_dir():
                        agent_name = agent_dir.name
                        progress.update(task, description=f"Installing {agent_name}...")

                        # Install agent-specific requirements
                        req_file = agent_dir / "requirements.txt"
                        if req_file.exists():
                            subprocess.run(
                                ["pip", "install", "-r", str(req_file)], check=True
                            )

                        # Create destination directory
                        dest_dir = self.agents_dir / agent_name
                        if dest_dir.exists():
                            shutil.rmtree(dest_dir)
                        dest_dir.mkdir(parents=True)

                        # Copy agent files and resources
                        for file in [
                            "agent.yml",
                            "state_model.yml",
                            "README.md",
                            "requirements.txt",
                        ]:
                            if (agent_dir / file).exists():
                                shutil.copy2(agent_dir / file, dest_dir / file)

                        # Copy additional resources
                        for resource in ["tests", "examples"]:
                            src = temp_path / resource / agent_name
                            if src.exists():
                                shutil.copytree(src, dest_dir / resource)

                        # Display agent README if exists
                        agent_readme = agent_dir / "README.md"
                        if agent_readme.exists():
                            progress.stop()
                            self.console.print(f"\n{agent_name} Information:")
                            self.console.print(Markdown(agent_readme.read_text()))
                            progress.start()

                progress.update(task, description="Installation complete!")
