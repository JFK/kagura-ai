# RFC-029: Secret & Config Management System

**Status**: Draft
**Author**: AI Development Team  
**Created**: 2025-10-15
**Priority**: High (Production Feature)
**Target Version**: v2.6.0

---

## 📋 Executive Summary

現在、Kagura AIでは API keys/tokens を環境変数や`.env`ファイルで管理していますが、以下の課題があります：

**現状の課題**:
- セキュリティリスク（平文での管理、誤コミット）
- 管理が煩雑（複数の環境変数、ファイル散在）
- チーム共有が困難（個人のキーを安全に共有できない）
- 動的な設定変更が不可（再起動必要）

**提案する解決策**:
Kagura内部でセキュアにシークレットと設定を管理し、プラガブルなバックエンド、階層的な設定、動的なLLM選択を実現します。

---

## 🎯 Goals

### Primary Goals
1. **セキュアなシークレット管理** - 暗号化、アクセス制御、監査ログ
2. **プラガブルなストレージ** - Local/DB/Cloud対応
3. **階層的な設定管理** - Global/Project/Envスコープ
4. **動的なLLM設定** - プロバイダー・モデルの実行時選択

### Success Criteria
- ✅ 暗号化されたシークレットストレージ（複数バックエンド対応）
- ✅ CLI/APIでのシークレット管理
- ✅ LLMConfigとの自動統合
- ✅ 設定の階層的オーバーライド
- ✅ 動的プロバイダー/モデル選択
- ✅ キーローテーション対応

---

## 💡 Proposed Solution

### Architecture Overview

```
┌─────────────────────────────────────────────────┐
│         Kagura Application Layer                │
│  @agent(llm_config=LLMConfig(provider="auto"))  │
└────────────────┬────────────────────────────────┘
                 │
        ┌────────┴────────┐
        │  ConfigManager   │  ← Hierarchical config
        │  SecretManager   │  ← Secret auto-injection
        └────────┬────────┘
                 │
    ┌────────────┴───────────────┐
    │    SecretBackend (ABC)     │
    └────────────┬───────────────┘
                 │
    ┌────────────┼────────────┬─────────────┐
    │            │            │             │
┌───▼───┐  ┌───▼────┐  ┌───▼────┐   ┌────▼─────┐
│ Local │  │Database│  │ Redis  │   │ Vault    │
│Encrypt│  │(SQLite)│  │        │   │(HashiCorp│
└───────┘  └────────┘  └────────┘   └──────────┘
```

---

## 🏗️ Component Design

### 1. SecretBackend (Abstract Base Class)

```python
from abc import ABC, abstractmethod

class SecretBackend(ABC):
    """Abstract base for secret storage backends"""
    
    @abstractmethod
    async def get(self, key: str) -> str | None:
        """Retrieve secret value
        
        Args:
            key: Secret key name
            
        Returns:
            Secret value or None if not found
        """
        pass
    
    @abstractmethod
    async def set(self, key: str, value: str, metadata: dict | None = None) -> None:
        """Store secret value
        
        Args:
            key: Secret key name
            value: Secret value (will be encrypted)
            metadata: Optional metadata (tags, expiry, etc.)
        """
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete secret
        
        Args:
            key: Secret key name
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    @abstractmethod
    async def list(self) -> list[str]:
        """List all secret keys (not values)
        
        Returns:
            List of secret key names
        """
        pass
    
    @abstractmethod
    async def rotate(self, key: str, new_value: str) -> None:
        """Rotate secret (keep old version for grace period)
        
        Args:
            key: Secret key name
            new_value: New secret value
        """
        pass
```

### 2. LocalEncryptedBackend (Default)

