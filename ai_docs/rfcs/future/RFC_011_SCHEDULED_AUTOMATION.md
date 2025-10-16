# RFC-011: Scheduled Agents & Automation - 自動実行システム

## ステータス
- **状態**: Draft
- **作成日**: 2025-10-04
- **関連Issue**: #71
- **優先度**: Medium

## 概要

Kaguraエージェントをスケジュール実行・イベント駆動で自動化するシステムを実装します。Cron的なスケジュール実行、Webhook対応、ファイル監視、デーモン化により、エージェントを完全自動化します。

### 目標
- Cron風のスケジュール実行（毎日9時、毎週月曜など）
- Webhookによるイベント駆動実行
- ファイル・ディレクトリ監視トリガー
- デーモン化（バックグラウンド実行）
- リトライ・エラーハンドリング

### 非目標
- 分散ジョブキュー（単一マシン内に注力）
- GUI管理画面（CLIベース、将来的に検討）

## モチベーション

### 現在の課題
1. エージェントの手動実行が必要
2. 定期タスクの自動化が困難
3. 外部イベントへの対応が手動

### 解決するユースケース
- **定期実行**: 毎朝レポート生成、毎週データバックアップ
- **イベント駆動**: GitHub Webhook → コードレビュー自動化
- **ファイル監視**: 新しいファイルが追加されたら自動処理
- **デーモン**: 常駐プロセスとして稼働

### なぜ今実装すべきか
- エージェントの実用化には自動化が必須
- Cronの代替としてのニーズ
- CI/CD、DevOps統合の需要

## 設計

### アーキテクチャ

```
┌─────────────────────────────────────────────┐
│         Scheduler Daemon                    │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  Cron Scheduler                     │   │
│  │  - Parse cron expressions          │   │
│  │  - Schedule jobs                    │   │
│  │  - Execute at specified time        │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  Webhook Server                     │   │
│  │  - HTTP endpoint                    │   │
│  │  - Signature verification           │   │
│  │  - Trigger agents                   │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  File Watcher                       │   │
│  │  - Monitor directories              │   │
│  │  - Detect file changes              │   │
│  │  - Trigger on create/modify/delete  │   │
│  └─────────────────────────────────────┘   │
│                                             │
│  ┌─────────────────────────────────────┐   │
│  │  Job Queue                          │   │
│  │  - Task queue                       │   │
│  │  - Retry logic                      │   │
│  │  - Error handling                   │   │
│  └─────────────────────────────────────┘   │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│         Kagura Agents                       │
│         (Automated Execution)               │
└─────────────────────────────────────────────┘
```

### コンポーネント設計

#### 1. Cron Scheduling

Cron風のスケジュール実行：

```python
from kagura import agent, schedule

@agent(model="gpt-4o-mini")
@schedule.cron("0 9 * * *")  # 毎日9時
async def morning_report() -> str:
    """Generate morning report"""
    pass

@agent(model="gpt-4o-mini")
@schedule.cron("0 0 * * 1")  # 毎週月曜0時
async def weekly_summary() -> str:
    """Generate weekly summary"""
    pass

@agent(model="gpt-4o-mini")
@schedule.cron("*/30 * * * *")  # 30分ごと
async def health_check() -> str:
    """Check system health"""
    pass

# スケジューラー起動
scheduler = schedule.Scheduler()
scheduler.start()

# または CLI
# $ kagura schedule start
```

#### 2. Interval Scheduling

シンプルな間隔実行：

```python
from kagura import agent, schedule

@agent(model="gpt-4o-mini")
@schedule.every(hours=1)
async def hourly_task() -> str:
    """Run every hour"""
    pass

@agent(model="gpt-4o-mini")
@schedule.every(minutes=30)
async def half_hourly_task() -> str:
    """Run every 30 minutes"""
    pass

@agent(model="gpt-4o-mini")
@schedule.every(days=1, at="09:00")
async def daily_at_9am() -> str:
    """Run daily at 9 AM"""
    pass
```

#### 3. Webhook Triggers

外部イベント駆動：

```python
from kagura import agent, webhook

@agent(model="gpt-4o")
@webhook.on("github.push")
async def on_github_push(payload: dict) -> str:
    """
    Triggered on GitHub push webhook.

    Payload: {{ payload }}
    """
    repo = payload["repository"]["full_name"]
    commits = payload["commits"]

    return f"Analyzing {len(commits)} commits in {repo}"

# Webhookサーバー起動
webhook.serve(port=8000)

# GitHub Webhook設定:
# URL: http://your-server:8000/webhook/github.push
# Secret: (環境変数 GITHUB_WEBHOOK_SECRET)
```

#### 4. File Watching

ファイル監視トリガー：

