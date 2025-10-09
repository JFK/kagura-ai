# MCP Integration

## Overview

Kagura AI supports **MCP (Model Context Protocol)**, enabling your agents to be used as tools in Claude Desktop, Claude Code, Cline, and other MCP-compatible applications.

With MCP integration, you can:
- **Expose Kagura agents** as MCP tools
- **Use agents from Claude Desktop/Code** directly
- **Share agents** across MCP-compatible applications
- **Build agent ecosystems** with standard protocols

## What is MCP?

[Model Context Protocol (MCP)](https://spec.modelcontextprotocol.io/) is an open protocol developed by Anthropic that standardizes how AI applications connect to external tools and data sources.

## Installation

Install Kagura AI with MCP support:

```bash
pip install kagura-ai[mcp]
```

Or with uv:

```bash
uv add "kagura-ai[mcp]"
```

This installs additional dependencies:
- `mcp>=1.0.0` - MCP SDK
- `jsonschema>=4.20.0` - Schema validation

## Quick Start

### 1. Create an Agent

Create a simple agent in `my_agents.py`:

```python
from kagura import agent

@agent
async def analyze_code(code: str, language: str = "python") -> str:
    """
    Analyze code quality and suggest improvements.

    code: Source code to analyze
    language: Programming language (default: python)
    """
    pass
```

**That's it!** The agent is automatically registered and ready to use via MCP.

### 2. Start MCP Server

Start the Kagura MCP server:

```bash
kagura mcp serve
```

This starts a stdio-based MCP server that listens for requests.

### 3. Configure Claude Desktop

Add Kagura to your Claude Desktop configuration:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "kagura": {
      "command": "kagura",
      "args": ["mcp", "serve"],
      "env": {
        "OPENAI_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

**Note**: Replace `OPENAI_API_KEY` with your actual API key, or use `ANTHROPIC_API_KEY` if using Claude models.

### 4. Restart Claude Desktop

1. Quit Claude Desktop completely
2. Restart Claude Desktop
3. Your Kagura agents are now available as tools!

### 5. Use Your Agent in Claude Desktop

In Claude Desktop, simply ask:

```
Can you analyze this Python code for me?

def calculate(x):
    return x * 2 + 3
```

Claude will automatically use your `analyze_code` agent via MCP.

## Configuration Options

### Custom Server Name

```bash
kagura mcp serve --name my-custom-server
```

### Environment Variables

Set API keys and other environment variables in the configuration:

```json
{
  "mcpServers": {
    "kagura": {
      "command": "kagura",
      "args": ["mcp", "serve"],
      "env": {
        "OPENAI_API_KEY": "${OPENAI_API_KEY}",
        "MODEL": "gpt-4o-mini"
      }
    }
  }
}
```

### Multiple Agent Files

If you have agents in multiple files, import them before starting the server:

```python
# startup.py
import my_agents
import more_agents

# Agents are automatically registered on import
```

Then configure Claude Desktop to run your startup script:

```json
{
  "mcpServers": {
    "kagura": {
      "command": "python",
      "args": ["-c", "import startup; from kagura.cli.main import cli; cli(['mcp', 'serve'])"]
    }
  }
}
```

## Managing Agents

### List Registered Agents

See all agents available via MCP:

```bash
kagura mcp list
```

Output:
```
Registered agents (1):

  • analyze_code
    Analyze code quality and suggest improvements
```

### Agent Naming Convention

MCP tool names are prefixed with `kagura_`:
- Agent function: `analyze_code`
- MCP tool name: `kagura_analyze_code`

This prevents naming conflicts with other MCP tools.

## Advanced Usage

### Multiple Agents

Create multiple specialized agents:

```python
from kagura import agent

@agent
async def review_code(code: str) -> str:
    """Review code and provide feedback"""
    pass

@agent
async def generate_tests(code: str, framework: str = "pytest") -> str:
    """Generate unit tests for the code"""
    pass

@agent
async def explain_code(code: str, audience: str = "beginner") -> str:
    """Explain code for different audiences"""
    pass
```

All three agents are automatically available in Claude Desktop.

### Complex Input Types

Use Pydantic models for structured inputs:

```python
from kagura import agent
from pydantic import BaseModel

class CodeReviewRequest(BaseModel):
    code: str
    language: str
    focus_areas: list[str]

@agent
async def detailed_review(request: CodeReviewRequest) -> dict:
    """Perform detailed code review"""
    return {
        "score": 8.5,
        "issues": [...],
        "suggestions": [...]
    }
```

The Pydantic model is automatically converted to JSON Schema for MCP.

### Error Handling

Agents should handle errors gracefully:

```python
@agent
async def safe_analysis(code: str) -> str:
    """Analyze code with error handling"""
    try:
        # Analysis logic
        return "Analysis complete"
    except Exception as e:
        return f"Error during analysis: {str(e)}"
```

## Integration with Other MCP Clients

Kagura MCP works with any MCP-compatible client:

### Claude Code (VS Code Extension)

Add to `.vscode/settings.json`:

```json
{
  "mcp.servers": {
    "kagura": {
      "command": "kagura",
      "args": ["mcp", "serve"]
    }
  }
}
```

### Cline (VS Code Extension)

Similar configuration in Cline settings.

### Custom MCP Clients

Use the MCP Python SDK to connect:

```python
from mcp import ClientSession
import asyncio

async def test_kagura_mcp():
    async with ClientSession() as session:
        # Connect to Kagura MCP server
        await session.initialize()

        # List tools
        tools = await session.list_tools()
        print(f"Available tools: {[t.name for t in tools]}")

        # Call agent
        result = await session.call_tool(
            "kagura_analyze_code",
            {"code": "def hello(): print('hi')"}
        )
        print(result)

asyncio.run(test_kagura_mcp())
```

## Debugging

### Enable Verbose Logging

```bash
kagura -v mcp serve
```

### Check Agent Registration

```bash
kagura mcp list
```

If your agent doesn't appear:
1. Ensure the file is imported
2. Check the `@agent` decorator is applied
3. Verify no import errors

### Test Without Claude Desktop

Use `mcp` CLI tool to test directly:

```bash
# Install MCP CLI
npm install -g @modelcontextprotocol/cli

# Test Kagura MCP server
mcp call kagura_analyze_code '{"code": "def test(): pass"}'
```

## Best Practices

### 1. Clear Descriptions

Write clear docstrings - they become tool descriptions in Claude:

```python
@agent
async def analyze_code(code: str, language: str = "python") -> str:
    """
    Analyze code quality and suggest improvements.

    This agent examines code structure, identifies potential issues,
    and provides actionable suggestions for improvement.

    code: Source code to analyze
    language: Programming language (python, javascript, etc.)
    """
    pass
```

### 2. Type Hints

Use type hints for automatic schema generation:

```python
@agent
async def process_data(
    data: list[dict[str, Any]],
    max_items: int = 100,
    include_metadata: bool = False
) -> dict[str, Any]:
    """Process data with options"""
    pass
```

### 3. Default Values

Provide sensible defaults for optional parameters:

```python
@agent
async def translate(
    text: str,
    target_language: str = "English",
    tone: str = "neutral"
) -> str:
    """Translate text"""
    pass
```

### 4. Structured Output

Return structured data when appropriate:

```python
@agent
async def analyze_sentiment(text: str) -> dict:
    """
    Analyze sentiment of text

    Returns:
        {
            "sentiment": "positive" | "negative" | "neutral",
            "confidence": float,
            "keywords": list[str]
        }
    """
    pass
```

## Troubleshooting

### Agent Not Appearing in Claude Desktop

1. **Check configuration file location**
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - Linux: `~/.config/Claude/claude_desktop_config.json`

2. **Verify JSON syntax**
   ```bash
   # Test JSON validity
   cat ~/Library/Application\ Support/Claude/claude_desktop_config.json | python -m json.tool
   ```

3. **Check server logs**
   ```bash
   kagura -v mcp serve 2> mcp_server.log
   ```

4. **Restart Claude Desktop completely**
   - Quit application
   - Restart
   - Check MCP indicator in status bar

### Authentication Errors

Make sure API keys are set:

```json
{
  "mcpServers": {
    "kagura": {
      "command": "kagura",
      "args": ["mcp", "serve"],
      "env": {
        "OPENAI_API_KEY": "sk-..."
      }
    }
  }
}
```

### Permission Errors

On Unix systems, ensure `kagura` is executable:

```bash
which kagura
chmod +x $(which kagura)
```

## Next Steps

- **[API Reference](../api/mcp.md)** - MCP API documentation
- **[CLI Reference](../api/cli.md)** - `kagura mcp` commands
- **[MCP Specification](https://spec.modelcontextprotocol.io/)** - Learn more about MCP

## Example Projects

See `examples/mcp_integration/` for complete examples:
- Code analysis agent
- Multi-agent workflow
- Custom tool integration
