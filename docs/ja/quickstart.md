# クイックスタート - Kagura AI

Kagura AIを5分で始めましょう。

---

## インストール

```bash
pip install kagura-ai[full]
```

## APIキーのセットアップ

```bash
export OPENAI_API_KEY=sk-...
```

---

## 最初のエージェント（30秒）

```python
from kagura import agent

@agent
async def translator(text: str, lang: str = "ja") -> str:
    '''Translate to {{ lang }}: {{ text }}'''

# 使用方法
result = await translator("Hello World", lang="ja")
print(result)  # "こんにちは世界"
```

---

## 型安全な出力

```python
from kagura import agent
from pydantic import BaseModel

class Person(BaseModel):
    name: str
    age: int
    occupation: str

@agent
async def extract_person(text: str) -> Person:
    '''Extract person info from: {{ text }}'''

person = await extract_person("Alice is 30 and works as an engineer")
print(person.name)  # "Alice" - 完全に型付けされています！
```

---

## 組み込みツールを使用

```python
@agent(tools=["web_search"])
async def researcher(topic: str) -> str:
    '''Research {{ topic }} using web_search(query) tool.'''

result = await researcher("Latest Python frameworks")
# Brave Searchを自動的に使用
```

---

## インタラクティブチャットを試す

```bash
kagura chat
```

次に試してみてください:
```
[You] > Read report.pdf and summarize
[AI] > (PDFを分析し、要約を提供)

[You] > Search for similar reports
[AI] > (ウェブを検索し、コンテンツを発見)
```

すべての機能が自動的に動作します。

---

## 次のステップ

- [SDKガイド](sdk-guide.md) - @agent、@tool、メモリーを学ぶ
- [サンプル](../examples/) - 30以上のコード例
- [チャットガイド](chat-guide.md) - インタラクティブチャット機能
