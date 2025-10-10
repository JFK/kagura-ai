# RFC-022: Agent Testing Framework - エージェントテストフレームワーク

## ステータス
- **状態**: Draft
- **作成日**: 2025-10-10
- **関連Issue**: #110
- **優先度**: High

## 概要

AIエージェントの振る舞いをテストするための専用テストフレームワークを提供します。

### 目標
- エージェントの品質保証
- 回帰テストの自動化
- 振る舞い駆動テスト (BDD)
- LLMレスポンスのアサーション

### 非目標
- 既存のpytestの置き換え
- 単体テストフレームワーク

## モチベーション

### 現在の課題

```python
# 現状：エージェントのテストが困難
@agent
async def translator(text: str, lang: str) -> str:
    '''Translate {{ text }} to {{ lang }}'''
    pass

# どうやってテストする？
async def test_translator():
    result = await translator("Hello", "ja")
    # ❓ 何をassertすれば良い？
    # ❓ LLMの出力は毎回変わる
    # ❓ 部分一致でOK？完全一致？
    assert "こんにちは" in result  # これで十分？
```

**問題**:
1. LLMの非決定性
2. テストの記述が曖昧
3. 品質基準が不明確
4. 回帰検出が困難

### 解決するユースケース

**ケース1: 出力検証**
```python
from kagura.testing import AgentTestCase

class TestTranslator(AgentTestCase):
    agent = translator

    async def test_japanese_translation(self):
        result = await self.agent("Hello", "ja")

        # Flexible assertions
        self.assert_contains_any(result, ["こんにちは", "ハロー", "やあ"])
        self.assert_language(result, "ja")
        self.assert_no_english(result)
```

**ケース2: 振る舞い検証**
```python
class TestCodeReview(AgentTestCase):
    agent = code_review_agent

    async def test_security_issues_detected(self):
        code = "password = '12345'"

        result = await self.agent(code)

        # Semantic assertions
        self.assert_mentions_security_issue(result)
        self.assert_suggests_improvements(result)
        self.assert_severity_level(result, min_level="medium")
```

**ケース3: LLM動作検証**
```python
class TestMyAgent(AgentTestCase):
    agent = my_agent

    async def test_llm_usage(self):
        with self.record_llm_calls():
            result = await self.agent("Simple query")

        # Verify LLM behavior
        self.assert_llm_calls(count=1)
        self.assert_llm_model("gpt-4o-mini")
        self.assert_token_usage(max_tokens=1000)
```

**ケース4: パフォーマンステスト**
```python
class TestPerformance(AgentTestCase):
    agent = my_agent

    @pytest.mark.benchmark
    async def test_response_time(self):
        with self.measure_time():
            result = await self.agent("test")

        self.assert_duration(max_seconds=5.0)
        self.assert_cost(max_cost=0.01)
```

### なぜ今実装すべきか
- エージェントの品質保証が重要
- 回帰テストの必要性
- エンタープライズ利用への準備
- TDDの推進

## 設計

### アーキテクチャ

```
┌──────────────────────────────────────┐
│      AgentTestCase                   │
│  (Base class for agent tests)        │
│                                      │
│  - Assertions                        │
│  - Mocking                           │
│  - Recording                         │
└───────────┬──────────────────────────┘
            │
            ▼
┌──────────────────────────────────────┐
│      Test Execution                  │
│  - Run agent                         │
│  - Record interactions               │
│  - Collect metrics                   │
└───────────┬──────────────────────────┘
            │
            ▼
┌──────────────────────────────────────┐
│      Assertions & Matchers           │
│  - Semantic matchers                 │
│  - Fuzzy comparisons                 │
│  - LLM-based assertions              │
└──────────────────────────────────────┘
```

### API設計

#### AgentTestCase

```python
from kagura.testing import AgentTestCase

class TestMyAgent(AgentTestCase):
    # Agent to test
    agent = my_agent

    # Setup/teardown
    async def setup_method(self):
        """Setup before each test"""
        pass

    async def teardown_method(self):
        """Cleanup after each test"""
        pass

    # Test methods
    async def test_basic_functionality(self):
        result = await self.agent("input")
        self.assert_not_empty(result)

    async def test_with_context(self):
        # Test with specific context
        with self.mock_memory(history=[...]):
            result = await self.agent("input")
```

