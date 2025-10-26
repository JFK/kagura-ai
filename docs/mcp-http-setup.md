# MCP over HTTP/SSE Setup Guide

**Kagura AI v4.0.0** - Universal AI Memory Platform

This guide explains how to connect to Kagura Memory via HTTP/SSE transport using the MCP (Model Context Protocol).

---

## 📋 Overview

Kagura AI provides an HTTP/SSE endpoint at `/mcp` that implements the MCP protocol, enabling:

- **ChatGPT Connectors**: Connect ChatGPT to Kagura memory
- **Other HTTP-based MCP clients**: Any MCP client that supports HTTP transport
- **Remote access**: Access Kagura memory from anywhere

**Supported Operations**:
- GET `/mcp` - SSE streaming (server → client messages)
- POST `/mcp` - JSON-RPC requests (client → server messages)
- DELETE `/mcp` - Session termination

---

## 🚀 Quick Start

### 1. Start Kagura API Server

```bash
# Install Kagura with API extras
pip install kagura-ai[api]

# Start the API server
uvicorn kagura.api.server:app --host 0.0.0.0 --port 8000
```

The `/mcp` endpoint will be available at `http://localhost:8000/mcp`.

---

### 2. Connect ChatGPT (Developer Mode)

**Note**: ChatGPT Connector support is currently in developer preview.

#### Step 1: Enable Developer Mode

1. Open ChatGPT settings
2. Navigate to: **Settings → Connectors → Advanced → Developer Mode**
3. Enable Developer Mode

#### Step 2: Add Kagura Connector

Add a custom connector with the following settings:

```json
{
  "name": "Kagura Memory",
  "url": "http://localhost:8000/mcp",
  "description": "Universal AI Memory Platform",
  "authentication": "none"
}
```

**For remote access** (using ngrok):

```bash
# Expose local server
ngrok http 8000

# Use the ngrok URL in ChatGPT
# Example: https://abc123.ngrok.app/mcp
```

#### Step 3: Test the Connection

In ChatGPT, try:

```
"Remember: I prefer Python for backend development"
"What do you know about my preferences?"
```

Kagura will store and recall your preferences across all AI platforms!

---

## 🔧 Advanced Configuration

### API Authentication (Phase C Task 2 ✅)

Kagura API now supports API Key authentication for secure remote access.

#### Generate API Key

```bash
# Create a new API key
kagura api create-key --name "chatgpt-connector"

# Output:
# ✓ API key created successfully!
# ⚠️  Save this key securely - it won't be shown again:
#
#   kagura_abc123xyz789...
```

**⚠️ Important**: The API key is only shown once during creation. Save it securely!

#### Use API Key in Requests

```bash
# Use in HTTP requests
curl -H "Authorization: Bearer kagura_abc123xyz789..." \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' \
     http://localhost:8000/mcp
```

#### Manage API Keys

```bash
# List all API keys
kagura api list-keys

# List keys for specific user
kagura api list-keys --user-id user_alice

# Revoke a key (keeps audit history)
kagura api revoke-key --name "old-key"

# Permanently delete a key
kagura api delete-key --name "unused-key"
```

#### API Key Options

```bash
# Create key with expiration (90 days)
kagura api create-key --name "temp-key" --expires 90

# Create key for specific user
kagura api create-key --name "alice-key" --user-id user_alice
```

---

### Tool Access Control (Phase C Task 3 ✅)

Kagura automatically filters dangerous tools when accessed remotely via HTTP/SSE.

#### Safe vs. Dangerous Tools

**✅ Safe for Remote Access** (allowed via `/mcp`):
- **Memory tools**: `memory_store`, `memory_recall`, `memory_search`, etc.
- **Web/API tools**: `web_search`, `brave_web_search`, `youtube_summarize`, etc.
- **Multimodal tools**: `multimodal_index`, `multimodal_search`
- **Telemetry tools**: `telemetry_stats`, `telemetry_cost`

**⛔ Dangerous - Local Only** (blocked via `/mcp`):
- **File operations**: `file_read`, `file_write`, `dir_list`
- **Shell execution**: `shell_exec`
- **Local app execution**: `media_open_audio`, `media_open_image`, `media_open_video`

#### Why Tool Filtering?

Remote access to file operations or shell commands would allow:
- Reading sensitive files (`/etc/passwd`, API keys, etc.)
- Writing malicious files
- Executing arbitrary commands on your server