```python
from kagura import agent, watch

@agent(model="gpt-4o-mini")
@watch.directory("~/Downloads", pattern="*.pdf")
async def process_pdf(file_path: str) -> str:
    """
    Process PDF file: {{ file_path }}

    Extract text and summarize.
    """
    pass

@agent(model="gpt-4o-mini")
@watch.directory("/var/log", pattern="error.log")
async def analyze_errors(file_path: str) -> str:
    """
    Analyze error log: {{ file_path }}

    Detect patterns and suggest fixes.
    """
    pass

# ファイルウォッチャー起動
watcher = watch.Watcher()
watcher.start()
```

#### 5. Daemon Mode

バックグラウンドプロセスとして実行：

```bash
# デーモン起動
kagura daemon start

# ステータス確認
kagura daemon status

# 出力:
# Kagura Daemon (PID: 12345)
# Status: Running
# Uptime: 2h 15m
#
# Scheduled Jobs: 3
#   - morning_report (next: 2025-10-05 09:00)
#   - weekly_summary (next: 2025-10-07 00:00)
#   - health_check (next: 2025-10-04 11:00)
#
# Webhooks: 2
#   - /webhook/github.push
#   - /webhook/slack.message
#
# File Watchers: 1
#   - ~/Downloads/*.pdf

# ログ確認
kagura daemon logs

# デーモン停止
kagura daemon stop
```

### 統合例

#### 例1: 毎朝のレポート生成

```python
from kagura import agent, schedule, tool

@tool
def fetch_metrics() -> dict:
    """Fetch daily metrics"""
    return {
        "users": 1234,
        "revenue": 56789,
        "errors": 12
    }

@agent(model="gpt-4o-mini")
@schedule.cron("0 9 * * *")  # 毎朝9時
async def daily_report() -> str:
    """
    Generate daily report.

    Include:
    - Key metrics
    - Issues
    - Recommendations
    """
    metrics = fetch_metrics()

    report = f"""
    Daily Report - {datetime.now().strftime('%Y-%m-%d')}

    Metrics:
    {metrics}

    Please analyze and provide insights.
    """

    return report

# Slackに送信
@schedule.cron("0 9 * * *")
async def send_report_to_slack():
    report = await daily_report()
    send_slack_message(channel="#daily-reports", text=report)
```

#### 例2: GitHub Webhook自動コードレビュー

```python
from kagura import agent, webhook

@agent(model="gpt-4o")
@webhook.on("github.pull_request")
async def auto_code_review(payload: dict) -> str:
    """
    Automatic code review on PR.

    Payload: {{ payload }}
    """
    if payload["action"] != "opened":
        return "Skipped (not a new PR)"

    pr_number = payload["number"]
    repo = payload["repository"]["full_name"]

    # PRの内容を取得
    pr_diff = fetch_pr_diff(repo, pr_number)

    # コードレビュー
    review = f"""
    Review this pull request:

    Repository: {repo}
    PR #{pr_number}

    Diff:
    {pr_diff}

    Provide:
    1. Code quality assessment
    2. Potential bugs
    3. Suggestions
    """

    review_result = await analyze_code(review)

    # GitHubにコメント投稿
    post_pr_comment(repo, pr_number, review_result)

    return f"Review posted for PR #{pr_number}"

# Webhookサーバー起動
webhook.serve(port=8000, secret=os.getenv("GITHUB_WEBHOOK_SECRET"))
```

#### 例3: ファイル監視自動処理

```python
from kagura import agent, watch

@agent(model="gpt-4o")
@watch.directory("~/Documents/invoices", pattern="*.pdf")
async def process_invoice(file_path: str) -> dict:
    """
    Extract invoice data from PDF: {{ file_path }}

    Extract:
    - Invoice number
    - Date
    - Amount
    - Items
    """
    pass

@watch.on_complete
async def save_invoice_data(result: dict, file_path: str):
    """処理完了後にデータベースに保存"""
    db.insert_invoice(result)
    os.rename(file_path, f"~/Documents/invoices/processed/{os.path.basename(file_path)}")

# ウォッチャー起動
watcher = watch.Watcher()
watcher.start()

# 新しいPDFが~/Documents/invoicesに追加されると自動処理
```

#### 例4: リトライ機能付きスケジュール

```python
from kagura import agent, schedule

@agent(model="gpt-4o-mini")
@schedule.cron("0 * * * *")  # 毎時
@schedule.retry(max_attempts=3, backoff_seconds=60)
async def unreliable_task() -> str:
    """
    Task that may fail.

    Retry up to 3 times with 60s backoff.
    """
    # API呼び出しなど、失敗する可能性のある処理
    result = await call_external_api()

    if not result:
        raise Exception("API call failed")

    return result

# エラーハンドラー
@schedule.on_error
async def handle_error(error: Exception, task_name: str):
    """スケジュールタスクのエラーハンドリング"""
    send_alert(f"Task {task_name} failed: {error}")
```

## 実装計画

### Phase 1: Cron Scheduling (v2.3.0)
- [ ] Cron式パーサー
- [ ] スケジューラー実装
- [ ] `@schedule.cron` デコレータ
- [ ] `kagura schedule` コマンド

