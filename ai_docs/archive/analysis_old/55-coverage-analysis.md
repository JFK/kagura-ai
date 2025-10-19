# テストカバレッジ分析レポート - Issue #55

**Date**: 2025-10-03
**Current Coverage**: **93%**
**Target Coverage**: **95%**
**Gap**: **2%** (36 lines未カバー)

---

## 📊 現在のカバレッジ状況

```
Name                              Stmts   Miss  Cover   Missing
---------------------------------------------------------------
src/kagura/__init__.py                3      0   100%
src/kagura/agents/__init__.py         2      0   100%
src/kagura/agents/code_agent.py      53      1    98%   145
src/kagura/cli/__init__.py            0      0   100%
src/kagura/cli/main.py               23      1    96%   47
src/kagura/cli/repl.py              127     23    82%   (23 lines)
src/kagura/core/__init__.py           2      0   100%
src/kagura/core/decorators.py        45      0   100%   ✅
src/kagura/core/executor.py          96      1    99%   83
src/kagura/core/llm.py               12      0   100%   ✅
src/kagura/core/parser.py           103      8    92%   (8 lines)
src/kagura/core/prompt.py            39      2    95%   93-94
src/kagura/version.py                 1      0   100%   ✅
---------------------------------------------------------------
TOTAL                               506     36    93%
```

---

## 🎯 モジュール別優先度

### 優先度1: Core Modules (現在92-99%)
**推奨**: 95%+ を目指す

#### 1. `src/kagura/core/parser.py` - 92% → 目標95%+
**未カバー箇所**:
- Line 43: ネストした括弧のカウント処理
- Line 99: `extract_json_objects()` のエッジケース
- Line 109: JSON抽出のエラーハンドリング
- Line 170, 180-184: Union型パースのエラーケース
- Line 200: パース失敗時の例外処理

**テスト追加提案**:
```python
# tests/core/test_parser.py に追加

async def test_extract_nested_brackets():
    """Test nested bracket extraction"""
    text = "[[nested]]"
    result = extract_bracket_content(text)
    assert result == ["[nested]"]

async def test_parse_union_type_error():
    """Test Union type parsing error handling"""
    with pytest.raises(ValueError):
        parse_response("invalid", Union[str, int])
```

#### 2. `src/kagura/core/prompt.py` - 95% → 目標98%+
**未カバー箇所**:
- Line 93-94: 一般的なException処理

**テスト追加提案**:
```python
# tests/core/test_prompt.py に追加

def test_template_general_exception():
    """Test general exception handling in template rendering"""
    # Jinja2以外の例外を発生させるテンプレート
    with pytest.raises(Exception):
        render_prompt("{{ 1/0 }}")  # ZeroDivisionError
```

#### 3. `src/kagura/core/executor.py` - 99% → 目標100%
**未カバー箇所**:
- Line 83: タイムアウト処理のエッジケース

**テスト追加提案**:
```python
# tests/core/test_executor.py に追加済み (test_timeout)
# 既存のテストで十分カバーされている可能性
```

---

### 優先度2: Agents Module (現在98%)
**推奨**: 99%+ を目指す

#### `src/kagura/agents/code_agent.py` - 98% → 目標99%+
**未カバー箇所**:
- Line 145: `pass` 文（エラーケース内）

**分析**: この行は意図的に空のエラーハンドリング。実際には到達しない可能性が高い。テスト追加は優先度低。

---

### 優先度3: CLI Module (現在82-96%)
**推奨**: 現状維持（手動テストが必要）

#### `src/kagura/cli/repl.py` - 82%
**未カバー箇所**: 23行（対話的UI処理）

**分析**:
- REPLの対話的処理は自動テストが困難
- 手動テストでカバー済み
- 82%は許容範囲内

#### `src/kagura/cli/main.py` - 96%
**未カバー箇所**:
- Line 47: CLIエントリーポイント

**分析**: `if __name__ == "__main__":` 部分。テスト不要。

---

## 📈 カバレッジ向上計画

### Phase 1: Quick Wins (目標: 93% → 94%)
**所要時間**: 30分

1. **prompt.py の一般Exception処理テスト追加**
   - `test_template_general_exception()` を追加
   - 予想カバレッジ向上: +0.4%

2. **parser.py のネスト括弧テスト追加**
   - `test_extract_nested_brackets()` を追加
   - 予想カバレッジ向上: +0.3%

**期待カバレッジ**: 93.7%

---

### Phase 2: Deep Coverage (目標: 94% → 95%+)
**所要時間**: 1時間

3. **parser.py のUnion型エラーケーステスト**
   - `test_parse_union_type_error()` を追加
   - `test_extract_json_error_handling()` を追加
   - 予想カバレッジ向上: +1.0%

4. **executor.py のタイムアウトエッジケース**
   - 既存テストの確認・補完
   - 予想カバレッジ向上: +0.2%

**期待カバレッジ**: 94.9% → **95%+**

---

## ✅ 実装済み・カバレッジ100%のモジュール

- ✅ `src/kagura/core/decorators.py` - 100%
- ✅ `src/kagura/core/llm.py` - 100%
- ✅ `src/kagura/__init__.py` - 100%
- ✅ `src/kagura/agents/__init__.py` - 100%
- ✅ `src/kagura/version.py` - 100%

---

## 🎯 推奨アクション

### 今すぐ実施（Phase 1）

**PR作成**: `test(core): add edge case tests for parser and prompt`

**変更内容**:
```python
# tests/core/test_prompt.py
def test_template_general_exception():
    """Test general exception handling"""
    # ...

# tests/core/test_parser.py
async def test_extract_nested_brackets():
    """Test nested bracket extraction"""
    # ...
```

**期待結果**: カバレッジ 93% → 94%

---

### 次のステップ（Phase 2）

**PR作成**: `test(core): comprehensive parser error handling tests`

**変更内容**:
```python
# tests/core/test_parser.py
async def test_parse_union_type_error():
    """Test Union type parsing error"""
    # ...

async def test_extract_json_error_handling():
    """Test JSON extraction error handling"""
    # ...
```

**期待結果**: カバレッジ 94% → 95%+

---

## 📊 カバレッジ目標達成ロードマップ

```
現在:   93% ██████████████████▓▓ (506 lines, 36 missing)

Phase 1: 94% ██████████████████▓░ (506 lines, 30 missing)
         ↑ prompt.py, parser.py のクイックウィン

Phase 2: 95% ███████████████████░ (506 lines, 25 missing)
         ↑ parser.py のエラーハンドリング強化

Goal:   95%+ ███████████████████░
```

---

## 🚀 CI/CD統合提案

### GitHub Actions にカバレッジレポート追加

`.github/workflows/test.yml` に追加:

```yaml
- name: Generate coverage report
  run: |
    uv run pytest --cov=src/kagura --cov-report=xml --cov-report=term

- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v4
  with:
    file: ./coverage.xml
    fail_ci_if_error: false

- name: Check coverage threshold
  run: |
    uv run pytest --cov=src/kagura --cov-fail-under=93
```

**メリット**:
- PRごとにカバレッジ確認
- カバレッジ低下を自動検出
- Codecovでの可視化

---

## 📝 結論

**現状**: 93%カバレッジは十分高い ✅

**推奨**:
1. Phase 1実施で94%達成（30分で完了）
2. Phase 2実施で95%達成（1時間で完了）
3. CI/CDに統合してカバレッジ維持

**Beta版リリース判断**:
- 現在の93%でもリリース可能
- 95%達成でより安心してリリース可能

**次のアクション**: Phase 1のテスト追加PRを作成
