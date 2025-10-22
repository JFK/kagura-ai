# Claude Code MCP Setup

Use all Kagura features from Claude Code with a single configuration.

## Quick Setup

### 1. Find your MCP configuration file

**Location** (varies by installation):
- `~/.config/claude-code/mcp.json` (Linux/macOS)
- `~/Library/Application Support/Claude/mcp.json` (macOS alternative)
- Check Claude Code documentation for exact path

### 2. Add Kagura to MCP config

Edit your MCP config file:

```json
{
  "mcpServers": {
    "kagura-ai": {
      "command": "kagura",
      "args": ["mcp", "serve"]
    }
  }
}
```

### 3. Restart Claude Code

Restart Claude Code to load the new MCP server.

### 4. Verify

In Claude Code, you should now have access to all Kagura tools:

```
User: List available Kagura tools
Claude: [Lists all 15+ built-in tools]
```

## Available Tools

### Memory Operations
- `kagura_tool_memory_store` - Store information
- `kagura_tool_memory_recall` - Recall stored information
- `kagura_tool_memory_search` - Semantic search in memory
- `kagura_tool_memory_list` - List all stored memories (debugging)

### Web Operations
- `kagura_tool_web_search` - Search the web
- `kagura_tool_web_scrape` - Scrape web pages

### File/Directory Operations
- `kagura_tool_file_read` - Read file contents
- `kagura_tool_file_write` - Write to files
- `kagura_tool_dir_list` - List directory contents
- `kagura_tool_shell_exec` - Execute shell commands safely

### Observability
- `kagura_tool_telemetry_stats` - Get execution statistics
- `kagura_tool_telemetry_cost` - Analyze costs

### Meta Agent
- `kagura_tool_meta_create_agent` - Generate new agents

### Multimodal (requires `web` extra)
- `kagura_tool_multimodal_index` - Index multimedia files
- `kagura_tool_multimodal_search` - Search indexed content

## Usage Examples

### Example 1: Memory

```
User: Remember that my favorite programming language is Python
Claude: [Uses kagura_tool_memory_store]
       ✓ Stored information

User: What's my favorite language?
Claude: [Uses kagura_tool_memory_recall]
       Your favorite programming language is Python
```

### Example 2: Web Search + File

```
User: Search for latest Python news and save to news.txt
Claude: [Uses kagura_tool_web_search]
       [Uses kagura_tool_file_write]
       ✓ Saved to news.txt
```

### Example 3: Code Generation

```
User: Create a translator agent
Claude: [Uses kagura_tool_meta_create_agent]
       Generated agent code...
```

## Troubleshooting

### Tools not appearing

1. Check MCP config syntax is valid JSON
2. Verify `kagura` command is in PATH
3. Restart Claude Code completely
4. Check Claude Code logs for errors

### "requires X extra" errors

Install required extras:

```bash
# All features
pip install kagura-ai[full]

# Specific features
pip install kagura-ai[ai]     # Memory, Routing
pip install kagura-ai[web]    # Web, Multimodal
```

### Permission errors

Ensure `kagura` command is executable:

```bash
which kagura
chmod +x $(which kagura)
```

## Advanced

### Custom Tools

You can also expose your own @tool definitions:

```python
# my_tools.py
from kagura import tool

@tool
def custom_calculator(x: float, y: float) -> float:
    '''Add two numbers'''
    return x + y
```

Just import before starting MCP:

```bash
python -c "import my_tools; import kagura.mcp.builtin" && kagura mcp serve
```

Or create a wrapper script.
