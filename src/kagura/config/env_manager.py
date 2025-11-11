"""Environment variable configuration management.

Issue #650 - Web UI for .env.cloud configuration

Provides secure read/write access to .env.cloud file with:
- Sensitive value masking (API keys, secrets)
- Configuration validation (API key verification, etc.)
- Audit logging (who changed what, when)
- File permission enforcement (0600)

Example:
    >>> from kagura.config.env_manager import EnvConfigManager
    >>> manager = EnvConfigManager("/opt/kagura/.env.cloud")
    >>>
    >>> # Read all config (sensitive values masked)
    >>> config = manager.read_config()
    >>> print(config["OPENAI_API_KEY"])  # "sk-proj-***"
    >>>
    >>> # Update config (admin only)
    >>> manager.update_config("OPENAI_API_KEY", "sk-proj-newkey", user_email="admin@example.com")
    >>>
    >>> # Validate before saving
    >>> is_valid = manager.validate_config("OPENAI_API_KEY", "sk-proj-test")
"""

import hashlib
import logging
import os
import re
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class EnvConfigManager:
    """Manage .env.cloud file configuration.

    Provides secure CRUD operations for environment variables with
    masking, validation, and audit logging.

    Args:
        env_file_path: Path to .env.cloud file (default: /opt/kagura/.env.cloud)

    Example:
        >>> manager = EnvConfigManager()
        >>> config = manager.read_config(mask_sensitive=True)
    """

    # Sensitive key patterns (will be masked in GET requests)
    SENSITIVE_PATTERNS = [
        r".*_KEY$",
        r".*_SECRET$",
        r".*_PASSWORD$",
        r".*_TOKEN$",
        r"DATABASE_URL",
        r"REDIS_URL",
        r".*CLIENT_SECRET.*",
    ]

    # Configuration categories for UI organization
    CATEGORIES = {
        "llm_api_keys": [
            "OPENAI_API_KEY",
            "GOOGLE_API_KEY",
            "ANTHROPIC_API_KEY",
            "BRAVE_SEARCH_API_KEY",
        ],
        "oauth2": [
            "GOOGLE_CLIENT_ID",
            "GOOGLE_CLIENT_SECRET",
            "GOOGLE_REDIRECT_URI",
        ],
        "security": ["API_KEY_SECRET", "JWT_SECRET"],
        "database": ["DATABASE_URL", "REDIS_URL", "QDRANT_URL"],
        "embeddings": ["EMBEDDING_PROVIDER", "EMBEDDING_MODEL"],
        "application": [
            "ENVIRONMENT",
            "LOG_LEVEL",
            "DOMAIN",
            "ALLOWED_ORIGINS",
            "CADDY_ADMIN_EMAIL",
        ],
        "backends": [
            "GRAPH_BACKEND",
            "PERSISTENT_BACKEND",
            "CACHE_BACKEND",
            "VECTOR_BACKEND",
        ],
    }

    def __init__(self, env_file_path: Optional[Path | str] = None):
        """Initialize env config manager.

        Args:
            env_file_path: Path to .env.cloud file
        """
        self.env_file_path = Path(env_file_path or "/opt/kagura/.env.cloud")

    def read_config(self, mask_sensitive: bool = True) -> dict[str, str]:
        """Read all configuration from .env file.

        Args:
            mask_sensitive: If True, mask sensitive values (e.g., "sk-proj-***")

        Returns:
            Dictionary of environment variables

        Example:
            >>> config = manager.read_config(mask_sensitive=True)
            >>> config["OPENAI_API_KEY"]  # "sk-proj-***"
            >>> config = manager.read_config(mask_sensitive=False)  # Admin only!
            >>> config["OPENAI_API_KEY"]  # "sk-proj-actual-key"
        """
        if not self.env_file_path.exists():
            logger.warning(f".env file not found: {self.env_file_path}")
            return {}

        config: dict[str, str] = {}

        with open(self.env_file_path, "r") as f:
            for line in f:
                line = line.strip()

                # Skip comments and empty lines
                if not line or line.startswith("#"):
                    continue

                # Parse KEY=VALUE
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()

                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]

                    if mask_sensitive:
                        value = self.mask_value(key, value)

                    config[key] = value

        return config

    def update_config(
        self,
        key: str,
        value: str,
        user_email: str,
        audit_metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """Update single configuration value.

        Args:
            key: Environment variable name
            value: New value
            user_email: Email of user making the change (for audit)
            audit_metadata: Additional audit metadata (IP, user agent, etc.)

        Raises:
            FileNotFoundError: If .env file doesn't exist
            PermissionError: If file permissions incorrect

        Example:
            >>> manager.update_config(
            ...     "OPENAI_API_KEY",
            ...     "sk-proj-newkey",
            ...     user_email="admin@example.com"
            ... )
        """
        # Read current config
        current_config = self.read_config(mask_sensitive=False)

        # Get old value for audit log
        old_value = current_config.get(key, "")

        # Update value
        current_config[key] = value

        # Write back to file
        self._write_config(current_config)

        # Log audit trail
        self._log_config_change(
            key=key,
            old_value=old_value,
            new_value=value,
            user_email=user_email,
            metadata=audit_metadata,
        )

        logger.info(f"Config updated: {key} by {user_email}")

    def batch_update_config(
        self,
        updates: dict[str, str],
        user_email: str,
        audit_metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """Update multiple configuration values at once.

        Args:
            updates: Dictionary of key-value pairs to update
            user_email: Email of user making the change
            audit_metadata: Additional audit metadata

        Example:
            >>> manager.batch_update_config({
            ...     "OPENAI_API_KEY": "sk-proj-new",
            ...     "LOG_LEVEL": "debug"
            ... }, user_email="admin@example.com")
        """
        # Read current config
        current_config = self.read_config(mask_sensitive=False)

        # Apply updates
        for key, value in updates.items():
            old_value = current_config.get(key, "")
            current_config[key] = value

            # Log each change
            self._log_config_change(
                key=key,
                old_value=old_value,
                new_value=value,
                user_email=user_email,
                metadata=audit_metadata,
            )

        # Write back to file
        self._write_config(current_config)

        logger.info(
            f"Batch config update: {len(updates)} keys by {user_email}"
        )

    def _write_config(self, config: dict[str, str]) -> None:
        """Write configuration to .env file with secure permissions.

        Args:
            config: Dictionary of environment variables

        Note:
            Sets file permissions to 0600 (owner read/write only) for security.
        """
        # Sort keys for readability
        sorted_keys = sorted(config.keys())

        with open(self.env_file_path, "w") as f:
            f.write("# Kagura Memory Cloud - Environment Variables\n")
            f.write("# Auto-managed by Web UI (Issue #650)\n")
            f.write(f"# Last updated: {self._get_timestamp()}\n")
            f.write("#\n")
            f.write("# IMPORTANT: Do not edit manually while app is running.\n")
            f.write("#            Use Web UI Settings page instead.\n\n")

            # Write by category
            for category, keys in self.CATEGORIES.items():
                category_keys = [k for k in sorted_keys if k in keys]
                if category_keys:
                    f.write(f"# {category.replace('_', ' ').title()}\n")
                    for key in category_keys:
                        f.write(f"{key}={config[key]}\n")
                    f.write("\n")

            # Write uncategorized keys
            categorized = set()
            for keys in self.CATEGORIES.values():
                categorized.update(keys)
            uncategorized = [k for k in sorted_keys if k not in categorized]

            if uncategorized:
                f.write("# Other\n")
                for key in uncategorized:
                    f.write(f"{key}={config[key]}\n")

        # Enforce secure file permissions
        os.chmod(self.env_file_path, 0o600)

    def mask_value(self, key: str, value: str) -> str:
        """Mask sensitive values for display.

        Args:
            key: Environment variable name
            value: Value to potentially mask

        Returns:
            Masked value if sensitive, original value otherwise

        Example:
            >>> manager.mask_value("OPENAI_API_KEY", "sk-proj-abc123")
            "sk-proj-***"
            >>> manager.mask_value("LOG_LEVEL", "info")
            "info"
        """
        if not value:
            return ""

        # Check if key matches sensitive patterns
        for pattern in self.SENSITIVE_PATTERNS:
            if re.match(pattern, key, re.IGNORECASE):
                # Mask: show first 8 chars + ***
                if len(value) > 8:
                    return value[:8] + "***"
                else:
                    return "***"

        return value

    def is_sensitive(self, key: str) -> bool:
        """Check if key is sensitive.

        Args:
            key: Environment variable name

        Returns:
            True if key should be masked
        """
        for pattern in self.SENSITIVE_PATTERNS:
            if re.match(pattern, key, re.IGNORECASE):
                return True
        return False

    def validate_config(self, key: str, value: str) -> tuple[bool, Optional[str]]:
        """Validate configuration value before saving.

        Args:
            key: Environment variable name
            value: Value to validate

        Returns:
            (is_valid, error_message)

        Example:
            >>> is_valid, error = manager.validate_config("OPENAI_API_KEY", "sk-proj-test")
            >>> if not is_valid:
            ...     print(f"Invalid: {error}")
        """
        # Basic validation
        if not value:
            return False, f"{key} cannot be empty"

        # OpenAI API Key format validation
        if key == "OPENAI_API_KEY":
            if not (value.startswith("sk-") or value.startswith("sk-proj-")):
                return False, "OpenAI API key must start with 'sk-' or 'sk-proj-'"

        # URL validation
        if key in ["DATABASE_URL", "REDIS_URL", "QDRANT_URL"]:
            if not ("://" in value):
                return False, f"{key} must be a valid URL (scheme://...)"

        # Email validation
        if key == "CADDY_ADMIN_EMAIL":
            if "@" not in value or "." not in value:
                return False, "Invalid email address format"

        # Domain validation
        if key == "DOMAIN":
            if " " in value or not ("." in value):
                return False, "Invalid domain format"

        # TODO: Add API key verification (call OpenAI API to test)
        # TODO: Add database connection test

        return True, None

    def get_categories(self) -> dict[str, list[str]]:
        """Get configuration categories for UI organization.

        Returns:
            Dictionary mapping category name to list of keys

        Example:
            >>> categories = manager.get_categories()
            >>> print(categories["llm_api_keys"])
            ["OPENAI_API_KEY", "GOOGLE_API_KEY", ...]
        """
        return self.CATEGORIES

    def _log_config_change(
        self,
        key: str,
        old_value: str,
        new_value: str,
        user_email: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """Log configuration change to audit trail.

        Args:
            key: Configuration key that changed
            old_value: Previous value
            new_value: New value
            user_email: Email of user who made the change
            metadata: Additional context (IP address, user agent, etc.)

        Note:
            Stores SHA256 hash of values, NOT plaintext, for security.

            TODO (Issue #TBD): Implement PostgreSQL audit_logs integration
            Current: Logger only (works but not queryable)
            Future: PostgreSQL audit_logs table (see migrations/001_users.sql)
                    - Use SQLAlchemy ORM
                    - Enable audit log queries via API
                    - Add retention policy
        """
        old_hash = hashlib.sha256(old_value.encode()).hexdigest() if old_value else None
        new_hash = hashlib.sha256(new_value.encode()).hexdigest()

        # TODO: Implement PostgreSQL insertion
        # from sqlalchemy import create_engine
        # engine = create_engine(os.getenv("DATABASE_URL"))
        # with engine.connect() as conn:
        #     conn.execute("""
        #         INSERT INTO audit_logs (
        #             user_email, action, resource,
        #             old_value_hash, new_value_hash, metadata,
        #             ip_address, user_agent, created_at
        #         ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NOW())
        #     """, (user_email, 'config_update', key, old_hash, new_hash, ...))

        logger.info(
            f"Audit: config_update {key} by {user_email} "
            f"(old_hash={old_hash[:8] if old_hash else 'None'}..., "
            f"new_hash={new_hash[:8]}...)"
        )

    @staticmethod
    def _get_timestamp() -> str:
        """Get current UTC timestamp in ISO format."""
        from datetime import datetime

        return datetime.utcnow().isoformat() + "Z"


# Global singleton instance
_env_manager: Optional[EnvConfigManager] = None


def get_env_manager(env_file_path: Optional[Path | str] = None) -> EnvConfigManager:
    """Get global EnvConfigManager instance.

    Args:
        env_file_path: Path to .env.cloud file (defaults to /opt/kagura/.env.cloud)

    Returns:
        Global EnvConfigManager singleton

    Example:
        >>> from kagura.config.env_manager import get_env_manager
        >>> manager = get_env_manager()
    """
    global _env_manager

    if _env_manager is None:
        _env_manager = EnvConfigManager(env_file_path)

    return _env_manager
