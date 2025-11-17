"""External API Key Manager for third-party service credentials.

Issues #690, #692 - Secure storage and management of external API keys.

Provides encrypted storage for API keys from external services (OpenAI, Anthropic,
Google, Brave, Cohere, Voyage, Jina, etc.) with:
- Fernet symmetric encryption (two-way, can decrypt for usage)
- Database persistence (PostgreSQL/SQLite)
- Admin-only access control
- Audit trail
- Migration from .env.cloud

Example:
    >>> from kagura.config.external_api_key_manager import ExternalAPIKeyManager
    >>> from kagura.utils.encryption import get_encryptor
    >>>
    >>> manager = ExternalAPIKeyManager(get_encryptor())
    >>> manager.create_key("OPENAI_API_KEY", "openai", "sk-proj-...", "admin@example.com")
    >>> keys = manager.list_keys()  # Returns masked values
    >>> plaintext = manager.get_decrypted_value("OPENAI_API_KEY")  # Decrypt for usage
"""

import logging
from datetime import datetime
from typing import Any

from sqlalchemy.exc import IntegrityError

from kagura.auth.models import ExternalAPIKey, get_session
from kagura.utils.encryption import APIKeyEncryption

logger = logging.getLogger(__name__)


class ExternalAPIKeyManager:
    """Manager for external API keys with encryption.

    Provides CRUD operations for external service API keys with
    transparent encryption/decryption using Fernet.
    """

    def __init__(self, encryptor: APIKeyEncryption):
        """Initialize manager with encryptor.

        Args:
            encryptor: APIKeyEncryption instance for encrypt/decrypt operations
        """
        self.encryptor = encryptor

    def create_key(
        self,
        key_name: str,
        provider: str,
        value: str,
        updated_by: str,
    ) -> ExternalAPIKey:
        """Create a new external API key.

        Args:
            key_name: Unique key identifier (e.g., "OPENAI_API_KEY")
            provider: Service provider (e.g., "openai", "anthropic")
            value: Plaintext API key value
            updated_by: Email of admin creating the key

        Returns:
            Created ExternalAPIKey instance

        Raises:
            ValueError: If key_name already exists or value is empty
            Exception: On database errors

        Example:
            >>> manager.create_key(
            ...     "OPENAI_API_KEY",
            ...     "openai",
            ...     "sk-proj-abc123...",
            ...     "admin@example.com"
            ... )
        """
        if not value:
            msg = "API key value cannot be empty"
            raise ValueError(msg)

        session = get_session()
        try:
            # Check if key already exists
            existing = session.query(ExternalAPIKey).filter_by(key_name=key_name).first()
            if existing:
                msg = f"API key '{key_name}' already exists. Use update_key() to modify."
                raise ValueError(msg)

            # Encrypt value
            encrypted_value = self.encryptor.encrypt(value)

            # Create model
            key = ExternalAPIKey(
                key_name=key_name,
                provider=provider,
                encrypted_value=encrypted_value,
                updated_by=updated_by,
            )

            session.add(key)
            session.commit()
            session.refresh(key)

            logger.info(f"External API key created: {key_name} (provider={provider})")

            return key

        except IntegrityError as e:
            session.rollback()
            logger.error(f"Database integrity error creating key '{key_name}': {e}")
            raise ValueError(f"Key '{key_name}' already exists") from e
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to create external API key '{key_name}': {e}")
            raise
        finally:
            session.close()

    def get_key(self, key_name: str) -> ExternalAPIKey | None:
        """Get external API key (encrypted value).

        Args:
            key_name: Key identifier

        Returns:
            ExternalAPIKey instance or None if not found

        Example:
            >>> key = manager.get_key("OPENAI_API_KEY")
            >>> key.encrypted_value  # Still encrypted
        """
        session = get_session()
        try:
            return session.query(ExternalAPIKey).filter_by(key_name=key_name).first()
        finally:
            session.close()

    def get_decrypted_value(self, key_name: str) -> str:
        """Get decrypted API key value for usage.

        Args:
            key_name: Key identifier

        Returns:
            Decrypted plaintext API key

        Raises:
            ValueError: If key not found or decryption fails

        Example:
            >>> plaintext = manager.get_decrypted_value("OPENAI_API_KEY")
            >>> plaintext
            'sk-proj-abc123...'
        """
        key = self.get_key(key_name)
        if not key:
            msg = f"External API key '{key_name}' not found"
            raise ValueError(msg)

        try:
            return self.encryptor.decrypt(key.encrypted_value)
        except Exception as e:
            logger.error(f"Failed to decrypt key '{key_name}': {e}")
            raise ValueError(f"Decryption failed for '{key_name}'") from e

    def update_key(
        self,
        key_name: str,
        value: str,
        updated_by: str,
    ) -> ExternalAPIKey:
        """Update an existing external API key.

        Args:
            key_name: Key identifier
            value: New plaintext API key value
            updated_by: Email of admin updating the key

        Returns:
            Updated ExternalAPIKey instance

        Raises:
            ValueError: If key not found or value is empty

        Example:
            >>> manager.update_key("OPENAI_API_KEY", "sk-proj-new...", "admin@example.com")
        """
        if not value:
            msg = "API key value cannot be empty"
            raise ValueError(msg)

        session = get_session()
        try:
            key = session.query(ExternalAPIKey).filter_by(key_name=key_name).first()
            if not key:
                msg = f"External API key '{key_name}' not found"
                raise ValueError(msg)

            # Encrypt new value
            encrypted_value = self.encryptor.encrypt(value)

            # Update
            key.encrypted_value = encrypted_value
            key.updated_by = updated_by
            key.updated_at = datetime.utcnow()

            session.commit()
            session.refresh(key)

            logger.info(f"External API key updated: {key_name}")

            return key

        except ValueError:
            session.rollback()
            raise
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to update external API key '{key_name}': {e}")
            raise
        finally:
            session.close()

    def delete_key(self, key_name: str) -> None:
        """Delete an external API key.

        Args:
            key_name: Key identifier

        Raises:
            ValueError: If key not found

        Example:
            >>> manager.delete_key("OLD_API_KEY")
        """
        session = get_session()
        try:
            key = session.query(ExternalAPIKey).filter_by(key_name=key_name).first()
            if not key:
                msg = f"External API key '{key_name}' not found"
                raise ValueError(msg)

            session.delete(key)
            session.commit()

            logger.info(f"External API key deleted: {key_name}")

        except ValueError:
            session.rollback()
            raise
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to delete external API key '{key_name}': {e}")
            raise
        finally:
            session.close()

    def list_keys(self, provider: str | None = None) -> list[dict[str, Any]]:
        """List all external API keys (with masked values).

        Args:
            provider: Optional provider filter (e.g., "openai")

        Returns:
            List of key dictionaries with masked values

        Example:
            >>> keys = manager.list_keys()
            >>> keys[0]
            {
                'id': 1,
                'key_name': 'OPENAI_API_KEY',
                'provider': 'openai',
                'masked_value': 'sk-proj-***',
                'created_at': '2025-11-17T...',
                'updated_at': '2025-11-17T...',
                'updated_by': 'admin@example.com'
            }
        """
        session = get_session()
        try:
            query = session.query(ExternalAPIKey)

            if provider:
                query = query.filter_by(provider=provider)

            keys = query.order_by(ExternalAPIKey.provider, ExternalAPIKey.key_name).all()

            result = []
            for key in keys:
                # Decrypt to mask (don't return encrypted value)
                try:
                    plaintext = self.encryptor.decrypt(key.encrypted_value)
                    masked = self.encryptor.mask_value(plaintext)
                except Exception as e:
                    logger.warning(f"Failed to decrypt key '{key.key_name}' for masking: {e}")
                    masked = "***"

                result.append({
                    "id": key.id,
                    "key_name": key.key_name,
                    "provider": key.provider,
                    "masked_value": masked,
                    "created_at": key.created_at.isoformat() if key.created_at else None,
                    "updated_at": key.updated_at.isoformat() if key.updated_at else None,
                    "updated_by": key.updated_by,
                })

            return result

        finally:
            session.close()

    def import_from_env(self, env_values: dict[str, str], updated_by: str) -> dict[str, str]:
        """Import API keys from environment variables.

        Reads API keys from .env.cloud and stores encrypted in database.
        Skips keys that already exist.

        Args:
            env_values: Dictionary of env var name -> plaintext value
            updated_by: Email of admin performing import

        Returns:
            Dictionary with import results:
            {
                'created': ['OPENAI_API_KEY', ...],
                'skipped': ['GOOGLE_API_KEY', ...],  # Already exists
                'failed': [('KEY_NAME', 'error message'), ...]
            }

        Example:
            >>> results = manager.import_from_env({
            ...     'OPENAI_API_KEY': 'sk-proj-...',
            ...     'ANTHROPIC_API_KEY': 'sk-ant-...',
            ... }, "admin@example.com")
            >>> results['created']
            ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY']
        """
        # Provider mapping (detect from key name)
        provider_map = {
            "OPENAI_API_KEY": "openai",
            "ANTHROPIC_API_KEY": "anthropic",
            "GOOGLE_API_KEY": "google",
            "GEMINI_API_KEY": "google",
            "BRAVE_SEARCH_API_KEY": "brave",
            "COHERE_API_KEY": "cohere",
            "VOYAGE_API_KEY": "voyage",
            "JINA_API_KEY": "jina",
        }

        results = {
            "created": [],
            "skipped": [],
            "failed": [],
        }

        for key_name, value in env_values.items():
            # Detect provider
            provider = provider_map.get(key_name, "custom")

            try:
                self.create_key(key_name, provider, value, updated_by)
                results["created"].append(key_name)
            except ValueError as e:
                # Key already exists or validation failed
                if "already exists" in str(e):
                    results["skipped"].append(key_name)
                    logger.info(f"Skipped existing key: {key_name}")
                else:
                    results["failed"].append((key_name, str(e)))
                    logger.warning(f"Failed to import key '{key_name}': {e}")
            except Exception as e:
                results["failed"].append((key_name, str(e)))
                logger.error(f"Unexpected error importing key '{key_name}': {e}")

        logger.info(
            f"Import completed: created={len(results['created'])}, "
            f"skipped={len(results['skipped'])}, failed={len(results['failed'])}"
        )

        return results
