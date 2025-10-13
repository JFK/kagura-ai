# OAuth2 Manual Testing Guide

このガイドでは、RFC-013 OAuth2認証機能の手動テスト方法を説明します。

## 前提条件

### 1. Google Cloud Consoleのセットアップ

OAuth2認証をテストするには、Google Cloud Consoleで以下の設定が必要です。

#### ステップ 1: プロジェクト作成

1. [Google Cloud Console](https://console.cloud.google.com/)にアクセス
2. 新しいプロジェクトを作成（または既存のプロジェクトを選択）

#### ステップ 2: APIの有効化

1. **APIs & Services** → **Library** に移動
2. **Generative Language API** を検索
3. **Enable** をクリック

#### ステップ 3: OAuth 2.0 Client ID作成

1. **APIs & Services** → **Credentials** に移動
2. **Create Credentials** → **OAuth client ID** をクリック
3. Application type: **Desktop app** を選択
4. Name: `Kagura AI Desktop` （任意の名前）
5. **Create** をクリック
6. **Download JSON** をクリックしてJSONファイルをダウンロード

#### ステップ 4: client_secrets.jsonの保存

ダウンロードしたJSONファイルを `~/.kagura/client_secrets.json` に保存：

```bash
mkdir -p ~/.kagura
mv ~/Downloads/client_secret_*.json ~/.kagura/client_secrets.json
chmod 600 ~/.kagura/client_secrets.json
```

### 2. 開発環境のセットアップ

```bash
# リポジトリをクローン
cd kagura-ai

# OAuth依存関係を含めてインストール
pip install -e ".[oauth,dev]"
```

## テストスクリプトの使い方

`scripts/test_oauth2.py` は、OAuth2認証機能をインタラクティブにテストするスクリプトです。

### 基本的な使い方

```bash
# ヘルプ表示
python scripts/test_oauth2.py

# 全テスト実行（ログアウトを除く）
python scripts/test_oauth2.py --all

# 個別テスト
python scripts/test_oauth2.py --login    # ログインテスト
python scripts/test_oauth2.py --status   # ステータス確認
python scripts/test_oauth2.py --token    # トークン取得
python scripts/test_oauth2.py --refresh  # トークンリフレッシュ
python scripts/test_oauth2.py --llm      # LLM呼び出し
python scripts/test_oauth2.py --cli      # CLIコマンド
python scripts/test_oauth2.py --logout   # ログアウト
```

## テストシナリオ

### シナリオ 1: 初回ログイン

新規ユーザーとしてOAuth2認証を試します。

```bash
# 1. ステータス確認（未認証のはず）
python scripts/test_oauth2.py --status

# 2. ログイン
python scripts/test_oauth2.py --login
# → ブラウザが開き、Google認証画面が表示される
# → 認証すると、認証情報が ~/.kagura/credentials.json.enc に保存される

# 3. ステータス確認（認証済みのはず）
python scripts/test_oauth2.py --status
```

**期待される出力:**

```
============================================================
  Test 2: Authentication Status
============================================================

✓ Authenticated with google
ℹ Token expires: 2025-10-13 16:00:00+00:00
```

### シナリオ 2: トークン取得

保存された認証情報からアクセストークンを取得します。

```bash
python scripts/test_oauth2.py --token
```

**期待される出力:**

```
============================================================
  Test 3: Token Retrieval
============================================================

✓ Token retrieved successfully
ℹ Token (first 20 chars): ya29.a0AfB_byC1234...
ℹ Token length: 187 characters
```

### シナリオ 3: LLM呼び出し

OAuth2認証を使って実際にGemini APIを呼び出します。

```bash
python scripts/test_oauth2.py --llm
```

**期待される出力:**

```
============================================================
  Test 6: LLM Call with OAuth2
============================================================

✓ Authentication verified
ℹ Calling Gemini API with OAuth2...
ℹ Prompt: 'What is 2+2? Answer in one word.'
✓ LLM call successful!
ℹ Response: Four
```

### シナリオ 4: CLI コマンド

`kagura auth` CLIコマンドが正しく動作することを確認します。

```bash
# CLIテスト
python scripts/test_oauth2.py --cli

# または直接CLIを実行
kagura auth status --provider google
kagura auth logout --provider google
kagura auth login --provider google
```

**期待される出力:**

```bash
$ kagura auth status --provider google
✓ Authenticated with google
Token expires: 2025-10-13 16:00:00 UTC
```

### シナリオ 5: トークンリフレッシュ

トークンの自動リフレッシュをテストします。

```bash
# トークンリフレッシュテスト
python scripts/test_oauth2.py --refresh
```

**注意:** トークンが期限切れでない場合は、リフレッシュは実行されません。実際にリフレッシュをテストするには：

1. トークンの有効期限を確認: `python scripts/test_oauth2.py --status`
2. 有効期限まで待つ（約1時間）
3. 再度トークン取得: `python scripts/test_oauth2.py --token`
   - この時、自動的にリフレッシュされる

### シナリオ 6: ログアウト

認証情報を削除します。

```bash
python scripts/test_oauth2.py --logout
```

**期待される出力:**

```
============================================================
  Test 5: Logout
============================================================

ℹ Logging out...
✓ Logged out successfully
✓ Verified: No longer authenticated
```

## 手動テストチェックリスト

以下のチェックリストを使って、OAuth2機能を網羅的にテストします。

### ✅ 基本機能

- [ ] `client_secrets.json` が正しく読み込まれる
- [ ] OAuth2ログインフローが完了する（ブラウザが開く）
- [ ] 認証情報が `~/.kagura/credentials.json.enc` に保存される
- [ ] ファイルパーミッションが 0600 になっている
- [ ] 暗号化キー `.key` が生成される

### ✅ 認証状態の確認

- [ ] `is_authenticated()` が正しく動作する
- [ ] `get_credentials()` が有効な認証情報を返す
- [ ] `get_token()` がアクセストークンを返す
- [ ] トークンの有効期限が表示される

### ✅ LLM統合

- [ ] `LLMConfig` で `auth_type="oauth2"` が設定できる
- [ ] `oauth_provider="google"` が必須になる
- [ ] `call_llm()` がOAuth2トークンを使用する
- [ ] Gemini APIが正常に呼び出せる
- [ ] レスポンスが返ってくる

### ✅ エラーハンドリング

- [ ] `client_secrets.json` がない場合に適切なエラーメッセージが表示される
- [ ] 未認証時に `NotAuthenticatedError` が発生する
- [ ] トークンリフレッシュ失敗時に適切なエラーが表示される
- [ ] `oauth_provider` なしで `auth_type="oauth2"` を使うとエラーになる

### ✅ CLIコマンド

- [ ] `kagura auth login --provider google` が動作する
- [ ] `kagura auth status --provider google` が動作する
- [ ] `kagura auth logout --provider google` が動作する
- [ ] ステータス表示が見やすい（✓/✗ 記号使用）

### ✅ セキュリティ

- [ ] 認証情報が暗号化されている（Fernet）
- [ ] ファイルパーミッションが適切（0600）
- [ ] トークンがコンソールに表示されない
- [ ] `.gitignore` に `~/.kagura/` が追加されている

### ✅ トークンリフレッシュ

- [ ] 期限切れトークンが自動的にリフレッシュされる
- [ ] リフレッシュ後の認証情報が保存される
- [ ] リフレッシュトークンが有効な間は再ログイン不要

## トラブルシューティング

### client_secrets.json not found

**エラー:**
```
✗ client_secrets.json not found at: /home/user/.kagura/client_secrets.json
```

**解決方法:**
1. Google Cloud Consoleから正しくJSONをダウンロードしたか確認
2. ファイルを `~/.kagura/client_secrets.json` に配置
3. パーミッションを確認: `chmod 600 ~/.kagura/client_secrets.json`

### OAuth2 dependencies not installed

**エラー:**
```
✗ OAuth2 dependencies not installed
ℹ Install with: pip install kagura-ai[oauth]
```

**解決方法:**
```bash
pip install -e ".[oauth]"
```

### Not authenticated

**エラー:**
```
✗ Not authenticated with google
```

**解決方法:**
```bash
python scripts/test_oauth2.py --login
```

### Token refresh failed

**エラー:**
```
✗ Token refresh failed: invalid_grant
```

**解決方法:**
1. ログアウト: `kagura auth logout --provider google`
2. 再ログイン: `kagura auth login --provider google`

### Browser did not open

**エラー:**
ブラウザが自動的に開かない

**解決方法:**
コンソールに表示されるURLを手動でブラウザで開く。

## CI/CD環境での扱い

OAuth2統合テストは、実際のブラウザ操作が必要なため、**通常のCIでは実行しません**。

### GitHub Actions設定

```yaml
# .github/workflows/test.yml

- name: Run tests (excluding integration)
  run: |
    pytest -m "not integration" --cov=src/kagura
```

### 統合テストの実行

統合テストは手動で実行します：

```bash
# ローカルでのみ実行
pytest -m integration -v

# または手動スクリプト
python scripts/test_oauth2.py --all
```

## 次のステップ

手動テストが完了したら：

1. ✅ 全テストケースをチェックリストで確認
2. ✅ 問題があればIssueに報告
3. ✅ PRにテスト結果を記載
4. ✅ ドキュメント（`docs/en/guides/oauth2-authentication.md`）を確認

## 参考資料

- [OAuth2 Authentication Guide](../docs/en/guides/oauth2-authentication.md)
- [API Reference: OAuth2Manager](../docs/en/api/auth.md)
- [RFC-013: OAuth2 Authentication](./rfcs/RFC_013_OAUTH2_AUTH.md)
- [Google OAuth2 Documentation](https://developers.google.com/identity/protocols/oauth2)