#### Assertions

```python
# String/content assertions
self.assert_contains(result, "keyword")
self.assert_contains_any(result, ["option1", "option2"])
self.assert_not_contains(result, "forbidden")
self.assert_matches_pattern(result, r"\d{3}-\d{4}")
self.assert_language(result, "ja")

# Semantic assertions
self.assert_sentiment(result, "positive")
self.assert_mentions_topic(result, "AI")
self.assert_provides_explanation(result)

# LLM behavior assertions
self.assert_llm_calls(count=2, model="gpt-4o-mini")
self.assert_token_usage(max_tokens=1000)
self.assert_tool_calls(["search_tool"])

# Performance assertions
self.assert_duration(max_seconds=5.0)
self.assert_cost(max_cost=0.01)

# Structured output assertions (Pydantic)
self.assert_valid_model(result, MyModel)
self.assert_field_value(result, "status", "success")
```

#### Mocking

```python
# Mock LLM responses
with self.mock_llm(response="Mocked response"):
    result = await self.agent("input")

# Mock tools
with self.mock_tool("search_tool", return_value=[...]):
    result = await self.agent("search for something")

# Mock memory
with self.mock_memory(history=[
    {"role": "user", "content": "Previous message"}
]):
    result = await self.agent("Follow-up")
```

#### Recording & Replay

```python
# Record interactions for replay
with self.record_mode():
    result = await self.agent("input")
# Saves to tests/fixtures/my_agent_001.json

# Replay recorded interactions
with self.replay_mode("my_agent_001.json"):
    result = await self.agent("input")
    # Uses recorded LLM responses instead of real API
```

### コンポーネント設計

#### 1. AgentTestCase Base Class