```python
from cryptography.fernet import Fernet
import json
from pathlib import Path

class LocalEncryptedBackend(SecretBackend):
    """Local file-based encrypted secret storage
    
    Storage format:
    - Encryption: Fernet (symmetric encryption)
    - Location: ~/.kagura/secrets/secrets.enc
    - Key: ~/.kagura/secrets/encryption.key (auto-generated)
    - Format: JSON with encrypted values
    """
    
    def __init__(
        self,
        secrets_file: Path | None = None,
        key_file: Path | None = None
    ):
        self.secrets_file = secrets_file or Path.home() / ".kagura/secrets/secrets.enc"
        self.key_file = key_file or Path.home() / ".kagura/secrets/encryption.key"
        
        # Initialize encryption key
        if not self.key_file.exists():
            self._generate_key()
        
        self.fernet = Fernet(self.key_file.read_bytes())
    
    def _generate_key(self) -> None:
        """Generate new encryption key"""
        self.key_file.parent.mkdir(parents=True, exist_ok=True)
        key = Fernet.generate_key()
        self.key_file.write_bytes(key)
        self.key_file.chmod(0o600)  # Read/write for owner only
    
    async def get(self, key: str) -> str | None:
        """Retrieve and decrypt secret"""
        if not self.secrets_file.exists():
            return None
        
        encrypted_data = self.secrets_file.read_bytes()
        decrypted = self.fernet.decrypt(encrypted_data)
        secrets = json.loads(decrypted)
        
        return secrets.get(key)
    
    async def set(self, key: str, value: str, metadata: dict | None = None) -> None:
        """Encrypt and store secret"""
        # Load existing secrets
        secrets = {}
        if self.secrets_file.exists():
            encrypted_data = self.secrets_file.read_bytes()
            decrypted = self.fernet.decrypt(encrypted_data)
            secrets = json.loads(decrypted)
        
        # Add/update secret
        secrets[key] = {
            "value": value,
            "metadata": metadata or {},
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Encrypt and save
        encrypted_data = self.fernet.encrypt(json.dumps(secrets).encode())
        self.secrets_file.parent.mkdir(parents=True, exist_ok=True)
        self.secrets_file.write_bytes(encrypted_data)
        self.secrets_file.chmod(0o600)
```

### 3. DatabaseBackend (SQLite/PostgreSQL)

```python
class DatabaseBackend(SecretBackend):
    """Database-backed secret storage
    
    Supports:
    - SQLite (local, simple)
    - PostgreSQL (production)
    - MySQL (alternative)
    
    Schema:
    - secrets table: (key, encrypted_value, metadata, created_at, updated_at)
    - encryption key stored separately (local file or KMS)
    """
    
    def __init__(
        self,
        connection_string: str,
        encryption_key: bytes | None = None
    ):
        self.connection_string = connection_string
        # Setup DB connection, create tables
        # Initialize encryption
        pass
    
    async def get(self, key: str) -> str | None:
        """Query DB and decrypt"""
        # SELECT encrypted_value FROM secrets WHERE key = ?
        # Decrypt with Fernet
        pass
```

### 4. ConfigManager (Hierarchical Configuration)

```python
class ConfigManager:
    """Hierarchical configuration manager
    
    Precedence (highest to lowest):
    1. Runtime parameters
    2. Environment variables
    3. Project config (./kagura.yaml)
    4. User config (~/.kagura/config.yaml)
    5. Global defaults
    """
    
    def __init__(self):
        self.global_config = self._load_global()
        self.user_config = self._load_user()
        self.project_config = self._load_project()
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Get config value with hierarchy resolution
        
        Example:
            >>> await config.get("llm.provider")
            'openai'
            >>> await config.get("llm.model")
            'gpt-4o-mini'
        """
        # Check in order: env vars → project → user → global
        pass
    
    async def set(
        self,
        key: str,
        value: Any,
        scope: Literal["global", "user", "project"] = "user"
    ) -> None:
        """Set config value at specific scope"""
        pass
    
    async def reload(self) -> None:
        """Reload all config files (hot reload)"""
        pass
```

### 5. Dynamic LLM Selection

