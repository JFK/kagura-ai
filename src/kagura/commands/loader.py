"""Command loader for loading custom commands from Markdown files.

Loads commands from Markdown files with YAML frontmatter.
"""

import frontmatter
from pathlib import Path
from typing import Optional

from .command import Command


class CommandLoader:
    """Load custom commands from Markdown files.

    Commands are stored as Markdown files with YAML frontmatter containing
    metadata and a Markdown body containing the command template.

    Example command file (~/.kagura/commands/example.md):
        ---
        name: example
        description: Example command
        allowed_tools: [git, gh]
        model: gpt-4o-mini
        ---

        ## Task
        Execute the following...
    """

    def __init__(self, commands_dir: Optional[Path] = None) -> None:
        """Initialize command loader.

        Args:
            commands_dir: Directory containing command files
                         (default: ~/.kagura/commands)
        """
        self.commands_dir = commands_dir or (Path.home() / ".kagura" / "commands")
        self.commands: dict[str, Command] = {}

    def load_all(self) -> dict[str, Command]:
        """Load all commands from commands directory.

        Returns:
            Dictionary mapping command names to Command objects

        Raises:
            FileNotFoundError: If commands directory doesn't exist
        """
        if not self.commands_dir.exists():
            raise FileNotFoundError(
                f"Commands directory not found: {self.commands_dir}"
            )

        self.commands.clear()

        for md_file in self.commands_dir.glob("*.md"):
            try:
                command = self.load_command(md_file)
                self.commands[command.name] = command
            except Exception as e:
                # Log error but continue loading other commands
                print(f"Warning: Failed to load {md_file.name}: {e}")

        return self.commands

    def load_command(self, path: Path) -> Command:
        """Load a single command from Markdown file.

        Args:
            path: Path to Markdown command file

        Returns:
            Loaded Command object

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If frontmatter is invalid or required fields missing
        """
        if not path.exists():
            raise FileNotFoundError(f"Command file not found: {path}")

        # Parse frontmatter and content
        post = frontmatter.load(path)

        # Extract metadata from frontmatter
        metadata = dict(post.metadata)

        # Get command name (use frontmatter name or filename)
        name = metadata.pop("name", path.stem)
        description = metadata.pop("description", "")
        allowed_tools = metadata.pop("allowed_tools", [])
        model = metadata.pop("model", "gpt-4o-mini")
        parameters = metadata.pop("parameters", {})

        # Template is the Markdown body
        template = post.content.strip()

        return Command(
            name=name,
            description=description,
            template=template,
            allowed_tools=allowed_tools,
            model=model,
            parameters=parameters,
            metadata=metadata,  # Store any additional metadata
        )

    def get_command(self, name: str) -> Optional[Command]:
        """Get a loaded command by name.

        Args:
            name: Command name

        Returns:
            Command object if found, None otherwise
        """
        return self.commands.get(name)

    def list_commands(self) -> list[str]:
        """List all loaded command names.

        Returns:
            List of command names
        """
        return list(self.commands.keys())

    def __repr__(self) -> str:
        """String representation."""
        return f"CommandLoader(dir={self.commands_dir}, commands={len(self.commands)})"
