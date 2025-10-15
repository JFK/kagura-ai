# RFC-034: Hippocampus Memory System - Personal AI with Local SLM

**ステータス**: Draft
**作成日**: 2025-10-15
**優先度**: ⭐️⭐️ High
**対象バージョン**: v2.6.0
**関連Issue**: TBD
**置き換え対象**: RFC-003 (Personal Assistant with Auto Fine-tuning)

---

## 📋 Executive Summary

**「使えば使うほど賢くなる」パーソナルAIを、ローカルSLM（Small Language Model）を活用して実現します。**

人間の脳の「海馬」のように、短期記憶をエピソード記憶に変換し、さらにセマンティック記憶（知識）へと統合する、段階的な記憶システムを構築します。

### 核心的な目的

**最終目標**: この記憶システム自体が「コンテキスト」となり、Main LLMがより良い回答を生成できるようにする。

```
ユーザーの質問
    ↓
Hippocampus Memory が「関連する過去の知識」を提供
    ↓
Main LLM が「豊富なコンテキスト」を元に回答生成
    ↓
より良い回答（ユーザー固有の文脈を理解）
```

---

## 🎯 問題定義

### 現状の課題

1. **RAGの限界**
   - ベクトル検索は「近い」情報を見つけるが、「意味的な繋がり」を理解しない
   - 時系列的な因果関係が失われる
   - 重要度の判定ができない

2. **Context Window の限界**
   - 10,000メッセージを要約しても、結局はテキスト化された情報
   - RFC-024（Context Compression）で対処中だが、本質的な解決ではない
   - 「記憶」ではなく「ログの圧縮」

3. **Fine-tuning の課題**（RFC-003の問題）
   - 高コスト（$5-20/回）
   - プライバシー懸念（外部送信）
   - 100件のデータで効果があるか不明

### 人間の脳との比較

| 人間の脳 | 現状のLLM | 理想のKagura AI |
|---------|----------|----------------|
| **短期記憶（海馬）** | Context Window | WorkingMemory + ContextMemory |
| **エピソード記憶** | なし（RAGで模倣） | Episodic Consolidation（SLMで抽出） |
| **セマンティック記憶** | 事前学習済み知識 | Semantic Integration（統合プロファイル） |
| **固着（新皮質）** | Fine-tuning（高コスト） | (Optional) LoRA（ローカル） |
| **忘却** | なし | TTL、重要度ベース削除 |

---

## 💡 解決策：海馬型記憶システム

### コンセプト

```
人間の脳              Kagura AI
───────────         ─────────────────────────────
短期記憶 (STM)   →  WorkingMemory + ContextMemory
  ↓ 海馬的処理          ↓ Personal Memory Agent (Local SLM)
エピソード記憶   →  MemoryRAG (episodic layer)
  ↓ 睡眠中の統合        ↓ Nightly consolidation (Local SLM)
セマンティック記憶 → PersistentMemory (semantic profile)
  ↓ 固着                ↓ (Optional) LoRA fine-tuning
長期記憶（新皮質）→  Fine-tuned model
```

### キーアイデア

1. **ローカルSLMを「海馬」として使用**
   - Qwen2.5 0.5B-3B、Phi-3 Mini、Gemma-2 2Bなど
   - 役割: 事実抽出、重要度判定、要約・統合
   - VRAM: 0.4GB-2GB（RTX 3060でも動作）

2. **段階的な記憶統合**
   - Phase 1: Episodic Consolidation（会話終了時）
   - Phase 2: Semantic Integration（夜間バッチ）
   - Phase 3: Knowledge Graph（オプション）
   - Phase 4: LoRA Learning（オプション）

3. **プライバシー第一**
   - 完全ローカル（外部送信なし）
   - コスト: $0（SLM実行コストのみ）

---

## 🏗️ アーキテクチャ

### 全体像

