# ChatGPT MCP Integration Guide

**Issue #674** - OAuth2 authentication support for ChatGPT MCP integration

This guide explains how to connect ChatGPT to Kagura AI's MCP server using OAuth2 authentication.

---

## Prerequisites

- ✅ Kagura AI v4.4.0+ deployed (with OAuth2 support)
- ✅ PostgreSQL database initialized with OAuth2 tables
- ✅ ChatGPT Plus or Team account
- ✅ HTTPS endpoint (required for OAuth2)

---

## Overview

**Kagura AI v4.4.0** supports **dual authentication**:

| Client | Auth Method | Endpoint |
|--------|-------------|----------|
| **ChatGPT** | OAuth2 (Authorization Code + PKCE) | `/mcp/sse` |
| **Claude Code** | API Key (Bearer token) | `/mcp/sse` |

Both clients use the **same MCP server endpoint**, but with different authentication mechanisms.

---

## Step 1: Database Migration

Run the OAuth2 migration to create required tables:

```bash
# Navigate to migrations directory
cd src/kagura/auth/migrations/

# Run migration (PostgreSQL)
psql -U your_user -d kagura_db -f 003_oauth_server.sql

# Verify tables created
psql -U your_user -d kagura_db -c "\dt oauth*"
```

**Expected output:**
```
                List of relations
 Schema |           Name            | Type  |  Owner
--------+---------------------------+-------+----------
 public | oauth_authorization_codes | table | your_user
 public | oauth_clients             | table | your_user
 public | oauth_tokens              | table | your_user
(3 rows)
```

---

## Step 2: Register OAuth2 Client

Register ChatGPT as an OAuth2 client in your database:

```sql
-- Insert ChatGPT client
INSERT INTO oauth_clients (
    client_id,
    client_secret_hash,
    client_name,
    redirect_uris,
    grant_types,
    response_types,
    scope,
    token_endpoint_auth_method
) VALUES (
    'chatgpt-connector',
    -- SHA256 hash of your secret (replace with actual hash)
    encode(digest('YOUR_SECRET_HERE', 'sha256'), 'hex'),
    'ChatGPT Connector',
    '["https://chat.openai.com/oauth/callback"]'::jsonb,
    '["authorization_code", "refresh_token"]'::jsonb,
    '["code"]'::jsonb,
    'mcp:tools mcp:memory mcp:coding',
    'client_secret_post'
);
```

**Important:**
- Replace `YOUR_SECRET_HERE` with a strong random secret:
  ```bash
  openssl rand -base64 32
  ```
