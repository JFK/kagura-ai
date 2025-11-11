-- Kagura Memory Cloud - Users Table Migration
-- Issue #650: OAuth2 Web Login & API Key Management
--
-- Creates users table for role-based access control.
-- First user to log in via OAuth2 is automatically assigned ADMIN role.

-- ============================================================================
-- Users Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,

    -- OAuth2 Identity
    email VARCHAR(255) NOT NULL UNIQUE,
    user_id VARCHAR(255) NOT NULL UNIQUE,  -- Google 'sub' claim
    name VARCHAR(255),                      -- Display name
    picture VARCHAR(512),                   -- Profile picture URL

    -- Role & Permissions
    role VARCHAR(50) NOT NULL DEFAULT 'user',  -- admin, user, read_only

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login_at TIMESTAMP,

    -- Constraints
    CONSTRAINT valid_role CHECK (role IN ('admin', 'user', 'read_only'))
);

-- Indexes for performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_user_id ON users(user_id);
CREATE INDEX idx_users_role ON users(role);

-- ============================================================================
-- Audit Logs Table (for configuration changes, role assignments, etc.)
-- ============================================================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,

    -- Who
    user_email VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,

    -- What
    action VARCHAR(100) NOT NULL,  -- e.g., 'config_update', 'role_assign', 'api_key_create'
    resource VARCHAR(255) NOT NULL,  -- e.g., 'OPENAI_API_KEY', 'user:user@example.com'

    -- Details
    old_value_hash VARCHAR(64),     -- SHA256 hash (not plaintext!)
    new_value_hash VARCHAR(64),     -- SHA256 hash
    metadata JSONB,                 -- Additional context

    -- Context
    ip_address INET,
    user_agent TEXT,

    -- Timestamp
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for audit queries
CREATE INDEX idx_audit_logs_user_email ON audit_logs(user_email);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);

-- ============================================================================
-- Comments
-- ============================================================================
COMMENT ON TABLE users IS 'Kagura Cloud users with OAuth2 authentication and role-based access control';
COMMENT ON COLUMN users.user_id IS 'Google OAuth2 sub claim (globally unique identifier)';
COMMENT ON COLUMN users.role IS 'Access control role: admin (full access), user (standard), read_only (view only)';

COMMENT ON TABLE audit_logs IS 'Audit trail for security-sensitive operations (config changes, role assignments, etc.)';
COMMENT ON COLUMN audit_logs.old_value_hash IS 'SHA256 hash of old value (NOT plaintext for security)';
COMMENT ON COLUMN audit_logs.new_value_hash IS 'SHA256 hash of new value (NOT plaintext for security)';

-- ============================================================================
-- First User Bootstrap
-- ============================================================================
-- Note: First user to complete OAuth2 login will be assigned ADMIN role
-- automatically by RoleManager.ensure_user() logic.
-- No manual intervention needed.