```
┌─────────────────────────────────────────────────┐
│              User Query: "画面の設定は？"        │
└────────────────────┬────────────────────────────┘
                     │
         ┌───────────▼──────────┐
         │  Hippocampus Memory  │ ← ローカルSLM（海馬）
         │  が関連記憶を検索     │
         └───────────┬──────────┘
                     │
         「ユーザーはダークモードを好む」← 過去の記憶
         「最終更新: 2025-10-10」
                     │
         ┌───────────▼──────────┐
         │  Main LLM (GPT-4o)   │
         │  + 豊富なコンテキスト │
         └───────────┬──────────┘
                     │
         ┌───────────▼──────────┐
         │ "ダークモードに設定   │ ← より良い回答
         │  しましょうか？"       │
         └────────────────────────┘
```

### 詳細アーキテクチャ

```
┌────────────────────────────────────────────────────────┐
│                    User Interaction                     │
└───────────────────────┬────────────────────────────────┘
                        │
            ┌───────────▼───────────┐
            │   Main LLM Agent      │ (GPT-4o/Claude/Gemini)
            │   @agent(...)         │
            └───┬───────────────┬───┘
                │               │
    ┌───────────▼───┐       ┌───▼──────────┐
    │ Hippocampus   │       │ MemoryManager │
    │ Memory Agent  │◄──────┤ (既存)        │
    │ (Local SLM)   │       └───────────────┘
    │               │
    │ Ultra-Light:  │       ┌───────────────┐
    │ 0.5B (0.4GB)  │       │ 4層メモリ     │
    │ Light: 2B     │       ├───────────────┤
    │ Standard: 3B  │       │ Working       │
    └───┬───────────┘       │ Context       │
        │                   │ Episodic (RAG)│
        │                   │ Semantic (DB) │
        │                   └───────────────┘
        │
    ┌───▼────────────────────────────────┐
    │  Consolidation Layer (NEW)         │
    │  ──────────────────────────────    │
    │  ├─ Episodic Consolidation         │
    │  │   - 会話終了時に事実抽出        │
    │  │   - 重要度判定（ゲート）        │
    │  │   - RAG保存（episodic layer）   │
    │  │                                 │
    │  ├─ Semantic Integration           │
    │  │   - 夜間バッチで統合            │
    │  │   - 重複削除・矛盾解消          │
    │  │   - プロファイル生成（DB保存）  │
    │  │                                 │
    │  ├─ Knowledge Graph (Optional)     │
    │  │   - エンティティ抽出            │
    │  │   - 関係性グラフ構築            │
    │  │                                 │
    │  └─ LoRA Learning (Optional)       │
    │      - 週1回の微調整               │
    │      - PEFT統合                    │
    └────────────────────────────────────┘
```

### ハードウェア要件（Ultra-Light Mode）

**最小環境**: RTX 3060 (8GB) でも余裕で動作 ✅

| Component | VRAM | RAM | 備考 |
|-----------|------|-----|------|
| **Main LLM** | 0GB | - | クラウドAPI |
| **Hippocampus SLM** | **0.4GB** | 2GB | Qwen2.5-0.5B (INT4) |
| **ChromaDB** | 0GB | 1GB | ベクトルDB |
| **合計** | **< 0.5GB** | **3GB** | 一般的なPCで動作 |

---

## 📦 Phase 1: Episodic Consolidation（2週間）⭐️ 最優先

### 目標

**会話終了時に自動的に重要事実を抽出し、RAGに保存する**

### 実装

#### 1.1 HippocampusConfig

