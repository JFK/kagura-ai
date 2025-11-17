-- Kagura Memory Cloud - External API Keys Table Migration
-- Issues #690, #692: External API Keys Management with Encryption
--
-- Creates external_api_keys table for storing external service API keys with:
-- - Fernet symmetric encryption (two-way, can decrypt for usage)
-- - Provider categorization (OpenAI, Anthropic, Google, etc.)
-- - Admin-only CRUD operations
-- - Audit trail (updated_by, updated_at)
--
-- Security:
-- - Values encrypted with API_KEY_SECRET (Fernet)
-- - Plaintext never stored or logged
-- - Only admin users can read/write
-- - Migration from .env.cloud on first run

-- ============================================================================
-- External API Keys Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS external_api_keys (
    id SERIAL PRIMARY KEY,

    -- API Key Identity
    key_name VARCHAR(100) NOT NULL UNIQUE,   -- e.g., "OPENAI_API_KEY", "ANTHROPIC_API_KEY"
    provider VARCHAR(50) NOT NULL,           -- e.g., "openai", "anthropic", "google"

    -- Encrypted Value (Fernet)
    encrypted_value TEXT NOT NULL,           -- Base64-encoded encrypted API key

    -- Audit Trail
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_by VARCHAR(255)                  -- Email of admin who last updated
);

-- Indexes for performance
CREATE INDEX idx_external_api_keys_provider ON external_api_keys(provider);
CREATE INDEX idx_external_api_keys_updated ON external_api_keys(updated_at DESC);

-- ============================================================================
-- Comments
-- ============================================================================
COMMENT ON TABLE external_api_keys IS 'External service API keys (OpenAI, Anthropic, etc.) with Fernet encryption';
COMMENT ON COLUMN external_api_keys.key_name IS 'Unique key identifier matching environment variable name (e.g., OPENAI_API_KEY)';
COMMENT ON COLUMN external_api_keys.provider IS 'Service provider identifier (openai, anthropic, google, brave, cohere, voyage, jina)';
COMMENT ON COLUMN external_api_keys.encrypted_value IS 'Fernet-encrypted API key value (decrypt with API_KEY_SECRET)';
COMMENT ON COLUMN external_api_keys.updated_by IS 'Email of admin user who last modified this key';

-- ============================================================================
-- Security Notes
-- ============================================================================
-- 1. Encrypted with Fernet symmetric encryption (AES-128-CBC + HMAC)
-- 2. Encryption key: API_KEY_SECRET environment variable (32-byte secret)
-- 3. Decryption only happens when key is used (e.g., calling OpenAI API)
-- 4. Plaintext NEVER logged or stored anywhere
-- 5. Admin role required for all CRUD operations
-- 6. Audit trail maintained (updated_by, updated_at)
--
-- ============================================================================
-- Migration from .env.cloud
-- ============================================================================
-- Use `python scripts/migrate_external_keys.py` to:
-- 1. Read API keys from .env.cloud file
-- 2. Encrypt with API_KEY_SECRET
-- 3. Insert into external_api_keys table
-- 4. Optional: Add warning comment to .env.cloud
--
-- Keys to migrate:
-- - OPENAI_API_KEY
-- - ANTHROPIC_API_KEY
-- - GOOGLE_API_KEY / GEMINI_API_KEY
-- - BRAVE_SEARCH_API_KEY
-- - COHERE_API_KEY (for reranking)
-- - VOYAGE_API_KEY (for reranking)
-- - JINA_API_KEY (for reranking)
--
-- ============================================================================
-- Key Rotation Procedure
-- ============================================================================
-- If API_KEY_SECRET needs to be changed:
-- 1. Decrypt all values with old secret
-- 2. Re-encrypt with new secret
-- 3. Update encrypted_value column
-- 4. Use `python scripts/rotate_encryption_key.py --old OLD_SECRET --new NEW_SECRET`
