-- Kagura Memory Cloud - API Keys Table Migration
-- Issue #655: API Key Management Page with CRUD Operations
--
-- Creates api_keys table for programmatic API access with:
-- - Secure SHA256 hashing (plaintext never stored)
-- - Optional expiration
-- - Revocation support
-- - Usage tracking

-- ============================================================================
-- API Keys Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,

    -- API Key Data
    key_hash VARCHAR(64) NOT NULL UNIQUE,    -- SHA256 hash for verification
    key_prefix VARCHAR(16) NOT NULL,         -- First 16 chars (for display only)
    name VARCHAR(100) NOT NULL,              -- Friendly name
    user_id VARCHAR(255) NOT NULL,           -- Owner (OAuth2 sub)

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_used_at TIMESTAMP,                  -- Last successful usage
    revoked_at TIMESTAMP,                    -- NULL = active, NOT NULL = revoked
    expires_at TIMESTAMP                     -- NULL = no expiration
);

-- Indexes for performance
CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_api_keys_user_name ON api_keys(user_id, name);
CREATE INDEX idx_api_keys_revoked ON api_keys(revoked_at);
CREATE INDEX idx_api_keys_expires ON api_keys(expires_at);

-- ============================================================================
-- Comments
-- ============================================================================
COMMENT ON TABLE api_keys IS 'API keys for programmatic access with expiration and revocation support';
COMMENT ON COLUMN api_keys.key_hash IS 'SHA256 hash of API key (plaintext NEVER stored for security)';
COMMENT ON COLUMN api_keys.key_prefix IS 'First 16 characters for display (e.g., kagura_abc123...)';
COMMENT ON COLUMN api_keys.name IS 'User-friendly name to identify the key (e.g., "Production Server", "CI/CD Pipeline")';
COMMENT ON COLUMN api_keys.user_id IS 'Owner user_id (OAuth2 sub claim from users table)';
COMMENT ON COLUMN api_keys.revoked_at IS 'Revocation timestamp - NULL means active, NOT NULL means revoked';
COMMENT ON COLUMN api_keys.expires_at IS 'Expiration timestamp - NULL means no expiration';

-- ============================================================================
-- Security Notes
-- ============================================================================
-- 1. Plaintext API key is ONLY shown once during creation
-- 2. After creation, only key_prefix is displayed for identification
-- 3. Usage statistics are tracked separately in Redis (TTL: 30 days)
-- 4. Revoked keys remain in database for audit trail (soft delete)
-- 5. Expired keys are checked during verification, not deleted

-- ============================================================================
-- Usage Statistics
-- ============================================================================
-- Note: Request counts and daily statistics are stored in Redis (not PostgreSQL)
-- for performance reasons. Redis keys format: apikey:stats:{key_hash}:{date}
-- TTL: 30 days (automatic cleanup)
