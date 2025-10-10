# Advanced Configuration Guide

This guide covers advanced configuration options for production deployments and custom use cases.

## Environment Variables

Sample Project can be configured via environment variables (takes precedence over `config.yaml`).

### Database Configuration

```bash
# PostgreSQL connection
export DATABASE_URL="postgresql://user:password@localhost:5432/sample_db"
export DATABASE_POOL_SIZE=20
export DATABASE_MAX_OVERFLOW=10

# Connection timeout
export DATABASE_CONNECT_TIMEOUT=10
export DATABASE_COMMAND_TIMEOUT=30
```

### API Server Configuration

```bash
# Server settings
export API_HOST="0.0.0.0"
export API_PORT=8000
export API_WORKERS=4

# CORS settings
export CORS_ORIGINS="https://app.example.com,https://admin.example.com"
export CORS_ALLOW_CREDENTIALS=true
```

### Authentication Configuration

```bash
# JWT settings
export AUTH_SECRET_KEY="your-secret-key-min-32-chars"
export AUTH_ALGORITHM="HS256"
export AUTH_ACCESS_TOKEN_EXPIRE=3600
export AUTH_REFRESH_TOKEN_EXPIRE=2592000  # 30 days

# OAuth providers
export GOOGLE_CLIENT_ID="your-google-client-id"
export GOOGLE_CLIENT_SECRET="your-google-client-secret"
export GITHUB_CLIENT_ID="your-github-client-id"
export GITHUB_CLIENT_SECRET="your-github-client-secret"
```

### Cache Configuration

```bash
# Redis cache
export REDIS_URL="redis://localhost:6379/0"
export CACHE_TTL=3600
export CACHE_MAX_SIZE=1000

# In-memory cache (if Redis unavailable)
export CACHE_BACKEND="memory"
export MEMORY_CACHE_SIZE_MB=100
```

### Logging Configuration

```bash
# Log level
export LOG_LEVEL="INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Log format
export LOG_FORMAT="json"  # json or text

# Log destination
export LOG_FILE="/var/log/sample-project/app.log"
export LOG_ROTATE_SIZE_MB=100
export LOG_ROTATE_BACKUP_COUNT=10
```

## Advanced Features

### Custom Database Models

Extend built-in models with custom fields:

```python
# models/custom.py
from sample_project.models import User
from sqlalchemy import Column, String

class CustomUser(User):
    """Extended user model with custom fields."""
    __tablename__ = "custom_users"

    department = Column(String(100))
    employee_id = Column(String(50), unique=True)
```

Register custom model:

```python
# config.py
from sample_project import configure
from models.custom import CustomUser

configure(
    user_model=CustomUser
)
```

### Custom Authentication Backend

Implement custom authentication:

```python
# auth/ldap_backend.py
from sample_project.auth import AuthBackend

class LDAPAuthBackend(AuthBackend):
    """LDAP authentication backend."""

    async def authenticate(self, username: str, password: str):
        # Connect to LDAP server
        ldap_client = connect_ldap()

        # Validate credentials
        if ldap_client.bind(username, password):
            return await self.get_or_create_user(username)

        return None
```

Register backend:

```yaml
# config.yaml
auth:
  backends:
    - sample_project.auth.backends.DatabaseBackend
    - auth.ldap_backend.LDAPAuthBackend
```

### Background Tasks

Use built-in task queue for async operations:

```python
from sample_project.tasks import task

@task(queue="default", retry=3)
async def send_email(user_id: str, subject: str, body: str):
    """Send email in background."""
    user = await User.get(user_id)
    await email_service.send(
        to=user.email,
        subject=subject,
        body=body
    )

# Enqueue task
await send_email.delay(
    user_id="usr_123",
    subject="Welcome!",
    body="Thanks for joining."
)
```

### Webhooks

Configure outgoing webhooks:

```yaml
# config.yaml
webhooks:
  enabled: true
  endpoints:
    user.created:
      - url: https://example.com/webhooks/user-created
        secret: webhook_secret_123
        retry_count: 3

    order.completed:
      - url: https://analytics.example.com/events
        headers:
          X-API-Key: analytics_key_456
```

Subscribe to webhook events:

```python
from sample_project.webhooks import on_event

@on_event("user.created")
async def notify_admin(event):
    """Notify admin when user created."""
    await admin_service.send_notification(
        f"New user: {event.data['email']}"
    )
```

### API Rate Limiting

Configure granular rate limits:

