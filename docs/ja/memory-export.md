# メモリーエクスポート/インポートガイド

**Kagura AI v4.0.0** - Universal AI Memory Platform

このガイドでは、バックアップ、移行、またはGDPRコンプライアンスのためにKaguraメモリーデータをエクスポート・インポートする方法を説明します。

---

## 📋 概要

KaguraはJSONL(JSON Lines)形式でエクスポート/インポート機能を提供します:

- **人間が読める** - プレーンテキストJSON、1行に1レコード
- **ポータブル** - 異なるマシンやバージョン間で動作
- **包括的** - メモリー、グラフデータ、メタデータをエクスポート
- **GDPR準拠** - ユーザーリクエストの完全なデータエクスポート

---

## 🚀 クイックスタート

### すべてのデータをエクスポート

```bash
# ./backupディレクトリにすべてをエクスポート
kagura memory export --output ./backup

# 出力:
# ✓ Export completed successfully!
#
# Exported:
#   • Memories: 150
#   • Graph nodes: 87
#   • Graph edges: 42
#
# Files created:
#   • memories.jsonl
#   • graph.jsonl
#   • metadata.json
```

### バックアップからインポート

```bash
# バックアップディレクトリからインポート
kagura memory import --input ./backup

# 出力:
# ✓ Import completed successfully!
#
# Imported:
#   • Memories: 150
#   • Graph nodes: 87
#   • Graph edges: 42
```

---

## 🔧 エクスポートオプション

### 選択的エクスポート

```bash
# 永続メモリーのみエクスポート(ワーキングメモリーはスキップ)
kagura memory export --output ./backup --no-working

# ワーキングメモリーのみエクスポート(永続メモリーはスキップ)
kagura memory export --output ./backup --no-persistent

# グラフデータなしでエクスポート
kagura memory export --output ./backup --no-graph
```

### ユーザー固有のエクスポート

```bash
# 特定のユーザー用にエクスポート
kagura memory export --output ./alice-backup --user-id user_alice

# 特定のエージェント用にエクスポート
kagura memory export --output ./backup --agent-name my_agent
```

---

## 📥 インポートオプション

### 既存データのクリア

```bash
# インポート前に既存データをクリア(⚠️ 破壊的)
kagura memory import --input ./backup --clear

# 警告: これはすべての既存メモリーデータを削除します!
```

### 特定ユーザーへのインポート

```bash
# 特定ユーザーのメモリーにインポート
kagura memory import --input ./backup --user-id user_alice --agent-name global
```

---

## 📁 エクスポート形式

### ディレクトリ構造

```
backup/
├── memories.jsonl       # すべてのメモリーレコード
├── graph.jsonl          # グラフノードとエッジ(有効な場合)
└── metadata.json        # エクスポートメタデータ
```

### JSONL形式

#### メモリーレコード(`memories.jsonl`)

```jsonl
{"type":"memory","scope":"working","key":"user_preference","value":"Python backend","user_id":"user_jfk","agent_name":"global","exported_at":"2025-10-27T10:30:00Z"}
{"type":"memory","scope":"persistent","key":"api_key","value":"***","user_id":"user_jfk","agent_name":"global","created_at":"2025-10-26T12:00:00Z","updated_at":"2025-10-27T10:00:00Z","metadata":{"tags":["config"],"importance":0.9},"exported_at":"2025-10-27T10:30:00Z"}
```

**フィールド**:
- `type`: 常に"memory"
- `scope`: "working"または"persistent"
- `key`: メモリーキー
- `value`: 保存された値(任意のJSON型)
- `user_id`: ユーザー識別子
- `agent_name`: エージェント名
- `created_at`, `updated_at`: タイムスタンプ(永続メモリーのみ)
- `metadata`: オプションのメタデータ辞書
- `exported_at`: エクスポートタイムスタンプ

#### グラフレコード(`graph.jsonl`)

```jsonl
{"type":"node","id":"mem_001","node_type":"memory","data":{"key":"user_preference"},"exported_at":"2025-10-27T10:30:00Z"}
{"type":"edge","src":"mem_001","dst":"mem_002","rel_type":"related_to","weight":0.8,"data":{},"exported_at":"2025-10-27T10:30:00Z"}
```

