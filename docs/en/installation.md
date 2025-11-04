# Installation

## Requirements

- **Python**: 3.11, 3.12, or 3.13
  - ⚠️ **Intel Mac (x86_64) users**: Python 3.13 is **not supported** with AI features due to PyTorch limitations. Use Python 3.11 or 3.12.
- **Package manager**: pip or uv

### Platform-Specific Requirements

| Platform | Python 3.11 | Python 3.12 | Python 3.13 |
|----------|-------------|-------------|-------------|
| macOS Intel (x86_64) | ✅ | ✅ | ❌ * |
| macOS Apple Silicon (ARM64) | ✅ | ✅ | ✅ |
| Linux (x86_64 / ARM64) | ✅ | ✅ | ✅ |
| Windows | ✅ | ✅ | ✅ |

\* **Why?** PyTorch 2.3+ dropped Intel Mac support. For AI features (`[ai]` extra) on Intel Mac, use Python 3.11 or 3.12. Core features work with all versions.

## Install from PyPI

### Using pip

```bash
pip install kagura-ai
```

### Using uv (recommended)

```bash
uv add kagura-ai
```

## Verify Installation

Check that Kagura AI is installed correctly:

```bash
kagura version
```

You should see output like:

```
Kagura AI v3.0
```

## Set API Key

Kagura AI uses LiteLLM, which supports multiple LLM providers. You need to set the appropriate API key for your chosen provider.

> **💡 Quick Start Tip**
>
> The fastest way to get started with Gemini:
> 1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
> 2. Click "Create API Key"
> 3. Copy the key and set: `export GOOGLE_API_KEY="your-key"`
>
> **No Google Cloud Console setup needed!** OAuth2 is an advanced feature for specific use cases. See [OAuth2 Authentication Guide](guides/oauth2-authentication.md) for details.

### OpenAI

```bash
export OPENAI_API_KEY="your-key-here"
```

Or in Python:
```python
import os
os.environ["OPENAI_API_KEY"] = "your-key-here"
```

### Anthropic (Claude)

```bash
export ANTHROPIC_API_KEY="your-key-here"
```

### Google (Gemini)

```bash
export GOOGLE_API_KEY="your-key-here"
```

### Azure OpenAI

```bash
export AZURE_API_KEY="your-key-here"
export AZURE_API_BASE="https://your-endpoint.openai.azure.com/"
export AZURE_API_VERSION="2023-05-15"
```

## Test Your Installation

Create a simple test file:

```python
# test_kagura.py
from kagura import agent

@agent
async def hello(name: str) -> str:
    '''Say hello to {{ name }}'''
    pass

if __name__ == "__main__":
    import asyncio

    async def main():
        result = await hello("Kagura AI")
        print(result)

    asyncio.run(main())
```

Run it:

```bash
python test_kagura.py
```

If successful, you should see a greeting message.

## Development Installation

For contributing to Kagura AI or running from source:

### Clone Repository

```bash
git clone https://github.com/JFK/kagura-ai.git
cd kagura-ai
```

### Install Dependencies

Using uv (recommended):

```bash
uv sync --dev
```

This will install:
- All runtime dependencies
- Development dependencies (pytest, pyright, ruff, etc.)

### Run Tests

```bash
pytest
```

### Type Checking

```bash
pyright
```

### Code Formatting

```bash
ruff check src/
```

## Optional Dependencies

Kagura AI provides several optional feature presets to install only what you need.

### 📦 User-Facing Presets

#### AI Features (`kagura-ai[ai]`)

Core AI capabilities: Memory, Routing, Context Compression

```bash
pip install kagura-ai[ai]
# or
uv add "kagura-ai[ai]"
```

**Includes**:
- `chromadb` - Vector storage for memory & RAG
- `semantic-router` - Semantic routing
- `tiktoken` - Token counting for context compression

**Use cases**:
- Agents with long-term memory
- Semantic routing between agents
- Context-aware conversation management

---

#### Web & Multimodal (`kagura-ai[web]`)

Web search, scraping, and multimodal (image/audio/video) processing

```bash
pip install kagura-ai[web]
# or
uv add "kagura-ai[web]"
```

**Includes**:
- `google-generativeai` - Gemini API for multimodal
- `pillow` - Image processing
- `httpx` - HTTP client
- `brave-search-python-client` - Brave Search API
- `beautifulsoup4` - HTML parsing

**Use cases**:
- Web search agents
- Image/audio/video analysis
- Web scraping and data extraction

---

#### OAuth2 Authentication (`kagura-ai[auth]`)

OAuth2 authentication with Google/Gemini (advanced feature)

```bash
pip install kagura-ai[auth]
# or
uv add "kagura-ai[auth]"
```

**Includes**:
- `google-auth` - Google authentication library
- `google-auth-oauthlib` - OAuth2 flow
- `google-auth-httplib2` - HTTP library
- `cryptography` - Credential encryption

