# Getting Started Guide

This guide will help you set up and start using Sample Project in under 10 minutes.

## Prerequisites

Before you begin, ensure you have:

- Python 3.11 or higher
- PostgreSQL 14+ (or use SQLite for development)
- Redis 6+ (optional, for caching)
- Git

## Installation

### Step 1: Install Sample Project

Using pip:
```bash
pip install sample-project
```

Using pipx (recommended for CLI tools):
```bash
pipx install sample-project
```

From source:
```bash
git clone https://github.com/example/sample-project.git
cd sample-project
pip install -e .
```

### Step 2: Initialize Configuration

Create a configuration file:
```bash
sample-project init
```

This creates `config.yaml` in the current directory:

```yaml
# config.yaml
database:
  url: postgresql://localhost/sample_db
  pool_size: 10

api:
  host: 0.0.0.0
  port: 8000
  debug: false

auth:
  secret_key: CHANGE_ME_IN_PRODUCTION
  access_token_expire: 3600

cache:
  enabled: true
  redis_url: redis://localhost:6379
```

**Important**: Change `auth.secret_key` in production!

### Step 3: Set Up Database

Run migrations:
```bash
sample-project db migrate
```

Seed with sample data (optional):
```bash
sample-project db seed
```

### Step 4: Start the Server

Development mode (auto-reload):
```bash
sample-project serve --reload
```

Production mode:
```bash
sample-project serve --workers 4
```

The API is now running at http://localhost:8000

## Your First Request

### Create an Account

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123!",
    "name": "John Doe"
  }'
```

Response:
```json
{
  "id": "usr_abc123",
  "email": "user@example.com",
  "name": "John Doe",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePassword123!"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

### Make an Authenticated Request

```bash
curl http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

Response:
```json
{
  "id": "usr_abc123",
  "email": "user@example.com",
  "name": "John Doe",
  "role": "user",
  "created_at": "2024-01-15T10:30:00Z",
  "last_login": "2024-01-15T10:35:00Z"
}
```

## Next Steps

Now that you have Sample Project running, explore:

1. **API Documentation**: Visit http://localhost:8000/docs for interactive API docs
2. **Advanced Configuration**: See `guides/advanced.md` for configuration options
3. **Authentication**: Read `api/authentication.md` for OAuth 2.0 setup
4. **Deployment**: Learn how to deploy to production environments

## Common Issues

### Database Connection Failed

**Error**: `Could not connect to database`

**Solution**: Ensure PostgreSQL is running and credentials are correct in `config.yaml`

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Create database if it doesn't exist
createdb sample_db
```

### Port Already in Use

**Error**: `Address already in use`

**Solution**: Change the port in `config.yaml` or stop the process using port 8000

```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>
```

### Import Errors

**Error**: `ModuleNotFoundError: No module named 'sample_project'`

**Solution**: Ensure Sample Project is installed correctly

```bash
pip install --upgrade sample-project
```

## Getting Help

If you encounter issues:

1. Check the [FAQ](https://docs.sample-project.com/faq)
2. Search [GitHub Issues](https://github.com/example/sample-project/issues)
3. Ask on [Discord](https://discord.gg/sample-project)
4. Email support: support@sample-project.com

## What's Next?

Continue learning:
- [Advanced Configuration](advanced.md) - Fine-tune your setup
- [API Reference](../api/authentication.md) - Detailed API documentation
- [Architecture Overview](../diagrams/) - Understand system design