**ノードフィールド**:
- `type`: "node"
- `id`: ノード識別子
- `node_type`: ノードタイプ(例: "memory", "user", "topic")
- `data`: ノード属性

**エッジフィールド**:
- `type`: "edge"
- `src`: ソースノードID
- `dst`: デスティネーションノードID
- `rel_type`: 関係タイプ
- `weight`: エッジウェイト(0.0-1.0)

#### メタデータ(`metadata.json`)

```json
{
  "exported_at": "2025-10-27T10:30:00Z",
  "user_id": "user_jfk",
  "agent_name": "global",
  "stats": {
    "memories": 150,
    "graph_nodes": 87,
    "graph_edges": 42
  },
  "format_version": "1.0"
}
```

---

## 🔄 ユースケース

### 1. 重要な変更前のバックアップ

```bash
# Kaguraアップグレード前
kagura memory export --output ./backup-before-upgrade

# Kaguraをアップグレード
pip install --upgrade kagura-ai

# 問題が発生した場合、復元
kagura memory import --input ./backup-before-upgrade --clear
```

### 2. 新しいマシンへの移行

```bash
# 古いマシンで
kagura memory export --output ./kagura-backup

# ./kagura-backupを新しいマシンにコピー

# 新しいマシンで
pip install kagura-ai
kagura memory import --input ./kagura-backup
```

### 3. GDPRデータエクスポート

```bash
# GDPRリクエスト用にすべてのユーザーデータをエクスポート
kagura memory export --output ./gdpr-export --user-id user_alice

# ./gdpr-exportをユーザーに提供
```

### 4. 選択的バックアップ

```bash
# 日次バックアップ(ワーキングメモリーのみ)
kagura memory export --output ./daily-backup-$(date +%Y%m%d) --no-persistent

# 週次完全バックアップ
kagura memory export --output ./weekly-backup-$(date +%Y%m%d)
```

---

## ⚠️ 重要な注意事項

### データ損失の防止

- **必ずバックアップを取る** `--clear`フラグを使用する前に
- **テストインポート** まずコピーで試す
- **ラウンドトリップを検証** 重要なデータで

### 大規模なエクスポート

大規模なメモリーデータベース(>10,000レコード)の場合:
- エクスポートに数分かかる場合があります
- JSONLファイルは大きくなる可能性があります(100MB+)
- ユーザーまたはスコープごとの選択的エクスポートを検討してください

### バージョン互換性

- フォーマットバージョン1.0(現在)
- 将来のバージョンは下位互換性を維持します
- メタデータには検証用の`format_version`が含まれています

---

## 🧪 エクスポート/インポートのテスト

### エクスポートの検証

```bash
# エクスポート
kagura memory export --output ./test-export

# ファイルが存在することを確認
ls -lh ./test-export/

# 期待される出力:
# memories.jsonl
# graph.jsonl
# metadata.json
```

### ラウンドトリップの検証

```bash
# テストデータを保存
echo 'manager.working.set("test", "value")' | python -c "..."

# エクスポート
kagura memory export --output ./roundtrip-test

# クリア(⚠️ テスト目的のみ)
rm ~/.local/share/kagura/memory.db

# インポート
kagura memory import --input ./roundtrip-test

# データが復元されたことを確認
# (kagura mcp toolsで確認)
```

---

## 📚 APIリファレンス

### Python API

```python
from kagura.core.memory import MemoryManager
from kagura.core.memory.export import MemoryExporter, MemoryImporter

# マネージャーを作成
manager = MemoryManager(user_id="user_jfk", agent_name="global")

# エクスポート
exporter = MemoryExporter(manager)
stats = await exporter.export_all(
    output_dir="./backup",
    include_working=True,
    include_persistent=True,
    include_graph=True,
)
print(f"Exported {stats['memories']} memories")

# インポート
importer = MemoryImporter(manager)
stats = await importer.import_all(
    input_dir="./backup",
    clear_existing=False,  # 既存データとマージ
)
print(f"Imported {stats['memories']} memories")
```

---

## 🔗 関連ドキュメント

- [APIリファレンス](./api-reference.md)
- [メモリー管理](./memory-management.md)
- [グラフメモリー](./graph-memory.md)

---

**最終更新**: 2025-10-27
**バージョン**: 4.0.0
