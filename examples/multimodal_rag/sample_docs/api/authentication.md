# Authentication API

Sample Project supports two authentication methods: OAuth 2.0 and API Keys.

## OAuth 2.0 Authentication

### Authorization Code Flow

1. **Request Authorization**

   Redirect users to:
   ```
   GET /oauth/authorize
   ```

   Parameters:
   - `client_id` (required): Your application's client ID
   - `redirect_uri` (required): Callback URL
   - `scope` (required): Space-separated scopes (e.g., `read write`)
   - `state` (required): CSRF protection token

2. **Exchange Code for Token**

   ```http
   POST /oauth/token
   Content-Type: application/x-www-form-urlencoded

   grant_type=authorization_code&
   code=AUTHORIZATION_CODE&
   client_id=YOUR_CLIENT_ID&
   client_secret=YOUR_CLIENT_SECRET&
   redirect_uri=YOUR_REDIRECT_URI
   ```

   Response:
   ```json
   {
     "access_token": "eyJhbGciOiJIUzI1NiIs...",
     "token_type": "Bearer",
     "expires_in": 3600,
     "refresh_token": "def50200...",
     "scope": "read write"
   }
   ```

3. **Use Access Token**

   Include in Authorization header:
   ```http
   GET /api/v1/users/me
   Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
   ```

### Refresh Token Flow

When access token expires, use refresh token:

```http
POST /oauth/token
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token&
refresh_token=REFRESH_TOKEN&
client_id=YOUR_CLIENT_ID&
client_secret=YOUR_CLIENT_SECRET
```

## API Key Authentication

For server-to-server communication, use API keys.

### Generate API Key

```http
POST /api/v1/api-keys
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
  "name": "Production Server",
  "scopes": ["read", "write"],
  "expires_at": "2025-12-31T23:59:59Z"
}
```

Response:
```json
{
  "id": "key_abc123",
  "key": "sk_live_1234567890abcdef",
  "name": "Production Server",
  "scopes": ["read", "write"],
  "created_at": "2024-01-15T10:30:00Z",
  "expires_at": "2025-12-31T23:59:59Z"
}
```

**Important**: Save the `key` value securely. It's only shown once.

### Use API Key

Include in `X-API-Key` header:

```http
GET /api/v1/data
X-API-Key: sk_live_1234567890abcdef
```

## Security Best Practices

1. **Use HTTPS**: Always use HTTPS in production
2. **Rotate Keys**: Rotate API keys every 90 days
3. **Least Privilege**: Grant minimum necessary scopes
4. **Monitor Usage**: Track API key usage for anomalies
5. **Revoke Compromised Keys**: Immediately revoke if compromised

## Rate Limiting

All authenticated requests are rate-limited:

- OAuth: 1000 requests/hour per user
- API Keys: 5000 requests/hour per key

Rate limit headers:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642262400
```

When rate limit exceeded:
```http
HTTP/1.1 429 Too Many Requests
Retry-After: 3600

{
  "error": "rate_limit_exceeded",
  "message": "Rate limit exceeded. Try again in 3600 seconds."
}
```

## Error Responses

Authentication errors follow this format:

```json
{
  "error": "invalid_token",
  "error_description": "The access token expired",
  "error_uri": "https://docs.sample-project.com/errors#invalid_token"
}
```

Common error codes:
- `invalid_request`: Malformed request
- `invalid_client`: Invalid client credentials
- `invalid_grant`: Invalid authorization code
- `unauthorized_client`: Client not authorized
- `unsupported_grant_type`: Grant type not supported
- `invalid_scope`: Requested scope invalid

## Testing

Use sandbox environment for testing:

Base URL: `https://sandbox.sample-project.com`

Test credentials:
- Client ID: `test_client_123`
- Client Secret: `test_secret_456`
- Test user: `test@example.com` / `password123`

Sandbox API keys are prefixed with `sk_test_`.
