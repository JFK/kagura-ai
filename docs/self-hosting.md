# Self-Hosting Guide

**Kagura AI v4.0.0** - Universal AI Memory Platform

This guide explains how to self-host Kagura AI for production use with Docker.

---

## 📋 Overview

Self-hosting Kagura AI gives you:
- **Full control** over your data
- **Multi-user support** with authentication
- **Remote access** from any MCP client
- **Production-ready** setup with SSL/TLS

**Stack**:
- **Kagura API** - FastAPI server with MCP endpoint
- **PostgreSQL** - Persistent storage with pgvector
- **Redis** - Caching and job queue
- **Caddy** - Reverse proxy with automatic HTTPS

---

## 🚀 Quick Start

### Prerequisites

- **Server**: Ubuntu 22.04 LTS (or similar)
- **Docker**: 20.10+ and Docker Compose v2
- **Domain**: A domain name pointing to your server
- **Ports**: 80, 443 open

### 1. Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh

# Install Docker Compose
sudo apt-get update
sudo apt-get install docker-compose-plugin

# Verify
docker --version
docker compose version
```

### 2. Clone Repository

```bash
git clone https://github.com/YourUsername/kagura-ai.git
cd kagura-ai
```

### 3. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env
nano .env
```

**Required settings** in `.env`:

```bash
# Domain name (required for HTTPS)
DOMAIN=your-domain.com

# PostgreSQL password (required)
POSTGRES_PASSWORD=your_secure_password_here

# Optional: API Key requirement
API_KEY_REQUIRED=false  # Set to true to require API keys

# Optional: CORS origins
CORS_ORIGINS=https://chat.openai.com,https://claude.ai
```

### 4. Start Services

```bash
# Build and start
docker compose -f docker-compose.prod.yml up -d

# Check logs
docker compose -f docker-compose.prod.yml logs -f

# Check health
curl https://your-domain.com/api/v1/health
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DOMAIN` | ✅ Yes | - | Your domain name |
| `POSTGRES_PASSWORD` | ✅ Yes | - | Database password |
| `POSTGRES_DB` | No | `kagura` | Database name |
| `POSTGRES_USER` | No | `kagura` | Database user |
| `LOG_LEVEL` | No | `warning` | Log level (debug/info/warning/error) |
| `CORS_ORIGINS` | No | * | Allowed CORS origins (comma-separated) |
| `API_KEY_REQUIRED` | No | `false` | Require API key for all requests |

### SSL/TLS Configuration

Caddy automatically obtains SSL certificates from Let's Encrypt.

**Requirements**:
1. Domain must resolve to your server
2. Ports 80 and 443 must be accessible
3. Valid email for Let's Encrypt (Caddy will prompt)

**Manual SSL** (if needed):

Edit `Caddyfile`:
```caddy
your-domain.com {
    tls your-email@example.com
    # ... rest of config
}
```

---

## 🔐 Security

### 1. API Key Authentication

```bash
# Generate API key
docker compose -f docker-compose.prod.yml exec api kagura api create-key --name "production"

# Output:
# kagura_abc123xyz789...

# Save securely and use in requests
curl -H "Authorization: Bearer kagura_abc123..." \
     https://your-domain.com/mcp
```

### 2. Firewall Configuration

```bash
# Allow HTTP/HTTPS only
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Block direct database access
sudo ufw deny 5432/tcp
```

### 3. Regular Updates

```bash
# Update Kagura
cd kagura-ai
git pull
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

# Update system packages
sudo apt-get update && sudo apt-get upgrade -y
```

---

## 💾 Backup & Restore

### Automated Backup

Create backup script `backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/backups/kagura-$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# Export memory data
docker compose -f docker-compose.prod.yml exec -T api \
  kagura memory export --output /app/data/export

# Copy export from container
docker cp kagura-api-prod:/app/data/export "$BACKUP_DIR/"

# Backup PostgreSQL
docker compose -f docker-compose.prod.yml exec -T postgres \
  pg_dump -U kagura kagura > "$BACKUP_DIR/postgres.sql"

# Compress
tar -czf "$BACKUP_DIR.tar.gz" "$BACKUP_DIR"
rm -rf "$BACKUP_DIR"

echo "Backup saved to $BACKUP_DIR.tar.gz"
```

**Schedule with cron**:

```bash
# Run daily at 2 AM
0 2 * * * /path/to/backup.sh
```

### Restore from Backup