```python
# src/kagura/testing/testcase.py
from typing import Optional, Any, Callable
import pytest
import time

class AgentTestCase:
    """Base class for agent tests"""

    agent: Optional[Callable] = None  # Agent to test

    def __init__(self):
        self._llm_calls = []
        self._tool_calls = []
        self._start_time = None

    # ===== Execution =====

    async def run_agent(self, *args, **kwargs) -> Any:
        """Run the agent under test"""
        if not self.agent:
            raise ValueError("No agent specified")

        self._start_time = time.time()

        try:
            result = await self.agent(*args, **kwargs)
        finally:
            self._duration = time.time() - self._start_time

        return result

    # ===== Content Assertions =====

    def assert_contains(self, text: str, substring: str):
        """Assert text contains substring"""
        assert substring in text, f"Expected '{substring}' in text"

    def assert_contains_any(self, text: str, options: list[str]):
        """Assert text contains at least one option"""
        assert any(opt in text for opt in options), \
            f"Expected one of {options} in text"

    def assert_not_contains(self, text: str, substring: str):
        """Assert text does not contain substring"""
        assert substring not in text, f"Did not expect '{substring}' in text"

    def assert_matches_pattern(self, text: str, pattern: str):
        """Assert text matches regex pattern"""
        import re
        assert re.search(pattern, text), f"Text does not match pattern: {pattern}"

    def assert_language(self, text: str, expected_lang: str):
        """Assert text is in expected language"""
        # Use langdetect or similar
        from langdetect import detect
        detected = detect(text)
        assert detected == expected_lang, \
            f"Expected language '{expected_lang}', got '{detected}'"

    def assert_not_empty(self, text: str):
        """Assert text is not empty"""
        assert text and text.strip(), "Expected non-empty text"

    # ===== Semantic Assertions =====

    def assert_sentiment(self, text: str, expected: str):
        """Assert text sentiment (positive/negative/neutral)"""
        # Use sentiment analysis library
        pass

    def assert_mentions_topic(self, text: str, topic: str):
        """Assert text mentions specific topic"""
        # Use NLP or LLM to check
        pass

    # ===== LLM Behavior Assertions =====

    def assert_llm_calls(
        self,
        count: Optional[int] = None,
        model: Optional[str] = None
    ):
        """Assert number of LLM calls"""
        if count is not None:
            actual = len(self._llm_calls)
            assert actual == count, f"Expected {count} LLM calls, got {actual}"

        if model is not None:
            models = [call["model"] for call in self._llm_calls]
            assert all(m == model for m in models), \
                f"Expected model '{model}', got {set(models)}"

    def assert_token_usage(
        self,
        max_tokens: Optional[int] = None,
        min_tokens: Optional[int] = None
    ):
        """Assert token usage"""
        total_tokens = sum(
            call.get("prompt_tokens", 0) + call.get("completion_tokens", 0)
            for call in self._llm_calls
        )

        if max_tokens:
            assert total_tokens <= max_tokens, \
                f"Token usage {total_tokens} exceeds max {max_tokens}"

        if min_tokens:
            assert total_tokens >= min_tokens, \
                f"Token usage {total_tokens} below min {min_tokens}"

    def assert_tool_calls(self, expected_tools: list[str]):
        """Assert specific tools were called"""
        called_tools = [call["name"] for call in self._tool_calls]
        for tool in expected_tools:
            assert tool in called_tools, f"Expected tool '{tool}' to be called"

    # ===== Performance Assertions =====

    def assert_duration(self, max_seconds: float):
        """Assert execution duration"""
        assert self._duration <= max_seconds, \
            f"Execution took {self._duration:.2f}s, max {max_seconds}s"

    def assert_cost(self, max_cost: float):
        """Assert execution cost"""
        total_cost = sum(call.get("cost", 0) for call in self._llm_calls)
        assert total_cost <= max_cost, \
            f"Cost ${total_cost:.4f} exceeds max ${max_cost:.4f}"

    # ===== Structured Output Assertions =====

    def assert_valid_model(self, result: Any, model_class: type):
        """Assert result is valid Pydantic model"""
        assert isinstance(result, model_class), \
            f"Expected {model_class.__name__}, got {type(result).__name__}"

    def assert_field_value(self, result: Any, field: str, expected: Any):
        """Assert model field has expected value"""
        actual = getattr(result, field)
        assert actual == expected, \
            f"Expected {field}={expected}, got {actual}"

    # ===== Context Managers =====

    def record_llm_calls(self):
        """Context manager to record LLM calls"""
        from kagura.testing.mocking import LLMRecorder
        return LLMRecorder(self._llm_calls)

    def mock_llm(self, response: str):
        """Context manager to mock LLM responses"""
        from kagura.testing.mocking import LLMMock
        return LLMMock(response)

    def mock_tool(self, tool_name: str, return_value: Any):
        """Context manager to mock tool calls"""
        from kagura.testing.mocking import ToolMock
        return ToolMock(tool_name, return_value)

    def mock_memory(self, history: list[dict]):
        """Context manager to mock memory"""
        from kagura.testing.mocking import MemoryMock
        return MemoryMock(history)

    def measure_time(self):
        """Context manager to measure execution time"""
        from kagura.testing.utils import Timer
        return Timer()
```

#### 2. Mocking Utilities

```python
# src/kagura/testing/mocking.py
from contextlib import contextmanager
from typing import Any
from unittest.mock import patch

@contextmanager
def mock_llm_response(response: str):
    """Mock LLM API calls"""
    def mock_completion(*args, **kwargs):
        return {
            "choices": [{"message": {"content": response}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 10}
        }

    with patch("litellm.completion", side_effect=mock_completion):
        yield

class LLMRecorder:
    """Record LLM calls"""
    def __init__(self, storage: list):
        self.storage = storage
        self.original_completion = None

    def __enter__(self):
        import litellm
        self.original_completion = litellm.completion

        def recording_completion(*args, **kwargs):
            result = self.original_completion(*args, **kwargs)
            self.storage.append({
                "model": kwargs.get("model"),
                "prompt_tokens": result["usage"]["prompt_tokens"],
                "completion_tokens": result["usage"]["completion_tokens"],
            })
            return result

        litellm.completion = recording_completion
        return self

    def __exit__(self, *args):
        import litellm
        litellm.completion = self.original_completion
```

