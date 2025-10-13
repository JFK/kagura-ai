# RFC-005 Phase 2: Code-Aware Agent

**Status**: Draft
**Created**: 2025-10-13
**Phase**: 2 of 3
**Priority**: High
**Estimated Time**: 1 week

## 概要

Meta Agent に **コード実行機能** を統合し、データ処理・計算・ファイル操作などを自動でコード生成・実行できる「Code-Aware Agent」を実装します。

## モチベーション

### 現在の問題

**Phase 1 の Meta Agent** は以下のようなエージェントを生成できますが：

```python
@agent
async def data_analyst(csv_path: str) -> str:
    """Analyze {{ csv_path }} and provide insights."""
    pass
```

このエージェントは：
- ❌ 実際にCSVを読み込めない
- ❌ データ処理コードを実行できない
- ❌ 結果を計算できない（LLMの推測のみ）

**ユーザーが期待する動作**:
```python
result = await data_analyst("sales.csv")
# → 実際にCSVを読んで分析し、具体的な数値を返してほしい！
```

### 解決するユースケース

1. **データ分析エージェント**
   ```
   "CSVファイルを読み込んで、売上の平均・最大・最小を計算するエージェント"
   → pandas コード生成 → 実行 → 結果返却
   ```

2. **計算エージェント**
   ```
   "フィボナッチ数列の第100項を計算するエージェント"
   → Python コード生成 → 実行 → 結果返却
   ```

3. **ファイル処理エージェント**
   ```
   "JSONファイルから全てのメールアドレスを抽出するエージェント"
   → JSON parse コード生成 → 実行 → 結果返却
   ```

## 設計

### アーキテクチャ

```
┌────────────────────────────────────────────────────┐
│              Meta Agent (Phase 2)                  │
│                                                    │
│  ┌──────────────────────────────────────────────┐ │
│  │  1. NLSpecParser                             │ │
│  │     - Task analysis                          │ │
│  │     - NEW: Code execution detection          │ │
│  │       (data processing, calculations, etc.)  │ │
│  └─────────────────┬────────────────────────────┘ │
│                    │                              │
│                    ▼                              │
│  ┌──────────────────────────────────────────────┐ │
│  │  2. CodeGenerator                            │ │
│  │     - Template selection                     │ │
│  │     - NEW: Auto-add execute_code tool        │ │
│  │     - NEW: Code-execution templates          │ │
│  └─────────────────┬────────────────────────────┘ │
│                    │                              │
│                    ▼                              │
│  ┌──────────────────────────────────────────────┐ │
│  │  Generated Agent                             │ │
│  │  @agent(tools=[execute_code])                │ │
│  │  - Prompt includes code generation guidance  │ │
│  │  - LLM generates code                        │ │
│  │  - execute_code tool executes it             │ │
│  │  - Results returned to user                  │ │
│  └──────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────┘
```

### コンポーネント設計

#### 1. Code Execution Detection

**実装場所**: `src/kagura/meta/parser.py`

**機能**:
- ユーザー説明からコード実行が必要か判定
- データ処理、計算、ファイル操作などのキーワード検出

**実装**:
```python
# src/kagura/meta/parser.py

CODE_EXECUTION_KEYWORDS = [
    # Data processing
    "csv", "json", "xml", "excel", "pandas", "numpy",
    "データ処理", "データ分析", "ファイル読み込み",

    # Calculations
    "計算", "calculate", "compute", "fibonacci", "素数",
    "平均", "合計", "最大", "最小", "統計",

    # File operations
    "ファイル", "file", "read", "write", "parse",
    "抽出", "extract", "変換", "convert",

    # Algorithms
    "ソート", "sort", "フィルタ", "filter", "集計",

    # Visualization
    "グラフ", "plot", "chart", "visualization", "matplotlib",
]

async def detect_code_execution_need(description: str) -> bool:
    """
    Detect if the task requires code execution.

    Args:
        description: User's agent description

    Returns:
        True if code execution is needed
    """
    description_lower = description.lower()

    # Keyword-based detection
    if any(keyword in description_lower for keyword in CODE_EXECUTION_KEYWORDS):
        return True

    # LLM-based detection (more accurate)
    prompt = f"""
    Does this task require Python code execution?
    Task: {description}

    Answer YES if:
    - Data processing (CSV, JSON, files)
    - Mathematical calculations
    - File manipulation
    - Complex algorithms

    Answer NO if:
    - Simple text generation
    - Conversation
    - Information retrieval only

    Answer: (YES/NO)
    """

    response = await call_llm(prompt, LLMConfig(model="gpt-4o-mini"))
    return "yes" in response.lower()
```