```python
# src/kagura/memory/hippocampus/config.py

from enum import Enum
from dataclasses import dataclass

class HippocampusMode(Enum):
    """動作モード"""
    ULTRA_LIGHT = "ultra_light"  # 0.5B モデル, 最小VRAM (< 0.5GB)
    LIGHT = "light"              # 2B モデル, バランス (< 1.5GB)
    STANDARD = "standard"        # 3B モデル, 高精度 (< 2.5GB)
    CLOUD = "cloud"              # クラウドAPI（Gemini Flash 8B）

@dataclass
class HippocampusConfig:
    """海馬メモリ設定"""

    mode: HippocampusMode = HippocampusMode.ULTRA_LIGHT

    # モデル選択（モード別デフォルト）
    model_map: dict = None

    # 量子化
    quantization: str = "int4"  # "int4" | "int8" | "fp16"

    # リソース制限
    max_vram_mb: int = 500  # 0.5GB まで（Ultra-Light）

    # 重要度閾値
    importance_threshold: int = 6  # 0-10スケール

    def __post_init__(self):
        if self.model_map is None:
            self.model_map = {
                HippocampusMode.ULTRA_LIGHT: "qwen2.5:0.5b-instruct-q4_K_M",
                HippocampusMode.LIGHT: "gemma-2:2b-instruct-q4_K_M",
                HippocampusMode.STANDARD: "qwen2.5:3b-instruct-q4_K_M",
                HippocampusMode.CLOUD: "gemini-1.5-flash-8b",
            }

    def get_model(self) -> str:
        """現在のモードに対応するモデルを取得"""
        return self.model_map[self.mode]
```

#### 1.2 EpisodicConsolidator

```python
# src/kagura/memory/hippocampus/episodic.py

from kagura import agent
from kagura.core.memory import MemoryManager
from kagura.memory.hippocampus.config import HippocampusConfig, HippocampusMode
from datetime import datetime
from typing import Any
import asyncio

class EpisodicConsolidator:
    """
    海馬のエピソード記憶統合
    - 会話終了時に「重要事実」を抽出
    - メタデータ付きでRAGに保存
    """

    def __init__(self, config: HippocampusConfig = None):
        self.config = config or HippocampusConfig(
            mode=HippocampusMode.ULTRA_LIGHT
        )
        self.model = self.config.get_model()

    @agent(
        model="ollama/{model}",  # 動的モデル選択
        temperature=0.0,  # 決定的出力
        max_tokens=200    # 短い出力
    )
    async def extract_facts(self, conversation: str) -> str:
        """
        会話から重要事実を箇条書きで抽出（最小タスク）

        Conversation:
        {{ conversation }}

        Task: Extract important facts (user preferences, settings, decisions, names, dates).
        Format: One fact per line, starting with "-".

        Example:
        - User prefers dark mode
        - User's name is John
        - Meeting scheduled for 2025-10-20

        Output (max 5 facts):
        """
        pass

    @agent(
        model="ollama/{model}",
        temperature=0.0,
        max_tokens=10
    )
    async def classify_importance(self, fact: str) -> str:
        """
        重要度を0-10で判定（単純分類）

        Fact: {{ fact }}

        Rate importance (0-10):
        - 0-3: Not important (chitchat, temporary info)
        - 4-6: Somewhat important
        - 7-10: Very important (user info, preferences, decisions)

        Output only a number (0-10):
        """
        pass

    async def consolidate_episode(
        self,
        memory: MemoryManager,
        session_id: str,
        importance_threshold: int = None
    ) -> dict[str, Any]:
        """
        エピソード統合（超軽量版）

        Args:
            memory: MemoryManager instance
            session_id: Session identifier
            importance_threshold: Importance threshold (0-10)

        Returns:
            Consolidation statistics
        """
        if importance_threshold is None:
            importance_threshold = self.config.importance_threshold

        # 1. 会話取得
        context = memory.get_context()
        conversation_text = "\n".join([
            f"{msg.role}: {msg.content}" for msg in context
        ])

        # 2. SLMで事実抽出（1回のLLM呼び出し）
        facts_text = await self.extract_facts(conversation_text)
        facts = [f.strip("- ").strip() for f in facts_text.split("\n") if f.strip()]

        # 3. 重要度判定（並列処理）
        importance_scores = await asyncio.gather(*[
            self.classify_importance(fact) for fact in facts
        ])

        # 4. フィルタリング + RAG保存
        saved_facts = []
        for fact, score_text in zip(facts, importance_scores):
            try:
                score = int(score_text.strip())
                if score >= importance_threshold:
                    memory.store_semantic(
                        content=fact,
                        metadata={
                            "importance": score,
                            "session_id": session_id,
                            "layer": "episodic",
                            "timestamp": datetime.now().isoformat()
                        }
                    )
                    saved_facts.append({"fact": fact, "score": score})
            except ValueError:
                continue  # スコア解析失敗はスキップ

        return {
            "total_facts": len(facts),
            "saved_facts": len(saved_facts),
            "model": self.model,
            "vram_estimate": "< 0.5 GB",
            "session_id": session_id
        }
```

