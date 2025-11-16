# Remote MCP Server Setup Guide

**Issue #668**: Remote MCP server configuration for GCP deployment

This guide explains how to set up Kagura's MCP (Model Context Protocol) server for remote access, enabling Claude Desktop, ChatGPT, and other AI clients to connect to your Kagura instance over HTTP/SSE.

## Architecture

```
AI Client (Claude Desktop/ChatGPT)
    ↓ HTTPS
Caddy Reverse Proxy (memory.kagura-ai.com)
    ↓ /mcp → http://kagura-api:8080/mcp
MCP HTTP Transport (FastAPI)
    ↓
Kagura MCP Server (Remote Context, Safe Tools Only)
    ↓
Backend Services (PostgreSQL, Redis, Qdrant)
```

## Security Model

**Remote MCP Context:**
- **Filtered Tools**: Dangerous tools (file ops, shell exec) are blocked
- **Allowed Tools**: Memory tools, coding tools, search tools, GitHub integration
- **Authentication**: Inherits API authentication (OAuth2/API keys)
- **Safe Operations Only**: Read-only and non-destructive operations

## Setup Instructions

### 1. GCP Instance Configuration

**Already Configured** (if using `docker-compose.cloud.yml`):
- MCP server runs automatically as part of `kagura-api` container
- HTTP/SSE transport enabled on internal port 8080
- Endpoint: `http://kagura-api:8080/mcp`

### 2. Reverse Proxy Configuration (Caddy)

Add the following to your `Caddyfile.cloud`:

```caddyfile
{$DOMAIN} {
    # Existing API routes
    reverse_proxy /api/* api:8080

    # MCP over HTTP/SSE (Issue #668)
    reverse_proxy /mcp api:8080 {
        # SSE requires longer timeouts
        flush_interval -1

        # Keep-alive for SSE connections
        header_up Connection "keep-alive"
        header_up Cache-Control "no-cache"

        # CORS for ChatGPT Connector (optional)
        @cors_preflight method OPTIONS
        handle @cors_preflight {
            header Access-Control-Allow-Origin "*"
            header Access-Control-Allow-Methods "GET, POST, DELETE, OPTIONS"
            header Access-Control-Allow-Headers "Content-Type, Authorization"
            respond 204
        }
    }

    # Existing web routes
    reverse_proxy /* web:3000
}
```

### 3. Enable Remote MCP (Optional)

Add to `.env.cloud`:

```bash
# Remote MCP Server (Issue #668)
MCP_REMOTE_ENABLED=true

# Optional: Filter tools by category
# MCP_ALLOWED_CATEGORIES=memory,coding,search,github
```

### 4. Rebuild and Restart

```bash
# On GCP instance
cd /opt/kagura
sudo docker-compose -f docker-compose.cloud.yml restart caddy
sudo docker-compose -f docker-compose.cloud.yml restart api
```

### 5. Verify Deployment

```bash
# Check doctor
curl https://memory.kagura-ai.com/api/v1/system/doctor

# Should show:
# "remote_mcp": {"status": "ok", "message": "Running (HTTP/SSE endpoint active)"}

# Test MCP endpoint (IMPORTANT: note the trailing slash and Accept header)
curl -X POST https://memory.kagura-ai.com/mcp/ \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc": "2.0", "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}, "id": 1}'

# Should return:
# {"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2024-11-05",...}}
```

**IMPORTANT Notes:**
- **Trailing slash required**: Use `/mcp/` not `/mcp` (FastAPI mount behavior)
- **Accept header required**: `Accept: application/json, text/event-stream`
- Authentication is optional for testing (uses "default_user")

## Client Configuration

### Claude Desktop (Official MCP Client)

**Not Recommended for Remote MCP** - Claude Desktop is designed for local stdio transport.

For remote access, use the Claude API or web interface at `https://memory.kagura-ai.com`.

### ChatGPT Connector (Custom GPT)

**Configuration:**

1. Create a custom GPT in ChatGPT
2. Add OpenAPI schema:

```yaml
openapi: 3.0.0
info:
  title: Kagura MCP Server
  version: 1.0.0
servers:
  - url: https://memory.kagura-ai.com
paths:
  /mcp:
    post:
      summary: MCP JSON-RPC endpoint
      operationId: mcpRequest
      security:
        - BearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [jsonrpc, method, id]
              properties:
                jsonrpc:
                  type: string
                  enum: ["2.0"]
                method:
                  type: string
                  description: MCP method name (e.g., tools/list, tools/call)
                params:
                  type: object
                id:
                  type: integer
      responses:
        '200':
          description: MCP response
components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
```

3. Add authentication (Bearer token from Kagura API keys)