```python
from typing import Literal

class LLMSelector:
    """Dynamic LLM provider/model selection"""
    
    async def select_provider(
        self,
        strategy: Literal["auto", "cost", "performance", "availability"],
        fallback_chain: list[str] | None = None
    ) -> str:
        """Select LLM provider based on strategy
        
        Strategies:
        - auto: First available in fallback_chain
        - cost: Cheapest option
        - performance: Lowest latency
        - availability: Check API status, select healthy
        
        Args:
            strategy: Selection strategy
            fallback_chain: Provider priority list
            
        Returns:
            Selected provider name
        """
        if strategy == "auto":
            return await self._auto_fallback(fallback_chain)
        elif strategy == "cost":
            return await self._cost_optimized()
        elif strategy == "performance":
            return await self._performance_based()
        elif strategy == "availability":
            return await self._availability_check(fallback_chain)
    
    async def _auto_fallback(self, providers: list[str]) -> str:
        """Try providers in order until one works"""
        for provider in providers:
            if await self._check_api_key(provider):
                return provider
        raise ValueError("No available LLM provider")
    
    async def _cost_optimized(self) -> str:
        """Select cheapest model based on pricing table"""
        # Cost table: gpt-4o-mini < claude-haiku < gemini-flash
        pass
    
    async def _performance_based(self) -> str:
        """Select fastest model based on latency stats"""
        # Latency tracking from observability
        pass
```

---

## 📦 Implementation Plan

### Phase 1: Core Secret Management (Week 1-2)

**Deliverables**:
1. `SecretBackend` abstract base class
2. `LocalEncryptedBackend` implementation (default)
3. `SecretManager` API
4. CLI commands: `kagura secrets add/list/delete`
5. Tests: 50+ tests

**Files**:
- `src/kagura/secrets/backend.py` - Abstract base
- `src/kagura/secrets/local.py` - Local encrypted backend
- `src/kagura/secrets/manager.py` - SecretManager API
- `src/kagura/cli/secrets_cli.py` - CLI commands
- `tests/secrets/` - Test suite

### Phase 2: Database Backends (Week 3-4)

**Deliverables**:
1. `DatabaseBackend` (SQLite/PostgreSQL)
2. `RedisBackend`
3. Migration utilities
4. Tests: 30+ tests

**Files**:
- `src/kagura/secrets/database.py` - DB backend
- `src/kagura/secrets/redis.py` - Redis backend
- `src/kagura/secrets/migrations.py` - DB migrations

### Phase 3: Configuration Management (Week 5-6)

**Deliverables**:
1. `ConfigManager` - Hierarchical config
2. Config file formats (YAML/TOML)
3. CLI commands: `kagura config set/get/list`
4. Hot reload support
5. Tests: 40+ tests

**Files**:
- `src/kagura/config/manager.py` - ConfigManager
- `src/kagura/config/loader.py` - Config file loader
- `src/kagura/cli/config_cli.py` - CLI commands
- `tests/config/` - Test suite

### Phase 4: LLM Integration & Dynamic Selection (Week 7-8)

**Deliverables**:
1. LLMConfig secret auto-injection
2. `LLMSelector` - Dynamic provider/model selection
3. Auto-fallback mechanism
4. Cost/Performance tracking integration
5. Tests: 30+ tests

**Files**:
- `src/kagura/llm/selector.py` - LLMSelector
- `src/kagura/core/llm.py` - Integration with ConfigManager
- `src/kagura/llm/pricing.py` - Cost tracking
- `tests/llm/` - Test suite

### Phase 5: Advanced Features (Week 9-10)

**Deliverables**:
1. Key rotation automation
2. Audit logging
3. Secret versioning
4. Cloud backends (AWS/GCP/Azure)
5. HashiCorp Vault integration

---

## 🎯 API Design

### Secret Management API

```python
from kagura.secrets import SecretManager

# Initialize with backend
secrets = SecretManager(backend="local")  # Default
# secrets = SecretManager(backend="sqlite://~/.kagura/secrets.db")
# secrets = SecretManager(backend="postgres://localhost/kagura")

# Basic operations
await secrets.set("openai_api_key", "sk-...")
api_key = await secrets.get("openai_api_key")
await secrets.delete("old_key")
all_keys = await secrets.list()

# Advanced operations
await secrets.rotate("api_key", new_value="sk-new...")
await secrets.set_with_expiry("temp_token", "token", expire_after=3600)

# Metadata
await secrets.set("api_key", "sk-...", metadata={
    "provider": "openai",
    "created_by": "user@example.com",
    "tags": ["production", "critical"]
})
```

