# OpenAI API Pricing (2025-10-16)

## GPT-5 Models

### GPT-5
> The best model for coding and agentic tasks across industries

- **Input:** $1.250 / 1M tokens
- **Cached input:** $0.125 / 1M tokens
- **Output:** $10.000 / 1M tokens

### GPT-5 mini
> A faster, cheaper version of GPT-5 for well-defined tasks

- **Input:** $0.250 / 1M tokens
- **Cached input:** $0.025 / 1M tokens
- **Output:** $2.000 / 1M tokens

### GPT-5 nano ⭐️ **最安値 - 検索・分類に最適**
> The fastest, cheapest version of GPT-5—great for summarization and classification tasks

- **Input:** $0.050 / 1M tokens
- **Cached input:** $0.005 / 1M tokens
- **Output:** $0.400 / 1M tokens

### GPT-5 pro
> The smartest and most precise model

- **Input:** $15.00 / 1M tokens
- **Cached input:** —
- **Output:** $120.00 / 1M tokens

---

## Fine-tuning Models

### GPT-4.1
- **Input:** $3.00 / 1M tokens
- **Cached input:** $0.75 / 1M tokens
- **Output:** $12.00 / 1M tokens
- **Training:** $25.00 / 1M tokens

### GPT-4.1 mini
- **Input:** $0.80 / 1M tokens
- **Cached input:** $0.20 / 1M tokens
- **Output:** $3.20 / 1M tokens
- **Training:** $5.00 / 1M tokens

### GPT-4.1 nano
- **Input:** $0.20 / 1M tokens
- **Cached input:** $0.05 / 1M tokens
- **Output:** $0.80 / 1M tokens
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

### タスク別モデル選択

| タスク | 推奨モデル | 理由 |
|--------|-----------|------|
| **Web検索** | GPT-5 nano | 最安値 ($0.05 input, $0.40 output) |
| **分類・ルーティング** | GPT-5 nano | 高速、安価 |
| **要約** | GPT-5 nano | 十分な性能、低コスト |
| **コード生成** | GPT-5 | バランス良好 |
| **複雑なタスク** | GPT-5 pro | 最高精度 |
| **チャット** | GPT-5 mini | バランス良好 |

### コスト削減戦略

1. **タスク別モデル切り替え**
   ```python
   # 検索: GPT-5 nano
   web_search_agent(model="gpt-5-nano")

   # コード: GPT-5
   code_agent(model="gpt-5")
   ```

2. **Prompt Caching活用**
   - システムプロンプト、ツール定義をキャッシュ
   - GPT-5 nano: $0.005 / 1M (90%削減!)

3. **Batch API**
   - 非緊急タスクで50%削減

---

**更新日**: 2025-10-16
**情報源**: OpenAI Pricing Page
