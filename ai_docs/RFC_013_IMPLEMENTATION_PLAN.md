# RFC-013: OAuth2 Authentication - Implementation Plan

**最終更新**: 2025-10-13
**Status**: In Progress (Phase 1)
**Issue**: [#74](https://github.com/JFK/kagura-ai/issues/74)
**RFC Document**: [RFC_013_OAUTH2_AUTH.md](./rfcs/RFC_013_OAUTH2_AUTH.md)

---

## 📋 実装概要

### 目標
Google OAuth2認証を実装し、APIキー不要でGemini APIを利用可能にする。

### スコープ (Phase 1)
- ✅ Google OAuth2フロー実装
- ✅ 認証情報の暗号化保存（Fernet）
- ✅ トークン自動リフレッシュ
- ✅ `kagura auth` CLI実装
- ✅ Gemini API統合

### 非スコープ（Phase 2以降）
- `@auto_auth` デコレータ
- OpenAI/Anthropic OAuth2対応
- 複数プロバイダー管理

---

## 🗂️ ファイル構造

```
src/kagura/
├── auth/
│   ├── __init__.py              # Public API exports
│   ├── oauth2.py                # OAuth2Manager core class
│   ├── config.py                # AuthConfig dataclass
│   └── exceptions.py            # Custom exceptions
│
├── cli/
│   └── auth_cli.py              # kagura auth commands
│
tests/
├── auth/
│   ├── __init__.py
│   ├── test_oauth2_manager.py   # OAuth2Manager tests
│   ├── test_auth_cli.py         # CLI tests
│   └── conftest.py              # Fixtures
│
ai_docs/
├── rfcs/
│   └── RFC_013_OAUTH2_AUTH.md   # RFC specification
└── RFC_013_IMPLEMENTATION_PLAN.md  # This file
```

---

## 📝 実装タスク

### Task 1: Dependencies追加
**File**: `pyproject.toml`

```toml
[project.optional-dependencies]
oauth = [
    "google-auth>=2.25.0",
    "google-auth-oauthlib>=1.2.0",
    "google-auth-httplib2>=0.2.0",
    "cryptography>=41.0.0",
]
```

**Tests**: なし（設定変更のみ）

---

### Task 2: OAuth2Manager実装
**File**: `src/kagura/auth/oauth2.py`

**Classes**:
- `OAuth2Manager`: Core authentication manager

**Methods**:
- `__init__(provider: str = "google")`
- `login() -> None`: Launch browser for OAuth2 login
- `logout() -> None`: Remove stored credentials
- `is_authenticated() -> bool`: Check authentication status
- `get_credentials() -> Credentials`: Get valid credentials (auto-refresh)
- `get_token() -> str`: Get access token for API calls
- `_save_credentials(creds: Credentials) -> None`: Encrypt and save
- `_load_credentials() -> Credentials`: Decrypt and load

**Tests**: 15+ tests
- `test_oauth2_manager_initialization()`
- `test_config_dir_creation()`
- `test_encryption_key_generation()`
- `test_is_authenticated_false_initially()`
- `test_logout_removes_credentials()`
- `test_save_and_load_credentials()`
- `test_token_refresh()`
- `test_get_token()`
- `test_invalid_provider()`
- `test_missing_client_secrets()`

---

### Task 3: AuthConfig実装
**File**: `src/kagura/auth/config.py`

**Classes**:
- `AuthConfig`: Configuration dataclass

**Fields**:
- `provider: str`
- `client_secrets_path: Path`
- `credentials_path: Path`
- `scopes: list[str]`

**Tests**: 8+ tests
- `test_auth_config_defaults()`
- `test_auth_config_custom_paths()`
- `test_scopes_validation()`

---

### Task 4: Custom Exceptions
**File**: `src/kagura/auth/exceptions.py`

**Classes**:
- `AuthenticationError`: Base exception
- `NotAuthenticatedError`: Not logged in
- `InvalidCredentialsError`: Invalid credentials
- `TokenRefreshError`: Refresh failed

**Tests**: 5+ tests
- `test_authentication_error()`
- `test_not_authenticated_error()`
- `test_invalid_credentials_error()`
- `test_token_refresh_error()`

---

### Task 5: CLI Commands実装
**File**: `src/kagura/cli/auth_cli.py`

**Commands**:
- `kagura auth login --provider google`
- `kagura auth logout --provider google`
- `kagura auth status`

**Features**:
- Rich formatting
- Progress indicators
- Error handling

**Tests**: 12+ tests
- `test_auth_login_command()`
- `test_auth_logout_command()`
- `test_auth_status_command()`
- `test_auth_login_invalid_provider()`
- `test_auth_logout_not_authenticated()`
- `test_auth_status_multiple_providers()`

---

### Task 6: LLMConfig統合
**File**: `src/kagura/core/llm.py`

**Changes**:
- Add `auth: OAuth2Manager | None = None` parameter
- Auto-detect authentication when `api_key` is None
- Use OAuth2 token for Gemini API calls

**Tests**: 8+ tests
- `test_llm_with_oauth2()`
- `test_llm_auto_auth_detection()`
- `test_llm_fallback_to_api_key()`
- `test_gemini_with_oauth2_token()`

---

### Task 7: Documentation
**Files**:
- `docs/en/guides/oauth2-setup.md`: Setup guide (400+ lines)
- `docs/en/api/auth.md`: API reference (350+ lines)

**Content**:
- Google Cloud Console setup
- `client_secrets.json` generation
- CLI usage examples
- Python API examples
- Troubleshooting

---

### Task 8: Integration Tests
**File**: `tests/auth/test_oauth2_integration.py`

**Tests** (Marked as `@pytest.mark.integration`):
- `test_oauth2_full_flow()`: End-to-end test
- `test_oauth2_with_agent()`: Agent integration
- `test_token_auto_refresh()`: Refresh flow

**Skipped by default**: Requires manual login

---

## ✅ 完了条件

### Functional Requirements
- ✅ `kagura auth login --provider google` でブラウザログイン成功
- ✅ 認証情報が暗号化保存される (`~/.kagura/credentials.json.enc`)
- ✅ `kagura auth status` で認証状態確認
- ✅ `kagura auth logout` でログアウト
- ✅ トークン期限切れ時に自動リフレッシュ
- ✅ Gemini APIでOAuth2トークン使用可能

### Non-Functional Requirements
- ✅ テストカバレッジ 95%+
- ✅ Pyright strict mode対応（0 errors）
- ✅ Ruff linter対応（0 warnings）
- ✅ ドキュメント完備

### Security Requirements
- ✅ Fernet暗号化（AES-128）
- ✅ ファイルパーミッション 0o600
- ✅ 暗号化キー別ファイル保存
- ✅ `.gitignore` に認証ファイル追加

---

## 🧪 テスト戦略

### Unit Tests (40+ tests)
- `tests/auth/test_oauth2_manager.py`: 15 tests
- `tests/auth/test_config.py`: 8 tests
- `tests/auth/test_exceptions.py`: 5 tests
- `tests/cli/test_auth_cli.py`: 12 tests

### Integration Tests (3 tests, skipped by default)
- `tests/auth/test_oauth2_integration.py`: 3 tests
- Requires `@pytest.mark.integration`
- Requires manual `client_secrets.json` setup

### Total Tests: 43+

---

## 📦 依存関係

### New Dependencies
```toml
google-auth = ">=2.25.0"
google-auth-oauthlib = ">=1.2.0"
google-auth-httplib2 = ">=0.2.0"
cryptography = ">=41.0.0"
```

### Installation
```bash
# Install with OAuth support
pip install kagura-ai[oauth]

# Development
uv sync --extra oauth
```

---

## 🚨 リスクと軽減策

### Risk 1: Google依存
**軽減策**: 抽象化レイヤー（`OAuth2Manager`）で他プロバイダー対応可能な設計

### Risk 2: 初回セットアップ複雑
**軽減策**: 詳細なドキュメント、スクリーンショット付きガイド作成

### Risk 3: ブラウザレス環境
**軽減策**: 従来のAPIキー方式も併用可能（後方互換性維持）

### Risk 4: トークン漏洩
**軽減策**: Fernet暗号化、ファイルパーミッション600、.gitignore設定

---

## 🔄 後方互換性

### 既存APIキー方式は引き続き利用可能

```python
# 従来通り（APIキー方式）
export GOOGLE_API_KEY=your-api-key
kagura chat

# 新方式（OAuth2）
kagura auth login --provider google
kagura chat  # APIキー不要
```

### `@agent` デコレータ互換性

```python
# APIキー（従来）
@agent(model="gemini-2.0-flash")
async def my_agent(query: str) -> str:
    """{{ query }}"""
    pass

# OAuth2（新）
from kagura.auth import get_auth

@agent(model="gemini-2.0-flash", auth=get_auth("google"))
async def my_agent(query: str) -> str:
    """{{ query }}"""
    pass
```

---

## 📅 実装スケジュール

### Week 1: Core Implementation (5 days)
- Day 1: Dependencies + OAuth2Manager skeleton
- Day 2: OAuth2Manager implementation
- Day 3: AuthConfig + Exceptions
- Day 4: CLI commands
- Day 5: Unit tests (40+ tests)

### Week 2: Integration & Documentation (3 days)
- Day 1: LLMConfig統合
- Day 2: Integration tests
- Day 3: Documentation (2 guides, 750+ lines)

### Total: 1.5 weeks

---

## 🎯 Success Metrics

### Before (Current)
- **Setup steps**: 5+
  1. Get Google API key
  2. Set environment variable
  3. Export to shell
  4. Add to .env file
  5. Run kagura

### After (With OAuth2)
- **Setup steps**: 2
  1. `kagura auth login --provider google`
  2. Run kagura

**Time saved**: 70% reduction in setup time

---

## 📚 参考資料

- [Google OAuth2 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [google-auth-oauthlib Documentation](https://google-auth-oauthlib.readthedocs.io/)
- [Fernet Encryption](https://cryptography.io/en/latest/fernet/)
- [RFC-013 Specification](./rfcs/RFC_013_OAUTH2_AUTH.md)

---

## ✅ チェックリスト

### Implementation
- [ ] Task 1: Dependencies追加
- [ ] Task 2: OAuth2Manager実装
- [ ] Task 3: AuthConfig実装
- [ ] Task 4: Custom Exceptions実装
- [ ] Task 5: CLI Commands実装
- [ ] Task 6: LLMConfig統合
- [ ] Task 7: Documentation作成
- [ ] Task 8: Integration Tests実装

### Quality Assurance
- [ ] Unit tests 40+ (95%+ coverage)
- [ ] Integration tests 3+
- [ ] Pyright strict mode (0 errors)
- [ ] Ruff linter (0 warnings)
- [ ] Security review (encryption, permissions)

### Documentation
- [ ] OAuth2 Setup Guide (400+ lines)
- [ ] API Reference (350+ lines)
- [ ] Code comments (complex functions)
- [ ] Troubleshooting section

### Release
- [ ] Create Draft PR
- [ ] CI/CD passes
- [ ] Code review
- [ ] Squash merge
- [ ] Update CHANGELOG.md
- [ ] GitHub Release

---

**実装準備完了！次はTask 1から順次実装開始します。**
