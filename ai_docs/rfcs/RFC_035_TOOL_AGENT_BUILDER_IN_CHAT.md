# RFC-035: Tool/Agent Builder in Chat (Dynamic Extension)

**ステータス**: Draft (思案中)
**作成日**: 2025-10-16
**優先度**: ⭐️ Medium (UX Enhancement)
**関連Issue**: TBD
**依存RFC**: RFC-033 (Chat Enhancement), RFC-005 (Meta Agent)

---

## 📋 概要

### アイデア

`kagura chat`内でツールやエージェントを作成し、即座に利用可能にする。

### コンセプト

```bash
$ kagura chat

[You] > CSVファイルを分析するツールを作って

🔧 Creating tool: csv_analyzer...
📦 Installing pandas...
✓ Tool created and ready

[AI] CSV分析ツールを作成しました。使ってみましょう。

[You] > data.csvを分析して

🔧 Using tool: csv_analyzer
📊 Analyzing data.csv...

[AI]
このCSVファイルには...
- 行数: 1000
- カラム: name, age, city
- 統計: 平均年齢 35.2歳
...

[You] > このツールを保存して

💾 Saved tool: csv_analyzer
📍 Location: ~/.kagura/tools/csv_analyzer.py
✓ Tool will be available in future sessions
```

---

## 🎯 目標

### 成功指標

1. **即座のツール作成**
   - ✅ Chat内でツール作成要求
   - ✅ Meta Agentが自動生成
   - ✅ 依存関係自動インストール
   - ✅ 即座に利用可能

2. **永続化・再利用**
   - ✅ ツール保存 (~/.kagura/tools/)
   - ✅ 次回session で自動ロード
   - ✅ バージョン管理

3. **エージェント作成**
   - ✅ Agent作成も同様
   - ✅ 複雑なワークフロー対応

---

## 🏗️ アーキテクチャ

### 現在の構成

```
kagura chat
  ↓
Fixed 8 tools (file_read, web_search, etc.)
  ↓
User requests
```

### 改善後の構成 (Dynamic Extension)

```
kagura chat
  ↓
Fixed tools (8) + Dynamic tools (N)
  ↓
User: "Create a tool for X"
  ↓
┌────────────────────────────┐
│ Tool/Agent Builder         │
│ - Analyze requirements     │
│ - Generate code            │
│ - Install dependencies     │
│ - Validate & test          │
│ - Save to ~/.kagura/tools/ │
└────────────┬───────────────┘
             │
             ↓
Tool/Agent Registry に追加
             │
             ↓
Immediately available for use
```

---

## 📦 Phase 1: Tool Builder (Week 1)

### 実装内容

#### 1.1 Tool Builder

```python
# src/kagura/meta/tool_builder.py

from dataclasses import dataclass
from pathlib import Path

@dataclass
class ToolSpec:
    """Tool specification"""
    name: str
    description: str
    input_params: dict[str, str]  # name: type
    output_type: str
    required_packages: list[str]
    implementation_hints: str

class ToolBuilder:
    """Build tools dynamically from user requests"""

    async def analyze_request(self, request: str) -> ToolSpec:
        """Analyze user request and create tool spec

        Args:
            request: User request like "Create a CSV analyzer tool"

        Returns:
            ToolSpec with requirements
        """
        prompt = f"""Analyze this tool creation request:

Request: {request}

Generate a tool specification:
- Name (snake_case)
- Description
- Input parameters (with types)
- Output type
- Required pip packages
- Implementation hints

Return JSON.
"""

        from kagura.core.llm import call_llm, LLMConfig
        from kagura.core.parser import parse_response

        config = LLMConfig(model="gpt-4o-mini", temperature=0.3)
        response = await call_llm(prompt, config)

        return parse_response(str(response), ToolSpec)

    async def generate_code(self, spec: ToolSpec) -> str:
        """Generate tool implementation code

        Args:
            spec: Tool specification

        Returns:
            Python code for the tool
        """
        from kagura.meta import MetaAgent

        meta = MetaAgent()

        prompt = f"""Generate a Kagura tool:

Name: {spec.name}
Description: {spec.description}
Input: {spec.input_params}
Output: {spec.output_type}
Packages: {spec.required_packages}

Requirements:
1. Use @tool decorator from kagura
2. Include docstring
3. Add type hints
4. Handle errors gracefully
5. Return clear error messages
"""

        code = await meta.generate(prompt)
        return code

    async def install_dependencies(
        self,
        packages: list[str],
        user_approval: bool = True
    ) -> bool:
        """Install required packages

        Args:
            packages: List of package names
            user_approval: Ask user before installing

        Returns:
            True if all packages installed successfully
        """
        from kagura.core.package_manager import PackageManager

        pkg_mgr = PackageManager()

        for pkg in packages:
            if not await pkg_mgr.check_package(pkg):
                if not await pkg_mgr.install_package(pkg, user_approval):
                    return False

        return True

    async def save_tool(self, name: str, code: str) -> Path:
        """Save tool to persistent storage

        Args:
            name: Tool name
            code: Tool code

        Returns:
            Path to saved tool file
        """
        tool_dir = Path.home() / ".kagura" / "tools"
        tool_dir.mkdir(parents=True, exist_ok=True)

        tool_file = tool_dir / f"{name}.py"
        tool_file.write_text(code)

        return tool_file
```

