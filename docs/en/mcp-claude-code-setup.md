# MCP Setup Guide - Claude Code Integration

> **Connect Kagura to Claude Code in 2 minutes**

This guide shows how to integrate Kagura's universal memory with Claude Code (Anthropic's official CLI) using the Model Context Protocol (MCP).

---

## 📋 Prerequisites

- Kagura AI v4.0+ installed
- Claude Code CLI (Anthropic's official CLI tool)

---

## ⚡ Quick Setup

### Step 1: Install Kagura

```bash
# Install with full dependencies
pip install kagura-ai[full]

# Or install from source
git clone https://github.com/JFK/kagura-ai.git
cd kagura-ai
uv sync --all-extras
```

### Step 2: Add MCP Server to Claude Code

```bash
# Add Kagura as an MCP server
claude mcp add --transport stdio kagura -- kagura mcp serve
```

**Output**:
```
Added stdio MCP server kagura with command: kagura mcp serve to local config
File modified: /home/user/.claude.json
```

### Step 3: Verify Connection

```bash
# Check MCP server status
claude mcp list
```

**Expected output**:
```
Checking MCP server health...

kagura: kagura mcp serve - ✓ Connected
```

**That's it!** Kagura is now connected to Claude Code.

---

## 🧠 Available Tools

Once integrated, Claude Code has access to **31 MCP tools** across these categories:

### Core Memory Tools (4)

| Tool | Purpose | Example Usage |
|------|---------|---------------|
| `memory_store` | Save information | "Remember that I prefer Python" |
| `memory_recall` | Retrieve by key | "What's my Python preference?" |
| `memory_search` | Semantic search | "Find memories about coding" |
| `memory_delete` | Remove memory | "Forget about X" |

### Knowledge Graph Tools (3)

| Tool | Purpose |
|------|---------|
| `graph_add_node` | Add concept |
| `graph_link` | Connect memories |
| `graph_query` | Multi-hop traversal |

### Search Tools (6)

| Tool | Purpose |
|------|---------|
| `search_memories` | Hybrid search (BM25 + vector) |
| `search_brave` | Web search via Brave API |
| `search_arxiv` | Academic papers |
| ... | ... |

### Coding Tools (14)

| Tool | Purpose |
|------|---------|
| `coding_store_file_change` | Track file modifications |
| `coding_store_error` | Log errors |
| `coding_store_design_decision` | Document design choices |
| `coding_summary` | AI-powered session summary |
| ... | ... |

### GitHub Tools (6)

| Tool | Purpose |
|------|---------|
| `github_shell_exec` | Safe shell execution |
| `github_issue_*` | Issue operations |
| `github_pr_*` | PR management |

**Full list**: Run `kagura mcp tools` to see all 31 tools.

---

## 🎯 Usage Examples

### Basic Memory Operations

**Store a memory**:
```
User: Remember that I prefer Python over JavaScript for backend projects
Claude: [Uses memory_store tool]
```

**Recall a memory**:
```
User: What programming languages do I prefer?
Claude: [Uses memory_recall/search to retrieve the information]
```

### Knowledge Graph

**Link related memories**:
```
User: Connect my Python preference with FastAPI knowledge
Claude: [Uses graph_link to create relationship]
```

**Find related concepts**:
```
User: What's related to my coding preferences?
Claude: [Uses graph_query for multi-hop traversal]
```

### Coding Session

**Track file changes**:
```
Claude: [Automatically uses coding_store_file_change when editing files]
```

**Summarize session**:
```
User: Summarize what we accomplished today
Claude: [Uses coding_summary to analyze session history]
```

---

## 🔧 Advanced Configuration

### Remote Mode (Safe Tools Only)

If you want to connect to a remote Kagura API:

```bash
# Configure remote connection
kagura mcp connect

# Add remote MCP server
claude mcp add --transport stdio kagura-remote -- kagura mcp serve --remote
```

### Custom Server Name

```bash
# Use custom name
claude mcp add --transport stdio my-kagura -- kagura mcp serve --name my-kagura
```

### Environment Variables

Add API keys for optional features:

```bash
# Add with environment variables
claude mcp add --transport stdio kagura \
  --env OPENAI_API_KEY=sk-... \
  --env BRAVE_API_KEY=... \
  -- kagura mcp serve
```

---

## 🔍 Troubleshooting

### "kagura command not found"

**Solution**: Use full path

```bash
# Find kagura path
which kagura
# Output: /home/user/.local/bin/kagura

# Add with full path
claude mcp add --transport stdio kagura -- /home/user/.local/bin/kagura mcp serve
```

### Check Configuration

**View current configuration**:
```bash
claude mcp get kagura
```

**Check logs**:
```bash
# Kagura MCP server logs
kagura mcp log
```

### Remove and Re-add

```bash
# Remove
claude mcp remove kagura

# Re-add
claude mcp add --transport stdio kagura -- kagura mcp serve
```

---

## 📊 Monitoring

### View Tool Usage Statistics

```bash
kagura mcp stats
```

**Example output**:
```
MCP Tool Usage Statistics
─────────────────────────────────────────────────
Total calls: 156

Top tools:
  memory_store: 45 calls
  memory_search: 32 calls
  coding_store_file_change: 28 calls
  graph_link: 15 calls
```

### View Server Logs

```bash
# Real-time logs
kagura mcp log --tail

# Last 100 lines
kagura mcp log --lines 100
```

---

## 🚫 Uninstall

To remove Kagura from Claude Code:

```bash
claude mcp remove kagura
```

This removes the configuration but **does not delete your stored memories**.

To delete memories:
```bash
# Export first (backup)
kagura memory export --output=./backup

# Clear all memories
rm -rf ~/.local/share/kagura/
rm -rf ~/.cache/kagura/
```

---

## 🔗 Related Documentation

- [MCP Setup (Claude Desktop)](./mcp-setup.md) - Claude Desktop integration
- [MCP over HTTP/SSE](./mcp-http-setup.md) - Remote MCP setup
- [Getting Started](./getting-started.md) - Installation guide
- [API Reference](./api-reference.md) - REST API docs

---

## 📚 Additional Resources

### Claude Code Documentation
- [Claude Code Official Docs](https://docs.claude.com/en/docs/claude-code)
- [MCP Protocol](https://modelcontextprotocol.io/)

### Kagura Documentation
- [GitHub Repository](https://github.com/JFK/kagura-ai)
- [PyPI Package](https://pypi.org/project/kagura-ai/)

---

**Version**: 4.0.0
**Last updated**: 2025-11-02
