# Troubleshooting Guide

> **Common issues and solutions for Kagura AI**

This guide helps you diagnose and fix common problems with Kagura AI integration.

---

## 🔍 Quick Diagnostics

### Step 1: Run Doctor Command

```bash
kagura mcp doctor
```

**Expected output**:
```
Kagura MCP Diagnostics
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Python version: 3.11.5
✅ Kagura installed: 4.0.0
✅ MCP server: Configured
✅ Database: Connected (342 memories)
✅ Vector store: Healthy (ChromaDB)

Configuration:
  Data dir: ~/.local/share/kagura
  Cache dir: ~/.cache/kagura
  Config dir: ~/.config/kagura
```

### Step 2: Check Server Status

**Local MCP (Claude Desktop/Code)**:
```bash
# Claude Code
claude mcp list

# Check Kagura logs
kagura mcp log --tail
```

**Remote MCP (ChatGPT)**:
```bash
# Check API health
curl http://localhost:8080/api/v1/health

# Check MCP endpoint
curl http://localhost:8080/mcp

# Check logs
docker compose logs -f api
```

---

## 🚨 Common Issues

### Issue 0: "No result received from client-side tool execution"

**Symptoms**:
- MCP tool hangs and times out
- Error: "No result received from client-side tool execution"
- Happens on first use of memory tools

**Root Cause**:
First-time execution downloads embeddings model (~500MB), taking 30-60 seconds. MCP client times out waiting for response.

**Solution**: Pre-download embeddings model

```bash
# Run this ONCE before using MCP memory tools
kagura memory setup
```

**Output**:
```
Kagura Memory Setup

Downloading embeddings model: intfloat/multilingual-e5-large
(~500MB, may take 30-60 seconds)

✓ Model downloaded successfully!

  Model: intfloat/multilingual-e5-large
  Dimension: 1024

MCP memory tools are now ready to use!
```

**After setup**: MCP memory tools work instantly (no timeout).

**Alternative**: Use Claude Code terminal to run setup during first conversation.

---

### Issue 1: MCP Server Not Connecting

**Symptoms**:
- Claude can't see Kagura tools
- "Server not responding" error
- Tools list is empty

**Diagnosis**:

```bash
# Claude Code
claude mcp list
# Should show: kagura: ✓ Connected

# If not connected, check logs
kagura mcp log
```

**Solutions**:

#### Solution A: Restart MCP Server (Local)

```bash
# Claude Desktop
# 1. Quit Claude Desktop completely
# 2. Restart Claude Desktop
# 3. Start new conversation

# Claude Code
# 1. Remove and re-add server
claude mcp remove kagura
claude mcp add --transport stdio kagura -- kagura mcp serve

# 2. Verify
claude mcp list
```

#### Solution B: Check Command Path

**Problem**: `kagura: command not found`

```bash
# Find kagura path
which kagura
# Output: /home/user/.local/bin/kagura

# Use full path in config
claude mcp add --transport stdio kagura -- /home/user/.local/bin/kagura mcp serve
```

#### Solution C: Check Permissions

```bash
# Make sure kagura is executable
chmod +x $(which kagura)

# Check Python environment
python --version  # Should be 3.11+
pip show kagura-ai  # Should show version 4.0.0+
```

---

### Issue 2: Memory Not Persisting

**Symptoms**:
- Memories disappear after conversation ends
- "No memories found" in next session
- Lost progress

**Diagnosis**:

```bash
# Check memory statistics
kagura mcp tools  # In Claude, run: "Show memory stats"

# Check database
ls -lh ~/.local/share/kagura/memory.db
```

**Solutions**:

#### Solution A: Verify Memory Storage

**Problem**: Memory not being stored correctly

**Fix**: Ensure memory operations are successful

```
❌ "Remember that I prefer Python"  # Vague instruction
✅ "Store in memory: I prefer Python"  # Clear instruction
✅ memory_store(key="python_preference", value="Python")
```

**In prompts**:
```python
memory_store(
    key="python_preference",
    value="FastAPI over Django"
)
```

**Note**: As of v4.4.0, all memory is persistent by default. No need for `scope` parameter.

#### Solution B: Check user_id

**Problem**: Different `user_id` in each session

```
# Session 1
"Remember for user_id='john': I prefer Python"

# Session 2 (different user_id!)
"What do I prefer?"  # Uses default user_id → no results
```

**Fix**: Use consistent `user_id`:

```
# Always specify the same user_id
"For user_id='john': What programming languages do I prefer?"
```

---

### Issue 3: File Operations Not Working (Remote MCP)

**Symptoms**:
- "file_read not found"
- "Cannot access files"
- Upload doesn't work

**Diagnosis**:

This is **expected behavior** for Remote MCP (ChatGPT, Claude Chat).

**Why**: Remote MCP runs over HTTP/SSE and doesn't have direct file system access for security reasons.

**Solutions**:

#### Solution A: Use Local MCP for File Operations

Switch to Claude Desktop or Claude Code:

```bash
# Claude Desktop
kagura mcp install

# Claude Code
claude mcp add --transport stdio kagura -- kagura mcp serve
```

Now you can use:
- `file_read`
- `file_write`
- `dir_list`
- `media_open_*`

#### Solution B: Copy/Paste Content (Remote MCP)

If you must use Remote MCP:

```
# Instead of "Read config.py"
# → Copy/paste the file content into chat

User: "Here's my config.py content:
      [paste content]

      Analyze this configuration"
```

#### Solution C: Wait for v4.1 File Upload

**Future**: Multimodal Upload API is planned for v4.1

See: [Issue #462](https://github.com/JFK/kagura-ai/issues/462)

---

### Issue 4: Search Returns No Results

**Symptoms**:
- `memory_search` returns empty
- "No memories found"
- Can't find stored information

**Diagnosis**:

```
# In Claude/ChatGPT:
"List all my memories"
[Uses memory_list]

"Show memory statistics"
[Uses memory_stats]
```

**Solutions**:

#### Solution A: Check Memory Exists

```
"List all memories"

# If empty → No memories stored yet
# If has memories → Continue to next solutions
```

#### Solution B: Use Correct Search Type

**Semantic search** (meaning-based):
```
✅ "Find memories about backend development"
✅ "Search for information on API design"
```

**Exact key recall**:
```
✅ "Recall memory with key='python_preference'"
```

**Wrong approach**:
```
❌ "Search for exact text 'I prefer FastAPI over Django'"
```

#### Solution C: Check Filters

**Problem**: Too restrictive filters

```python
# Too specific (no results)
memory_search(
    query="FastAPI",
    tags=["python", "web", "api", "backend", "2024"]  # Too many tags
)

# Better (more results)
memory_search(
    query="FastAPI",
    tags=["python"]  # Fewer tags
)

# Best (most results)
memory_search(
    query="FastAPI"  # No filters
)
```

#### Solution D: Verify user_id and agent_name

```
# Check what you're searching
"Search memories for user_id='john' with agent_name='global'"

# If no results, try different combinations
"Search all memories regardless of user_id"
```

---

### Issue 5: High API Costs

**Symptoms**:
- Unexpected OpenAI/Anthropic bills
- Embedding API costs too high
- Token usage warnings

**Diagnosis**:

```
# Check cost summary
"Show telemetry cost summary"
[Uses telemetry_cost]

# Check tool usage
kagura mcp stats
```

**Solutions**:

#### Solution A: Use Local Embeddings

**Problem**: Using OpenAI API for embeddings

**Fix**: Switch to local sentence-transformers

```bash
# Install AI extras (includes sentence-transformers)
pip install kagura-ai[ai]

# Configure to use local embeddings
# In .env or environment:
KAGURA_EMBEDDING_MODEL=local  # Uses E5 model (free, local)
```

**Cost comparison**:
- OpenAI embeddings: $0.0001 per 1K tokens
- Local E5 embeddings: $0 (runs on your machine)

#### Solution B: Use Low-Token Search

Instead of `memory_search` (returns full content), use `memory_search_ids`:

```python
# High token usage
memory_search(query="FastAPI", k=10)
# Returns 10 full memories → ~5000 tokens

# Low token usage
memory_search_ids(query="FastAPI", k=10)
# Returns 10 IDs + previews → ~500 tokens
```

#### Solution C: Reduce Search Frequency

Cache search results:

```
# Instead of searching multiple times
"Find memories about Python"  # Search 1
"Find memories about Python"  # Search 2 (duplicate!)

# Better: Search once, then reference
"Find memories about Python"  # Search once
"Based on those memories, what should I use for backend?"  # No search
```

#### Solution D: Monitor Costs

```
# Regular cost checks
"Show me telemetry cost for the last week"

# Set budget alerts (future feature)
```

---

### Issue 6: Slow Performance

**Symptoms**:
- Search takes > 5 seconds
- Memory operations timeout
- API responses slow

**Diagnosis**:

```bash
# Check database size
du -sh ~/.local/share/kagura/

# Check memory count
kagura mcp tools  # Then: "Show memory stats"

# Check system resources
top  # Look for high CPU/memory usage
```

**Solutions**:

#### Solution A: Clean Up Old Memories

```bash
# Export first (backup)
kagura memory export --output=./backup

# Delete old/unused memories
# In Claude/ChatGPT:
"Delete memories older than 6 months with usefulness score < 0.3"
```

#### Solution B: Optimize ChromaDB

```bash
# Compact database
cd ~/.cache/kagura/chromadb
# ChromaDB auto-compacts, but you can restart to force it

# Or rebuild from scratch
kagura memory export --output=./backup
rm -rf ~/.cache/kagura/chromadb
kagura memory import --input=./backup
```

#### Solution C: Use BM25 for Exact Matches

**Semantic search (slow for large datasets)**:
```python
memory_search(query="FastAPI", mode="vector")  # Slow for 10K+ memories
```

**BM25 lexical search (fast)**:
```python
memory_search(query="FastAPI", mode="bm25")  # Fast even for 100K+ memories
```

**Hybrid (best accuracy + speed)**:
```python
memory_search(query="FastAPI", mode="hybrid")  # Balanced
```

---

### Issue 7: Authentication Errors (Remote MCP)

**Symptoms**:
- "401 Unauthorized"
- "Invalid API key"
- "Authentication required"

**Diagnosis**:

```bash
# Check API key exists
kagura api list-keys

# Test authentication
curl -H "Authorization: Bearer YOUR_KEY" \
     http://localhost:8080/api/v1/health
```

**Solutions**:

#### Solution A: Create API Key

```bash
# Generate new API key
kagura api create-key --name "chatgpt-integration"

# Output:
# Created API key: kg_xxxxxxxxxxxxxxxxxxxxxxxx
# Save this key securely!
```

#### Solution B: Configure MCP with API Key

**ChatGPT MCP configuration**:
```json
{
  "url": "https://your-domain.com/mcp",
  "headers": {
    "Authorization": "Bearer kg_xxxxxxxxxxxxxxxxxxxxxxxx"
  }
}
```

#### Solution C: Check Key Permissions

```bash
# View key details
kagura api get-key kg_xxxxxxxx

# Rotate if compromised
kagura api rotate-key kg_xxxxxxxx

# Revoke if needed
kagura api revoke-key kg_xxxxxxxx
```

---

### Issue 8: Docker Issues

**Symptoms**:
- "Cannot connect to Docker daemon"
- Containers not starting
- Port conflicts

**Diagnosis**:

```bash
# Check Docker status
docker ps

# Check logs
docker compose logs -f

# Check ports
lsof -i :8080  # API port
lsof -i :5432  # PostgreSQL port
lsof -i :6379  # Redis port
```

**Solutions**:

#### Solution A: Start Docker

```bash
# Linux
sudo systemctl start docker

# macOS
# Open Docker Desktop

# Verify
docker ps
```

#### Solution B: Fix Port Conflicts

**Problem**: Port 8080 already in use

```bash
# Find what's using the port
lsof -i :8080

# Kill the process
kill -9 <PID>

# Or change Kagura port in docker-compose.yml
ports:
  - "8090:8080"  # Use 8090 instead
```

#### Solution C: Reset Docker Environment

```bash
# Stop all containers
docker compose down

# Remove volumes (⚠️ deletes data!)
docker compose down -v

# Rebuild
docker compose up -d --build

# Check health
curl http://localhost:8080/api/v1/health
```

---

## 🔧 Advanced Troubleshooting

### Enable Debug Logging

```bash
# Set log level
export KAGURA_LOG_LEVEL=DEBUG

# Start MCP server with debug logs
kagura mcp serve

# Or for API
uvicorn kagura.api.server:app --log-level debug
```

### Check Database Integrity

```bash
# SQLite integrity check
sqlite3 ~/.local/share/kagura/memory.db "PRAGMA integrity_check;"

# Expected output: ok
```

### Rebuild Vector Index

```bash
# Export memories
kagura memory export --output=./backup

# Clear vector store
rm -rf ~/.cache/kagura/chromadb

# Re-import (will rebuild vectors)
kagura memory import --input=./backup
```

### Test MCP Tools Manually

```bash
# Test individual tools via API
curl -X POST http://localhost:8080/api/v1/memory/store \
  -H "Content-Type: application/json" \
  -d '{
    "key": "test",
    "value": "test value",
    "scope": "working"
  }'

# Check if it was stored
curl http://localhost:8080/api/v1/memory/list
```

---

## 📚 Getting Help

### 1. Check Documentation

- [Chat Integration Tips](./chat-integration-tips.md)
- [MCP Setup Guides](./mcp-setup.md)
- [API Reference](./api-reference.md)
- [Architecture](./architecture.md)

### 2. Search Existing Issues

[GitHub Issues](https://github.com/JFK/kagura-ai/issues)

### 3. Ask the Community

[GitHub Discussions](https://github.com/JFK/kagura-ai/discussions)

### 4. Report a Bug

```bash
# Create a new issue with diagnostic info
kagura mcp doctor > diagnostics.txt

# Attach diagnostics.txt when creating issue
gh issue create --title "Bug: [describe issue]" \
                --body "See attached diagnostics.txt"
```

---

## 📊 Diagnostic Checklist

Before reporting an issue, collect this information:

```bash
# 1. Version info
kagura --version
python --version
pip show kagura-ai

# 2. System info
uname -a  # Linux/macOS
cat /etc/os-release  # Linux distribution

# 3. Diagnostic report
kagura mcp doctor

# 4. Recent logs
kagura mcp log --lines 100

# 5. Error message
# Copy the full error message + stack trace

# 6. Steps to reproduce
# Write down exact steps that cause the issue
```

---

**Version**: 4.0.0
**Last updated**: 2025-11-02