#### 1.2 Chat統合

```python
# src/kagura/chat/session.py

class ChatSession:
    def __init__(self, ...):
        # ... existing ...
        self.tool_builder = ToolBuilder()
        self.dynamic_tools: dict[str, callable] = {}
        self._load_saved_tools()

    def _load_saved_tools(self):
        """Load tools from ~/.kagura/tools/"""
        tool_dir = Path.home() / ".kagura" / "tools"

        if not tool_dir.exists():
            return

        for tool_file in tool_dir.glob("*.py"):
            # Load and register tool
            tool_func = self._load_tool_from_file(tool_file)
            self.dynamic_tools[tool_func.__name__] = tool_func

    async def handle_tool_creation(self, request: str):
        """Handle tool creation request"""

        # 1. Analyze request
        spec = await self.tool_builder.analyze_request(request)

        console.print(f"🔧 Creating tool: {spec.name}...")

        # 2. Install dependencies
        if spec.required_packages:
            console.print(f"📦 Installing {', '.join(spec.required_packages)}...")
            success = await self.tool_builder.install_dependencies(
                spec.required_packages
            )

            if not success:
                console.print("[red]Failed to install dependencies[/]")
                return

        # 3. Generate code
        code = await self.tool_builder.generate_code(spec)

        # 4. Save tool
        tool_path = await self.tool_builder.save_tool(spec.name, code)

        console.print(f"✓ Tool created: {spec.name}")
        console.print(f"📍 Location: {tool_path}")

        # 5. Load tool immediately
        tool_func = self._load_tool_from_file(tool_path)
        self.dynamic_tools[spec.name] = tool_func

        # 6. Update chat_agent with new tool
        # (Requires dynamic tool injection)
```

---

## 📦 Phase 2: Agent Builder (Week 2)

### 実装内容

同様のアプローチでAgentも作成可能に:

```python
[You] > YouTube動画を分析するエージェントを作って

🤖 Creating agent: youtube_analyzer...
📦 Installing yt-dlp, youtube-transcript-api...
✓ Agent created and ready

[AI] YouTube分析エージェントを作成しました。

[You] > このYouTube動画を分析して: https://...

🤖 Using agent: youtube_analyzer
📺 Analyzing video...

[AI] この動画は...
```

---

## 📦 Phase 3: Dynamic Tool Injection (Week 3)

### 課題

現在の`@agent`デコレータは、定義時にツールリストを固定:

```python
@agent(tools=[tool1, tool2, tool3])  # 固定
async def chat_agent(...): ...
```

動的にツールを追加するには:

#### Option A: Agent再生成

```python
# 新しいツールが追加されたら、chat_agentを再定義
def rebuild_chat_agent(tools: list):
    @agent(tools=tools)
    async def chat_agent(...): ...

    return chat_agent
```

#### Option B: Tool Registry パターン

```python
# Global tool registry
TOOL_REGISTRY: dict[str, callable] = {}

@agent
async def chat_agent(...):
    """Available tools: check TOOL_REGISTRY"""

# Runtime でツール追加
TOOL_REGISTRY["new_tool"] = new_tool_func
```

#### Option C: プラグインシステム

```python
# ~/.kagura/tools/ を動的ロード
class ToolLoader:
    def load_all_tools(self) -> list[callable]:
        """Load all tools from directory"""
        # ... scan and import ...

# Chat起動時に全ツールをロード
@agent(tools=ToolLoader().load_all_tools())
async def chat_agent(...): ...
```

---

## 📊 成功指標

### Phase 1完了時
- ✅ Chat内でツール作成可能
- ✅ 依存関係自動インストール
- ✅ ツール永続化
- ✅ 10+ tests

### Phase 2完了時
- ✅ Chat内でエージェント作成可能
- ✅ Agent永続化・再利用
- ✅ 10+ tests

### Phase 3完了時
- ✅ 動的ツール追加動作
- ✅ Chat agent自動更新
- ✅ 5+ tests

---

## 🚨 課題・リスク

### 1. セキュリティ

**リスク**: ユーザーが作成したツールが悪意あるコード実行

**対策**:
- AST validation (既存のCodeExecutor活用)
- Sandbox実行
- ユーザー承認プロセス

### 2. 依存関係の肥大化

**リスク**: 多くのツールが多くのパッケージをインストール

**対策**:
- venv分離（ツールごと）
- パッケージサイズ制限
- ユーザー承認

### 3. ツール品質

**リスク**: 自動生成されたツールが低品質

**対策**:
- テスト自動生成
- ユーザーレビュー
- バージョン管理（改善可能）

---

