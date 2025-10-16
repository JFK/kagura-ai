# RFC-023: Google Workspace Integration

**ステータス**: Draft
**作成日**: 2025-10-16
**優先度**: ⭐️⭐️ Medium
**対象バージョン**: v2.7.0+
**関連Issue**: [#155](https://github.com/JFK/kagura-ai/issues/155)
**関連RFC**: RFC-013 (OAuth2 Authentication)

---

## 📋 概要

Kagura AIからGoogle Workspace（Drive、Calendar、Gmail）にアクセスし、ドキュメント検索・予定管理・メール操作を可能にします。

**Note**: 元々RFC-002（Multimodal RAG）の一部として提案されていましたが、独立したRFCとして分離しました。

---

## 🎯 目標

### 主要機能

1. **Google Drive統合**
   - ファイル検索（名前、タイプ、更新日時）
   - ファイル内容読み込み（Docs, Sheets, Slides）
   - ファイルメタデータ取得
   - ファイルダウンロード・アップロード

2. **Google Calendar統合**
   - イベント検索（日時範囲、キーワード）
   - イベント作成・更新・削除
   - 参加者管理
   - リマインダー設定

3. **Gmail統合**
   - メール検索（差出人、件名、本文）
   - メール読み込み・要約
   - メール送信
   - ラベル・アーカイブ操作

### 成功指標

- ✅ OAuth2認証がスムーズ（RFC-013活用）
- ✅ Drive/Calendar/Gmailの基本操作が動作
- ✅ 42+テスト（100%カバレッジ）
- ✅ エラーハンドリング適切
- ✅ レート制限対応
- ✅ 包括的なドキュメント

---

## 🏗️ アーキテクチャ

### 依存関係

```
RFC-023 (Google Workspace)
    ↓ 依存
RFC-013 (OAuth2 Authentication) ← v2.4.0完了済み
```

### 技術スタック

```toml
[project.optional-dependencies]
workspace = [
    "google-auth>=2.25.0",              # OAuth2（RFC-013と共通）
    "google-auth-oauthlib>=1.2.0",     # OAuth2フロー
    "google-api-python-client>=2.0.0", # Workspace API
    "google-auth-httplib2>=0.2.0",     # HTTP client
]
```

---

## 📦 実装Phase

### Phase 1: Drive統合（Week 1-2）
- OAuth2スコープ追加（Drive API）
- Drive API client実装
- `search_drive()`, `read_drive_file()` ツール
- 15+テスト

### Phase 2: Calendar統合（Week 3-4）
- Calendar API client実装
- `get_calendar_events()`, `create_event()` ツール
- 12+テスト

### Phase 3: Gmail統合（Week 5-6）
- Gmail API client実装
- `search_gmail()`, `read_email()`, `send_email()` ツール
- 15+テスト

### Phase 4: 統合・最適化（Week 7-8）
- エラーハンドリング改善
- レート制限対応
- キャッシング機能
- CLI統合（`kagura workspace` コマンド）
- エンドツーエンドテスト

---

## 🔒 セキュリティ・プライバシー考慮

### 懸念事項

1. **プライバシー**: Drive/Gmail/Calendarへのアクセス権限
2. **スコープ管理**: 最小限の権限で実装
3. **データ保持**: ローカルキャッシュの扱い
4. **監査**: アクセスログの記録

### 対策

- ✅ 明示的なユーザー同意取得
- ✅ 必要最小限のスコープのみ要求
- ✅ OAuth2トークンの安全な保存（RFC-013）
- ✅ アクセスログ記録（Observability統合）
- ✅ キャッシュデータの自動削除

---

## 💡 議論ポイント

1. **Microsoft 365対応**: OneDrive/Outlook/Teams も実装すべきか？
2. **スコープ範囲**: 読み取り専用 vs 書き込み権限
3. **キャッシング戦略**: どのデータをどれだけキャッシュするか
4. **レート制限**: クォータ超過時のフォールバック

---

## 📅 スケジュール

**Duration**: 8週間（2ヶ月）

- Week 1-2: Phase 1（Drive）
- Week 3-4: Phase 2（Calendar）
- Week 5-6: Phase 3（Gmail）
- Week 7-8: Phase 4（統合・最適化）

**Target**: v2.7.0+

---

## 🔗 関連

- **RFC-013**: OAuth2 Authentication（完了） - 認証システム活用
- **RFC-002**: Multimodal RAG（完了） - ファイル読み込み統合可能
- **Issue #62**: 元の提案（クローズ済み）
- **Issue #155**: このRFC

---

**Status**: Draft - コミュニティフィードバック募集中
