# OpenAI API Pricing (Updated 2025-10-17)

## 📊 Price Comparison: Main Models

| Model | Input | Cached Input | Output | Use Case |
|-------|-------|--------------|--------|----------|
| **gpt-5** ⭐️ | $1.25 | $0.125 | $10.00 | **Best for coding/agents** |
| gpt-5-mini | $0.25 | $0.025 | $2.00 | Well-defined tasks |
| gpt-5-nano | $0.05 | $0.005 | $0.40 | Search/classification |
| gpt-4o | $2.50 | $1.25 | $10.00 | Legacy (2x more expensive) |
| gpt-4o-mini | $0.15 | $0.075 | $0.60 | Legacy (cheaper input) |

**Key Insight**: 🔥 **gpt-5 is 50% cheaper than gpt-4o** for input ($1.25 vs $2.50)!

---

## GPT-5 Series (Latest, Recommended)

### GPT-5 ⭐️ **推奨デフォルト**
> The best model for coding and agentic tasks across industries

- **Input:** $1.25 / 1M tokens
- **Cached input:** $0.125 / 1M tokens (90% discount)
- **Output:** $10.00 / 1M tokens
- **Best for**: Coding, agents, complex reasoning

**Why choose gpt-5**:
- ✅ Better quality than gpt-4o
- ✅ 50% cheaper input than gpt-4o ($1.25 vs $2.50)
- ✅ Same output cost as gpt-4o ($10.00)
- ✅ Better prompt caching ($0.125 vs $1.25)

### GPT-5 mini
> A faster, cheaper version of GPT-5 for well-defined tasks

- **Input:** $0.25 / 1M tokens
- **Cached input:** $0.025 / 1M tokens
- **Output:** $2.00 / 1M tokens
- **Best for**: Simple tasks, high-volume requests

### GPT-5 nano ⭐️ **最安値**
> The fastest, cheapest version of GPT-5—great for summarization and classification tasks

- **Input:** $0.05 / 1M tokens (67% cheaper than gpt-4o-mini)
- **Cached input:** $0.005 / 1M tokens (93% cheaper)
- **Output:** $0.40 / 1M tokens (33% cheaper)
- **Best for**: Search, routing, classification, summarization

### GPT-5 pro
> The smartest and most precise model

- **Input:** $15.00 / 1M tokens
- **Output:** $120.00 / 1M tokens
- **Best for**: Critical tasks requiring maximum precision

---

## GPT-4 Series (Legacy)

### GPT-4o
- **Input:** $2.50 / 1M tokens (2x more expensive than gpt-5!)
- **Cached input:** $1.25 / 1M tokens
- **Output:** $10.00 / 1M tokens

### GPT-4o-mini
- **Input:** $0.15 / 1M tokens (3x more expensive than gpt-5-nano!)
- **Cached input:** $0.075 / 1M tokens
- **Output:** $0.60 / 1M tokens (1.5x more expensive than gpt-5-nano!)

**Note**: gpt-4o series is legacy. Prefer gpt-5 series for better value.

---

## Fine-tuning Models

### GPT-4.1
- **Input:** $2.00 / 1M tokens
- **Cached input:** $0.50 / 1M tokens
- **Output:** $8.00 / 1M tokens
- **Training:** $25.00 / 1M tokens

### GPT-4.1 mini
- **Input:** $0.40 / 1M tokens
- **Cached input:** $0.10 / 1M tokens
- **Output:** $1.60 / 1M tokens
- **Training:** $5.00 / 1M tokens

### GPT-4.1 nano
- **Input:** $0.10 / 1M tokens
- **Cached input:** $0.025 / 1M tokens
- **Output:** $0.40 / 1M tokens
- **Training:** $1.50 / 1M tokens

### o4-mini (Reinforcement fine-tuning)
- **Input:** $4.00 / 1M tokens
- **Cached input:** $1.00 / 1M tokens
- **Output:** $16.00 / 1M tokens
- **Training:** $100.00 / training hour

---

## Realtime API

### Text
| Model | Input | Cached Input | Output |
|--------|--------|--------------|---------|
| gpt-realtime | $4.00 / 1M | $0.40 / 1M | $16.00 / 1M |
| gpt-realtime-mini | $0.60 / 1M | $0.06 / 1M | $2.40 / 1M |

### Audio
| Model | Input | Cached Input | Output |
|--------|--------|--------------|---------|
| gpt-realtime | $32.00 / 1M | $0.40 / 1M | $64.00 / 1M |
| gpt-realtime-mini | $10.00 / 1M | $0.30 / 1M | $20.00 / 1M |

