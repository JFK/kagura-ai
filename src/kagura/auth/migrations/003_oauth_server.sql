-- Kagura Memory Cloud - OAuth2 Server Migration
-- Issue #674: OAuth2 authentication support for ChatGPT MCP integration
--
-- Creates OAuth2 server tables for:
-- - oauth_clients: Registered OAuth2 clients (ChatGPT, etc.)
-- - oauth_authorization_codes: Short-lived authorization codes
-- - oauth_tokens: Access tokens and refresh tokens
--
-- Architecture:
--     Follows Authlib's SQLAlchemy integration pattern for OAuth2
--     authorization server with support for:
--     - Authorization Code Grant (RFC 6749)
--     - Refresh Token Grant (RFC 6749)
--     - PKCE Extension (RFC 7636)

-- ============================================================================
-- OAuth2 Clients Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS oauth_clients (
    id SERIAL PRIMARY KEY,

    -- Client Identity
    client_id VARCHAR(48) NOT NULL UNIQUE,           -- Public identifier
    client_secret_hash VARCHAR(64),                   -- SHA256 hash (confidential)
    client_name VARCHAR(100) NOT NULL,                -- Display name

    -- OAuth2 Configuration (JSON for flexibility)
    redirect_uris JSONB NOT NULL,                     -- ["https://example.com/callback"]
    grant_types JSONB NOT NULL DEFAULT '["authorization_code", "refresh_token"]'::jsonb,
    response_types JSONB NOT NULL DEFAULT '["code"]'::jsonb,
    scope VARCHAR(255) NOT NULL DEFAULT 'mcp:tools mcp:memory mcp:coding',
    token_endpoint_auth_method VARCHAR(50) NOT NULL DEFAULT 'client_secret_post',

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_oauth_clients_client_id ON oauth_clients(client_id);

-- ============================================================================
-- OAuth2 Authorization Codes Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS oauth_authorization_codes (
    id SERIAL PRIMARY KEY,

    -- Authorization Code Data
    code VARCHAR(120) NOT NULL UNIQUE,                -- Random code (single-use)
    client_id VARCHAR(48) NOT NULL,                   -- Client that requested
    user_id VARCHAR(255) NOT NULL,                    -- User who authorized

    -- OAuth2 Flow Data
    redirect_uri VARCHAR(512) NOT NULL,               -- Redirect URI used
    scope VARCHAR(255),                                -- Granted scope

    -- PKCE Support (RFC 7636 - for public clients)
    code_challenge VARCHAR(128),                       -- Base64-URL(SHA256(verifier))
    code_challenge_method VARCHAR(10),                 -- "S256" or "plain"

    -- Timestamps
    auth_time TIMESTAMP NOT NULL DEFAULT NOW(),        -- When user consented
    expires_at TIMESTAMP NOT NULL                      -- auth_time + 600s (10 min)
);

-- Indexes for performance
CREATE INDEX idx_oauth_codes_code ON oauth_authorization_codes(code);
CREATE INDEX idx_oauth_codes_client_id ON oauth_authorization_codes(client_id);
CREATE INDEX idx_oauth_codes_user_id ON oauth_authorization_codes(user_id);
CREATE INDEX idx_oauth_codes_client_user ON oauth_authorization_codes(client_id, user_id);
CREATE INDEX idx_oauth_codes_expires_at ON oauth_authorization_codes(expires_at);

-- ============================================================================
-- OAuth2 Tokens Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS oauth_tokens (
    id SERIAL PRIMARY KEY,

    -- Token Owner
    client_id VARCHAR(48) NOT NULL REFERENCES oauth_clients(client_id) ON DELETE CASCADE,
    user_id VARCHAR(255) NOT NULL,                    -- User who authorized

    -- Token Data
    token_type VARCHAR(20) NOT NULL DEFAULT 'Bearer',
    access_token VARCHAR(255) NOT NULL UNIQUE,        -- Random access token
    refresh_token VARCHAR(255) UNIQUE,                 -- Random refresh token (optional)
    scope VARCHAR(255),                                -- Granted scope

    -- Status
    revoked BOOLEAN NOT NULL DEFAULT FALSE,            -- Global revocation flag

    -- Timestamps
    issued_at TIMESTAMP NOT NULL DEFAULT NOW(),
    access_token_revoked_at TIMESTAMP,                 -- NULL = active
    refresh_token_revoked_at TIMESTAMP,                -- NULL = active

    -- Expiration
    expires_in INTEGER NOT NULL DEFAULT 3600           -- Access token lifetime (seconds)
);

-- Indexes for performance
CREATE INDEX idx_oauth_tokens_access_token ON oauth_tokens(access_token);
CREATE INDEX idx_oauth_tokens_refresh_token ON oauth_tokens(refresh_token);
CREATE INDEX idx_oauth_tokens_client_id ON oauth_tokens(client_id);
CREATE INDEX idx_oauth_tokens_user_id ON oauth_tokens(user_id);
CREATE INDEX idx_oauth_tokens_client_user ON oauth_tokens(client_id, user_id);
CREATE INDEX idx_oauth_tokens_revoked ON oauth_tokens(revoked);

-- ============================================================================
-- Comments
-- ============================================================================
COMMENT ON TABLE oauth_clients IS 'Registered OAuth2 clients (ChatGPT Connectors, etc.)';
COMMENT ON COLUMN oauth_clients.client_id IS 'OAuth2 client identifier (public, unique)';
COMMENT ON COLUMN oauth_clients.client_secret_hash IS 'SHA256 hash of client secret (confidential clients only)';
COMMENT ON COLUMN oauth_clients.redirect_uris IS 'Allowed callback URLs (JSON array)';
COMMENT ON COLUMN oauth_clients.grant_types IS 'Allowed grant types (JSON array: authorization_code, refresh_token)';
COMMENT ON COLUMN oauth_clients.token_endpoint_auth_method IS 'How client authenticates (client_secret_post, client_secret_basic, none)';

COMMENT ON TABLE oauth_authorization_codes IS 'Short-lived authorization codes (single-use, 10 min expiry)';
COMMENT ON COLUMN oauth_authorization_codes.code IS 'Random authorization code (use once then delete)';
COMMENT ON COLUMN oauth_authorization_codes.code_challenge IS 'PKCE code challenge (Base64-URL encoded SHA256 of verifier)';
COMMENT ON COLUMN oauth_authorization_codes.expires_at IS 'Code expiration (auth_time + 600s per RFC 6749)';

COMMENT ON TABLE oauth_tokens IS 'OAuth2 access tokens and refresh tokens';
COMMENT ON COLUMN oauth_tokens.access_token IS 'Bearer token for API access';
COMMENT ON COLUMN oauth_tokens.refresh_token IS 'Token for refreshing access tokens (optional)';
COMMENT ON COLUMN oauth_tokens.expires_in IS 'Access token lifetime in seconds (default: 3600 = 1 hour)';
COMMENT ON COLUMN oauth_tokens.revoked IS 'Global revocation flag (for immediate revocation)';

-- ============================================================================
-- Security Notes
-- ============================================================================
-- 1. Client secrets are SHA256 hashed (never stored in plaintext)
-- 2. Authorization codes expire after 10 minutes (RFC 6749 recommendation)
-- 3. Authorization codes are single-use (delete after token exchange)
-- 4. PKCE is supported for public clients (mobile apps, SPAs)
-- 5. Tokens can be revoked individually (access_token_revoked_at) or globally (revoked flag)
-- 6. Refresh tokens are optional (only for long-lived access)

-- ============================================================================
-- Usage Example (ChatGPT Connector Registration)
-- ============================================================================
-- INSERT INTO oauth_clients (client_id, client_secret_hash, client_name, redirect_uris, scope)
-- VALUES (
--     'chatgpt-connector',
--     SHA256('your_secret_here'),  -- Replace with actual hash
--     'ChatGPT Connector',
--     '["https://chat.openai.com/oauth/callback"]'::jsonb,
--     'mcp:tools mcp:memory mcp:coding'
-- );

-- ============================================================================
-- Cleanup Policy
-- ============================================================================
-- 1. Authorization codes: Delete after exchange OR after expiration (automated cleanup)
-- 2. Expired tokens: Keep for audit trail (soft delete with access_token_revoked_at)
-- 3. Revoked tokens: Keep for audit trail (do not hard delete)