**AgentSpec に追加**:
```python
# src/kagura/meta/spec.py

class AgentSpec(BaseModel):
    name: str
    description: str
    parameters: list[AgentParameter]
    return_type: str
    tools: list[str] = Field(default_factory=list)

    # NEW: Code execution flag
    requires_code_execution: bool = Field(
        default=False,
        description="Whether this agent needs code execution capabilities"
    )
```

#### 2. Auto-add execute_code Tool

**実装場所**: `src/kagura/meta/generator.py`

**機能**:
- `requires_code_execution=True` なら自動で `execute_code` をツールに追加
- テンプレートに code execution guidance 追加

**実装**:
```python
# src/kagura/meta/generator.py

def generate(self, spec: AgentSpec) -> str:
    """Generate agent code from spec."""

    # Auto-add execute_code tool if needed
    tools = spec.tools.copy()
    if spec.requires_code_execution and "execute_code" not in tools:
        tools.append("execute_code")

    # Select template
    if spec.requires_code_execution:
        template = self.env.get_template("agent_with_code_exec.py.j2")
    elif tools:
        template = self.env.get_template("agent_with_tools.py.j2")
    elif spec.enable_memory:
        template = self.env.get_template("agent_with_memory.py.j2")
    else:
        template = self.env.get_template("agent_base.py.j2")

    # Render
    return template.render(
        spec=spec,
        tools=tools,
        generation_date=datetime.now().strftime("%Y-%m-%d"),
    )
```

#### 3. Enhanced Template

**新規テンプレート**: `src/kagura/meta/templates/agent_with_code_exec.py.j2`

```jinja2
"""
{{ spec.name }}

{{ spec.description }}

Auto-generated by Kagura Meta Agent on {{ generation_date }}
This agent has code execution capabilities.
"""

from kagura import agent
from kagura.agents import execute_code

@agent(
    model="{{ spec.model }}",
    tools=[execute_code],
)
async def {{ spec.name }}(
{%- for param in spec.parameters %}
    {{ param.name }}: {{ param.type }}{% if param.default_value %} = {{ param.default_value }}{% endif %}{% if not loop.last %},{% endif %}
{%- endfor %}
) -> {{ spec.return_type }}:
    """
    {{ spec.description }}

    IMPORTANT: You have access to Python code execution via execute_code tool.

    When you need to:
    - Process data (CSV, JSON, files)
    - Perform calculations
    - Manipulate files
    - Run algorithms

    Generate Python code and use execute_code tool to run it.

    Example:
    ```python
    code = '''
    import pandas as pd
    df = pd.read_csv("data.csv")
    result = df["column"].mean()
    print(result)
    '''
    result = execute_code(code)
    ```

    Args:
{%- for param in spec.parameters %}
        {{ param.name }}: {{ param.description }}
{%- endfor %}

    Returns:
        {{ spec.return_description }}
    """
    pass
```

### 生成されるエージェント例

#### 例1: Data Analyst Agent

**ユーザー入力**:
```
CSVファイルを読み込んで、売上の平均・最大・最小を計算するエージェント
```