### Configuration Management API

```python
from kagura.config import ConfigManager

config = ConfigManager()

# Get config with hierarchy
provider = await config.get("llm.provider")  # Check env → project → user → global
model = await config.get("llm.model", default="gpt-4o-mini")

# Set config at scope
await config.set("llm.provider", "anthropic", scope="user")
await config.set("llm.model", "gpt-4o", scope="project")

# List all config
all_config = await config.list()

# Hot reload
await config.reload()  # Re-read config files
```

### Agent Integration (Auto-Secret Injection)

```python
from kagura import agent
from kagura.secrets import use_secrets

# Method 1: Decorator-based injection
@agent
@use_secrets(["openai_api_key"])
async def translator(text: str) -> str:
    """Translate {{ text }}"""
    pass

# Method 2: Automatic provider detection
@agent(llm_config=LLMConfig(
    provider="auto",  # Auto-detect from available secrets
    secret_keys=["openai_api_key", "anthropic_api_key"]
))
async def smart_agent(query: str) -> str:
    """Answer {{ query }}"""
    pass

# Kagura automatically:
# 1. Checks which API keys are available
# 2. Selects provider based on availability
# 3. Injects secret into LLMConfig
```

### Dynamic LLM Selection

```python
from kagura import agent, LLMConfig

# Auto-fallback (if OpenAI fails, try Anthropic, then Google)
@agent(llm_config=LLMConfig(
    provider="auto",
    fallback_chain=["openai", "anthropic", "google"]
))
async def resilient_agent(query: str) -> str:
    """Answer {{ query }}"""
    pass

# Cost-optimized (auto-select cheapest)
@agent(llm_config=LLMConfig(
    strategy="cost_optimized",
    max_cost_per_request=0.01  # $0.01 limit
))
async def cheap_agent(query: str) -> str:
    """Answer {{ query }}"""
    pass

# Performance-based (auto-select fastest)
@agent(llm_config=LLMConfig(
    strategy="performance",
    max_latency_ms=500  # 500ms limit
))
async def fast_agent(query: str) -> str:
    """Answer {{ query }}"""
    pass

# Runtime dynamic selection
from kagura.config import ConfigManager

config = ConfigManager()
await config.set("llm.provider", "anthropic")
await config.set("llm.model", "claude-3-5-sonnet")

# Agent automatically uses new config (no restart needed)
result = await my_agent("Hello")
```

---

## 🎯 Use Cases

### Use Case 1: Individual Developer

```bash
# Setup personal API key (one-time)
$ kagura secrets add openai_api_key
Enter secret (hidden): sk-...
✓ Secret stored securely in ~/.kagura/secrets/

# Set preferred model
$ kagura config set llm.model gpt-4o

# Run agent - auto uses personal key & config
$ python my_agent.py
```

### Use Case 2: Team Development

**Developer A**:
```bash
$ kagura secrets add openai_api_key
Enter secret: [Personal Key A]

$ kagura config set llm.model gpt-4o-mini  # Dev env
```

**Developer B**:
```bash
$ kagura secrets add anthropic_api_key
Enter secret: [Personal Key B]

$ kagura config set llm.provider anthropic  # Prefers Anthropic
```

**Same code, different secrets** - No key sharing, no conflicts!

### Use Case 3: Production Environment

```bash
# Production uses PostgreSQL for secret storage
$ kagura config set secrets.backend postgres
$ kagura config set secrets.connection_string $POSTGRES_URL

# Store production keys
$ kagura secrets add openai_api_key --scope production
Enter secret: sk-prod-...

# Production model
$ kagura config set llm.model gpt-4o --scope production
```

### Use Case 4: Multi-Provider Fallback