### Phase 2: Webhook & Events (v2.4.0)
- [ ] Webhookサーバー
- [ ] 署名検証（GitHub, Slack等）
- [ ] `@webhook.on` デコレータ
- [ ] イベントルーティング

### Phase 3: File Watching (v2.5.0)
- [ ] ファイルウォッチャー
- [ ] `@watch.directory` デコレータ
- [ ] パターンマッチング
- [ ] イベントフィルター

### Phase 4: Daemon & Advanced (v2.6.0)
- [ ] デーモン化
- [ ] `kagura daemon` コマンド
- [ ] ジョブキュー
- [ ] リトライ・エラーハンドリング

## 技術的詳細

### 依存関係

```toml
[project.optional-dependencies]
automation = [
    "apscheduler>=3.10.0",     # Job scheduling
    "croniter>=2.0.0",         # Cron parsing
    "watchdog>=3.0.0",         # File watching
    "fastapi>=0.104.0",        # Webhook server
    "python-daemon>=3.0.0",    # Daemonization
]
```

### Cron Implementation

```python
# src/kagura/schedule/cron.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from croniter import croniter

class CronScheduler:
    """Cron-style job scheduler"""

    def __init__(self):
        self._scheduler = AsyncIOScheduler()
        self._jobs = []

    def add_job(self, func, cron_expr: str):
        """Add a cron job"""
        # Validate cron expression
        if not croniter.is_valid(cron_expr):
            raise ValueError(f"Invalid cron expression: {cron_expr}")

        job = self._scheduler.add_job(
            func,
            trigger="cron",
            **self._parse_cron(cron_expr)
        )

        self._jobs.append(job)

    def _parse_cron(self, expr: str) -> dict:
        """Parse cron expression to APScheduler format"""
        parts = expr.split()
        return {
            "minute": parts[0],
            "hour": parts[1],
            "day": parts[2],
            "month": parts[3],
            "day_of_week": parts[4]
        }

    def start(self):
        """Start scheduler"""
        self._scheduler.start()

    def stop(self):
        """Stop scheduler"""
        self._scheduler.shutdown()
```

### Webhook Implementation

```python
# src/kagura/webhook/server.py
from fastapi import FastAPI, Request, HTTPException
import hmac
import hashlib

app = FastAPI()

class WebhookServer:
    def __init__(self, secret: str = None):
        self.secret = secret
        self._handlers = {}

    def on(self, event: str):
        """Decorator to register webhook handler"""
        def decorator(func):
            self._handlers[event] = func
            return func
        return decorator

    async def handle_webhook(self, event: str, request: Request):
        """Handle incoming webhook"""
        # Verify signature
        if self.secret:
            signature = request.headers.get("X-Hub-Signature-256")
            if not self._verify_signature(signature, await request.body()):
                raise HTTPException(401, "Invalid signature")

        # Get handler
        handler = self._handlers.get(event)
        if not handler:
            raise HTTPException(404, "No handler for event")

        # Execute
        payload = await request.json()
        result = await handler(payload)

        return {"status": "success", "result": result}

    def _verify_signature(self, signature: str, body: bytes) -> bool:
        """Verify HMAC signature"""
        expected = hmac.new(
            self.secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(f"sha256={expected}", signature)
```

### Configuration File

`~/.kagura/automation.toml`:

```toml
[automation]
enabled = true

[automation.daemon]
pid_file = "~/.kagura/daemon.pid"
log_file = "~/.kagura/daemon.log"

[automation.schedule]
# スケジュールジョブ
[[automation.schedule.jobs]]
name = "morning_report"
agent = "reports.morning_report"
cron = "0 9 * * *"
enabled = true

[[automation.schedule.jobs]]
name = "health_check"
agent = "monitoring.health_check"
cron = "*/30 * * * *"
enabled = true

[automation.webhook]
enabled = true
port = 8000
secret = "${WEBHOOK_SECRET}"

# Webhookハンドラー
[[automation.webhook.handlers]]
event = "github.push"
agent = "github.on_push"

[automation.watch]
enabled = true

# ファイル監視
[[automation.watch.watchers]]
directory = "~/Downloads"
pattern = "*.pdf"
agent = "pdf.process_pdf"
```

## テスト戦略

```python
# tests/schedule/test_cron.py
import pytest
from kagura.schedule import CronScheduler
from datetime import datetime

@pytest.mark.asyncio
async def test_cron_scheduling():
    scheduler = CronScheduler()

    executed = False

    async def job():
        nonlocal executed
        executed = True

    scheduler.add_job(job, "* * * * *")  # Every minute
    scheduler.start()

    # Wait for execution
    await asyncio.sleep(65)

    assert executed
```

## 参考資料

- [APScheduler](https://apscheduler.readthedocs.io/)
- [Celery](https://docs.celeryq.dev/)
- [Airflow](https://airflow.apache.org/)

## 改訂履歴

- 2025-10-04: 初版作成
