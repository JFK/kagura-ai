# RFC-008: Plugin Marketplace - コミュニティエージェント共有プラットフォーム

## ステータス
- **状態**: Draft
- **作成日**: 2025-10-04
- **関連Issue**: #68
- **優先度**: High

## 概要

Kagura AIのエージェント、ツール、ワークフローをコミュニティで共有できるプラグインマーケットプレイスを構築します。npm、PyPI、VS Code Marketplaceのようなエコシステムを実現します。

### 目標
- `kagura install <plugin-name>`で即座にインストール
- コミュニティが作成したエージェント/ツールの発見と共有
- レーティング、レビュー、バージョン管理
- 公式プラグインと認証システム
- セキュリティスキャンと品質保証

### 非目標
- 有料プラグインの販売（将来的に検討）
- ノーコードプラグインビルダー（RFC-005で対応）

## モチベーション

### 現在の課題
1. 各ユーザーが同じようなエージェントを個別に実装
2. 優れたエージェントの共有方法がない
3. コミュニティの知見が分散

### 解決するユースケース
- **エージェント再利用**: 他人が作った高品質なエージェントを即座に利用
- **ベストプラクティス共有**: 実装例から学ぶ
- **エコシステム成長**: コミュニティ主導の機能拡張
- **発見性**: 目的に合ったエージェントを検索

### なぜ今実装すべきか
- Kagura v2.0がリリースされ、基盤が安定
- コミュニティが形成され始めている
- エコシステム構築は早期が重要

## 設計

### アーキテクチャ

```
┌─────────────────────────────────────────────┐
│         Plugin Marketplace Web              │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  Discovery & Search                 │   │
│  │  - Browse plugins                   │   │
│  │  - Search by keyword                │   │
│  │  - Category filtering               │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  Plugin Details                     │   │
│  │  - README, docs                     │   │
│  │  - Ratings, reviews                 │   │
│  │  - Install instructions             │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  Publisher Dashboard                │   │
│  │  - Upload plugin                    │   │
│  │  - Manage versions                  │   │
│  │  - View analytics                   │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────┐
│         Plugin Registry API                 │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  Plugin Management                  │   │
│  │  - CRUD operations                  │   │
│  │  - Version control                  │   │
│  │  - Security scanning                │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  User Management                    │   │
│  │  - Authentication                   │   │
│  │  - Authorization                    │   │
│  │  - Publisher verification           │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────┐
│         Kagura CLI                          │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  kagura install <plugin>            │   │
│  │  kagura search <keyword>            │   │
│  │  kagura publish                     │   │
│  │  kagura update                      │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

### コンポーネント設計

#### 1. Plugin Package Format

標準的なプラグインパッケージ構造：

```
my-kagura-plugin/
├── kagura.toml          # Plugin manifest
├── README.md            # Documentation
├── agents/              # Agent definitions
│   ├── main_agent.py
│   └── helper_agent.py
├── tools/               # Custom tools
│   └── custom_tool.py
├── workflows/           # Workflow definitions
│   └── workflow.py
├── tests/               # Tests
│   └── test_agent.py
└── requirements.txt     # Dependencies
```

**kagura.toml:**
```toml
[plugin]
name = "data-analyzer"
version = "1.0.0"
description = "Advanced data analysis agents"
author = "username"
license = "MIT"
homepage = "https://github.com/username/data-analyzer"
repository = "https://github.com/username/data-analyzer"

[plugin.metadata]
categories = ["data", "analysis", "visualization"]
tags = ["pandas", "plotly", "statistics"]
min_kagura_version = "2.0.0"

[plugin.dependencies]
# Python dependencies
python = [
    "pandas>=2.0.0",
    "plotly>=5.0.0",
    "scipy>=1.10.0"
]

# Other Kagura plugins
plugins = [
    "kagura-math-utils>=1.0.0"
]

[plugin.agents]
# Exported agents
main = "agents.main_agent:analyze_data"
visualize = "agents.main_agent:visualize_data"

[plugin.tools]
# Exported tools
stats = "tools.custom_tool:calculate_statistics"
```

#### 2. CLI Commands

```bash
# プラグイン検索
kagura search "data analysis"

# プラグイン情報表示
kagura info data-analyzer

# プラグインインストール
kagura install data-analyzer

# 特定バージョンインストール
kagura install data-analyzer@1.2.0

# プラグイン一覧
kagura list

# プラグイン更新
kagura update data-analyzer

# 全プラグイン更新
kagura update --all

# プラグイン削除
kagura uninstall data-analyzer

# プラグイン公開
kagura publish