```bash
# Extract backup
tar -xzf kagura-20251027.tar.gz

# Import memory data
docker compose -f docker-compose.prod.yml exec api \
  kagura memory import --input /app/data/export

# Restore PostgreSQL (if needed)
docker compose -f docker-compose.prod.yml exec -T postgres \
  psql -U kagura kagura < postgres.sql
```

---

## 📊 Monitoring

### Health Checks

```bash
# API health
curl https://your-domain.com/api/v1/health

# Expected:
# {"status":"healthy","services":{"database":"healthy","redis":"healthy"}}

# Service status
docker compose -f docker-compose.prod.yml ps
```

### Logs

```bash
# All services
docker compose -f docker-compose.prod.yml logs -f

# API only
docker compose -f docker-compose.prod.yml logs -f api

# Caddy access logs
docker compose -f docker-compose.prod.yml exec caddy \
  tail -f /var/log/caddy/access.log
```

### Metrics

```bash
# Memory usage
curl https://your-domain.com/api/v1/metrics

# Expected:
# {
#   "memories_count": 1500,
#   "graph_nodes": 800,
#   "graph_edges": 450,
#   "storage_size_mb": 25.3
# }
```

---

## 🔧 Maintenance

### Update Kagura

```bash
cd kagura-ai
git pull
docker compose -f docker-compose.prod.yml build api
docker compose -f docker-compose.prod.yml up -d api
```

### Restart Services

```bash
# Restart all
docker compose -f docker-compose.prod.yml restart

# Restart API only
docker compose -f docker-compose.prod.yml restart api
```

### Database Maintenance

```bash
# Vacuum database (cleanup)
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U kagura -c "VACUUM ANALYZE;"

# Check database size
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U kagura -c "SELECT pg_size_pretty(pg_database_size('kagura'));"
```

---

## 🌐 Connecting Clients

### ChatGPT Connector

1. Enable Developer Mode in ChatGPT
2. Add connector:
   - **Name**: Kagura Memory
   - **URL**: `https://your-domain.com/mcp`
   - **Authentication**: Bearer token (if API key required)

### Claude Desktop (Remote)

Coming soon - stdio → HTTP proxy connector

### Custom MCP Clients

```python
import httpx

# MCP over HTTP/SSE
response = httpx.post(
    "https://your-domain.com/mcp",
    json={
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    },
    headers={"Authorization": "Bearer kagura_your_api_key"}
)
```

---

## 🐛 Troubleshooting

### Issue: Caddy cannot obtain SSL certificate

**Symptoms**: HTTP works but HTTPS fails

**Solutions**:
1. Verify domain DNS points to server: `nslookup your-domain.com`
2. Check ports 80/443 are accessible: `telnet your-domain.com 80`
3. Check Caddy logs: `docker logs kagura-caddy-prod`
4. Verify email is valid for Let's Encrypt

### Issue: API returns 503 Service Unavailable

**Symptoms**: `/api/v1/health` returns 503

**Solutions**:
1. Check database is healthy: `docker compose -f docker-compose.prod.yml ps postgres`
2. Check logs: `docker logs kagura-api-prod`
3. Verify DATABASE_URL is correct in `.env`

### Issue: High memory usage

**Symptoms**: Container using >2GB RAM

**Solutions**:
1. Enable Redis caching
2. Limit RAG vector database size
3. Run memory consolidation: `kagura memory export` then clear old data

### Issue: Cannot connect from ChatGPT

**Symptoms**: 401 Unauthorized or CORS errors

**Solutions**:
1. Verify API key is valid: `kagura api list-keys`
2. Check CORS_ORIGINS includes `https://chat.openai.com`
3. Verify domain is accessible: `curl https://your-domain.com/mcp`

---

## 📈 Performance Tuning

### Database Optimization

```bash
# Increase connection pool
# Add to docker-compose.prod.yml api environment:
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
```

### Redis Caching

```bash
# Configure Redis for caching
# Add to docker-compose.prod.yml redis command:
command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
```

### API Workers

```bash
# Use gunicorn for multiple workers
# Update api command in docker-compose.prod.yml:
command: gunicorn kagura.api.server:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8080
```

---

## 🔗 Related Documentation

- [MCP over HTTP/SSE Setup](./mcp-http-setup.md)
- [API Authentication](./api-authentication.md) *(coming soon)*
- [Memory Export/Import](./memory-export.md)
- [API Reference](./api-reference.md)

---

## 💬 Support

- **Issues**: [GitHub Issues](https://github.com/YourUsername/kagura-ai/issues)
- **Discussions**: [GitHub Discussions](https://github.com/YourUsername/kagura-ai/discussions)

---

**Last Updated**: 2025-10-27
**Version**: 4.0.0