#### 1.3 @agent デコレータ統合

```python
# src/kagura/core/decorators.py（既存ファイルを拡張）

from kagura.memory.hippocampus import HippocampusConfig, EpisodicConsolidator

def agent(
    model: str = "gpt-4o-mini",
    # ... 既存パラメータ ...
    enable_hippocampus: bool = False,  # ← NEW
    hippocampus_config: HippocampusConfig = None,  # ← NEW
):
    """
    Agent decorator with hippocampus memory

    Args:
        enable_hippocampus: Enable hippocampus memory system
        hippocampus_config: Hippocampus configuration
    """
    def decorator(func):
        # ... 既存コード ...

        if enable_hippocampus and enable_memory:
            # Hippocampus初期化
            config = hippocampus_config or HippocampusConfig()
            consolidator = EpisodicConsolidator(config)

            # 会話終了時にconsolidate
            async def cleanup():
                session_id = agent_instance.memory.get_session_id()
                if session_id:
                    await consolidator.consolidate_episode(
                        memory=agent_instance.memory,
                        session_id=session_id
                    )

            # Register cleanup hook
            agent_instance._cleanup_hooks.append(cleanup)

        return wrapper
    return decorator
```

### 使用例

```python
from kagura import agent
from kagura.memory.hippocampus import HippocampusConfig, HippocampusMode

# 最小構成（RTX 3060 8GB でも動作）
@agent(
    model="gpt-4o-mini",  # クラウド API
    enable_memory=True,
    enable_hippocampus=True,  # ← 海馬機能ON
    hippocampus_config=HippocampusConfig(
        mode=HippocampusMode.ULTRA_LIGHT  # 0.5B, VRAM < 0.5GB
    )
)
async def my_assistant(query: str) -> str:
    """
    あなたの秘書です。

    ユーザーの質問: {{ query }}
    """
    pass

# 使用例
await my_assistant("私はダークモードが好きです")
# → 終了時に自動的に「ユーザーはダークモードを好む」を記憶

# 次回
await my_assistant("画面の設定を教えて")
# → RAGから「ダークモード好き」を検索 → Main LLMに渡す
# → "ダークモードに設定しましょうか？" ← より良い回答
```

### 成功指標（Phase 1）

- ✅ 会話終了時に自動要約（SLMで事実抽出）
- ✅ 重要事実をRAG保存（importance >= 6）
- ✅ VRAM使用量 < 0.5GB（Ultra-Light）
- ✅ レイテンシ < 50ms（事実抽出）
- ✅ RTX 3060 (8GB) で動作確認

---

## 📦 Phase 2: Semantic Integration（2週間）

### 目標

**夜間バッチでエピソード記憶を統合し、「恒久プロファイル」を生成**

### 実装

#### 2.1 SemanticIntegrator