```python
# Auto-fallback if primary provider fails
@agent(llm_config=LLMConfig(
    provider="auto",
    fallback_chain=["openai", "anthropic", "google"]
))
async def resilient_translator(text: str) -> str:
    """Translate {{ text }} to Japanese"""
    pass

# Execution flow:
# 1. Try OpenAI API
# 2. If fails (rate limit, outage), try Anthropic
# 3. If fails, try Google
# 4. Return result from first successful provider
```

### Use Case 5: Automated Key Rotation

```python
from kagura.secrets import SecretManager
from kagura import scheduled

secrets = SecretManager()

# Monthly key rotation
@scheduled(cron="0 0 1 * *")  # 1st of month, midnight
async def rotate_api_keys():
    """Rotate API keys monthly for security"""
    
    # Generate new key (external API)
    new_key = await openai.create_api_key()
    
    # Rotate (keeps old key for 24h grace period)
    await secrets.rotate("openai_api_key", new_key)
    
    # Log rotation
    logger.info(f"Rotated openai_api_key at {datetime.utcnow()}")
    
    # Notify team
    await notify_slack("API key rotated successfully")
```

---

## 🔒 Security Considerations

### Encryption

**Local Backend**:
- **Algorithm**: Fernet (AES-128 CBC + HMAC)
- **Key Storage**: `~/.kagura/secrets/encryption.key` (0o600 permissions)
- **Data Storage**: `~/.kagura/secrets/secrets.enc`

**Database Backend**:
- **At-Rest**: DB-level encryption (if supported)
- **In-Transit**: TLS/SSL connections
- **Application**: Fernet encryption before DB insert

### Access Control

```python
# Future: RBAC support
secrets = SecretManager()

# Set access policy
await secrets.set_policy("openai_api_key", policy={
    "read": ["developer", "admin"],
    "write": ["admin"],
    "delete": ["admin"]
})
```

### Audit Logging

```python
# All secret operations logged
await secrets.get("api_key")
# → Log: [2025-10-15 12:34:56] user@example.com READ openai_api_key

await secrets.set("api_key", "new")
# → Log: [2025-10-15 12:35:00] user@example.com WRITE openai_api_key

await secrets.rotate("api_key", "rotated")
# → Log: [2025-10-15 12:36:00] user@example.com ROTATE openai_api_key
```

---

## 📋 Configuration File Format

### Option A: YAML (Recommended)

```yaml
# ~/.kagura/config.yaml (user config)
llm:
  provider: openai
  model: gpt-4o-mini
  temperature: 0.7
  max_tokens: 2000

secrets:
  backend: local
  encryption_key_path: ~/.kagura/secrets/encryption.key

observability:
  enabled: true
  track_costs: true

# ./kagura.yaml (project config - overrides user)
llm:
  model: gpt-4o  # Project uses gpt-4o (override)
  
secrets:
  backend: postgres  # Project uses PostgreSQL (override)
  connection_string: ${POSTGRES_URL}
```

### Option B: TOML (Python ecosystem standard)

```toml
# ~/.kagura/config.toml
[llm]
provider = "openai"
model = "gpt-4o-mini"
temperature = 0.7

[secrets]
backend = "local"
encryption_key_path = "~/.kagura/secrets/encryption.key"
```

**Recommendation**: **YAML** for readability and ecosystem compatibility

---

## 🚀 CLI Design

### Secret Management Commands

```bash
# Add secret (interactive)
$ kagura secrets add openai_api_key
Enter secret (hidden): ****
✓ Secret stored securely

# Add secret (non-interactive, for CI/CD)
$ kagura secrets add openai_api_key --value sk-... --scope production

# List secrets (keys only, not values!)
$ kagura secrets list
Secrets (3):
- openai_api_key (updated: 2025-10-15)
- anthropic_api_key (updated: 2025-10-14)
- google_api_key (updated: 2025-10-10)

# Get secret (for debugging, with confirmation)
$ kagura secrets get openai_api_key
⚠️  This will display secret in plaintext. Continue? [y/N] y
sk-...

# Delete secret
$ kagura secrets delete old_api_key
✓ Deleted old_api_key

# Rotate secret
$ kagura secrets rotate openai_api_key
Enter new secret: ****
✓ Secret rotated (old value valid for 24h)

# Show secret info (metadata, not value)
$ kagura secrets info openai_api_key
Key: openai_api_key
Provider: openai
Created: 2025-10-01 12:00:00
Updated: 2025-10-15 10:30:00
Access count: 1,234
```

