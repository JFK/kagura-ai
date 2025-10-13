# Authentication API Reference

API reference for Kagura AI's OAuth2 authentication system.

## OAuth2Manager

Main class for managing OAuth2 authentication with Google services.

### Class Definition

```python
from kagura.auth import OAuth2Manager

class OAuth2Manager:
    """OAuth2 authentication manager for Google services

    Handles OAuth2 authentication flow, token management, and secure credential storage.

    Args:
        provider: OAuth2 provider name (default: "google")
        config: Optional AuthConfig instance

    Example:
        >>> auth = OAuth2Manager(provider="google")
        >>> auth.login()  # Opens browser for authentication
        >>> creds = auth.get_credentials()  # Returns valid credentials
        >>> token = auth.get_token()  # Returns access token

    Security:
        - Credentials are encrypted using Fernet (AES-128)
        - Encryption key stored separately with 0o600 permissions
        - Credentials file has 0o600 permissions
        - Automatic token refresh when expired
    """
```

### Methods

#### `__init__(provider="google", config=None)`

Initialize OAuth2 manager.

**Parameters:**
- `provider` (str): OAuth2 provider name (default: "google")
- `config` (AuthConfig | None): Optional authentication configuration

**Example:**
```python
auth = OAuth2Manager(provider="google")
```

#### `login()`

Launch browser for OAuth2 authentication.

**Raises:**
- `FileNotFoundError`: If client_secrets.json not found
- `InvalidCredentialsError`: If authentication fails

**Example:**
```python
auth = OAuth2Manager()
auth.login()  # Opens browser, saves credentials
```

#### `logout()`

Remove stored credentials.

**Raises:**
- `NotAuthenticatedError`: If not authenticated

**Example:**
```python
auth = OAuth2Manager()
auth.logout()  # Removes ~/.kagura/credentials.json.enc
```

#### `is_authenticated() -> bool`

Check if user is authenticated.

**Returns:**
- `bool`: True if valid credentials exist

**Example:**
```python
auth = OAuth2Manager()
if auth.is_authenticated():
    print("Already logged in")
else:
    auth.login()
```

#### `get_credentials() -> Credentials`

Get valid credentials with automatic refresh.

**Returns:**
- `google.oauth2.credentials.Credentials`: Valid Google OAuth2 credentials

**Raises:**
- `NotAuthenticatedError`: If not authenticated
- `TokenRefreshError`: If token refresh fails

**Example:**
```python
auth = OAuth2Manager()
creds = auth.get_credentials()
print(creds.token)  # Access token
```

#### `get_token() -> str`

Get access token for API calls.

**Returns:**
- `str`: Access token string

**Raises:**
- `NotAuthenticatedError`: If not authenticated
- `TokenRefreshError`: If token refresh fails

**Example:**
```python
auth = OAuth2Manager()
token = auth.get_token()
# Use token in API calls
```

### Attributes

#### `SCOPES`

Default OAuth2 scopes for each provider.

```python
SCOPES = {
    "google": [
        "https://www.googleapis.com/auth/generative-language",
        "openid",
    ]
}
```

---

## AuthConfig

Configuration for OAuth2 authentication.

### Class Definition

```python
from kagura.auth import AuthConfig
from pathlib import Path

class AuthConfig(BaseModel):
    """OAuth2 authentication configuration

    Configuration for OAuth2 authentication manager.

    Args:
        provider: OAuth2 provider name (e.g., "google")
        scopes: Optional list of OAuth2 scopes
        client_secrets_path: Optional path to client_secrets.json

    Example:
        >>> config = AuthConfig(
        ...     provider="google",
        ...     client_secrets_path=Path("/custom/path/client_secrets.json")
        ... )
        >>> auth = OAuth2Manager(config=config)
    """
```

### Fields

#### `provider: str = "google"`

OAuth2 provider name.

**Default:** `"google"`

**Example:**
```python
config = AuthConfig(provider="google")
```

#### `scopes: list[str] | None = None`

Custom OAuth2 scopes. If None, uses default scopes from `OAuth2Manager.SCOPES`.

**Default:** `None`

**Example:**
```python
config = AuthConfig(
    provider="google",
    scopes=[
        "https://www.googleapis.com/auth/generative-language",
        "openid",
        "https://www.googleapis.com/auth/userinfo.email"
    ]
)
```

#### `client_secrets_path: Path | None = None`

Custom path to `client_secrets.json`. If None, uses `~/.kagura/client_secrets.json`.

**Default:** `None`

**Example:**
```python
from pathlib import Path

config = AuthConfig(
    provider="google",
    client_secrets_path=Path("/custom/path/client_secrets.json")
)
```

---

## Exceptions

### AuthenticationError

Base exception for authentication errors.

```python
from kagura.auth.exceptions import AuthenticationError

class AuthenticationError(Exception):
    """Base exception for authentication errors"""
```

**Example:**
```python
try:
    auth.login()
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
```

### NotAuthenticatedError

Raised when user is not authenticated.

```python
from kagura.auth.exceptions import NotAuthenticatedError

class NotAuthenticatedError(AuthenticationError):
    """Raised when user is not authenticated with OAuth2 provider"""
```

**Message Format:**
```
Not authenticated with {provider}. Please run: kagura auth login --provider {provider}
```