```python
# src/kagura/memory/hippocampus/semantic.py

from kagura import agent
from kagura.core.memory import MemoryManager
from datetime import datetime
from typing import Any

class SemanticIntegrator:
    """
    海馬のセマンティック記憶統合
    - 夜間バッチでエピソードを統合
    - ユーザープロファイル生成
    """

    @agent(
        model="gemini-1.5-flash-8b",  # 超安価（$0.0375 / 1M tokens）
        temperature=0.2
    )
    async def integrate_profile(self, episodes: list[str]) -> dict:
        """
        エピソードを統合してプロファイル生成

        Recent episodes (last 7 days):
        {% for ep in episodes %}
        - {{ ep }}
        {% endfor %}

        Generate a unified user profile JSON:
        {
          "preferences": {
            "ui_theme": "dark",
            "programming_language": "Python"
          },
          "personal_info": {
            "name": "...",
            "role": "..."
          },
          "recurring_topics": [
            "Project X",
            "Team meeting"
          ],
          "decisions": [
            "2025-10-10: Decided to use PostgreSQL"
          ],
          "updated_at": "2025-10-15T00:00:00"
        }

        Rules:
        - Remove duplicates
        - Resolve contradictions (prefer newer info)
        - Merge related items
        """
        pass

    async def nightly_consolidation(
        self,
        memory: MemoryManager,
        use_cloud: bool = True  # デフォルトはクラウド
    ) -> dict[str, Any]:
        """
        夜間統合（バッチ処理、VRAM使用ゼロ）

        Args:
            memory: MemoryManager instance
            use_cloud: Use cloud API (Gemini Flash 8B)

        Returns:
            Consolidated profile
        """
        # エピソード取得
        episodes = memory.recall_semantic(query="", top_k=100)
        episode_texts = [
            ep["content"] for ep in episodes
            if ep.get("metadata", {}).get("layer") == "episodic"
        ]

        if not episode_texts:
            return {"message": "No episodes to consolidate"}

        # 統合（クラウド推奨）
        profile = await self.integrate_profile(episode_texts)

        # 保存
        memory.remember(
            "semantic_profile",
            profile,
            metadata={
                "layer": "semantic",
                "updated_at": datetime.now().isoformat()
            }
        )

        return profile
```

#### 2.2 CLI統合

```python
# src/kagura/cli/memory_cli.py

import click
import asyncio
from kagura.core.memory import MemoryManager
from kagura.memory.hippocampus import SemanticIntegrator

@click.group()
def memory():
    """Memory management commands"""
    pass

@memory.command()
@click.option('--agent-name', '-a', required=True, help='Agent name')
def consolidate(agent_name: str):
    """Run nightly consolidation"""

    # MemoryManager初期化
    memory = MemoryManager(
        agent_name=agent_name,
        enable_rag=True
    )

    # 統合実行
    integrator = SemanticIntegrator()
    profile = asyncio.run(integrator.nightly_consolidation(memory))

    print(f"""
✅ Consolidation completed!

Profile:
{json.dumps(profile, indent=2, ensure_ascii=False)}
    """)

@memory.command()
@click.option('--interval', '-i', default='24h', help='Consolidation interval')
def daemon(interval: str):
    """Run consolidation daemon"""
    print(f"Starting consolidation daemon (interval: {interval})")
    # デーモン実装...
```

### 使用例

```bash
# 夜間バッチ（cronで実行）
$ kagura memory consolidate --agent-name my_assistant

# または自動デーモン
$ kagura memory daemon --interval 24h
```

### 成功指標（Phase 2）

- ✅ 夜間統合で重複削除・矛盾解消
- ✅ 恒久プロファイル生成（JSON）
- ✅ コスト < $0.0001/run（Gemini Flash 8B）
- ✅ 次回会話でプロファイル自動注入

---

## 📦 Phase 3: Knowledge Graph（オプション・2週間）

### 目標

**エンティティ関係のグラフを構築し、関連性ベースの検索を可能にする**

### 実装概要

```python
# src/kagura/memory/hippocampus/graph.py

import networkx as nx

class KnowledgeGraphBuilder:
    """エンティティ関係のグラフ構築"""

    def __init__(self):
        self.graph = nx.DiGraph()

    @agent(model="ollama/qwen2.5:3b-instruct")
    async def extract_entities_relations(self, text: str) -> dict:
        """エンティティと関係を抽出"""
        pass

    def query_relations(self, entity: str, depth: int = 2) -> dict:
        """エンティティの関係を取得（depth-hop）"""
        pass
```