**Note**: OAuth2 is an advanced feature. For most users, **using API Keys is recommended** as it's simpler. See [OAuth2 Authentication Guide](guides/oauth2-authentication.md) for when to use OAuth2.

---

#### MCP Integration (`kagura-ai[mcp]`)

Use Kagura agents with Claude Desktop, Claude Code, and other MCP clients

```bash
pip install kagura-ai[mcp]
# or
uv add "kagura-ai[mcp]"
```

**Includes**:
- `mcp` - Model Context Protocol SDK
- `jsonschema` - JSON Schema validation

See [MCP Integration Tutorial](tutorials/06-mcp-integration.md) for setup guide.

---

### 🎁 Combined Presets (Recommended)

#### Full Features (`kagura-ai[full]`)

All user-facing features in one install

```bash
pip install kagura-ai[full]
# or
uv add "kagura-ai[full]"
```

**Includes**: `ai` + `web` + `auth` + `mcp`

**Recommended for**: Most users who want to explore all Kagura AI capabilities

---

#### Everything (`kagura-ai[all]`)

All features including development tools

```bash
pip install kagura-ai[all]
# or
uv add "kagura-ai[all]"
```

**Includes**: `full` + `dev` + `docs`

**Recommended for**: Contributors and advanced users

---

### 🛠️ Development Presets

#### Development Tools (`kagura-ai[dev]`)

Testing and linting tools (included with `uv sync --dev`)

```bash
pip install kagura-ai[dev]
# or
uv add "kagura-ai[dev]"
```

**Includes**:
- `pytest` - Testing framework
- `pytest-asyncio` - Async test support
- `pytest-cov` - Code coverage
- `pytest-timeout` - Test timeout
- `langdetect` - For agent testing
- `pyright` - Type checker
- `ruff` - Linter and formatter

---

#### Documentation Tools (`kagura-ai[docs]`)

Build documentation locally

```bash
pip install kagura-ai[docs]
# or
uv add "kagura-ai[docs]"
```

**Includes**:
- `mkdocs` - Documentation generator
- `mkdocs-material` - Material theme
- `pymdown-extensions` - Markdown extensions

Then run:
```bash
mkdocs serve
```

Visit `http://localhost:8000` to view docs.

---

### 📊 Installation Size Comparison

| Preset | Dependencies | Approximate Size | Use Case |
|--------|-------------|------------------|----------|
| `base` | 8 packages | ~50 MB | Basic agents only |
| `ai` | +3 packages | +150 MB | AI features |
| `web` | +7 packages | +200 MB | Web & Multimodal |
| `auth` | +4 packages | +20 MB | OAuth2 |
| `mcp` | +2 packages | +10 MB | MCP integration |
| `full` | +16 packages | +380 MB | All features |
| `all` | +23 packages | +420 MB | Everything |

## Troubleshooting

### Import Error

If you get import errors:

```python
ImportError: cannot import name 'agent' from 'kagura'
```

Make sure you're using Python 3.11+:

```bash
python --version
```

### API Key Not Found

If you see authentication errors:

```
AuthenticationError: The api_key client option must be set
```

Set your API key as described above. The key must be set before importing kagura.

### Type Errors

If pyright shows errors in your IDE:

1. Make sure your Python interpreter is set to 3.11+
2. Ensure kagura-ai is installed in your environment
3. Restart your IDE/language server

### Intel Mac (x86_64) Installation Issues

If you're on an Intel Mac and encounter installation failures with AI features (`[ai]` extra):

```
ERROR: Could not find a version that satisfies the requirement torch
ERROR: No matching distribution found for torch
```

**Cause**: PyTorch 2.3+ dropped Intel Mac support. Kagura AI uses PyTorch 2.2.2 (last version with Intel Mac wheels).

**Solutions**:

#### Option 1: Use Python 3.11 or 3.12 (Recommended)
```bash
# Check your Python version
python --version

# If using Python 3.13, switch to 3.12
pyenv install 3.12
pyenv local 3.12

# Reinstall Kagura with AI features
pip install kagura-ai[ai]
```

#### Option 2: Use Docker (Supports Python 3.13)
```bash
git clone https://github.com/your-org/kagura-ai.git
cd kagura-ai
docker-compose up -d
```

#### Option 3: Use Core Features Only (No PyTorch)
```bash
# Install without AI features - still get MCP server, CLI, API
pip install kagura-ai
```

**Note**: Core features (MCP server, CLI, REST API) work on all platforms with Python 3.11-3.13. Only the `[ai]` extra (embeddings, RAG) requires PyTorch.

## Upgrading

### From PyPI

```bash
pip install --upgrade kagura-ai
```

or with uv:

```bash
uv add kagura-ai --upgrade
```

### From Git

```bash
cd kagura-ai
git pull
uv sync --dev
```

## Uninstalling

```bash
pip uninstall kagura-ai
```

or with uv:

```bash
uv remove kagura-ai
```

## Next Steps

- [Quick Start](quickstart.md) - Build your first agent
- [API Reference](api/agent.md) - Detailed API documentation
- [Examples](../../examples/) - Example code