# プラグイン作成（テンプレート）
kagura create plugin my-plugin
```

#### 3. Plugin Discovery API

```python
from kagura.plugins import search, install, list_plugins

# プラグイン検索
results = search("data analysis", category="data")
for plugin in results:
    print(f"{plugin.name}: {plugin.description}")
    print(f"⭐ {plugin.rating}/5 ({plugin.downloads} downloads)")

# プログラマティックにインストール
install("data-analyzer", version="1.0.0")

# インストール済みプラグイン
plugins = list_plugins()
for plugin in plugins:
    print(f"{plugin.name} v{plugin.version}")
```

#### 4. Plugin Usage

```python
# プラグインのエージェントを使用
from kagura.plugins import use

# プラグインをロード
data_analyzer = use("data-analyzer")

# エージェント実行
result = await data_analyzer.analyze_data(
    data=df,
    analysis_type="correlation"
)

# ツール使用
stats = data_analyzer.tools.stats(data)
```

### 統合例

#### 例1: プラグインの検索とインストール

```bash
# データ分析系のプラグインを検索
$ kagura search data

Found 15 plugins:

1. data-analyzer ⭐ 4.8/5 (2.5k downloads)
   Advanced data analysis with pandas and plotly
   Categories: data, analysis
   Author: @data-science-team

2. csv-processor ⭐ 4.5/5 (1.2k downloads)
   CSV file processing and transformation
   Categories: data, etl
   Author: @csv-wizard

3. ml-insights ⭐ 4.9/5 (3.1k downloads)
   Machine learning insights and AutoML
   Categories: data, ml, ai
   Author: @ml-community

# 詳細情報
$ kagura info data-analyzer

data-analyzer v1.0.0
====================
Advanced data analysis agents powered by pandas and plotly

Author: @data-science-team
License: MIT
Homepage: https://kagura-plugins.dev/data-analyzer

Agents:
  - analyze_data: Perform statistical analysis
  - visualize_data: Create interactive visualizations
  - clean_data: Data cleaning and preprocessing

Dependencies:
  - pandas>=2.0.0
  - plotly>=5.0.0

Install: kagura install data-analyzer

# インストール
$ kagura install data-analyzer

Installing data-analyzer v1.0.0...
✓ Downloading package
✓ Verifying signature
✓ Installing dependencies
✓ Registering agents

Successfully installed data-analyzer v1.0.0

Try: kagura run data-analyzer.analyze_data --help
```

#### 例2: プラグイン作成と公開

```bash
# プラグインテンプレート作成
$ kagura create plugin github-analytics

Created plugin: github-analytics/
├── kagura.toml
├── README.md
├── agents/
│   └── main_agent.py
├── tools/
├── tests/
│   └── test_agent.py
└── requirements.txt

# エージェント実装
$ cat agents/main_agent.py
```

```python
from kagura import agent, tool
from github import Github

@tool
def fetch_repo_stats(repo: str) -> dict:
    """Fetch GitHub repository statistics"""
    g = Github()
    repository = g.get_repo(repo)

    return {
        "stars": repository.stargazers_count,
        "forks": repository.forks_count,
        "issues": repository.open_issues_count
    }

@agent(model="gpt-4o-mini")
async def analyze_repo(repo: str) -> str:
    """
    Analyze GitHub repository: {{ repo }}

    Provide insights on activity, popularity, and health.
    """
    stats = fetch_repo_stats(repo)
    return f"Analyzing stats: {stats}"
```

```bash
# テスト実行
$ kagura test

Running tests...
✓ test_analyze_repo passed

# 公開
$ kagura publish

Publishing github-analytics v0.1.0...
✓ Validating plugin
✓ Running security scan
✓ Building package
✓ Uploading to registry

Successfully published github-analytics v0.1.0
View at: https://kagura-plugins.dev/github-analytics
```

#### 例3: プラグインの組み合わせ

```python
from kagura.plugins import use

# 複数のプラグインを組み合わせる
github = use("github-analytics")
slack = use("slack-notifier")
scheduler = use("task-scheduler")

# GitHub分析
async def daily_github_report(repos: list[str]):
    """毎日のGitHub活動レポート"""

    reports = []
    for repo in repos:
        analysis = await github.analyze_repo(repo)
        reports.append(f"**{repo}**\n{analysis}\n")

    # Slackに通知
    await slack.post_message(
        channel="#dev-team",
        text="\n".join(reports)
    )

