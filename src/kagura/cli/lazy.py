"""Lazy-loading Click Group for fast CLI startup"""

from __future__ import annotations

import importlib
from typing import Optional

import click


class LazyGroup(click.Group):
    """Lazy-loading Click Group

    Subcommands are imported only when invoked.
    This dramatically reduces CLI startup time.

    Example:
        >>> @click.group(cls=LazyGroup, lazy_subcommands={
        ...     "mcp": ("kagura.cli.mcp", "mcp", "MCP commands"),
        ...     "chat": ("kagura.cli.chat", "chat", "Start chat session"),
        ... })
        >>> def cli():
        ...     pass
    """

    def __init__(
        self,
        *args,
        lazy_subcommands: Optional[
            dict[str, tuple[str, str] | tuple[str, str, str]]
        ] = None,
        **kwargs,
    ):
        """Initialize lazy group

        Args:
            lazy_subcommands: Dict mapping command names to import info.
                Format: {name: (module_path, attr_name, help_text?)}
                Example: {"mcp": ("kagura.cli.mcp", "mcp", "MCP commands")}
            *args: Positional arguments for click.Group
            **kwargs: Keyword arguments for click.Group
        """
        super().__init__(*args, **kwargs)
        self.lazy_subcommands = lazy_subcommands or {}
        self._loaded_commands: dict[str, click.Command] = {}

    def get_command(self, ctx: click.Context, cmd_name: str) -> Optional[click.Command]:
        """Get command, importing lazily if needed

        Args:
            ctx: Click context
            cmd_name: Command name

        Returns:
            Command instance or None if not found
        """
        # Try regular command first (already loaded)
        cmd = super().get_command(ctx, cmd_name)
        if cmd is not None:
            return cmd

        # Check if already loaded
        if cmd_name in self._loaded_commands:
            return self._loaded_commands[cmd_name]

        # Lazy load if defined
        if cmd_name in self.lazy_subcommands:
            subcommand_info = self.lazy_subcommands[cmd_name]

            # Handle tuple with or without help text
            if len(subcommand_info) == 3:
                module_path, attr_name, _ = subcommand_info
            else:
                module_path, attr_name = subcommand_info

            try:
                # Import module lazily
                module = importlib.import_module(module_path)

                # Get command
                cmd = getattr(module, attr_name)

                # Cache it for next time
                self._loaded_commands[cmd_name] = cmd
                self.add_command(cmd, cmd_name)

                return cmd

            except (ImportError, AttributeError) as e:
                # Command loading failed
                raise click.ClickException(
                    f"Failed to load command '{cmd_name}': {e}"
                ) from e

        return None

    def list_commands(self, ctx: click.Context) -> list[str]:
        """List all commands (including lazy ones)

        Args:
            ctx: Click context

        Returns:
            Sorted list of command names
        """
        # Only return lazy commands - don't load them yet
        # Regular commands will be added by parent class
        return sorted(self.lazy_subcommands.keys())

    def format_commands(
        self, ctx: click.Context, formatter: click.HelpFormatter
    ) -> None:
        """Format commands for help text WITHOUT loading them

        Args:
            ctx: Click context
            formatter: Help formatter
        """
        commands = []

        # Collect all commands (regular + lazy) without loading lazy ones
        all_names = set(super().list_commands(ctx)) | set(self.lazy_subcommands.keys())

        for name in sorted(all_names):
            # Try to get regular command first (already loaded)
            cmd = super().get_command(ctx, name)

            if cmd is not None:
                # Regular command loaded
                help_text = cmd.get_short_help_str(limit=formatter.width)
                commands.append((name, help_text))
            elif name in self.lazy_subcommands:
                # Lazy command - use help text from lazy_subcommands if provided
                subcommand_info = self.lazy_subcommands[name]
                if len(subcommand_info) == 3:
                    _, _, help_text = subcommand_info
                    commands.append((name, help_text))
                else:
                    commands.append((name, ""))
            else:
                # Should not happen
                continue

        if not commands:
            return

        # Format command list (use Click's default formatting)
        rows = []
        for name, help_text in commands:
            rows.append((name, help_text))

        if rows:
            with formatter.section("Commands"):
                formatter.write_dl(rows)


__all__ = ["LazyGroup"]
