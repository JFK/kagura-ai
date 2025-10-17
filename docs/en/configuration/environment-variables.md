# Environment Variables

Kagura AI uses environment variables for configuration, including API keys, default settings, and feature toggles. This guide documents all available environment variables and how to use them.

## Quick Start

1. **Copy the example file**:
   ```bash
   cp .env.example .env
   ```

2. **Add your API keys**:
   ```bash
   # At least one LLM provider is required
   OPENAI_API_KEY=sk-...
   ```

3. **Load environment variables** (optional):
   ```bash
   # Kagura automatically loads .env files
   # Or use python-dotenv:
   python -m dotenv run kagura chat
   ```

## Required Variables

At least **one LLM provider API key** is required for Kagura to work:

| Variable | Provider | Get API Key | Models |
|----------|----------|-------------|--------|
| `OPENAI_API_KEY` | OpenAI | [platform.openai.com](https://platform.openai.com/api-keys) | gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-3.5-turbo |
| `ANTHROPIC_API_KEY` | Anthropic | [console.anthropic.com](https://console.anthropic.com/) | claude-3-5-sonnet, claude-3-opus, claude-3-haiku |
| `GOOGLE_API_KEY` | Google AI | [aistudio.google.com](https://aistudio.google.com/app/apikey) | gemini-1.5-pro, gemini-1.5-flash, gemini-pro |

### Example

```bash
# Option 1: OpenAI (most common)
OPENAI_API_KEY=sk-proj-...

# Option 2: Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Option 3: Google AI (for multimodal features)
GOOGLE_API_KEY=AIza...

# Or use multiple providers
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...
```

## Optional Variables

### Web Search

| Variable | Service | Get API Key | Purpose |
|----------|---------|-------------|---------|
| `BRAVE_SEARCH_API_KEY` | Brave Search | [brave.com/search/api](https://brave.com/search/api/) | Web search capabilities |

**Example**:
```bash
BRAVE_SEARCH_API_KEY=BSA...
```

**Note**: This API key is required for web search functionality.

### Default Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `DEFAULT_MODEL` | `gpt-4o-mini` | Default LLM model to use |
| `DEFAULT_TEMPERATURE` | `0.7` | Default temperature (0.0-2.0) |

**Example**:
```bash
# Use GPT-4o by default
DEFAULT_MODEL=gpt-4o

# Make responses more creative
DEFAULT_TEMPERATURE=1.0
```

## Programmatic Access

Kagura provides a centralized API for accessing environment variables:

```python
from kagura.config.env import (
    get_openai_api_key,
    get_anthropic_api_key,
    get_google_api_key,
    get_brave_search_api_key,
    get_default_model,
    get_default_temperature,
)

# Get API keys (returns None if not set)
openai_key = get_openai_api_key()
brave_key = get_brave_search_api_key()

# Get defaults (returns default value if not set)
model = get_default_model()  # "gpt-4o-mini"
temperature = get_default_temperature()  # 0.7
```

### Utility Functions

```python
from kagura.config.env import list_env_vars, check_required_env_vars

# List all environment variables (API keys are masked)
env_vars = list_env_vars()
print(env_vars)
# {
#   'OPENAI_API_KEY': '***',
#   'ANTHROPIC_API_KEY': None,
#   'GOOGLE_API_KEY': '***',
#   'BRAVE_SEARCH_API_KEY': '***',
#   'DEFAULT_MODEL': 'gpt-4o-mini',
#   'DEFAULT_TEMPERATURE': '0.7'
# }

# Check for missing required variables
missing = check_required_env_vars()
if missing:
    print(f"Missing: {', '.join(missing)}")
```

## Backward Compatibility

### Brave Search API Key

The old `BRAVE_SEARCH_API_KEY` variable is deprecated. Use `BRAVE_SEARCH_API_KEY` instead.

**Migration**:
```bash
# Old (deprecated, but still works with warning)
BRAVE_SEARCH_API_KEY=...

# New (recommended)
BRAVE_SEARCH_API_KEY=...
```

**Deprecation Warning**:
```python
import warnings

# Using old variable name will show:
# DeprecationWarning: BRAVE_SEARCH_API_KEY is deprecated.
# Use BRAVE_SEARCH_API_KEY instead.
```

## Additional Providers

Kagura uses [LiteLLM](https://docs.litellm.ai/docs/providers) which supports 100+ LLM providers. You can add keys for any supported provider:

### Azure OpenAI

```bash
AZURE_API_KEY=...
AZURE_API_BASE=https://your-resource.openai.azure.com/
AZURE_API_VERSION=2024-02-15-preview
```

### AWS Bedrock

```bash
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION_NAME=us-east-1
```

### Other Providers

- **Cohere**: `COHERE_API_KEY`
- **Hugging Face**: `HUGGINGFACE_API_KEY`
- **Together AI**: `TOGETHERAI_API_KEY`
- **Replicate**: `REPLICATE_API_KEY`

See [LiteLLM Providers](https://docs.litellm.ai/docs/providers) for full list.

## Security Best Practices

### 1. Never Commit API Keys

```bash
# ✅ Good: Use .env (already in .gitignore)
echo "OPENAI_API_KEY=sk-..." > .env

# ❌ Bad: Never commit keys to Git
git add .env  # Don't do this!
```

### 2. Use Environment-Specific Files

```bash
.env              # Local development (gitignored)
.env.production   # Production (never committed)
.env.example      # Template (safe to commit)
```

### 3. Rotate Keys Regularly

- Rotate API keys every 90 days
- Use separate keys for development/production
- Revoke keys immediately if compromised

### 4. Limit Key Permissions

- Use read-only keys when possible
- Set spending limits on API keys
- Use service-specific keys (not admin keys)

## Troubleshooting

### "No API key found"

**Error**:
```
ValueError: Google API key not found.
Set GOOGLE_API_KEY environment variable or pass api_key parameter.
```

**Solution**:
```bash
# Check if variable is set
echo $GOOGLE_API_KEY

# Set the variable
export GOOGLE_API_KEY=AIza...

# Or add to .env
echo "GOOGLE_API_KEY=AIza..." >> .env
```

### "Invalid temperature"

**Error**:
```
UserWarning: Invalid DEFAULT_TEMPERATURE value: abc. Using default: 0.7
```

**Solution**:
```bash
# Temperature must be a number between 0.0 and 2.0
DEFAULT_TEMPERATURE=0.7  # ✅ Valid
DEFAULT_TEMPERATURE=abc  # ❌ Invalid
```

### Environment not loading

**Problem**: Changes to `.env` not taking effect

**Solutions**:
```bash
# 1. Restart your shell/terminal

# 2. Explicitly load .env
python -m dotenv run kagura chat

# 3. Check .env file location
pwd  # Should be in project root

# 4. Verify .env syntax
cat .env  # Check for typos, missing =, etc.
```

## Related Documentation

- [Quick Start Guide](../quickstart.md)
- [Agent Configuration](./agents.md)
- [LiteLLM Providers](https://docs.litellm.ai/docs/providers)
- [API Reference](../api/config.md)

## Reference: All Variables

### LLM Providers (Required)
- `OPENAI_API_KEY` - OpenAI API key
- `ANTHROPIC_API_KEY` - Anthropic API key
- `GOOGLE_API_KEY` - Google AI API key

### Features (Optional)
- `BRAVE_SEARCH_API_KEY` - Brave Search API key

### Defaults (Optional)
- `DEFAULT_MODEL` - Default LLM model (default: `gpt-4o-mini`)
- `DEFAULT_TEMPERATURE` - Default temperature (default: `0.7`)

### Deprecated
- `BRAVE_SEARCH_API_KEY` - Use `BRAVE_SEARCH_API_KEY` instead

---

**Last updated**: 2025-10-16
**Version**: 2.5.10