- Save the **plaintext secret** securely (you'll need it for ChatGPT setup)

**Verify client created:**
```sql
SELECT client_id, client_name, scope FROM oauth_clients;
```

---

## Step 3: Configure ChatGPT Connector

### 3.1 Enable Developer Mode

1. Open **ChatGPT** → Settings → Connectors
2. Scroll to **Advanced** → Enable **Developer Mode**
3. Click **Add Custom Connector**

### 3.2 Connector Configuration

Fill in the following details:

| Field | Value |
|-------|-------|
| **Name** | Kagura Memory |
| **Base URL** | `https://memory.kagura-ai.com` |
| **Description** | Universal AI Memory Platform for ChatGPT |
| **Logo** | (Optional) Upload Kagura logo |

### 3.3 OAuth2 Configuration

| Field | Value |
|-------|-------|
| **OAuth2 Client ID** | `chatgpt-connector` |
| **OAuth2 Client Secret** | `YOUR_SECRET_HERE` (from Step 2) |
| **Authorization Endpoint** | `https://memory.kagura-ai.com/api/v1/oauth/authorize` |
| **Token Endpoint** | `https://memory.kagura-ai.com/api/v1/oauth/token` |
| **Scopes** | `mcp:tools mcp:memory mcp:coding` |
| **Token Auth Method** | `client_secret_post` |

### 3.4 MCP Endpoint

| Field | Value |
|-------|-------|
| **MCP Endpoint** | `https://memory.kagura-ai.com/api/v1/mcp/sse` |
| **Transport** | `SSE (Server-Sent Events)` |

### 3.5 Save and Test

1. Click **Save Connector**
2. ChatGPT will redirect you to Kagura's **Authorization Page**
3. Log in to Kagura (if not already logged in)
4. Click **Approve** to grant ChatGPT access
5. You'll be redirected back to ChatGPT with confirmation

---

## Step 4: Test MCP Connection

### 4.1 Verify in ChatGPT

Open a new ChatGPT conversation and try:

```
@KaguraMemory What tools are available?
```

**Expected response:**
```
I have access to the following Kagura Memory tools:
- memory_store: Store information in persistent memory
- memory_recall: Retrieve stored memories
- memory_search: Search memories semantically
- coding_start_session: Start a coding session
- [... 30+ more tools]
```

### 4.2 Test Memory Storage

```
@KaguraMemory Store the fact that my favorite color is blue
```

**Expected response:**
```
✅ Memory stored successfully:
- Key: favorite_color
- Value: blue
- User: {your_user_id}
```

### 4.3 Test Memory Recall

```
@KaguraMemory What is my favorite color?
```

**Expected response:**
```
Your favorite color is blue (retrieved from persistent memory).
```

---

## Troubleshooting

### Problem: "Invalid client_id" error

**Solution:**
- Verify client_id in database matches ChatGPT configuration
- Check `oauth_clients` table:
  ```sql
  SELECT * FROM oauth_clients WHERE client_id = 'chatgpt-connector';
  ```

### Problem: "Invalid client_secret" error

**Solution:**
- Regenerate secret and update both database and ChatGPT:
  ```bash
  # Generate new secret
  SECRET=$(openssl rand -base64 32)
  echo "Secret: $SECRET"

  # Hash for database
  echo -n "$SECRET" | sha256sum

  # Update database
  UPDATE oauth_clients
  SET client_secret_hash = 'NEW_HASH_HERE'
  WHERE client_id = 'chatgpt-connector';
  ```

### Problem: "Authorization timeout" error

**Solution:**
- Check that `/oauth/authorize` endpoint is accessible:
  ```bash
  curl -I https://memory.kagura-ai.com/api/v1/oauth/authorize
  ```
- Ensure HTTPS is properly configured (OAuth2 requires HTTPS)

### Problem: "Token expired" error

**Solution:**
- Tokens expire after 1 hour by default
- ChatGPT should auto-refresh using refresh token
- If persistent issue, revoke and re-authorize:
  ```sql
  -- Revoke old tokens
  UPDATE oauth_tokens
  SET revoked = true, access_token_revoked_at = NOW()
  WHERE client_id = 'chatgpt-connector' AND user_id = '{your_user_id}';
  ```

### Problem: "MCP connection failed" error

**Solution:**
1. Check MCP endpoint is accessible:
   ```bash
   curl -I https://memory.kagura-ai.com/api/v1/mcp/sse
   ```

2. Verify Bearer token authentication:
   ```bash
   curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
        https://memory.kagura-ai.com/api/v1/mcp/sse
   ```

3. Check server logs:
   ```bash
   docker-compose logs -f kagura-api | grep -i oauth
   ```

---

## Advanced Configuration

### Custom Token Expiration

Update token lifetime in database:

```sql
-- Set tokens to expire after 8 hours (28800 seconds)
UPDATE oauth_tokens
SET expires_in = 28800
WHERE client_id = 'chatgpt-connector';
```

### Limit Scopes

Restrict ChatGPT's access by modifying scopes:

```sql
-- Only allow memory tools (no coding tools)
UPDATE oauth_clients
SET scope = 'mcp:memory'
WHERE client_id = 'chatgpt-connector';
```

**Available scopes:**
- `mcp:tools` - All MCP tools
- `mcp:memory` - Memory storage/recall/search only
- `mcp:coding` - Coding session management only
- `mcp:graph` - Knowledge graph access
- `mcp:web` - Web scraping tools

### PKCE for Public Clients

ChatGPT mobile apps use PKCE (no client_secret). To support:

```sql
-- Update client to allow PKCE
UPDATE oauth_clients
SET token_endpoint_auth_method = 'none'
WHERE client_id = 'chatgpt-mobile';
```

---

## Security Considerations

### Client Secret Storage

- **NEVER** commit client secrets to version control
- Store in environment variables:
  ```bash
  export CHATGPT_CLIENT_SECRET="your_secret_here"
  ```

### Token Rotation

- Access tokens expire after 1 hour
- Refresh tokens are long-lived but can be revoked
- Revoke tokens on security incidents:
  ```sql
  UPDATE oauth_tokens
  SET revoked = true
  WHERE client_id = 'chatgpt-connector';
  ```

### Audit Logging

- All OAuth2 events are logged in `audit_logs` table
- Monitor for suspicious activity:
  ```sql
  SELECT * FROM audit_logs
  WHERE action LIKE 'oauth%'
  ORDER BY created_at DESC
  LIMIT 50;
  ```

---

## API Reference

### OAuth2 Endpoints

#### Authorization Endpoint

```
GET /api/v1/oauth/authorize
```

**Parameters:**
- `client_id` (required): OAuth2 client identifier
- `redirect_uri` (required): Callback URL
- `response_type` (required): Must be `code`
- `scope` (optional): Requested permissions
- `state` (recommended): CSRF protection token
- `code_challenge` (optional): PKCE challenge
- `code_challenge_method` (optional): `S256` or `plain`

**Response:**
- HTML consent screen (if user not authenticated)
- Redirect to `redirect_uri?code={auth_code}&state={state}` (if approved)
- Redirect to `redirect_uri?error=access_denied` (if denied)

#### Token Endpoint

```
POST /api/v1/oauth/token
```

**Parameters (Authorization Code Grant):**
- `grant_type=authorization_code` (required)
- `code` (required): Authorization code from `/authorize`
- `redirect_uri` (required): Same as authorization request
- `client_id` (required)
- `client_secret` (required for confidential clients)
- `code_verifier` (required if PKCE used)

**Response:**
```json
{
  "access_token": "...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "...",
  "scope": "mcp:tools mcp:memory mcp:coding"
}
```

**Parameters (Refresh Token Grant):**
- `grant_type=refresh_token` (required)
- `refresh_token` (required)
- `client_id` (required)
- `client_secret` (required for confidential clients)

---

## Next Steps

- **Issue #651**: Web UI for OAuth client management
- **Issue #675**: ChatGPT custom actions integration
- **Future**: Support for other AI platforms (Gemini, Claude Desktop)

---

## Related Documentation

- [MCP Setup Guide](./mcp-setup.md) - General MCP configuration
- [API Key Management](./api-keys.md) - Alternative authentication for Claude Code
- [Security Best Practices](./security.md) - Securing your Kagura deployment

---

**Feedback?** Please report issues at [GitHub Issues](https://github.com/JFK/kagura-ai/issues/674)
