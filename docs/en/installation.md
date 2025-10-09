# Installation

## Requirements

- Python 3.11 or higher
- pip or uv package manager

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
Kagura AI v2.0.0-alpha.1
```

## Set API Key

Kagura AI uses LiteLLM, which supports multiple LLM providers. You need to set the appropriate API key for your chosen provider.

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

### For MCP Integration

To use Kagura agents with Claude Desktop, Claude Code, and other MCP clients:

```bash
pip install kagura-ai[mcp]
```

Or with uv:

```bash
uv add "kagura-ai[mcp]"
```

This installs:
- `mcp>=1.0.0` - Model Context Protocol SDK
- `jsonschema>=4.20.0` - JSON Schema validation

See [MCP Integration Tutorial](tutorials/06-mcp-integration.md) for setup guide.

### For Development

Development tools are already included with `--dev` flag:

- `pytest` - Testing framework
- `pytest-asyncio` - Async test support
- `pytest-cov` - Code coverage
- `pyright` - Type checker
- `ruff` - Linter and formatter

### For Documentation

To build documentation locally:

```bash
pip install mkdocs mkdocs-material
mkdocs serve
```

Then visit `http://localhost:8000`

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
