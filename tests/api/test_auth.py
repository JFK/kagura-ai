"""Tests for API Key authentication."""

import pytest
from pathlib import Path
import tempfile

from kagura.api.auth import APIKeyManager, API_KEY_PREFIX


class TestAPIKeyManager:
    """Test API Key manager functionality."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = Path(f.name)
        yield db_path
        # Cleanup
        if db_path.exists():
            db_path.unlink()

    @pytest.fixture
    def manager(self, temp_db):
        """Create API Key manager with temporary database."""
        return APIKeyManager(db_path=temp_db)

    def test_create_key(self, manager):
        """Test creating a new API key."""
        api_key = manager.create_key(
            name="test-key",
            user_id="test_user",
        )

        # Should return key with correct prefix
        assert api_key.startswith(API_KEY_PREFIX)
        assert len(api_key) > len(API_KEY_PREFIX)

    def test_create_key_with_expiration(self, manager):
        """Test creating API key with expiration."""
        api_key = manager.create_key(
            name="expiring-key",
            user_id="test_user",
            expires_days=30,
        )

        assert api_key.startswith(API_KEY_PREFIX)

    def test_create_duplicate_name_fails(self, manager):
        """Test that creating duplicate name fails."""
        manager.create_key(name="dup-key", user_id="test_user")

        with pytest.raises(ValueError, match="already exists"):
            manager.create_key(name="dup-key", user_id="test_user")

    def test_verify_valid_key(self, manager):
        """Test verifying a valid API key."""
        api_key = manager.create_key(name="valid-key", user_id="test_user")

        # Verify should return user_id
        user_id = manager.verify_key(api_key)
        assert user_id == "test_user"

    def test_verify_invalid_key(self, manager):
        """Test verifying an invalid API key."""
        user_id = manager.verify_key("kagura_invalid_key")
        assert user_id is None

    def test_verify_revoked_key(self, manager):
        """Test that revoked keys cannot be verified."""
        api_key = manager.create_key(name="revoke-test", user_id="test_user")

        # Revoke the key
        success = manager.revoke_key(name="revoke-test", user_id="test_user")
        assert success is True

        # Verify should fail
        user_id = manager.verify_key(api_key)
        assert user_id is None

    def test_list_keys(self, manager):
        """Test listing API keys."""
        # Create some keys
        manager.create_key(name="key1", user_id="user1")
        manager.create_key(name="key2", user_id="user1")
        manager.create_key(name="key3", user_id="user2")

        # List all keys
        all_keys = manager.list_keys()
        assert len(all_keys) == 3

        # List keys for user1
        user1_keys = manager.list_keys(user_id="user1")
        assert len(user1_keys) == 2
        assert all(k["user_id"] == "user1" for k in user1_keys)

    def test_revoke_key(self, manager):
        """Test revoking an API key."""
        manager.create_key(name="to-revoke", user_id="test_user")

        # Revoke
        success = manager.revoke_key(name="to-revoke", user_id="test_user")
        assert success is True

        # Check status
        keys = manager.list_keys(user_id="test_user")
        assert len(keys) == 1
        assert keys[0]["revoked_at"] is not None

    def test_revoke_nonexistent_key(self, manager):
        """Test revoking a non-existent key."""
        success = manager.revoke_key(name="nonexistent", user_id="test_user")
        assert success is False

    def test_delete_key(self, manager):
        """Test permanently deleting an API key."""
        manager.create_key(name="to-delete", user_id="test_user")

        # Delete
        success = manager.delete_key(name="to-delete", user_id="test_user")
        assert success is True

        # Check it's gone
        keys = manager.list_keys(user_id="test_user")
        assert len(keys) == 0

    def test_delete_nonexistent_key(self, manager):
        """Test deleting a non-existent key."""
        success = manager.delete_key(name="nonexistent", user_id="test_user")
        assert success is False

    def test_last_used_at_updated(self, manager):
        """Test that last_used_at is updated on verification."""
        api_key = manager.create_key(name="usage-test", user_id="test_user")

        # Check initial state
        keys = manager.list_keys(user_id="test_user")
        assert keys[0]["last_used_at"] is None

        # Verify key
        manager.verify_key(api_key)

        # Check last_used_at is now set
        keys = manager.list_keys(user_id="test_user")
        assert keys[0]["last_used_at"] is not None

    def test_expired_key_fails_verification(self, manager):
        """Test that expired keys cannot be verified."""
        from datetime import datetime, timedelta

        api_key = manager.create_key(
            name="expired-key",
            user_id="test_user",
            expires_days=-1,  # Already expired
        )

        # Verification should fail
        user_id = manager.verify_key(api_key)
        assert user_id is None


class TestAPIKeyHashing:
    """Test API key hashing security."""

    def test_keys_are_hashed(self, tmp_path):
        """Test that API keys are hashed, not stored in plaintext."""
        import sqlite3

        manager = APIKeyManager(db_path=tmp_path / "test.db")
        api_key = manager.create_key(name="hash-test", user_id="test_user")

        # Query database directly
        with sqlite3.connect(manager.db_path) as conn:
            cursor = conn.execute("SELECT key_hash FROM api_keys WHERE name = ?", ("hash-test",))
            row = cursor.fetchone()

        # Hash should not match the plaintext key
        assert row[0] != api_key

        # Hash should be 64 chars (SHA256 hex)
        assert len(row[0]) == 64

    def test_different_keys_have_different_hashes(self, tmp_path):
        """Test that different keys produce different hashes."""
        manager = APIKeyManager(db_path=tmp_path / "test.db")

        key1 = manager.create_key(name="key1", user_id="test_user")
        key2 = manager.create_key(name="key2", user_id="test_user")

        # Keys should be different
        assert key1 != key2

        # Hashes should be different
        hash1 = manager._hash_key(key1)
        hash2 = manager._hash_key(key2)
        assert hash1 != hash2
