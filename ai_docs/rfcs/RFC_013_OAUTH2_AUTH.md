# RFC-013: OAuth2 Authentication - APIキー不要のブラウザ認証

## ステータス
- **状態**: Draft
- **作成日**: 2025-10-04
- **関連Issue**: TBD
- **優先度**: Medium-High

## 概要

Kagura AIにOAuth2認証を追加し、**APIキー不要**でLLMを利用できるようにします。ブラウザでログインするだけで、以降は自動的に認証されます。

### 目標
- ブラウザベースのOAuth2ログイン
- APIキー管理不要
- 認証情報の安全な保存（暗号化）
- トークン自動リフレッシュ
- Google/Gemini統合

### 非目標
- 非公式API・セッショントークンの利用
- 複数プロバイダーの同時サポート（Phase 1ではGoogle優先）

## モチベーション

### 現在の課題
1. **APIキー管理が面倒**
   - 環境変数の設定が必要
   - .envファイルの管理
   - セキュリティリスク（平文保存）

2. **複数環境での管理**
   - 開発・本番で異なるAPIキー
   - チーム共有が困難

3. **初心者の障壁**
   - APIキー取得手順が複雑
   - 課金設定が必要

### 解決するユースケース
- **即座に利用開始**: `kagura auth login`→ブラウザログイン→完了
- **APIキー不要**: Googleアカウントで認証
- **セキュア**: 暗号化されたトークン保存
- **自動更新**: トークン期限切れを自動リフレッシュ

### なぜ今実装すべきか
- Claude CodeがOAuth2採用（ユーザー体験が向上）
- Google/GeminiがOAuth2対応済み
- APIキー管理の課題解決

## 設計

### 基本フロー

```
1. kagura auth login --provider google
   ↓
2. ブラウザが開く
   ↓
3. Googleアカウントでログイン
   ↓
4. トークンを ~/.kagura/credentials.json.enc に保存（暗号化）
   ↓
5. 以降、自動的に認証
```

### CLI API

```bash
# 初回ログイン
$ kagura auth login --provider google

Opening browser for authentication...
Please log in to your Google account...

✓ Authentication successful!
✓ Credentials saved to: ~/.kagura/credentials.json.enc

# ステータス確認
$ kagura auth status

Authenticated providers:
  ✓ google (expires: 2025-11-04 10:00:00)

# ログアウト
$ kagura auth logout --provider google

✓ Logged out from google
```

### Python API

```python
from kagura import agent
from kagura.auth import OAuth2Manager

# 認証マネージャー
auth = OAuth2Manager(provider="google")

# ログイン（ブラウザで認証、1回のみ）
if not auth.is_authenticated():
    auth.login()

# エージェント使用（APIキー不要）
@agent(model="gemini-2.0-flash", auth=auth)
async def my_agent(query: str) -> str:
    """{{ query }}"""
    pass

# 実行
result = await my_agent("Hello")
```

### 認証情報の保存

**暗号化保存:**

```
~/.kagura/
├── .key                      # 暗号化キー（自動生成）
├── credentials.json.enc      # 暗号化された認証情報
└── auth.toml                 # 設定ファイル
```

**auth.toml:**

```toml
[auth.google]
client_id = "your-app.apps.googleusercontent.com"
client_secret = "your-client-secret"
scopes = [
    "https://www.googleapis.com/auth/generative-language",
    "openid"
]
```

### 使用例

```python
# 例1: APIキー不要でGemini使用
from kagura import agent, auto_auth

@agent(model="gemini-2.0-flash")
@auto_auth  # 自動的にOAuth2認証
async def chat(message: str) -> str:
    """{{ message }}"""
    pass

result = await chat("最新のニュースは？")

# 例2: 明示的な認証
from kagura.auth import get_auth

auth = get_auth("google")  # 自動的にログイン確認

@agent(model="gemini-2.0-flash", auth=auth)
async def gemini_agent(query: str) -> str:
    """{{ query }}"""
    pass
```

## 実装計画

### Phase 1: Google OAuth2 (v2.3.0)
- [ ] OAuth2Managerクラス実装
- [ ] google-auth-oauthlib統合
- [ ] `kagura auth login/logout/status`コマンド
- [ ] 認証情報の暗号化保存（Fernet）
- [ ] トークン自動リフレッシュ
- [ ] Gemini API統合

### Phase 2: 自動認証 (v2.4.0)
- [ ] `@auto_auth`デコレータ
- [ ] 認証状態の自動チェック
- [ ] エラーハンドリング（未認証時の案内）

### Phase 3: 追加プロバイダー (v2.5.0)
- [ ] OpenAI OAuth2対応（将来的に）
- [ ] 複数プロバイダー管理

## 技術的詳細

### 依存関係