**生成されるコード**:
```python
"""
sales_analyzer

Analyze sales CSV file and calculate average, max, and min values.

Auto-generated by Kagura Meta Agent on 2025-10-13
This agent has code execution capabilities.
"""

from kagura import agent
from kagura.agents import execute_code

@agent(
    model="gpt-4o-mini",
    tools=[execute_code],
)
async def sales_analyzer(csv_path: str) -> dict:
    """
    Analyze sales CSV file and calculate average, max, and min values.

    IMPORTANT: You have access to Python code execution via execute_code tool.

    Generate Python code to:
    1. Read the CSV file using pandas
    2. Calculate average, max, min
    3. Return results as dict

    Args:
        csv_path: Path to CSV file

    Returns:
        Dict with average, max, min values
    """
    pass

# Example usage
if __name__ == "__main__":
    import asyncio
    result = asyncio.run(sales_analyzer("sales.csv"))
    print(result)
```

**実際の実行動作**:
```python
# ユーザー
result = await sales_analyzer("sales.csv")

# 内部動作（LLM + execute_code）:
# 1. LLMがプロンプトを読む
# 2. "CSVを読み込んで計算が必要 → pandasコード生成"
# 3. execute_code tool を呼び出し:
code = """
import pandas as pd
df = pd.read_csv('sales.csv')
result = {
    'average': df['amount'].mean(),
    'max': df['amount'].max(),
    'min': df['amount'].min(),
}
print(result)
"""
# 4. CodeExecutor で実行
# 5. 結果を返却

# => {'average': 15234.56, 'max': 50000, 'min': 100}
```

#### 例2: Fibonacci Calculator

**ユーザー入力**:
```
フィボナッチ数列の第n項を計算するエージェント
```

**生成されるコード**:
```python
from kagura import agent
from kagura.agents import execute_code

@agent(model="gpt-4o-mini", tools=[execute_code])
async def fibonacci_calculator(n: int) -> int:
    """
    Calculate the nth Fibonacci number.

    Use execute_code tool to generate and run efficient Python code.

    Args:
        n: Position in Fibonacci sequence

    Returns:
        nth Fibonacci number
    """
    pass
```

**実行例**:
```python
result = await fibonacci_calculator(100)
# => 354224848179261915075 (actual calculation!)
```

## 実装計画

### Phase 2-1: Code Detection & Spec Extension (Day 1-2)

**タスク**:
1. `CODE_EXECUTION_KEYWORDS` リスト作成
2. `detect_code_execution_need()` 関数実装
3. `AgentSpec` に `requires_code_execution` フィールド追加
4. `NLSpecParser` を拡張してコード実行検出を統合

**成果物**:
- `src/kagura/meta/parser.py`: +50行
- `src/kagura/meta/spec.py`: +5行
- `tests/meta/test_parser.py`: +3テスト

### Phase 2-2: Auto-add Tool & Template (Day 3-4)

**タスク**:
1. `CodeGenerator.generate()` にツール自動追加ロジック
2. 新テンプレート `agent_with_code_exec.py.j2` 作成
3. テンプレート選択ロジック更新

**成果物**:
- `src/kagura/meta/generator.py`: +20行
- `src/kagura/meta/templates/agent_with_code_exec.py.j2`: 新規（60行）
- `tests/meta/test_generator.py`: +3テスト

### Phase 2-3: CLI & Integration (Day 5)

**タスク**:
1. `kagura build agent` CLI でコード実行検出を有効化
2. 対話モード (`--chat`) で "Code execution: Yes/No" 表示
3. 統合テスト追加

**成果物**:
- `src/kagura/cli/build_cli.py`: +30行
- `tests/meta/test_cli.py`: +2テスト

### Phase 2-4: Documentation (Day 6-7)

**タスク**:
1. `docs/en/guides/meta-agent.md` に Phase 2 セクション追加
2. `docs/en/api/meta.md` に API更新
3. サンプルコード追加（`examples/meta_agent/`)