### Image
| Model | Input | Cached Input |
|--------|--------|--------------|
| gpt-realtime | $5.00 / 1M | $0.50 / 1M |
| gpt-realtime-mini | $0.80 / 1M | $0.08 / 1M |

---

## Sora Video API

| Model | Size | Price / second |
|--------|------|----------------|
| sora-2 | 720×1280 / 1280×720 | $0.10 |
| sora-2-pro | 720×1280 / 1280×720 | $0.30 |
| sora-2-pro | 1024×1792 / 1792×1024 | $0.50 |

---

## Image Generation API

### Text
| Model | Input | Cached Input |
|--------|--------|--------------|
| GPT-image-1 | $5.00 / 1M | $1.25 / 1M |
| GPT-image-1-mini | $2.00 / 1M | $0.20 / 1M |

### Image
| Model | Input | Cached Input | Output |
|--------|--------|--------------|---------|
| GPT-image-1 | $10.00 / 1M | $2.50 / 1M | $40.00 / 1M |
| GPT-image-1-mini | $2.50 / 1M | $0.25 / 1M | $8.00 / 1M |

Image outputs:
- Low: $0.01
- Medium: $0.04
- High: $0.17

---

## Built-in Tools

| Tool | Cost |
|------|------|
| Code Interpreter | $0.03 / session |
| File Search Storage | $0.10 / GB per day (first GB free) |
| File Search Tool Call | $2.50 / 1k tool calls |
| Web Search (all models) | $10.00 / 1K calls + model tokens |
| Web Search preview (reasoning) | $10.00 / 1K calls + model tokens |
| Web Search preview (non-reasoning) | $25.00 / 1K calls + free search tokens |

---

## 💡 Optimization Options

### Batch API
- **Save 50%** on inputs and outputs
- Asynchronous processing (within 24 hours)

### Priority Processing
- Reliable, high-speed performance
- Pay-as-you-go

---

## 🎯 Kagura AI での推奨使用パターン

### 推奨デフォルトモデル: **gpt-5**

**理由**:
- ✅ **50% cheaper** than gpt-4o for input ($1.25 vs $2.50)
- ✅ **Same output cost** as gpt-4o ($10.00)
- ✅ **Better quality** - Latest generation
- ✅ **Better caching** - 90% discount ($0.125 vs $1.25)
- ✅ **Best for agents** - Optimized for tool use

### タスク別モデル選択

| タスク | 推奨モデル | コスト（例: 100k in, 50k out） | 理由 |
|--------|-----------|-------------------------------|------|
| **デフォルト（チャット）** | **gpt-5** | $0.625 | バランス最良 |
| **Web検索・ルーティング** | gpt-5-nano | $0.025 | 最安値、高速 |
| **要約・分類** | gpt-5-nano | $0.025 | 十分な性能 |
| **コード生成** | gpt-5 | $0.625 | 高品質 |
| **複雑な推論** | gpt-5-pro | $7.50 | 最高精度 |
| **シンプルなタスク** | gpt-5-mini | $0.125 | コスパ良 |

### コスト比較（100k input, 50k output）

| Model | Input Cost | Output Cost | Total | vs gpt-5 |
|-------|-----------|-------------|-------|----------|
| **gpt-5** | $0.125 | $0.500 | **$0.625** | baseline |
| gpt-5-mini | $0.025 | $0.100 | $0.125 | -80% ✅ |
| gpt-5-nano | $0.005 | $0.020 | $0.025 | -96% ✅✅ |
| gpt-4o | $0.250 | $0.500 | $0.750 | +20% ❌ |
| gpt-4o-mini | $0.015 | $0.030 | $0.045 | -93% ✅ |

**結論**:
- 🏆 **gpt-5**: デフォルトに最適（品質・コストバランス）
- 🥈 **gpt-5-nano**: ルーティング・検索に最適（最安値）
- 🥉 **gpt-5-mini**: シンプルなタスクに（コスパ良）

### コスト削減戦略

1. **タスク別モデル切り替え**
   ```python
   # ルーティング: GPT-5 nano（最安値）
   router = AgentRouter(model="gpt-5-nano")

   # メインエージェント: GPT-5（バランス良）
   @agent(model="gpt-5")
   async def my_agent(query: str) -> str:
       ...

   # 重要タスク: GPT-5 pro
   @agent(model="gpt-5-pro")
   async def critical_agent(query: str) -> str:
       ...
   ```

2. **Prompt Caching活用**
   - システムプロンプト、ツール定義をキャッシュ
   - gpt-5: $0.125 / 1M (90%削減!)
   - gpt-5-nano: $0.005 / 1M (90%削減!)

3. **Batch API**
   - 非緊急タスクで50%削減

---

**更新日**: 2025-10-17
**情報源**: OpenAI Pricing Page
