# OpenAPI Specification

**Kagura Memory API v4.0** - Complete OpenAPI Reference

---

## 📋 Overview

Kagura Memory API provides RESTful endpoints for memory management, graph operations, and system monitoring.

**OpenAPI Version**: 3.1.0
**API Version**: 4.0.0

---

## 🔗 Interactive Documentation

### 1. Redocly Documentation (Recommended) ⭐

**Static HTML**: [index.html](index.html)
- Beautiful, interactive API explorer
- Generated from `reference.yaml` using Redocly
- No server required - open in browser
- **Build**: `make build_docs`

### 2. Live API Documentation (Server Required)

When running the Kagura API server:

**Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- Interactive API testing
- Try endpoints directly from browser
- See request/response examples
- Execute requests with authentication

**ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- Clean, readable API documentation
- Search functionality
- Code samples

### 3. OpenAPI YAML

**Spec File**: [reference.yaml](reference.yaml)
- Source of truth for API specification
- Use for client SDK generation
- Import into Postman, Insomnia, etc.

---

## 📄 OpenAPI Specification File

**File**: [`reference.yaml`](reference.yaml)

Download and use with your favorite tools:

```bash
# Download spec
curl http://localhost:8000/openapi.json > openapi.json

# Generate client SDK
npx @openapitools/openapi-generator-cli generate \
  -i openapi.json \
  -g python \
  -o ./kagura-client

# Validate spec
npx @stoplight/spectral-cli lint openapi.json
```

---

## 🌐 API Endpoints

### Memory Operations

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/memory` | Create/update memory |
| GET | `/api/v1/memory` | List memories |
| GET | `/api/v1/memory/{key}` | Get memory by key |
| PUT | `/api/v1/memory/{key}` | Update memory |
| DELETE | `/api/v1/memory/{key}` | Delete memory |

### Search & Recall

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/search` | Full-text search |
| POST | `/api/v1/recall` | Semantic search (RAG) |

### Graph Operations

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/graph/interactions` | Record AI-User interaction |
| GET | `/api/v1/graph/{node_id}/related` | Get related nodes |
| GET | `/api/v1/graph/users/{user_id}/pattern` | Analyze user pattern |

### System

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API root information |
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/metrics` | System metrics |

### MCP Transport (Phase C)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/mcp` | SSE streaming (server → client) |
| POST | `/mcp` | JSON-RPC requests (client → server) |
| DELETE | `/mcp` | Session termination |

---

## 🔐 Authentication

### Headers

**X-User-ID** (optional):
```
X-User-ID: user_jfk
```
Specifies which user's memory to access. Defaults to `default_user`.

**Authorization** (optional, Phase C):
```
Authorization: Bearer kagura_abc123xyz789...
```
API Key for authentication. User ID is extracted from validated key.

---

## 📦 Schemas

### Memory

**MemoryCreate**:
```yaml
type: object
required: [key, value]
properties:
  key: string
  value: string
  scope: string (working|persistent)
  tags: array of strings
  importance: number (0.0-1.0)
  metadata: object
```

**MemoryResponse**:
```yaml
type: object
properties:
  key: string
  value: string
  scope: string
  tags: array
  importance: number
  created_at: string (datetime)
  updated_at: string (datetime)
```

### Search

**RecallRequest**:
```yaml
type: object
required: [query]
properties:
  query: string
  k: integer (default: 5)
  scope: string (all|working|persistent)
```

**RecallResponse**:
```yaml
type: object
properties:
  results: array
    items:
      key: string
      value: string
      score: number
```

### Graph

**InteractionCreate**:
```yaml
type: object
required: [user_id, query, response]
properties:
  user_id: string
  query: string
  response: string
  metadata: object
  ai_platform: string (optional)
```

**UserPattern**:
```yaml
type: object
properties:
  user_id: string
  total_interactions: integer
  topics: object (topic → count)
  platforms: object (platform → count)
  learning_trajectory: array
```

---

## 🛠️ Tools & SDKs

### Official Tools

**Python** (httpx):
```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/api/v1/memory",
        json={"key": "test", "value": "data"},
        headers={"X-User-ID": "user_jfk"}
    )
```

**cURL**:
```bash
curl -X POST http://localhost:8000/api/v1/memory \
  -H "Content-Type: application/json" \
  -H "X-User-ID: user_jfk" \
  -d '{"key":"test","value":"data","scope":"persistent"}'
```

### Client SDK Generation

Generate clients for any language using OpenAPI Generator:

```bash
# Python
openapi-generator-cli generate -i reference.yaml -g python -o ./client-python

# TypeScript/Axios
openapi-generator-cli generate -i reference.yaml -g typescript-axios -o ./client-ts

# Go
openapi-generator-cli generate -i reference.yaml -g go -o ./client-go

# Rust
openapi-generator-cli generate -i reference.yaml -g rust -o ./client-rust
```

---

## 📚 Related Documentation

- [API Reference Guide](../api-reference.md) - Human-readable API guide
- [REST API Usage](../rest-api-usage.md) - Usage examples and patterns
- [MCP over HTTP/SSE](../mcp-http-setup.md) - MCP protocol endpoint
- [Getting Started](../getting-started.md)

---

## 🔄 Keeping Spec Updated

The OpenAPI spec can be regenerated from the running server:

```bash
# Start server
uvicorn kagura.api.server:app --port 8000

# Download current spec
curl http://localhost:8000/openapi.json > docs/api/reference.json

# Convert to YAML (optional)
python -c "import json, yaml; print(yaml.dump(json.load(open('docs/api/reference.json'))))" > docs/api/reference.yaml
```

---

**Last Updated**: 2025-10-27
**API Version**: 4.0.0
**OpenAPI Version**: 3.1.0