**成果物**:
- `docs/en/guides/meta-agent.md`: +150行
- `examples/meta_agent/data_analyst.py`: 新規
- `examples/meta_agent/fibonacci.py`: 新規

## テスト戦略

### ユニットテスト

```python
# tests/meta/test_parser.py

@pytest.mark.asyncio
async def test_detect_code_execution_csv():
    """Detect code execution need for CSV processing"""
    description = "Analyze sales.csv and calculate average"
    result = await detect_code_execution_need(description)
    assert result is True

@pytest.mark.asyncio
async def test_detect_code_execution_simple_text():
    """No code execution for simple text tasks"""
    description = "Translate English to Japanese"
    result = await detect_code_execution_need(description)
    assert result is False
```

```python
# tests/meta/test_generator.py

def test_generate_with_code_exec():
    """Generate agent with code execution tool"""
    spec = AgentSpec(
        name="data_analyst",
        description="Analyze CSV",
        parameters=[],
        return_type="dict",
        requires_code_execution=True,
    )

    code = generator.generate(spec)

    assert "execute_code" in code
    assert "tools=[execute_code]" in code
    assert "code execution capabilities" in code
```

### 統合テスト

```python
# tests/meta/test_integration.py

@pytest.mark.asyncio
async def test_end_to_end_code_aware_agent():
    """Test full workflow: description → code → execution"""

    # 1. Generate agent
    meta = MetaAgent()
    code = await meta.generate(
        "Calculate fibonacci(10)"
    )

    # 2. Save and load
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py') as f:
        f.write(code)
        f.flush()

        # 3. Execute generated agent
        # (mock execute_code tool)
        result = await run_generated_agent(f.name)

    # 4. Verify
    assert result == 55  # fibonacci(10) = 55
```

## 成功指標

### Phase 2 完了条件

- ✅ コード実行が必要なタスクを90%以上の精度で検出
- ✅ `execute_code` ツールが自動で追加される
- ✅ 生成されたエージェントが実際にコードを実行できる
- ✅ 10個以上のテストが全パス
- ✅ ドキュメント完備

### 実用性確認

以下のエージェントが生成・実行できること:

1. ✅ CSVデータ分析エージェント
2. ✅ フィボナッチ計算エージェント
3. ✅ JSONファイル処理エージェント
4. ✅ 数学問題解答エージェント

## Breaking Changes

なし。Phase 1 の機能は全て維持。

## 代替案

### 案1: execute_code を常に追加

- **メリット**: シンプル
- **デメリット**: 不要なエージェントにも追加される、セキュリティ懸念
- **結論**: ❌ 却下

### 案2: ユーザーが手動で指定

```bash
kagura build agent --enable-code-exec
```

- **メリット**: 明示的
- **デメリット**: ユーザーが判断する必要、UX悪い
- **結論**: ❌ 却下

### 案3: 自動検出（今回の提案）

- **メリット**: UX最高、安全性も確保
- **デメリット**: 検出精度に依存
- **結論**: ✅ 採用

## 未解決の問題

1. **コード実行の安全性**
   - 現状: CodeExecutor の AST検証に依存
   - 今後: Sandbox環境（Docker）検討（Phase 3）

2. **エラーハンドリング**
   - 現状: execute_code がエラーを返す
   - 今後: 自動修正・リトライ（Phase 3: Self-Improving Agent）

## Phase 3 への展望

Phase 2 完了後、以下を検討:

- **Self-Improving Agent**: エラー時に自動でコード修正
- **Enhanced CodeExecutor**: より多くのライブラリサポート
- **Streaming Execution**: コード実行の進捗をリアルタイム表示

## 参考資料

- Phase 1 実装: `ai_docs/rfcs/RFC_005_PHASE1_PLAN.md`
- CodeExecutor: `src/kagura/core/executor.py`
- execute_code agent: `src/kagura/agents/code_agent.py`

## 改訂履歴

- 2025-10-13: 初版作成