```toml
[project.optional-dependencies]
oauth = [
    "google-auth>=2.25.0",
    "google-auth-oauthlib>=1.2.0",
    "google-auth-httplib2>=0.2.0",
    "cryptography>=41.0.0",
]
```

### OAuth2Manager実装

```python
# src/kagura/auth/oauth2.py
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from cryptography.fernet import Fernet
from pathlib import Path
import json

class OAuth2Manager:
    """OAuth2 authentication manager"""

    SCOPES = {
        "google": [
            "https://www.googleapis.com/auth/generative-language",
            "openid"
        ]
    }

    def __init__(self, provider: str = "google"):
        self.provider = provider
        self.config_dir = Path.home() / ".kagura"
        self.config_dir.mkdir(exist_ok=True)

        self.creds_file = self.config_dir / "credentials.json.enc"
        self.key_file = self.config_dir / ".key"

        # 暗号化キー生成
        if not self.key_file.exists():
            key = Fernet.generate_key()
            self.key_file.write_bytes(key)
            self.key_file.chmod(0o600)

        self.cipher = Fernet(self.key_file.read_bytes())

    def login(self):
        """Launch browser for OAuth2 login"""
        client_secrets = self.config_dir / "client_secrets.json"

        if not client_secrets.exists():
            raise FileNotFoundError(
                f"Please download client_secrets.json from Google Cloud Console\n"
                f"and save to: {client_secrets}"
            )

        flow = InstalledAppFlow.from_client_secrets_file(
            str(client_secrets),
            self.SCOPES[self.provider]
        )

        # ブラウザでログイン
        creds = flow.run_local_server(port=0)

        # 暗号化して保存
        self._save_credentials(creds)

        print("✓ Authentication successful!")
        print(f"✓ Credentials saved to: {self.creds_file}")

    def get_credentials(self) -> Credentials:
        """Get valid credentials (auto-refresh)"""
        if not self.is_authenticated():
            raise Exception(
                f"Not authenticated. Please run: kagura auth login --provider {self.provider}"
            )

        creds = self._load_credentials()

        # トークンリフレッシュ
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            self._save_credentials(creds)

        return creds

    def is_authenticated(self) -> bool:
        """Check if authenticated"""
        return self.creds_file.exists()

    def logout(self):
        """Remove credentials"""
        if self.creds_file.exists():
            self.creds_file.unlink()
        print(f"✓ Logged out from {self.provider}")

    def _save_credentials(self, creds: Credentials):
        """Save credentials (encrypted)"""
        creds_data = {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": creds.scopes,
        }

        encrypted = self.cipher.encrypt(
            json.dumps(creds_data).encode()
        )

        self.creds_file.write_bytes(encrypted)
        self.creds_file.chmod(0o600)

    def _load_credentials(self) -> Credentials:
        """Load credentials (decrypt)"""
        encrypted = self.creds_file.read_bytes()
        decrypted = self.cipher.decrypt(encrypted)
        creds_data = json.loads(decrypted)

        return Credentials.from_authorized_user_info(
            creds_data,
            self.SCOPES[self.provider]
        )
```

## セキュリティ考慮事項

1. **認証情報の保護**
   - Fernet（AES-128）で暗号化
   - ファイルパーミッション: 0o600（owner only）
   - 暗号化キーは別ファイル（.key）

2. **トークン管理**
   - リフレッシュトークンで自動更新
   - 期限切れの自動検出

3. **client_secrets.json**
   - ユーザーがGoogle Cloud Consoleから取得
   - .gitignoreに追加（公開しない）

## テスト戦略

```python
# tests/auth/test_oauth2.py
import pytest
from kagura.auth import OAuth2Manager

def test_oauth2_manager_init():
    auth = OAuth2Manager(provider="google")
    assert auth.provider == "google"
    assert auth.config_dir.exists()

@pytest.mark.skipif(not has_credentials(), reason="Manual login required")
def test_get_credentials():
    auth = OAuth2Manager(provider="google")
    creds = auth.get_credentials()
    assert creds.valid
```

## マイグレーション

既存ユーザーへの影響なし。OAuth2はオプション：

```bash
# 従来通りAPIキーでも利用可能
export GOOGLE_API_KEY=your-api-key
kagura chat

# またはOAuth2を選択
kagura auth login --provider google
kagura chat  # APIキー不要
```

## ドキュメント

### 必要なドキュメント
1. OAuth2 Setup Guide
2. Google Cloud Console設定手順
3. client_secrets.json取得方法
4. トラブルシューティング

## 参考資料

- [Google OAuth2](https://developers.google.com/identity/protocols/oauth2)
- [google-auth-oauthlib](https://google-auth-oauthlib.readthedocs.io/)

## 改訂履歴

- 2025-10-04: 初版作成（RFC-013とRFC-014に分割）