## 💡 追加アイデア

### 1. Tool Marketplace

```bash
# Community tools
kagura tools search "csv analyzer"
kagura tools install kagura-ai/community/csv-analyzer

# Share your tools
kagura tools publish csv_analyzer
```

### 2. Tool Templates

```python
# Pre-defined templates
CSV_ANALYZER_TEMPLATE = """
@tool
async def csv_analyzer(file_path: str, question: str) -> str:
    '''Analyze CSV: {{ file_path }}
    Question: {{ question }}
    '''
    import pandas as pd
    df = pd.read_csv(file_path)
    # ... analysis ...
"""
```

### 3. Tool Suggestions

```python
[You] > data.csvを分析したい

💡 Suggestions:
  1. Create new CSV analyzer tool (recommended)
  2. Use execute_python (manual analysis)
  3. Use file_read (view data only)

Select [1]: _
```

---

## 🎓 参考

### 類似システム

- **ChatGPT Custom GPTs**: カスタムGPT作成
- **Claude Projects**: Project-specific tools
- **Cursor AI**: Workspace tools
- **Replit Agent**: Dynamic code generation

### Kagura の差別化

- ✅ Python-native (no-code不要)
- ✅ ローカル実行（プライバシー）
- ✅ マルチモデル対応
- ✅ 完全な制御（コード編集可能）

---

## 🚀 実装スケジュール（仮）

### Week 1: Tool Builder基礎
- ToolSpec, ToolBuilder実装
- 基本的なツール生成
- 保存・ロード

### Week 2: Chat統合
- ツール作成コマンド
- 動的ロード
- UI/UX

### Week 3: Agent Builder
- AgentSpec, AgentBuilder
- 同様の仕組み

### Week 4: 動的ツール追加
- Runtime tool injection
- Chat agent更新

### Week 5: テスト・ドキュメント
- 包括的テスト
- ユーザーガイド

---

## ❓ 検討事項

### 1. ツール作成のトリガー

**Option A**: 明示的コマンド
```
[You] > /create-tool csv analyzer
```

**Option B**: 自然言語検出
```
[You] > CSVを分析するツールを作って
→ 自動的にツール作成フロー開始
```

**推奨**: Option B (自然言語) - より直感的

### 2. 承認プロセス

**Option A**: 完全自動
```
[You] > ツール作って
→ 自動生成・自動インストール
```

**Option B**: ステップごと承認
```
[You] > ツール作って
[AI] このツールを作成します:
     - Name: csv_analyzer
     - Packages: pandas, matplotlib
     OK? [Y/n]:
```

**推奨**: Option B (承認あり) - セキュリティ

### 3. ツールの永続化

**Option A**: 常に保存
```
生成されたツールは自動的に ~/.kagura/tools/ に保存
```

**Option B**: 明示的保存
```
[You] > このツールを保存して
[AI] ✓ Saved
```

**推奨**: Option B (明示的) - ユーザー制御

---

## 🔗 他機能との統合

### RFC-033 (Chat Enhancement) との関係

- ✅ Chat内でツール作成
- ✅ 既存の8 toolsと共存
- ✅ 同じUX (自然言語)

### RFC-005 (Meta Agent) との関係

- ✅ Meta AgentをTool生成に活用
- ✅ 既存のコード生成ロジック再利用

### RFC-034 (Smart Model Selection) との関係

- ✅ ツール生成にはGPT-5使用
- ✅ ツール実行は適切なモデル選択

---

## 💬 オープンクエスチョン

### Q1: ツール vs エージェントの区別は？

**Tool**: 単一機能（入力→出力）
```python
@tool
def calculate(x: int, y: int) -> int:
    return x + y
```

**Agent**: 複数ステップ、LLM活用
```python
@agent
async def analyzer(data: str) -> str:
    """Analyze data with LLM reasoning"""
```

### Q2: ツールのスコープは？

**Session-scoped**: その session のみ
**Global**: 全sessionで利用可能

**推奨**: Global (~/.kagura/tools/) - 再利用性

### Q3: ツールのテストは？

**Option A**: テスト自動生成
```python
# Meta Agentがテストも生成
# test_csv_analyzer.py
```

**Option B**: テストなし（ユーザー任せ）

**推奨**: Option A (テスト生成) - 品質保証

---

## 🎯 最小実装 (MVP)

### 必須機能

1. ✅ ツール作成要求の検出
2. ✅ Meta Agentでコード生成
3. ✅ 依存関係インストール
4. ✅ ツール保存 (~/.kagura/tools/)
5. ✅ 次回起動時に自動ロード

### 除外（v2で追加）

- ❌ Agent作成 (v2)
- ❌ Marketplace (v2)
- ❌ Templates (v2)
- ❌ バージョン管理 (v2)

---

**このRFCは、Kagura Chatを真の「自己拡張型システム」にするための構想です。**

**実装開始**: TBD (RFC-034完了後を推奨)
**優先度**: Medium (UX向上には重要だが、コア機能ではない)
