"""MCP configuration management.

Manages MCP server configuration and Claude Desktop integration.
"""

import json
import os
import shutil
from pathlib import Path
from typing import Any


class MCPConfig:
    """MCP configuration manager."""

    def __init__(self):
        """Initialize config manager."""
        # Platform-specific Claude Desktop config paths
        import platform

        system = platform.system()
        if system == "Windows":
            # Windows: %APPDATA%\Claude\claude_desktop_config.json
            appdata = os.getenv("APPDATA")
            if appdata:
                self.claude_config_path = (
                    Path(appdata) / "Claude" / "claude_desktop_config.json"
                )
            else:
                self.claude_config_path = (
                    Path.home()
                    / "AppData"
                    / "Roaming"
                    / "Claude"
                    / "claude_desktop_config.json"
                )
        elif system == "Darwin":
            # macOS: ~/Library/Application Support/Claude/claude_desktop_config.json
            self.claude_config_path = (
                Path.home()
                / "Library"
                / "Application Support"
                / "Claude"
                / "claude_desktop_config.json"
            )
        else:
            # Linux: ~/.config/claude/claude_desktop_config.json
            self.claude_config_path = (
                Path.home() / ".config" / "claude" / "claude_desktop_config.json"
            )

        from kagura.config.paths import get_config_dir

        self.kagura_config_path = get_config_dir() / "mcp-config.yaml"

    def get_claude_desktop_config(self) -> dict[str, Any] | None:
        """Get Claude Desktop MCP configuration.

        Returns:
            Configuration dict or None if not found
        """
        if not self.claude_config_path.exists():
            return None

        try:
            with open(self.claude_config_path) as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

    def add_to_claude_desktop(
        self, server_name: str = "kagura-memory", kagura_command: str = "kagura"
    ) -> bool:
        """Add Kagura to Claude Desktop MCP configuration.

        Args:
            server_name: Server name in Claude config
            kagura_command: Command to start Kagura MCP server

        Returns:
            True if successful, False otherwise
        """
        # Create config directory if it doesn't exist
        self.claude_config_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing config or create new
        config = self.get_claude_desktop_config()
        if config is None:
            config = {"mcpServers": {}}
        elif "mcpServers" not in config:
            config["mcpServers"] = {}

        # Add Kagura server configuration
        config["mcpServers"][server_name] = {
            "command": kagura_command,
            "args": ["mcp", "serve"],
            "env": {},
        }

        # Backup existing config
        if self.claude_config_path.exists():
            backup_path = self.claude_config_path.with_suffix(".json.backup")
            shutil.copy(self.claude_config_path, backup_path)

        # Write updated config
        try:
            with open(self.claude_config_path, "w") as f:
                json.dump(config, f, indent=2)
            return True
        except OSError:
            return False

    def remove_from_claude_desktop(self, server_name: str = "kagura-memory") -> bool:
        """Remove Kagura from Claude Desktop configuration.

        Args:
            server_name: Server name to remove

        Returns:
            True if successful, False otherwise
        """
        config = self.get_claude_desktop_config()
        if config is None or "mcpServers" not in config:
            return False

        if server_name not in config["mcpServers"]:
            return False

        # Remove server
        del config["mcpServers"][server_name]

        # Backup and write
        if self.claude_config_path.exists():
            backup_path = self.claude_config_path.with_suffix(".json.backup")
            shutil.copy(self.claude_config_path, backup_path)

        try:
            with open(self.claude_config_path, "w") as f:
                json.dump(config, f, indent=2)
            return True
        except OSError:
            return False

    def is_configured_in_claude_desktop(
        self, server_name: str = "kagura-memory"
    ) -> bool:
        """Check if Kagura is configured in Claude Desktop.

        Args:
            server_name: Server name to check

        Returns:
            True if configured
        """
        config = self.get_claude_desktop_config()
        if config is None:
            return False

        return server_name in config.get("mcpServers", {})
