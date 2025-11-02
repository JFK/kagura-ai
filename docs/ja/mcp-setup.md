# MCP Setup Guide - Claude Desktop Integration

> **Connect Kagura to Claude Desktop in 2 minutes**

This guide shows how to integrate Kagura's universal memory with Claude Desktop using the Model Context Protocol (MCP).

---

## 📋 Prerequisites

- Kagura AI v4.0+ installed
- Claude Desktop (supports MCP)

---

## ⚡ Automatic Setup (Recommended)

Kagura can automatically configure Claude Desktop for you:

```bash
# Install Kagura MCP server to Claude Desktop
kagura mcp install
```

**Output**:
```
✅ Successfully installed!

Configuration:
  Server name: kagura-memory
  Command: kagura mcp serve
  Config file: ~/.config/claude/claude_desktop_config.json

Next steps:
  1. Restart Claude Desktop
  2. Start a new conversation
  3. Try: 'Remember that I prefer Python'
```

**That's it!** Kagura is now connected to Claude Desktop.

---

## 🔧 Manual Setup (Alternative)

If automatic setup doesn't work, you can manually edit the config file.

### Step 1: Locate Claude Desktop Config

**macOS/Linux**:
```
~/.config/claude/claude_desktop_config.json
```

**Windows**:
```
%APPDATA%\Claude\claude_desktop_config.json
```

### Step 2: Edit Configuration

Add Kagura to the `mcpServers` section:

```json
{
  "mcpServers": {
    "kagura-memory": {
      "command": "kagura",
      "args": ["mcp", "serve"],
      "env": {}
    }
  }
}
```

**Full example**:
```json
{
  "mcpServers": {
    "kagura-memory": {
      "command": "kagura",
      "args": ["mcp", "serve"],
      "env": {}
    },
    "other-server": {
      "command": "other-command",
      "args": ["serve"]
    }
  }
}
```

### Step 3: Restart Claude Desktop

Close and reopen Claude Desktop to apply changes.

---

## ✅ Verify Integration

### Method 1: Ask Claude

Start a new conversation in Claude Desktop and try:

> **You**: "Remember that I prefer Python over JavaScript for backend projects"

Claude will use the `memory_store` tool to save this.

> **You**: "What programming languages do I prefer?"

Claude will use `memory_recall` or `memory_search` to retrieve the information.

### Method 2: Check Diagnostics

```bash
kagura mcp doctor
```

Look for:
```
Claude Desktop │ ✅ configured │ Kagura MCP server configured
```

---

## 🧠 Available Memory Tools

Once integrated, Claude has access to these memory tools:

### Core Tools

| Tool | Purpose | Example |
|------|---------|---------|
| **memory_store** | Save information | "Remember X" |
| **memory_recall** | Get by key | "What did I say about Y?" |
| **memory_search** | Semantic search | "Find memories about Z" |
| **memory_list** | List all memories | "What do you remember about me?" |
| **memory_feedback** | Mark useful/outdated | Automatic |
| **memory_delete** | Forget information | "Forget about X" |

### Memory Scopes

- **working**: Temporary, session-only (default)
- **persistent**: Saved to disk, survives restart

### Example Interactions

**Store persistent memory**:
> "Remember that my favorite Python library is FastAPI. This is important and should be persistent."

**Search memories**:
> "What do you know about my coding preferences?"

**Feedback** (automatic):
> Claude automatically marks memories as "useful" when they help answer your questions.

**Delete**:
> "Forget about my old JavaScript preference"

---

## 🔍 Troubleshooting

### Claude Desktop doesn't see Kagura tools

**Check 1**: Verify installation
```bash
kagura mcp doctor
```

**Check 2**: Restart Claude Desktop
- Quit Claude Desktop completely
- Reopen it
- Start a new conversation

**Check 3**: Check logs
```bash
# Claude Desktop logs (macOS)
tail -f ~/Library/Logs/Claude/mcp*.log
```

### "kagura command not found"

**Solution**: Use full path in config

```json
{
  "mcpServers": {
    "kagura-memory": {
      "command": "/full/path/to/kagura",
      "args": ["mcp", "serve"]
    }
  }
}
```

Find full path:
```bash
which kagura
# Output: /home/user/.local/bin/kagura
```

### Memory not persisting across conversations

**Cause**: Using `scope="working"` (default)

**Solution**: Explicitly use `scope="persistent"`

Or tell Claude:
> "Remember this **permanently**: I prefer Python"

---

## 🚫 Uninstall

To remove Kagura from Claude Desktop:

```bash
kagura mcp uninstall
```

This removes the configuration but **does not delete your stored memories**.

---

## 🔗 Related

- [Getting Started](./getting-started.md) - Installation guide
- [API Reference](./api-reference.md) - REST API docs
- [Architecture](./architecture.md) - System design

---

**Version**: 4.0.0a
**Last updated**: 2025-10-26
