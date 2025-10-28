"""User configuration manager for Kagura AI"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class UserConfig(BaseModel):
    """User configuration model

    Attributes:
        name: User's name
        location: Default location (e.g., "Tokyo", "New York")
        language: Preferred language code ("en", "ja", etc.)
        news_topics: List of preferred news topics
        cuisine_prefs: List of preferred cuisines
        created_at: Config creation timestamp
        updated_at: Last update timestamp
        version: Config version
    """

    name: str = Field(default="", description="User's name")
    location: str = Field(default="", description="Default location")
    language: str = Field(default="en", description="Preferred language code (en/ja)")
    news_topics: list[str] = Field(
        default_factory=lambda: ["technology"],
        description="Preferred news topics",
    )
    cuisine_prefs: list[str] = Field(
        default_factory=list, description="Preferred cuisines"
    )
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    version: str = Field(default="3.0.0", description="Config version")

    model_config = ConfigDict(extra="allow")


class ConfigManager:
    """Manages user configuration

    Handles loading, saving, and accessing user preferences from
    ~/.kagura/config.json
    """

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize config manager

        Args:
            config_path: Custom config file path
                (default: XDG config dir or ~/.config/kagura/config.json)
        """
        if config_path is None:
            from kagura.config.paths import get_config_dir

            config_path = get_config_dir() / "config.json"

        self.config_path = config_path
        self._config: Optional[UserConfig] = None

    def load(self) -> UserConfig:
        """Load config from file

        Returns:
            UserConfig instance (defaults if file doesn't exist)
        """
        if self.config_path.exists():
            try:
                data = json.loads(self.config_path.read_text(encoding="utf-8"))
                return UserConfig(**data)
            except Exception:
                # Invalid config, return defaults
                return UserConfig()
        else:
            # No config file, return defaults
            return UserConfig()

    def save(self, config: UserConfig) -> None:
        """Save config to file

        Args:
            config: UserConfig instance to save
        """
        # Update timestamp
        config.updated_at = datetime.now().isoformat()

        # Ensure directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Save to file
        self.config_path.write_text(
            json.dumps(config.model_dump(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def get(self) -> UserConfig:
        """Get current config (cached)

        Returns:
            UserConfig instance
        """
        if self._config is None:
            self._config = self.load()
        return self._config

    def update(self, **kwargs: Any) -> None:
        """Update config fields

        Args:
            **kwargs: Fields to update
        """
        config = self.get()

        # Update fields
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)

        # Save
        self.save(config)

        # Update cache
        self._config = config

    def reset(self) -> None:
        """Reset config to defaults"""
        self._config = UserConfig()
        if self.config_path.exists():
            self.config_path.unlink()


# Global instance
_global_config: Optional[ConfigManager] = None


def get_user_config() -> UserConfig:
    """Get global user config instance

    Returns:
        UserConfig instance

    Example:
        >>> config = get_user_config()
        >>> print(config.name)
        Kiyota
        >>> print(config.location)
        Tokyo
    """
    global _global_config
    if _global_config is None:
        _global_config = ConfigManager()
    return _global_config.get()


def set_config_manager(manager: ConfigManager) -> None:
    """Set custom config manager (for testing)

    Args:
        manager: Custom ConfigManager instance
    """
    global _global_config
    _global_config = manager


__all__ = ["UserConfig", "ConfigManager", "get_user_config", "set_config_manager"]
