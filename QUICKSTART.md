# Kagura AI - Quick Start Guide

Get started with Kagura AI in **less than 5 minutes**.

---

## What is Kagura?

Kagura is an **MCP-enabled universal memory platform** that connects all your AI tools (Claude Desktop, Claude Code, ChatGPT, custom agents) to **one shared memory**.

**Key Features**:
- Store/recall memories across all AI platforms
- Track coding sessions with automatic summaries
- Connect via MCP (Claude Desktop/Code) or REST API
- Local-first, privacy-focused, 100% open source

---

## Installation

### Option 1: Install via pip (Recommended)

```bash
pip install kagura-ai[full]
```

### Option 2: Docker (Production)

```bash
git clone https://github.com/JFK/kagura-ai.git
cd kagura-ai
docker compose up -d
```

### Option 3: From Source (Development)

```bash
git clone https://github.com/JFK/kagura-ai.git
cd kagura-ai
uv sync --all-extras
```

---

## 5-Minute Tutorial: Your First Memory

### Step 1: Store a Memory

```bash
# Store your first memory
kagura memory store \
  --key "python_preference" \
  --value "I prefer FastAPI over Django for new projects" \
  --tags "preferences,backend"
```

### Step 2: Recall the Memory

```bash
# Search using semantic recall
kagura memory search --query "What web framework do I like?"
```

**Output**:
```
📝 python_preference (similarity: 0.92)
   I prefer FastAPI over Django for new projects
   Tags: preferences, backend
```

**That's it!** You've created a persistent memory that any AI can access.

---

## MCP Setup (Connect to Claude Desktop/Code)

### For Claude Desktop

**Step 1**: Install Kagura (if not already done)
```bash
pip install kagura-ai[full]
```

**Step 2**: Auto-configure Claude Desktop
```bash
kagura mcp install
```

**Step 3**: Restart Claude Desktop

**Step 4**: Test the connection
```
You: "Run memory_stats to show Kagura status"
Claude: "You have 1 memory stored..."
```

**Manual Configuration** (if auto-install fails):

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "kagura": {
      "command": "kagura",
      "args": ["mcp", "serve"]
    }
  }
}
```

### For Claude Code

**Step 1**: Install Kagura
```bash
pip install kagura-ai[full]
```

**Step 2**: Add MCP server to Claude Code
```bash
claude mcp add --transport stdio kagura -- kagura mcp serve
```

**Step 3**: Verify connection
```bash
claude mcp list
# Expected output: kagura ✓ Connected
```

**Step 4**: Test in Claude Code
```
You: "Start coding session for 'implement user authentication'"
Claude: "Started coding session: implement user authentication..."
```

---

## Coding Sessions (for Developers)

Track your AI-assisted coding work automatically.

### Start a Session

```bash
kagura coding start \
  --description "Implement user authentication" \
  --tags "feature,auth"
```

### Track File Changes (via MCP)

In Claude Desktop/Code:
```
You: "I just updated auth.py to add OAuth2 support"
Claude: [Uses coding_track_file_change tool automatically]
```

Or manually:
```bash
kagura coding track \
  --file src/auth.py \
  --action edit \
  --reason "Added OAuth2 authentication"
```

### End Session

```bash
kagura coding end --save-github
```

**Result**: Automatic AI-generated summary saved to GitHub Issue (if linked)!

---

## Common Commands Cheat Sheet

### Memory Management

```bash
# Store memory
kagura memory store --key KEY --value "VALUE" --tags "tag1,tag2"

# Search memories (semantic)
kagura memory search --query "QUERY"

# Delete memory
kagura memory delete --id MEMORY_ID

# List all memories
kagura memory list

# Export all memories
kagura memory export --output ./backup
```

### Coding Sessions

```bash
# Start session
kagura coding start --description "TASK"

# View current session
kagura coding status

# List all sessions
kagura coding sessions

# Search past work
kagura coding search --query "authentication"

# View past decisions
kagura coding decisions

# View past errors and solutions
kagura coding errors
```

### MCP Server

```bash
# Start MCP server (for Claude Desktop/Code)
kagura mcp serve

# View MCP tools
kagura mcp tools