**Example:**
```python
try:
    token = auth.get_token()
except NotAuthenticatedError as e:
    print(f"Please login first: {e}")
    auth.login()
```

### InvalidCredentialsError

Raised when credentials are invalid or corrupted.

```python
from kagura.auth.exceptions import InvalidCredentialsError

class InvalidCredentialsError(AuthenticationError):
    """Raised when credentials are invalid or fail validation"""
```

**Example:**
```python
try:
    creds = auth.get_credentials()
except InvalidCredentialsError as e:
    print(f"Credentials invalid: {e}")
    auth.logout()  # Remove corrupted credentials
    auth.login()   # Re-authenticate
```

### TokenRefreshError

Raised when token refresh fails.

```python
from kagura.auth.exceptions import TokenRefreshError

class TokenRefreshError(AuthenticationError):
    """Raised when OAuth2 token refresh fails"""
```

**Example:**
```python
try:
    creds = auth.get_credentials()
except TokenRefreshError as e:
    print(f"Token refresh failed: {e}")
    auth.logout()
    auth.login()
```

---

## LLMConfig OAuth2 Integration

OAuth2 authentication is integrated into `LLMConfig` for seamless use with LLM calls.

### OAuth2 Fields

#### `auth_type: Literal["api_key", "oauth2"] = "api_key"`

Authentication type for LLM calls.

**Options:**
- `"api_key"`: Use environment variables (default)
- `"oauth2"`: Use OAuth2 token from OAuth2Manager

**Example:**
```python
from kagura.core.llm import LLMConfig

# OAuth2 authentication
config = LLMConfig(
    model="gemini/gemini-1.5-flash",
    auth_type="oauth2",
    oauth_provider="google"
)

# API key authentication (default)
config = LLMConfig(
    model="gpt-4o-mini",
    auth_type="api_key"  # Uses OPENAI_API_KEY env var
)
```

#### `oauth_provider: str | None = None`

OAuth2 provider name when `auth_type="oauth2"`.

**Required when:** `auth_type="oauth2"`

**Example:**
```python
config = LLMConfig(
    model="gemini/gemini-1.5-flash",
    auth_type="oauth2",
    oauth_provider="google"  # Required for OAuth2
)
```

### Methods

#### `get_api_key() -> str | None`

Get API key or OAuth2 token based on `auth_type`.

**Returns:**
- `str | None`: API key or OAuth2 access token

**Raises:**
- `ValueError`: If OAuth2 is requested but auth module not installed
- `NotAuthenticatedError`: If OAuth2 auth required but not logged in

**Example:**
```python
config = LLMConfig(
    model="gemini/gemini-1.5-flash",
    auth_type="oauth2",
    oauth_provider="google"
)

# Get OAuth2 token automatically
token = config.get_api_key()  # Returns OAuth2 access token
```

---

## CLI Commands

### kagura auth login

Authenticate with OAuth2 provider.

**Usage:**
```bash
kagura auth login [OPTIONS]
```

**Options:**
- `--provider TEXT`: OAuth2 provider name (default: `google`)

**Example:**
```bash
kagura auth login --provider google
```

**Output:**
```
✓ Authentication successful!
✓ Credentials saved to: /home/user/.kagura/credentials.json.enc
```

### kagura auth logout

Remove stored OAuth2 credentials.

**Usage:**
```bash
kagura auth logout [OPTIONS]
```

**Options:**
- `--provider TEXT`: OAuth2 provider name (default: `google`)

**Example:**
```bash
kagura auth logout --provider google
```

**Output:**
```
✓ Logged out from google
```

### kagura auth status

Check OAuth2 authentication status.

**Usage:**
```bash
kagura auth status [OPTIONS]
```

**Options:**
- `--provider TEXT`: OAuth2 provider name (default: `google`)

**Example:**
```bash
kagura auth status --provider google
```

**Output (authenticated):**
```
✓ Authenticated with google
Token expires: 2025-10-13 15:30:00 UTC
```

**Output (not authenticated):**
```
✗ Not authenticated with google
Run: kagura auth login --provider google
```

---

## Complete Example

Here's a complete example using OAuth2 authentication:

```python
from kagura import agent
from kagura.core.llm import LLMConfig
from kagura.auth import OAuth2Manager
from kagura.auth.exceptions import NotAuthenticatedError

# Check if authenticated
auth = OAuth2Manager(provider="google")
if not auth.is_authenticated():
    print("Not authenticated. Please run: kagura auth login --provider google")
    exit(1)

# Create OAuth2 LLM config
gemini_config = LLMConfig(
    model="gemini/gemini-1.5-flash",
    auth_type="oauth2",
    oauth_provider="google",
    temperature=0.7,
    max_tokens=1000
)

# Define agent with OAuth2
@agent(
    name="gemini_assistant",
    template="Answer the question: {{ question }}",
    llm_config=gemini_config
)
def ask_gemini(question: str) -> str:
    pass

# Use the agent
try:
    response = ask_gemini("What is the capital of France?")
    print(response)  # "The capital of France is Paris."
except NotAuthenticatedError:
    print("Please authenticate: kagura auth login --provider google")
```

---

## See Also

- [OAuth2 Authentication Guide](../guides/oauth2-authentication.md)
- [LLM API Reference](llm.md)
- [Installation Guide](../installation.md)