### 成功指標（Phase 3）

- ✅ NetworkX統合
- ✅ エンティティ・関係抽出
- ✅ グラフクエリAPI

---

## 📦 Phase 4: LoRA Fine-tuning（オプション・3週間）

### 目標

**週1回の軽量Fine-tuning（ローカル）でパラメトリック統合**

### 実装概要

```python
# src/kagura/memory/hippocampus/learning.py

from transformers import AutoModelForCausalLM
from peft import get_peft_model, LoraConfig

class IncrementalLearner:
    """週1回のLoRA微調整"""

    async def finetune_lora(self, dataset: list[dict]):
        """LoRA微調整（軽量）"""
        model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-3B-Instruct")
        lora_config = LoraConfig(r=8, lora_alpha=16)
        model = get_peft_model(model, lora_config)
        # 学習...
```

### 成功指標（Phase 4）

- ✅ PEFT（LoRA）統合
- ✅ 週次学習スケジューラ
- ✅ CPU可能（GPU不要）

---

## 📊 RFC-003との比較

| 項目 | RFC-003（旧）| RFC-034（新）|
|------|-------------|-------------|
| **核心目的** | Fine-tuning中心 | **記憶→コンテキスト強化** |
| **コスト** | $5-20/回（FT） | **$0（ローカルSLM）** |
| **プライバシー** | ⚠️ 外部送信 | ✅ **完全ローカル** |
| **VRAM** | 不明 | **< 0.5GB（Ultra-Light）** |
| **効果** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **段階性** | FT中心 | **段階的（Phase 1-4）** |
| **記憶モデル** | データ収集→FT | **海馬型（統合・要約）** |
| **Knowledge Graph** | なし | **あり（Phase 3）** |
| **最小実装** | 4週間 | **2週間（Phase 1）** |
| **Hardware** | 不明 | **RTX 3060 OK** |

---

## 📅 実装スケジュール

### v2.6.0: Hippocampus Memory System（8週間）

**Week 1-2: Phase 1 - Episodic Consolidation** ⭐️ 最優先
- [ ] `HippocampusConfig` 実装
- [ ] `EpisodicConsolidator` 実装
- [ ] `@agent(enable_hippocampus=True)` 統合
- [ ] Qwen2.5-0.5B統合（Ollama）
- [ ] 20+ tests
- [ ] **成果**: 会話終了時に自動要約、VRAM < 0.5GB

**Week 3-4: Phase 2 - Semantic Integration**
- [ ] `SemanticIntegrator` 実装
- [ ] 夜間統合バッチ（Gemini Flash 8B）
- [ ] CLI: `kagura memory consolidate`
- [ ] 15+ tests
- [ ] **成果**: 恒久プロファイル生成、コスト < $0.0001/run

**Week 5-6: Phase 3 - Knowledge Graph (Optional)**
- [ ] `KnowledgeGraphBuilder` 実装
- [ ] NetworkX統合
- [ ] エンティティ・関係抽出
- [ ] 10+ tests

**Week 7-8: Phase 4 - LoRA Learning (Optional)**
- [ ] `IncrementalLearner` 実装
- [ ] PEFT（LoRA）統合
- [ ] 週次学習スケジューラ
- [ ] 5+ tests

---

## 🎯 成功指標（全体）

### Phase 1-2完了時（必須）

**技術指標**:
- ✅ VRAM使用量 < 0.5GB（Ultra-Light）
- ✅ レイテンシ < 50ms（事実抽出）
- ✅ コスト < $0.01/日（夜間統合）
- ✅ RTX 3060 (8GB) で動作

**ユーザー価値**:
- ✅ **即座の記憶**: 会話ごとに重要事実を自動保存
- ✅ **統合知識**: 夜間バッチでプロファイル生成
- ✅ **コンテキスト強化**: Main LLMがより良い回答を生成
- ✅ **プライバシー**: 完全ローカル（外部送信なし）

