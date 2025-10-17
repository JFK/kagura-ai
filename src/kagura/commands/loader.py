"""Command loader for loading custom commands from Markdown files.

Loads commands from Markdown files with YAML frontmatter.
"""

from pathlib import Path
from typing import Any, Optional

import frontmatter

from .command import Command


class CommandLoader:
    """Load custom commands from Markdown files.

    Commands are stored as Markdown files with YAML frontmatter containing
    metadata and a Markdown body containing the command template.

    By default, searches both project-local (./.kagura/commands) and
    global (~/.kagura/commands) directories. Local commands take priority
    over global commands with the same name.

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
            commands_dir: Directory containing command files.
                         If None, searches both local (./.kagura/commands)
                         and global (~/.kagura/commands) directories.
                         Local commands take priority over global ones.
        """
        if commands_dir is not None:
            # Single directory specified
            self.commands_dirs = [commands_dir]
        else:
            # Default: search global then local (so local overrides global)
            self.commands_dirs = [
                Path.home() / ".kagura" / "commands",  # Global
                Path.cwd() / ".kagura" / "commands",  # Local (priority)
            ]

        self.commands: dict[str, Command] = {}

    def load_all(self) -> dict[str, Command]:
        """Load all commands from commands directories.

        Searches all configured directories. When multiple directories
        contain commands with the same name, later directories take
        priority (local overrides global).

        Returns:
            Dictionary mapping command names to Command objects

        Raises:
            FileNotFoundError: If no commands directory exists
        """
        self.commands.clear()
        found_any = False

        for commands_dir in self.commands_dirs:
            if not commands_dir.exists():
                continue

            found_any = True

            for md_file in commands_dir.glob("*.md"):
                try:
                    command = self.load_command(md_file)
                    # Later directories override earlier ones (local > global)
                    self.commands[command.name] = command
                except Exception as e:
                    # Log error but continue loading other commands
                    print(f"Warning: Failed to load {md_file.name}: {e}")

        if not found_any:
            dirs_str = ", ".join(str(d) for d in self.commands_dirs)
            raise FileNotFoundError(
                f"No commands directory found. Searched: {dirs_str}"
            )

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
        post = frontmatter.load(str(path))

        # Extract metadata from frontmatter
        metadata = dict(post.metadata)

        # Get command name (use frontmatter name or filename)
        name = str(metadata.pop("name", path.stem))
        description = str(metadata.pop("description", ""))
        allowed_tools_raw = metadata.pop("allowed_tools", [])
        allowed_tools: list[str] = (
            allowed_tools_raw if isinstance(allowed_tools_raw, list) else []
        )
        model = str(metadata.pop("model", "gpt-5-mini"))
        parameters_raw = metadata.pop("parameters", {})
        parameters: dict[str, Any] = (
            parameters_raw if isinstance(parameters_raw, dict) else {}
        )

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
        dirs_str = ", ".join(str(d) for d in self.commands_dirs)
        return f"CommandLoader(dirs=[{dirs_str}], commands={len(self.commands)})"