### Configuration Management Commands

```bash
# Get config
$ kagura config get llm.provider
openai

# Set config (user scope)
$ kagura config set llm.model gpt-4o

# Set config (project scope)
$ kagura config set llm.model gpt-4o --scope project

# List all config
$ kagura config list
LLM:
  provider: openai (user)
  model: gpt-4o (project, overrides user: gpt-4o-mini)
  temperature: 0.7 (global default)

Secrets:
  backend: local (user)

# Reset to defaults
$ kagura config reset llm.model

# Validate config
$ kagura config validate
✓ Config is valid
```

---

## 🎓 Migration Guide (for Users)

### Current Usage (環境変数)

```bash
# .env file
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Code
from kagura import agent

@agent  # Reads from env vars
async def my_agent(query: str) -> str:
    """Answer {{ query }}"""
    pass
```

### New Usage (Secret Manager)

```bash
# One-time setup
$ kagura secrets add openai_api_key
Enter secret: sk-...

$ kagura config set llm.provider openai
$ kagura config set llm.model gpt-4o-mini
```

```python
# Code (unchanged!)
from kagura import agent

@agent  # Auto-reads from SecretManager
async def my_agent(query: str) -> str:
    """Answer {{ query }}"""
    pass
```

**Benefits**:
- ✅ More secure (encrypted storage)
- ✅ Easier management (CLI commands)
- ✅ Better team collaboration (no .env conflicts)
- ✅ Dynamic config changes (no restart needed)

---

## 📊 Comparison with Alternatives

| Feature | Env Vars | .env Files | Kagura Secrets |
|---------|----------|------------|----------------|
| Encryption | ❌ | ❌ | ✅ Fernet |
| Centralized | ❌ | ❌ | ✅ |
| Team-friendly | ❌ | ⚠️ | ✅ |
| Rotation | Manual | Manual | ✅ Automated |
| Audit logs | ❌ | ❌ | ✅ |
| DB support | ❌ | ❌ | ✅ |
| Dynamic reload | ❌ | ❌ | ✅ |

---

## 🎯 Success Metrics

### Phase 1-2 (Secret Management)
- ✅ Local encrypted backend working
- ✅ Database backends (SQLite/PostgreSQL/Redis)
- ✅ CLI commands functional
- ✅ 80+ tests passing

### Phase 3-4 (Config & LLM)
- ✅ Hierarchical config resolution
- ✅ LLM auto-injection working
- ✅ Dynamic provider selection
- ✅ 70+ tests passing

### Phase 5 (Advanced)
- ✅ Key rotation automation
- ✅ Audit logging
- ✅ Cloud backends (1+ provider)

---

## 📚 References

### External Documentation
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [HashiCorp Vault](https://www.vaultproject.io/)
- [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/)
- [Fernet Spec](https://github.com/fernet/spec/)

### Related RFCs
- RFC-013: OAuth2 Authentication (credential encryption precedent)
- RFC-010: Observability (cost tracking integration)

---

## ✅ Approval & Sign-off

**Created**: 2025-10-15
**Status**: Draft → Pending Review

**Target**: v2.6.0 (8-10 weeks)
**Priority**: High (Production-ready feature)

---

## 🤔 Open Questions

1. **Backend Priority**: Local → SQLite → PostgreSQL → Redis → Vault?
2. **Config Format**: YAML (recommended) or TOML?
3. **Encryption**: Fernet (current) or AES-256-GCM?
4. **Dynamic LLM**: Which strategies are most important?
   - Auto-fallback (必須)
   - Cost-optimized (推奨)
   - Performance-based (推奨)
   - Load-balancing (将来)
5. **Secret Sharing**: Team secret sharing機能は必要？

---

**このRFCについて、フィードバックをお願いします！**
