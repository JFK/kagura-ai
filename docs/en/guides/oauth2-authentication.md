# OAuth2 Authentication Guide

Learn how to use OAuth2 authentication with Kagura AI to access Google models (like Gemini) without managing API keys.

> **📌 Important Note**
>
> **For most users, using API Keys is recommended** as it's simpler and faster to set up:
> - **Gemini**: Get API key from [Google AI Studio](https://aistudio.google.com/app/apikey) → Set `GOOGLE_API_KEY`
> - **Claude**: Get API key from [Anthropic Console](https://console.anthropic.com/) → Set `ANTHROPIC_API_KEY`
> - **OpenAI**: Get API key from [OpenAI Platform](https://platform.openai.com/api-keys) → Set `OPENAI_API_KEY`
>
> **OAuth2 is an advanced feature** for specific use cases like:
> - Multi-user applications where each user authenticates with their own Google account
> - Production environments requiring strict access controls
> - Applications that need per-user quota management
>
> Currently, **only Google/Gemini supports OAuth2**. Claude and OpenAI use API keys only.

## Overview

Kagura AI supports OAuth2 authentication for **Google services only**, allowing you to:

- **No API Key Management**: Use Google models without storing API keys
- **Secure Authentication**: OAuth2 tokens are encrypted locally (Fernet/AES-128)
- **Automatic Token Refresh**: Tokens are automatically refreshed when expired
- **Simple CLI Commands**: Easy login/logout/status management

## Prerequisites

1. **Google Cloud Project** with Generative Language API enabled
2. **OAuth 2.0 Client ID** (Desktop application type)
3. **Kagura AI with OAuth support** installed:

```bash
pip install kagura-ai[oauth]
```

## Setup Guide

### Step 1: Create OAuth 2.0 Client ID

1. Go to [Google Cloud Console - Credentials](https://console.cloud.google.com/apis/credentials)
2. Click **"Create Credentials"** → **"OAuth client ID"**
3. Select **"Desktop app"** as the application type
4. Name it (e.g., "Kagura AI Desktop")
5. Click **"Create"**
6. Download the JSON file

### Step 2: Save Client Secrets

Save the downloaded JSON file as `~/.kagura/client_secrets.json`:

```bash
mkdir -p ~/.kagura
mv ~/Downloads/client_secret_*.json ~/.kagura/client_secrets.json
chmod 600 ~/.kagura/client_secrets.json
```

**Important**: Keep this file secure! It contains your OAuth client credentials.

### Step 3: Login

Run the `kagura auth login` command:

```bash
kagura auth login --provider google
```

This will:
1. Open your browser for Google OAuth2 authentication
2. Ask you to authorize Kagura AI to access Google Generative Language API
3. Save encrypted credentials to `~/.kagura/credentials.json.enc`

**Output:**
```
✓ Authentication successful!
✓ Credentials saved to: /home/user/.kagura/credentials.json.enc
```

### Step 4: Verify Authentication

Check your authentication status:

```bash
kagura auth status --provider google
```

**Output:**
```
✓ Authenticated with google
Token expires: 2025-10-13 15:30:00 UTC
```

## Using OAuth2 in Your Code

### Basic Usage with LLMConfig

```python
from kagura.core.llm import LLMConfig, call_llm

# Configure OAuth2 authentication
config = LLMConfig(
    model="gemini/gemini-1.5-flash",
    auth_type="oauth2",
    oauth_provider="google"
)

# Call LLM (OAuth2 token retrieved automatically)
response = await call_llm("What is the capital of France?", config)
print(response)  # "The capital of France is Paris."
```

### Using with @agent Decorator

```python
from kagura import agent
from kagura.core.llm import LLMConfig

# Create OAuth2 config
gemini_config = LLMConfig(
    model="gemini/gemini-1.5-flash",
    auth_type="oauth2",
    oauth_provider="google",
    temperature=0.7
)

@agent(
    name="translator",
    template="Translate '{{ text }}' to {{ language }}",
    llm_config=gemini_config
)
def translate(text: str, language: str) -> str:
    pass

# Use the agent
result = translate("Hello", "Japanese")
print(result)  # "こんにちは"
```

### Switching Between API Key and OAuth2

You can use both authentication methods in the same project:

```python
from kagura.core.llm import LLMConfig

# OpenAI with API key (uses OPENAI_API_KEY env var)
openai_config = LLMConfig(
    model="gpt-4o-mini",
    auth_type="api_key"  # default
)

# Gemini with OAuth2
gemini_config = LLMConfig(
    model="gemini/gemini-1.5-flash",
    auth_type="oauth2",
    oauth_provider="google"
)
```

## CLI Commands

### Login

Authenticate with Google OAuth2:

```bash
kagura auth login --provider google
```

**Options:**
- `--provider`: OAuth2 provider (default: `google`)

### Logout

Remove stored credentials:

```bash
kagura auth logout --provider google
```

**Output:**
```
✓ Logged out from google
```

### Status

Check authentication status:

```bash
kagura auth status --provider google
```

**Possible outputs:**

**Authenticated:**
```
✓ Authenticated with google
Token expires: 2025-10-13 15:30:00 UTC
```

**Not Authenticated:**
```
✗ Not authenticated with google
Run: kagura auth login --provider google
```

## Security

### Credential Storage

OAuth2 credentials are stored securely:

- **Location**: `~/.kagura/credentials.json.enc`
- **Encryption**: Fernet (AES-128 in CBC mode)
- **Key Storage**: `~/.kagura/.key` (with 0600 permissions)
- **File Permissions**: Both files have 0600 (owner read/write only)

### Token Refresh

Access tokens are automatically refreshed:

1. **Automatic**: Tokens are checked before each API call
2. **Transparent**: Refresh happens automatically when expired
3. **Secure**: Refresh tokens are encrypted and stored locally

### Best Practices

1. **Never commit** `~/.kagura/` directory to version control
2. **Keep `client_secrets.json` secure** - it's like a password
3. **Don't share** your `credentials.json.enc` file
4. **Logout** when you're done on shared machines
5. **Regenerate** OAuth client ID if credentials are compromised

## Troubleshooting

### "Client secrets file not found"

**Error:**
```
FileNotFoundError: Client secrets file not found: /home/user/.kagura/client_secrets.json
```

**Solution:**
1. Download OAuth 2.0 Client ID JSON from Google Cloud Console
2. Save it as `~/.kagura/client_secrets.json`

### "Not authenticated with google"

**Error:**
```
NotAuthenticatedError: Not authenticated with google. Please run: kagura auth login --provider google
```

**Solution:**
Run `kagura auth login --provider google` to authenticate.

### "Token refresh failed"

**Error:**
```
TokenRefreshError: Failed to refresh token for google
```

**Solution:**
1. Logout: `kagura auth logout --provider google`
2. Login again: `kagura auth login --provider google`

### "Invalid credentials"

**Error:**
```
InvalidCredentialsError: Failed to decrypt credentials
```

**Possible causes:**
- Corrupted credentials file
- Encryption key was regenerated

**Solution:**
1. Remove credentials: `rm ~/.kagura/credentials.json.enc`
2. Login again: `kagura auth login --provider google`

## Environment Variables

OAuth2 authentication does NOT use environment variables. All authentication is handled through the OAuth2 flow and stored encrypted credentials.

If you prefer to use API keys instead:

```bash
# For Gemini (using API key)
export GOOGLE_API_KEY="your-api-key"

# Then use api_key auth type (default)
config = LLMConfig(model="gemini/gemini-1.5-flash")
```

## Comparison: OAuth2 vs API Key

| Feature | OAuth2 | API Key |
|---------|--------|---------|
| **Supported LLMs** | Google/Gemini only | All LLMs (OpenAI, Claude, Gemini) |
| **Setup Complexity** | Complex (Google Cloud Console setup required) | Simple (just get API key) |
| **Security** | OAuth2 tokens (short-lived, auto-refresh) | Long-lived API keys |
| **Use Case** | Multi-user apps, production with strict access control | Personal development, prototyping, CI/CD |
| **Recommended For** | Advanced users with specific needs | **Most users (recommended)** |
| **Expiration** | Auto-refresh | Manual rotation |
| **Revocation** | Can revoke from Google Console | Delete/regenerate key |

### When to Use API Key (Recommended)

✅ **Use API Key if:**
- You're doing personal development or prototyping
- You want quick and simple setup
- You're using Claude or OpenAI (OAuth2 not supported)
- You're running in CI/CD pipelines
- You're building single-user applications

**How to get API Keys:**
- **Gemini**: [Google AI Studio](https://aistudio.google.com/app/apikey) (fastest way!)
- **Claude**: [Anthropic Console](https://console.anthropic.com/account/keys)
- **OpenAI**: [OpenAI Platform](https://platform.openai.com/api-keys)

### When to Use OAuth2 (Advanced)

⚠️ **Use OAuth2 only if:**
- You're building a multi-user application
- Each user needs their own Google account authentication
- You need strict per-user quota management
- You have specific security requirements
- You're comfortable with Google Cloud Console setup

**Note**: OAuth2 is only available for Google/Gemini.

## Advanced Configuration

### Custom Client Secrets Path

If you want to store `client_secrets.json` in a custom location:

```python
from kagura.auth import OAuth2Manager, AuthConfig
from pathlib import Path

# Custom config
config = AuthConfig(
    provider="google",
    client_secrets_path=Path("/custom/path/client_secrets.json")
)

# Use custom config
auth = OAuth2Manager(config=config)
auth.login()
```

### Custom Scopes

The default scopes are:
- `https://www.googleapis.com/auth/generative-language`
- `openid`

To use custom scopes:

```python
from kagura.auth import OAuth2Manager, AuthConfig

config = AuthConfig(
    provider="google",
    scopes=[
        "https://www.googleapis.com/auth/generative-language",
        "openid",
        "https://www.googleapis.com/auth/userinfo.email"
    ]
)

auth = OAuth2Manager(config=config)
```

## Next Steps

- Learn about [Agent Routing](agent-routing.md)
- Explore [Memory Management](../tutorials/08-memory-management.md)
- Try [MCP Integration](../tutorials/06-mcp-integration.md)

## Related Documentation

- [API Reference: OAuth2Manager](../api/auth.md)
- [Installation Guide](../installation.md)
- [Quickstart Tutorial](../quickstart.md)