```yaml
# config.yaml
rate_limiting:
  enabled: true
  storage: redis  # or memory

  # Default limits
  default:
    requests: 100
    period: 60  # seconds

  # Per-endpoint limits
  endpoints:
    /api/v1/auth/login:
      requests: 5
      period: 60

    /api/v1/data/export:
      requests: 10
      period: 3600

  # Per-user limits
  authenticated:
    requests: 1000
    period: 3600
```

Custom rate limit decorator:

```python
from sample_project.middleware import rate_limit

@app.post("/api/v1/expensive-operation")
@rate_limit(requests=1, period=60)
async def expensive_operation():
    """Rate-limited endpoint."""
    return {"status": "processing"}
```

### Monitoring and Metrics

Enable Prometheus metrics:

```yaml
# config.yaml
monitoring:
  enabled: true
  metrics_path: /metrics

  # Custom metrics
  custom_metrics:
    - name: api_request_duration_seconds
      type: histogram
      description: API request duration
      buckets: [0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
```

Export metrics:

```python
from sample_project.metrics import Counter, Histogram

request_counter = Counter(
    "api_requests_total",
    "Total API requests",
    ["method", "endpoint", "status"]
)

request_duration = Histogram(
    "api_request_duration_seconds",
    "Request duration",
    ["endpoint"]
)

@app.middleware("http")
async def metrics_middleware(request, call_next):
    with request_duration.time(endpoint=request.url.path):
        response = await call_next(request)

    request_counter.inc(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    )

    return response
```

### Database Sharding

Configure database sharding for horizontal scaling:

```yaml
# config.yaml
database:
  sharding:
    enabled: true
    strategy: hash  # or range
    key: user_id

    shards:
      - name: shard_0
        url: postgresql://localhost:5432/db_shard_0
        range: [0, 1000000]

      - name: shard_1
        url: postgresql://localhost:5433/db_shard_1
        range: [1000001, 2000000]
```

## Performance Optimization

### Connection Pooling

Optimize database connections:

```yaml
# config.yaml
database:
  pool_size: 20
  max_overflow: 10
  pool_timeout: 30
  pool_recycle: 3600
  pool_pre_ping: true
```

### Query Optimization

Use query hints and indexes:

```python
from sample_project.models import User
from sqlalchemy import select

# Use index hint
query = select(User).with_hint(
    User,
    "USE INDEX (idx_email)"
).where(User.email == "user@example.com")

# Eager loading to avoid N+1
query = select(User).options(
    selectinload(User.orders)
)
```

### Caching Strategies

Implement multi-layer caching:

```python
from sample_project.cache import cache

@cache(ttl=3600, key="user:{user_id}")
async def get_user_profile(user_id: str):
    """Cached user profile lookup."""
    return await User.get(user_id)

# Cache invalidation
await cache.delete("user:usr_123")

# Bulk cache operations
await cache.delete_pattern("user:*")
```

## Security Hardening

### HTTPS Configuration

Force HTTPS in production:

```yaml
# config.yaml
security:
  force_https: true
  hsts_max_age: 31536000  # 1 year
  hsts_include_subdomains: true
```

### Content Security Policy

Configure CSP headers:

```yaml
# config.yaml
security:
  csp:
    default-src: ["'self'"]
    script-src: ["'self'", "cdn.example.com"]
    style-src: ["'self'", "'unsafe-inline'"]
    img-src: ["'self'", "data:", "https:"]
```

### API Key Encryption

Encrypt API keys at rest:

```yaml
# config.yaml
security:
  encryption:
    enabled: true
    algorithm: AES-256-GCM
    key_rotation_days: 90
```

## Deployment

### Docker Configuration

Optimized Dockerfile:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run as non-root
RUN useradd -m appuser
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["sample-project", "serve", "--workers", "4"]
```

### Kubernetes Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sample-project
spec:
  replicas: 3
  selector:
    matchLabels:
      app: sample-project
  template:
    metadata:
      labels:
        app: sample-project
    spec:
      containers:
      - name: api
        image: sample-project:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

## Troubleshooting

### Enable Debug Logging

```bash
export LOG_LEVEL=DEBUG
sample-project serve
```

### Database Connection Pool Exhausted

Increase pool size:

```yaml
database:
  pool_size: 50
  max_overflow: 20
```

### High Memory Usage

Reduce cache size:

```yaml
cache:
  max_size: 500
  memory_cache_size_mb: 50
```

## Further Reading

- [Database Optimization](https://docs.sample-project.com/db-optimization)
- [Security Best Practices](https://docs.sample-project.com/security)
- [Production Checklist](https://docs.sample-project.com/production)