#### 3. pytest Plugin

```python
# src/kagura/testing/plugin.py
import pytest

def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line(
        "markers",
        "agent: mark test as agent test"
    )
    config.addinivalue_line(
        "markers",
        "benchmark: mark test as performance benchmark"
    )

@pytest.fixture
def agent_context():
    """Fixture for agent testing context"""
    from kagura.testing import AgentTestCase
    return AgentTestCase()
```

### 統合例

#### 例1: 基本的なテスト

```python
from kagura.testing import AgentTestCase
from my_agents import translator

class TestTranslator(AgentTestCase):
    agent = translator

    async def test_english_to_japanese(self):
        result = await self.agent("Hello", "ja")

        self.assert_contains_any(result, ["こんにちは", "ハロー"])
        self.assert_language(result, "ja")
        self.assert_not_contains(result, "Hello")

    async def test_preserves_names(self):
        result = await self.agent("My name is Alice", "ja")

        self.assert_contains(result, "Alice")  # Name preserved
```

#### 例2: LLM動作検証

```python
class TestCodeReview(AgentTestCase):
    agent = code_review_agent

    async def test_uses_appropriate_model(self):
        code = "def hello(): print('hi')"

        with self.record_llm_calls():
            result = await self.agent(code)

        # Should use small model for simple code
        self.assert_llm_calls(count=1, model="gpt-4o-mini")
        self.assert_token_usage(max_tokens=500)

    async def test_complex_code_uses_better_model(self):
        code = """
        # Complex code with potential issues
        [1000 lines of code]
        """

        with self.record_llm_calls():
            result = await self.agent(code)

        # Should use better model for complex code
        self.assert_llm_calls(model="gpt-4o")
```

#### 例3: モックとスタブ

```python
class TestResearchAgent(AgentTestCase):
    agent = research_agent

    async def test_with_mock_search(self):
        # Mock external search tool
        mock_results = [
            {"title": "AI News", "url": "..."},
            {"title": "ML Update", "url": "..."},
        ]

        with self.mock_tool("search_tool", return_value=mock_results):
            result = await self.agent("research AI trends")

        # Agent should process mock results
        self.assert_contains(result, "AI News")
        self.assert_contains(result, "ML Update")
```

#### 例4: スナップショットテスト

```python
class TestFormatter(AgentTestCase):
    agent = formatter_agent

    async def test_output_format(self):
        input_data = {"name": "Alice", "age": 30}

        result = await self.agent(input_data)

        # Compare with saved snapshot
        self.assert_matches_snapshot(result, "formatter_output_001")
```

## 実装計画

### Phase 1: Core Framework (v2.2.0) - 1週間
- [ ] AgentTestCase基本実装
- [ ] 基本的なアサーション
- [ ] LLM recording
- [ ] pytest統合

### Phase 2: Advanced Features (v2.2.0) - 1週間
- [ ] モック機能
- [ ] セマンティックアサーション
- [ ] スナップショットテスト
- [ ] ベンチマーク機能

### Phase 3: Enhanced Testing (v2.3.0)
- [ ] カバレッジレポート
- [ ] ビジュアルレポート
- [ ] CI/CD統合ガイド

## 技術的詳細

### 依存関係

```toml
[project.optional-dependencies]
testing = [
    "pytest>=8.3",         # Already dev dependency
    "pytest-asyncio>=0.25",
    "langdetect>=1.0.9",   # Language detection
]
```

### pytest統合

```toml
# pyproject.toml
[tool.pytest.ini_options]
markers = [
    "agent: Agent tests",
    "benchmark: Performance benchmarks",
]
```

## テスト戦略

```python
# Test the testing framework itself!
def test_assert_contains():
    testcase = AgentTestCase()
    testcase.assert_contains("hello world", "hello")

    with pytest.raises(AssertionError):
        testcase.assert_contains("hello world", "goodbye")
```

## ドキュメント

- Agent Testing クイックスタート
- Assertion Reference
- Mocking Guide
- Best Practices

## 参考資料

- [pytest Documentation](https://docs.pytest.org/)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)

## 改訂履歴

- 2025-10-10: 初版作成