**Solution**: The `/mcp` endpoint automatically filters out dangerous tools.

#### Checking Tool Permissions

```bash
# List all available tools (via HTTP/SSE)
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'

# file_read, shell_exec, etc. will NOT appear in the list
```

#### Local vs. Remote Context

```python
# Local MCP server (stdio) - ALL tools available
kagura mcp serve  # Exposes all 31 tools

# Remote HTTP/SSE server - Only safe tools
uvicorn kagura.api.server:app  # Exposes ~24 safe tools
```

---

### User ID Header

Specify which user's memory to access:

```bash
# Request with user ID
curl -H "X-User-ID: user_alice" \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' \
     http://localhost:8000/mcp
```

**Default**: If no `X-User-ID` header is provided, `default_user` is used.

---

### CORS Configuration

For production deployments, configure CORS in `src/kagura/api/server.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://chat.openai.com"],  # Specify origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)
```

---

## 🧪 Testing the Endpoint

### 1. Health Check

```bash
curl http://localhost:8000/
# Expected: {"name":"Kagura Memory API","version":"4.0.0",...}
```

### 2. MCP Protocol Test

#### Initialize Session

```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {"name": "test-client", "version": "1.0.0"}
    }
  }'
```

#### List Available Tools

```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": {}
  }'
```

#### Store a Memory

```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "X-User-ID: test_user" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "kagura_tool_memory_store",
      "arguments": {
        "user_id": "test_user",
        "agent_name": "global",
        "key": "my_preference",
        "value": "I prefer Python for backend",
        "scope": "persistent",
        "tags": "[\"preferences\"]",
        "importance": 0.8
      }
    }
  }'
```

---

## 🌐 Production Deployment

### Docker Compose

```yaml
version: '3.8'

services:
  kagura-api:
    image: kagura-ai:4.0.0
    ports:
      - "8000:8000"
    environment:
      - KAGURA_API_KEY=${KAGURA_API_KEY}
    command: uvicorn kagura.api.server:app --host 0.0.0.0 --port 8000
    restart: always

  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl
    depends_on:
      - kagura-api
```

### Nginx Configuration

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /etc/ssl/cert.pem;
    ssl_certificate_key /etc/ssl/key.pem;

    location /mcp {
        proxy_pass http://kagura-api:8000/mcp;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;

        # SSE support
        proxy_buffering off;
        proxy_set_header X-Accel-Buffering no;
    }
}
```

---

## 🔍 Troubleshooting

### Connection Refused

**Problem**: Cannot connect to `/mcp` endpoint

**Solutions**:
1. Verify API server is running: `curl http://localhost:8000/`
2. Check firewall rules
3. Verify port 8000 is not in use

### 406 Not Acceptable

**Problem**: Receiving HTTP 406 errors

**Cause**: Missing `Accept` header for MCP protocol

**Solution**: Include proper MCP headers in requests

### Background Task Not Starting

**Problem**: MCP server background task fails to start

**Cause**: Event loop not available

**Solution**: Ensure the first request to `/mcp` is made after the API server has fully started

---

## 📚 API Reference

### Available MCP Tools

When connected via `/mcp`, the following tools are available:

#### Memory Tools
- `kagura_tool_memory_store` - Store information
- `kagura_tool_memory_recall` - Semantic search
- `kagura_tool_memory_search` - Full-text search
- `kagura_tool_memory_list` - List all memories
- `kagura_tool_memory_delete` - Delete memory

#### Graph Tools (if enabled)
- `kagura_tool_graph_link` - Link memories
- `kagura_tool_graph_query` - Query knowledge graph

For full tool documentation, call `tools/list` via the MCP protocol.

---

## 🔗 Related Documentation

- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [Kagura API Reference](./api-reference.md)
- [ChatGPT Connectors Documentation](https://developers.openai.com/apps-sdk/deploy/connect-chatgpt/)
- [Self-Hosting Guide](./self-hosting.md) *(coming soon)*

---

## 💬 Support

- **Issues**: [GitHub Issues](https://github.com/YourUsername/kagura-ai/issues)
- **Discussions**: [GitHub Discussions](https://github.com/YourUsername/kagura-ai/discussions)

---

**Last Updated**: 2025-10-27
**Version**: 4.0.0