### Python Client (mcp package)

```python
from mcp import ClientSession
from mcp.client.sse import sse_client

async def connect_to_kagura():
    async with sse_client(
        url="https://memory.kagura-ai.com/mcp",
        headers={"Authorization": "Bearer YOUR_API_KEY"}
    ) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize
            await session.initialize()

            # List tools
            tools = await session.list_tools()
            print(f"Available tools: {len(tools.tools)}")

            # Call a tool
            result = await session.call_tool(
                "kagura_tool_memory_search",
                arguments={
                    "user_id": "your-user-id",
                    "agent_name": "global",
                    "query": "test query"
                }
            )
```

## Available Tools (Remote Context)

Remote MCP server provides **safe tools only**:

### Memory Tools (10+)
- `memory_store`, `memory_recall`, `memory_delete`
- `memory_search`, `memory_search_ids`, `memory_fetch`
- `memory_timeline`, `memory_fuzzy_recall`
- `memory_stats`, `memory_list`, `memory_feedback`

### Coding Tools (20+)
- `coding_start_session`, `coding_end_session`, `coding_resume_session`
- `coding_track_file_change`, `coding_record_error`, `coding_record_decision`
- `coding_search_errors`, `coding_get_project_context`
- `coding_sessions`, `coding_decisions`, `coding_errors`

### Search Tools
- `brave_web_search`, `brave_news_search`, `brave_image_search`
- `arxiv_search`, `youtube_summarize`, `fact_check_claim`

### GitHub Integration
- `github_issue_create`, `github_issue_view`, `github_pr_create`
- `github_pr_view`, `github_pr_merge`

### **Filtered Out** (Dangerous Operations)
- ❌ `file_read`, `file_write` - File system access
- ❌ `shell_exec` - Shell command execution
- ❌ `media_open_*` - Local file opening

## Troubleshooting

### MCP Endpoint Returns 404

**Cause:** Caddy not routing `/mcp` to API container

**Fix:**
1. Check Caddyfile.cloud has `/mcp` reverse_proxy directive
2. Restart Caddy: `docker-compose -f docker-compose.cloud.yml restart caddy`
3. Check Caddy logs: `docker logs kagura-caddy`

### MCP Endpoint Returns 401 Unauthorized

**Cause:** Missing or invalid authentication

**Fix:**
1. Generate API key: `https://memory.kagura-ai.com/api-keys`
2. Include in request: `Authorization: Bearer YOUR_KEY`

### Doctor Shows "Remote MCP: Not enabled"

**Cause:** `MCP_REMOTE_ENABLED=true` not set

**Fix:**
1. Add to `.env.cloud`: `MCP_REMOTE_ENABLED=true`
2. Restart API: `docker-compose -f docker-compose.cloud.yml restart api`
3. Run doctor: `kagura doctor`

### ChatGPT Connector Timeout

**Cause:** SSE connection timeout or CORS issues

**Fix:**
1. Ensure Caddyfile has CORS headers (see Step 2 above)
2. Check `flush_interval -1` is set for SSE
3. Increase timeout in ChatGPT configuration

## Monitoring

```bash
# Check doctor status
kagura doctor

# Check remote MCP in doctor output:
# 5. Remote MCP Server
#    ✓ HTTP/SSE Endpoint: Running (HTTP/SSE, 45 tools)

# Check API doctor endpoint
curl https://memory.kagura-ai.com/api/v1/system/doctor | python -m json.tool

# Monitor MCP requests (if telemetry enabled)
kagura telemetry stats --limit 100 | grep mcp
```

## Performance Considerations

- **SSE Connections**: Keep-alive connections consume resources
- **Tool Filtering**: Remote context filters ~10 dangerous tools automatically
- **Rate Limiting**: Consider adding rate limiting for remote MCP endpoints
- **Authentication**: Every MCP request validates bearer token (slight overhead)

## Security Best Practices

1. **Use HTTPS Only**: Never expose MCP over plain HTTP
2. **API Key Rotation**: Rotate API keys regularly
3. **Tool Categories**: Limit tool access using `MCP_ALLOWED_CATEGORIES`
4. **Audit Logging**: Enable telemetry to track MCP tool usage
5. **Network Isolation**: Use VPC/firewall rules to restrict access

## Related Documentation

- [MCP Specification](https://github.com/anthropics/mcp)
- [Kagura API Reference](./api-reference.md)
- [API Keys Management](../README.md#api-keys)
- [Docker Deployment](../docker-compose.cloud.yml)

## Support

For issues or questions:
- GitHub Issues: https://github.com/JFK/kagura-ai/issues
- Label: `mcp`, `deployment`, `documentation`
