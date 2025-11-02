# Getting Started with Kagura AI v4.0

> **Universal AI Memory Platform - 10-minute setup**

Kagura is a universal memory layer that connects all your AI platforms (Claude, ChatGPT, Gemini, etc.) with shared context and memory.

---

## 📋 What is Kagura v4.0?

**Kagura v4.0** = **MCP-native Universal Memory**

- **For Claude Desktop**: Local MCP server with all 31 tools
- **For ChatGPT**: HTTP/SSE connector with memory access
- **For Teams**: Self-hosted API with authentication
- **For Developers**: REST API + Python SDK

---

## 🚀 Quick Start (Choose Your Path)

### Path 1: Claude Desktop User (Recommended)

**Setup time**: 5 minutes

```bash
# Install Kagura
pip install kagura-ai[full]

# Auto-configure Claude Desktop
kagura mcp install

# Restart Claude Desktop
# That's it! Kagura is now available in Claude
```

**Try it in Claude Desktop**:
```
"Remember: I prefer Python for backend development"
"What do you know about my preferences?"
```

**See**: [MCP Setup Guide](mcp-setup.md)

---

### Path 2: ChatGPT Connector User

**Setup time**: 10 minutes

1. **Start Kagura API**:
   ```bash
   # Using Docker
   docker compose up -d

   # Or local
   pip install kagura-ai[api]
   uvicorn kagura.api.server:app --port 8000
   ```

2. **Expose with ngrok** (for testing):
   ```bash
   ngrok http 8000
   # Get URL: https://abc123.ngrok.app
   ```

3. **Configure ChatGPT**:
   - Enable Developer Mode
   - Add Connector:
     - URL: `https://abc123.ngrok.app/mcp`
     - Name: Kagura Memory

**See**: [MCP over HTTP/SSE Guide](mcp-http-setup.md)

---

### Path 3: Self-Hosted Production

**Setup time**: 30 minutes

```bash
# Clone repository
git clone https://github.com/JFK/kagura-ai.git
cd kagura-ai

# Configure
cp .env.example .env
nano .env  # Set DOMAIN and POSTGRES_PASSWORD

# Deploy
docker compose -f docker-compose.prod.yml up -d

# Generate API key
docker compose -f docker-compose.prod.yml exec api \
  kagura api create-key --name "production"

# Verify
curl https://your-domain.com/api/v1/health
```

**See**: [Self-Hosting Guide](self-hosting.md)

---

## 🧩 Key Features

### 1. Universal Memory

Store memories once, access from any AI:

```python
# Via MCP tool (Claude Desktop, ChatGPT, etc.)
memory_store(
    user_id="jfk",
    agent_name="global",
    key="coding_style",
    value="Always use type hints in Python",
    scope="persistent",
    tags='["python", "best-practices"]'
)
```

### 2. Graph Memory

Track relationships and patterns:

```python
# Record interaction
memory_record_interaction(
    user_id="jfk",
    query="How do I write async functions?",
    response="...",
    metadata={"topic": "python", "skill_level": "intermediate"}
)

# Analyze patterns
memory_get_user_pattern(user_id="jfk")
```

### 3. Remote Access

Access your memory from anywhere:

- **ChatGPT Connector**: HTTP/SSE transport
- **API Keys**: Secure authentication
- **Tool Filtering**: Automatic security (no file ops remotely)

### 4. Export/Import

Own your data completely:

```bash
# Backup
kagura memory export --output ./backup

# Restore
kagura memory import --input ./backup
```

---

## 📚 Next Steps

### For Claude Desktop Users

1. [Complete MCP Setup](mcp-setup.md)
2. Try built-in tools: `kagura mcp tools`
3. Explore memory operations

### For ChatGPT Users

1. [Setup HTTP/SSE Connector](mcp-http-setup.md)
2. Generate API key: `kagura api create-key`
3. Connect and test

### For Self-Hosters

1. [Follow Self-Hosting Guide](self-hosting.md)
2. Configure SSL/TLS with Caddy
3. Set up backups

### For Developers

1. [REST API Reference](api-reference.md)
2. [Architecture Overview](architecture.md)
3. [Memory Export/Import](memory-export.md)

---

## 🔍 Available Commands

```bash
# MCP Management
kagura mcp serve           # Start MCP server (Claude Desktop)
kagura mcp install         # Auto-configure Claude Desktop
kagura mcp tools           # List available tools
kagura mcp doctor          # Run diagnostics
kagura mcp connect         # Configure remote connection
kagura mcp test-remote     # Test remote API

# API Key Management
kagura api create-key      # Generate API key
kagura api list-keys       # List all keys
kagura api revoke-key      # Revoke key

# Memory Management
kagura memory export       # Export to JSONL
kagura memory import       # Import from JSONL

# System
kagura --version           # Show version
```

---

## 💬 Support

- **Documentation**: https://kagura-ai.com/docs
- **GitHub Issues**: https://github.com/JFK/kagura-ai/issues
- **Discussions**: https://github.com/JFK/kagura-ai/discussions

---

**Version**: 4.0.0
**Protocol**: MCP (Model Context Protocol)
**License**: Apache 2.0