# MCP diagnostics
kagura mcp doctor

# View MCP stats
kagura mcp stats
```

### REST API

```bash
# Start API server
kagura api serve

# Or using uvicorn directly
uvicorn kagura.api.server:app --reload
```

**API Docs**: http://localhost:8000/docs

### Configuration

```bash
# View current config
kagura config show

# Run system diagnostics
kagura doctor

# Set default user/project
export KAGURA_DEFAULT_USER=your_name
export KAGURA_DEFAULT_PROJECT=your_project
```

---

## Next Steps

### For Individual Users

- **[Chat Integration Tips](docs/en/chat-integration-tips.md)** - Use with ChatGPT, Claude, etc.
- **[MCP Setup Guide](docs/en/mcp-setup.md)** - How to configure MCP
- **[Export Your Data](docs/en/memory-export.md)** - Complete data portability

### For Developers

- **[REST API Reference](docs/en/api-reference.md)** - Build custom agents
- **[MCP Tools Guide](docs/en/mcp-setup.md)** - All 56 MCP tools explained
- **[Coding Memory Guide](docs/en/coding-memory.md)** - Track development sessions
- **[Self-Hosting Guide](docs/en/self-hosting.md)** - Deploy to your own server

### For Contributors

- **[Architecture Docs](ai_docs/ARCHITECTURE.md)** - System design
- **[CLAUDE.md](CLAUDE.md)** - AI assistant development guide
- **[Contributing Guide](CONTRIBUTING.md)** - How to contribute

---

## Troubleshooting

### "Command 'kagura' not found"

**Solution**: Ensure `pip install kagura-ai[full]` succeeded and Python's bin directory is in your PATH.

```bash
# macOS/Linux
export PATH="$HOME/.local/bin:$PATH"

# Or use pipx for global installs
pipx install kagura-ai[full]
```

### MCP server won't start in Claude Desktop

**Check**:
1. Run `kagura mcp doctor` to diagnose issues
2. Verify config file location:
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
3. Check logs: `~/.cache/kagura/logs/mcp.log`

### ChromaDB errors

**Solution**: ChromaDB requires SQLite 3.35+. Upgrade:

```bash
# macOS
brew install sqlite

# Ubuntu/Debian
sudo apt update && sudo apt install sqlite3
```

### More help

- **[Full Troubleshooting Guide](docs/troubleshooting.md)**
- **[GitHub Issues](https://github.com/JFK/kagura-ai/issues)**
- **[Discussions](https://github.com/JFK/kagura-ai/discussions)**

---

## Example: Complete Workflow

Here's a complete workflow showing Kagura in action:

### 1. Morning: Store Knowledge

```bash
# Store a best practice you learned
kagura memory store \
  --key "fastapi_testing" \
  --value "Always use pytest-asyncio for async FastAPI tests. Use TestClient for sync endpoints only." \
  --tags "python,testing,fastapi"
```

### 2. Afternoon: Code with Claude Code

```
You: "Start coding session for 'add API tests'"
Claude: ✓ Started session

[... coding happens ...]

Claude: [Automatically tracks file changes via MCP tools]
You: "I got a TypeError in the async test"
Claude: [Records error and solution automatically]
```

### 3. Evening: Review Your Work

```bash
# See what you accomplished
kagura coding sessions --limit 1

# Check if similar errors happened before
kagura coding errors --type TypeError

# Search your past work
kagura coding search --query "API testing"
```

### 4. Share with AI Assistants

**In ChatGPT**:
```
You: "Search my memories for FastAPI testing best practices"
ChatGPT: [Uses remote MCP to query Kagura]
        "You prefer pytest-asyncio for async tests..."
```

**Result**: Your knowledge persists across **all AI platforms**!

---

## What's Next?

You're now ready to use Kagura! Here are some ideas:

1. **Connect Claude Desktop** → Use MCP tools in conversations
2. **Track a coding session** → See AI-generated summaries
3. **Build a custom agent** → Use the REST API
4. **Export your data** → Verify complete ownership

**Welcome to universal AI memory!** 🎉

---

*Last updated: 2025-11-09 (v4.3.0)*