# スケジュール登録
scheduler.daily(hour=9, func=daily_github_report, repos=["owner/repo1", "owner/repo2"])
```

## 実装計画

### Phase 1: Registry Backend (v2.3.0)
- [ ] Plugin Registry API実装
- [ ] データベース設計（PostgreSQL）
- [ ] ユーザー認証（GitHub OAuth）
- [ ] プラグインCRUD操作

### Phase 2: CLI Integration (v2.4.0)
- [ ] `kagura install/search/publish` コマンド
- [ ] プラグイン管理（ローカルDB）
- [ ] バージョン管理
- [ ] 依存関係解決

### Phase 3: Marketplace Web (v2.5.0)
- [ ] プラグイン検索UI
- [ ] プラグイン詳細ページ
- [ ] レーティング・レビュー
- [ ] パブリッシャーダッシュボード

### Phase 4: Advanced Features (v2.6.0)
- [ ] セキュリティスキャン
- [ ] 自動テスト実行
- [ ] 使用統計・分析
- [ ] 公式プラグイン認証

## 技術的詳細

### 依存関係

```toml
[project.optional-dependencies]
marketplace = [
    "httpx>=0.25.0",           # HTTP client
    "toml>=0.10.2",            # TOML parsing
    "packaging>=23.0",         # Version parsing
    "cryptography>=41.0.0",    # Signature verification
]
```

### Plugin Registry Schema

```sql
-- plugins table
CREATE TABLE plugins (
    id UUID PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    author_id UUID REFERENCES users(id),
    homepage VARCHAR(500),
    repository VARCHAR(500),
    license VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- plugin_versions table
CREATE TABLE plugin_versions (
    id UUID PRIMARY KEY,
    plugin_id UUID REFERENCES plugins(id),
    version VARCHAR(50) NOT NULL,
    changelog TEXT,
    package_url VARCHAR(500),
    package_hash VARCHAR(128),
    min_kagura_version VARCHAR(50),
    published_at TIMESTAMP DEFAULT NOW(),
    downloads INT DEFAULT 0,
    UNIQUE(plugin_id, version)
);

-- plugin_ratings table
CREATE TABLE plugin_ratings (
    id UUID PRIMARY KEY,
    plugin_id UUID REFERENCES plugins(id),
    user_id UUID REFERENCES users(id),
    rating INT CHECK (rating >= 1 AND rating <= 5),
    review TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(plugin_id, user_id)
);

-- plugin_categories table
CREATE TABLE plugin_categories (
    plugin_id UUID REFERENCES plugins(id),
    category VARCHAR(100),
    PRIMARY KEY(plugin_id, category)
);
```

### Security Scanning

```python
from kagura.plugins.security import PluginScanner

scanner = PluginScanner()

# プラグインのセキュリティスキャン
issues = scanner.scan_package("plugin.tar.gz")

for issue in issues:
    print(f"{issue.severity}: {issue.message}")
    # 検出項目:
    # - 危険なコード（eval, exec）
    # - 既知の脆弱性（dependency check）
    # - ハードコードされたシークレット
    # - ネットワークアクセス
```

## テスト戦略

### ユニットテスト

```python
# tests/plugins/test_registry.py
import pytest
from kagura.plugins import PluginRegistry

@pytest.mark.asyncio
async def test_search_plugins():
    registry = PluginRegistry()

    results = await registry.search("data")

    assert len(results) > 0
    assert all("data" in p.name.lower() or "data" in p.description.lower() for p in results)

@pytest.mark.asyncio
async def test_install_plugin():
    registry = PluginRegistry()

    plugin = await registry.install("test-plugin", version="1.0.0")

    assert plugin.name == "test-plugin"
    assert plugin.version == "1.0.0"
```

## セキュリティ考慮事項

1. **コード検証**
   - 公開前のセキュリティスキャン
   - 署名検証
   - サンドボックス実行

2. **レビュープロセス**
   - 公式プラグインの手動レビュー
   - コミュニティによるフラグ機能

3. **アクセス制限**
   - プラグインの権限管理
   - ネットワークアクセス制御

## マイグレーション

既存のKaguraユーザーへの影響なし。プラグインシステムは新機能：

```bash
# プラグイン機能を使い始める
kagura search <keyword>
kagura install <plugin-name>
```

## ドキュメント

### 必要なドキュメント
1. Plugin Development Guide
2. Publishing Guide
3. Security Best Practices
4. Plugin API Reference
5. Marketplace利用ガイド

## 参考資料

- [npm Registry](https://www.npmjs.com/)
- [PyPI](https://pypi.org/)
- [VS Code Marketplace](https://marketplace.visualstudio.com/)

## 改訂履歴

- 2025-10-04: 初版作成