### Phase 3-4完了時（オプション）

- ✅ **関係性理解**: Knowledge Graphでエンティティ関係管理
- ✅ **深い学習**: LoRAでパラメトリック統合
- ✅ **自己改善**: 使うほど賢くなる

---

## ⚠️ リスクと対策

### リスク1: SLM品質

**問題**: 0.5B-3Bモデルで十分な精度が出るか？
**対策**:
- Ultra-Light（0.5B）は最小タスクのみ（事実抽出・分類）
- 統合処理はクラウド（Gemini Flash 8B）推奨
- モード切替可能（Ultra-Light / Light / Standard / Cloud）

### リスク2: ユーザー体験

**問題**: 「覚えている」感覚が薄いかも
**対策**:
- フィードバック表示（"💾 記憶しました: ダークモード好き"）
- `kagura memory show` コマンドで記憶確認
- Main LLMの回答に記憶ソース表示

### リスク3: ストレージ肥大化

**問題**: RAGが肥大化する可能性
**対策**:
- TTL設定（90日後に自動削除）
- 重要度ベースの削除
- `kagura memory prune` コマンド

---

## 🔗 関連RFC・Issue

- **RFC-018**: Memory Management System（既存・基盤）
- **RFC-024**: Context Compression（既存・補完関係）
- **RFC-025**: Knowledge Graph Integration（未実装・Phase 3で統合）
- **Issue #63**: RFC-003 Personal Assistant（**置き換え対象**）

---

## 📝 次のステップ

1. **Issue作成**（今日）
   - GitHub Issue: RFC-034 Hippocampus Memory System
   - Issue #63にコメント（RFC-034への移行説明）

2. **コミュニティフィードバック**（1週間）
   - ローカルSLMアプローチへの意見
   - ハードウェア要件の確認
   - 優先度の調整

3. **Phase 1プロトタイプ**（1週間）
   - `EpisodicConsolidator` 最小実装
   - Qwen2.5-0.5B統合（Ollama）
   - 実使用テスト（RTX 3060）

4. **評価 → Phase 2以降の判断**

---

## 💬 議論ポイント

1. **Ultra-Light（0.5B）で十分か？**
   - 事実抽出・分類は単純タスク → 0.5Bで十分
   - 統合処理はクラウド（Gemini Flash）推奨

2. **統合頻度: 夜間バッチ vs リアルタイム？**
   - Phase 1: リアルタイム（会話終了時）
   - Phase 2: 夜間バッチ（コスト削減）

3. **Knowledge Graph: 必須 or オプション？**
   - Phase 3: オプション（効果検証後に判断）

4. **LoRA Fine-tuning: 本当に必要？**
   - Phase 4: オプション（Phase 1-2で十分かも）

---

## 🎓 まとめ

このRFCは、Kagura AIを「単なるフレームワーク」から**「継続的に記憶・学習するパーソナルAI」**へと進化させます。

### 核心的な価値

**「この記憶システム自体がコンテキストとなり、Main LLMがより良い回答を生成できる」**

### キーポイント

1. ✅ **段階的実装**（Phase 1-4、Phase 1のみで価値あり）
2. ✅ **ローカル優先**（プライバシー第一、コスト$0）
3. ✅ **軽量**（VRAM < 0.5GB、RTX 3060 OK）
4. ✅ **海馬型**（人間の記憶モデルを模倣）
5. ✅ **コンテキスト強化**（記憶→より良い回答）

### RFC-003からの進化

- ❌ Fine-tuning中心 → ✅ 記憶統合中心
- ❌ 高コスト（$5-20/回）→ ✅ 低コスト（$0）
- ❌ 外部送信 → ✅ 完全ローカル
- ❌ 4週間 → ✅ 2週間（Phase 1）

**コミュニティのフィードバックを歓迎します！**
