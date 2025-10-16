# RFC-004: Voice-First Interface

## ステータス
- **状態**: Draft
- **作成日**: 2025-10-04
- **関連Issue**: #64
- **優先度**: Medium

## 概要

Kagura AIに音声による入出力機能を追加し、ハンズフリーでAIエージェントと対話できるようにします。音声認識（STT）と音声合成（TTS）を統合し、自然な会話型インターフェースを提供します。

### 目標
- 音声でのコマンド実行とREPL操作
- 多言語音声対応（日本語、英語など）
- リアルタイム音声認識と応答
- オフライン音声処理のオプション
- 既存の`@agent`デコレータとシームレスに統合

### 非目標
- 音声感情認識（将来的に検討）
- リアルタイム会話の中断・割り込み（v1では非対応）

## モチベーション

### 現在の課題
1. キーボード入力が困難な状況での利用制限
2. 長文コマンドの入力が手間
3. マルチタスク中のAI操作の非効率性

### 解決するユースケース
- コーディング中に手を離さずにAIに質問
- 移動中や料理中などのハンズフリー操作
- 視覚障害者向けアクセシビリティ向上
- 自然言語での複雑なコマンド実行

### なぜ今実装すべきか
- OpenAI Whisper、Google Speech-to-Textなど高精度STTが利用可能
- ElevenLabs、Google TTSで自然な音声合成が実現可能
- 音声UIの需要増加（スマートスピーカー、音声アシスタント）

## 設計

### アーキテクチャ

```
┌─────────────────────────────────────────────┐
│           Voice Interface Layer             │
│                                             │
│  ┌──────────────┐      ┌──────────────┐   │
│  │  STT Engine  │      │  TTS Engine  │   │
│  │              │      │              │   │
│  │ - Whisper    │      │ - ElevenLabs │   │
│  │ - Google STT │      │ - Google TTS │   │
│  │ - Local STT  │      │ - pyttsx3    │   │
│  └──────┬───────┘      └───────┬──────┘   │
│         │                      │          │
│         ▼                      ▼          │
│  ┌─────────────────────────────────────┐  │
│  │     Voice Command Processor         │  │
│  │  - Intent Recognition               │  │
│  │  - Context Management               │  │
│  │  - Language Detection               │  │
│  └─────────────┬───────────────────────┘  │
└────────────────┼──────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────┐
│         Kagura Core (Existing)             │
│                                            │
│  ┌─────────────────────────────────────┐  │
│  │      @agent / @voice Decorator      │  │
│  └─────────────────────────────────────┘  │
│  ┌─────────────────────────────────────┐  │
│  │         CLI / REPL Layer            │  │
│  └─────────────────────────────────────┘  │
└────────────────────────────────────────────┘
```

### コンポーネント設計

#### 1. STT (Speech-to-Text) Engine

**サポートするエンジン:**
- **OpenAI Whisper** (デフォルト): 多言語、高精度
- **Google Cloud Speech-to-Text**: リアルタイムストリーミング
- **ローカルWhisper**: プライバシー重視、オフライン対応

```python
from kagura.voice import STTEngine, WhisperSTT, GoogleSTT

# 設定
stt = WhisperSTT(model="base", language="ja")
# または
stt = GoogleSTT(credentials_path="gcp-key.json", language_code="ja-JP")

# 音声からテキストへ
text = await stt.transcribe("audio.wav")
# => "ユーザー登録機能を実装して"

# ストリーミング
async for partial_text in stt.stream_transcribe(audio_stream):
    print(partial_text)
```

#### 2. TTS (Text-to-Speech) Engine

**サポートするエンジン:**
- **ElevenLabs**: 最も自然な音声（有料）
- **Google Cloud TTS**: 高品質、多言語対応
- **pyttsx3**: オフライン、無料

```python
from kagura.voice import TTSEngine, ElevenLabsTTS, GoogleTTS

# 設定
tts = ElevenLabsTTS(api_key="...", voice_id="rachel")
# または
tts = GoogleTTS(credentials_path="gcp-key.json", language_code="ja-JP", voice_name="ja-JP-Wavenet-A")

# テキストから音声へ
audio = await tts.synthesize("了解しました。ユーザー登録機能を実装します。")
await tts.play(audio)
```

#### 3. Voice Command Processor

```python
from kagura.voice import VoiceProcessor

processor = VoiceProcessor(
    stt_engine=WhisperSTT(),
    tts_engine=ElevenLabsTTS(),
    language="ja"
)

# インテント認識
intent = await processor.recognize_intent("ファイル一覧を表示して")
# => {"action": "list_files", "params": {}}

# コンテキスト管理
processor.set_context({"current_dir": "/home/user/project"})
```

### APIデザイン

#### `@voice` デコレータ

既存の`@agent`デコレータと組み合わせて使用：

```python
from kagura import agent, voice

@agent(model="gpt-4o-mini")
@voice.enable(
    stt="whisper",
    tts="elevenlabs",
    language="ja",
    auto_respond=True
)
async def voice_assistant(command: str) -> str:
    """{{ command }}"""
    pass

# 使用例
result = await voice_assistant.listen()  # マイクから音声入力
# 自動的に音声で応答
```

#### Voice REPL

```bash
# 音声REPLモード起動
kagura voice

# または既存REPLで音声モード切り替え
kagura repl
> /voice on
Voice mode enabled. Listening...

# 音声でコマンド実行
You: (音声) 「テストを実行して」
AI: (音声) 「はい、pytestを実行します」
[テスト実行結果表示]

You: (音声) 「エラーを修正して」
AI: (音声) 「test_user.pyの15行目のタイプエラーを修正します」
[コード修正]

# 音声モード終了
You: (音声) 「音声モード終了」
AI: (音声) 「音声モードを終了しました」
> /voice off
```

#### Voice Commands API

```python
from kagura.voice import VoiceCommands

vc = VoiceCommands()

# カスタムコマンド登録
@vc.register(intent="create_file")
async def create_file(filename: str):
    """ファイル作成コマンド"""
    with open(filename, "w") as f:
        f.write("")
    return f"{filename}を作成しました"

# 音声コマンド実行
await vc.execute_voice("main.pyを作成して")
# => "main.pyを作成しました" (音声で応答)
```

### 統合例

#### 例1: 音声コーディングアシスタント

```python
from kagura import agent, voice, tool
from kagura.voice import WhisperSTT, ElevenLabsTTS

@tool
def run_tests() -> str:
    """Run pytest"""
    import subprocess
    result = subprocess.run(["pytest"], capture_output=True, text=True)
    return result.stdout

@agent(model="gpt-4o-mini")
@voice.enable(
    stt=WhisperSTT(model="base", language="ja"),
    tts=ElevenLabsTTS(voice_id="rachel"),
    auto_listen=True  # 連続会話モード
)
async def coding_assistant(request: str) -> str:
    """{{ request }}"""
    pass

# 音声で対話
async def main():
    await coding_assistant.start_voice_session()
    # マイクから継続的に入力を受け付け、音声で応答

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

#### 例2: ハンズフリーREPL

```bash
# 音声REPL起動
kagura voice --language ja --stt whisper --tts elevenlabs

Listening... (Ctrl+C to stop)

You: 「今日のタスクを確認して」
AI: 「本日のタスクは3件です。1. プルリクエストのレビュー、2. テストの修正、3. ドキュメント更新」

You: 「1番目のタスクを詳しく教えて」
AI: 「プルリクエスト57番、REPLの改善です。変更内容を確認しますか？」

You: 「はい」
AI: 「3つのファイルが変更されています。main.py、repl.py、test_repl.pyです」

You: 「コードを見せて」
[コード表示 + 音声で要約]
```

#### 例3: 多言語音声エージェント

```python
from kagura import agent, voice

@agent(model="gpt-4o-mini")
@voice.enable(language="auto")  # 自動言語検出
async def multilingual_assistant(query: str) -> str:
    """{{ query }}"""
    pass

# 日本語で質問
await multilingual_assistant.listen()  # 音声入力: 「天気を教えて」
# => 音声応答: 「本日は晴れです」

# 英語で質問
await multilingual_assistant.listen()  # 音声入力: "What's the weather?"
# => 音声応答: "It's sunny today"
```

## 実装計画

### Phase 1: 基本音声機能 (v2.1.0)
- [ ] STTエンジン統合（Whisper、Google STT）
- [ ] TTSエンジン統合（ElevenLabs、Google TTS、pyttsx3）
- [ ] `@voice.enable` デコレータ実装
- [ ] 音声入出力の基本API

### Phase 2: Voice REPL (v2.2.0)
- [ ] `kagura voice` コマンド実装
- [ ] 既存REPLへの音声モード追加（`/voice on/off`）
- [ ] インテント認識システム
- [ ] コンテキスト管理

### Phase 3: 高度な機能 (v2.3.0)
- [ ] 連続会話モード（auto_listen）
- [ ] 多言語自動検出
- [ ] カスタムコマンド登録
- [ ] 音声フィードバックのカスタマイズ

### Phase 4: 最適化 (v2.4.0)
- [ ] ローカルWhisperのパフォーマンス最適化
- [ ] 音声キャッシング
- [ ] 低遅延モード
- [ ] バックグラウンド音声処理

## 技術的詳細

### 依存関係

```toml
[project.optional-dependencies]
voice = [
    "openai-whisper>=20231117",  # STT
    "elevenlabs>=0.2.27",         # TTS
    "google-cloud-speech>=2.21.0", # Google STT
    "google-cloud-texttospeech>=2.14.1", # Google TTS
    "pyttsx3>=2.90",              # Offline TTS
    "pyaudio>=0.2.13",            # Audio I/O
    "sounddevice>=0.4.6",         # Audio recording
    "soundfile>=0.12.1",          # Audio file handling
    "webrtcvad>=2.0.10",          # Voice Activity Detection
]
```

### 設定ファイル

`~/.kagura/voice.toml`:

```toml
[voice]
# デフォルトSTTエンジン
stt_engine = "whisper"
stt_model = "base"
stt_language = "ja"

# デフォルトTTSエンジン
tts_engine = "elevenlabs"
tts_voice_id = "rachel"

# オーディオ設定
sample_rate = 16000
channels = 1
chunk_size = 1024

# Voice Activity Detection
vad_aggressiveness = 3  # 0-3
silence_duration = 1.5  # seconds

[voice.whisper]
model = "base"  # tiny, base, small, medium, large
device = "cuda"  # cpu, cuda
language = "ja"

[voice.elevenlabs]
api_key = "${ELEVENLABS_API_KEY}"
voice_id = "rachel"
model = "eleven_multilingual_v2"

[voice.google]
credentials_path = "~/.config/gcp/key.json"
stt_language_code = "ja-JP"
tts_language_code = "ja-JP"
tts_voice_name = "ja-JP-Wavenet-A"
```

### エラーハンドリング

```python
from kagura.voice import VoiceError, STTError, TTSError

try:
    result = await voice_assistant.listen()
except STTError as e:
    print(f"音声認識エラー: {e}")
    # フォールバック: テキスト入力
    result = input("テキストで入力してください: ")
except TTSError as e:
    print(f"音声合成エラー: {e}")
    # フォールバック: テキスト出力のみ
    print(result)
```

### パフォーマンス考慮事項

**レイテンシ:**
- Whisper (tiny): ~100ms
- Whisper (base): ~200ms
- Google STT (streaming): ~50-100ms
- ElevenLabs TTS: ~500ms
- Google TTS: ~300ms

**最適化戦略:**
1. 音声認識結果のキャッシング
2. TTS音声の事前生成
3. ストリーミングSTTでリアルタイム応答
4. VAD（Voice Activity Detection）で無音検出

## テスト戦略

### ユニットテスト

```python
# tests/voice/test_stt.py
import pytest
from kagura.voice import WhisperSTT

@pytest.mark.asyncio
async def test_whisper_transcribe():
    stt = WhisperSTT(model="tiny")
    text = await stt.transcribe("tests/fixtures/audio_ja.wav")
    assert "こんにちは" in text

@pytest.mark.asyncio
async def test_language_detection():
    stt = WhisperSTT(language="auto")
    text = await stt.transcribe("tests/fixtures/audio_en.wav")
    assert stt.detected_language == "en"
```

### 統合テスト

```python
# tests/voice/test_voice_agent.py
import pytest
from kagura import agent, voice

@pytest.mark.asyncio
async def test_voice_agent():
    @agent(model="gpt-4o-mini")
    @voice.enable(stt="whisper", tts="pyttsx3")
    async def test_agent(cmd: str) -> str:
        return f"Executed: {cmd}"

    # モック音声入力
    with voice.mock_input("run tests"):
        result = await test_agent.listen()
        assert "Executed: run tests" in result
```

### E2Eテスト

```bash
# tests/voice/test_voice_repl.sh
#!/bin/bash

# 音声REPLのE2Eテスト
echo "Starting voice REPL test..."

# モック音声ファイルを使用
kagura voice --stt whisper --input tests/fixtures/voice_commands.wav

# 期待される出力を確認
expected_output="Test executed successfully"
# ... assertion logic
```

## セキュリティ考慮事項

1. **プライバシー**
   - ローカルWhisperオプションでオフライン処理
   - 音声データの一時保存と自動削除
   - クラウドSTT/TTSの利用同意確認

2. **認証**
   - APIキーの安全な管理（環境変数、キーチェーン）
   - Google Cloud認証情報の暗号化

3. **音声データ保護**
   - 音声ファイルの暗号化オプション
   - メモリ内処理の優先（ディスク書き込み最小化）

## マイグレーション

既存のKaguraユーザーへの影響なし。音声機能はオプトイン：

```bash
# 音声機能のインストール
pip install kagura-ai[voice]

# 設定ファイル生成
kagura voice init

# 音声REPL起動
kagura voice
```

## ドキュメント

### 必要なドキュメント
1. Voice機能クイックスタートガイド
2. STT/TTSエンジン比較表
3. カスタム音声コマンド作成チュートリアル
4. 多言語対応ガイド
5. トラブルシューティングFAQ

### サンプルコード
- 音声コーディングアシスタント
- ハンズフリーGit操作
- 音声会議記録と要約
- 音声駆動のテスト実行

## 代替案

### 案1: 外部音声アシスタント統合
- Google Assistant、Alexa、Siriとの連携
- **却下理由**: プラットフォーム依存、カスタマイズ性低い

### 案2: WebベースVoice UI
- ブラウザのWeb Speech API使用
- **却下理由**: CLI中心のKaguraの方針と不一致

### 案3: 音声専用CLIツール分離
- `kagura-voice`という別パッケージ
- **却下理由**: 統合体験が損なわれる

## 未解決の問題

1. **音声認識精度の保証方法**
   - テストデータセットの作成が必要
   - 多様なアクセント・方言への対応

2. **リアルタイム会話の割り込み処理**
   - ユーザーがAI応答中に話し始めた場合の制御
   - Phase 1では非対応、将来的に検討

3. **コスト管理**
   - ElevenLabs、Google APIの従量課金
   - 使用量制限・アラートの仕組み必要

## 参考資料

- [OpenAI Whisper](https://github.com/openai/whisper)
- [ElevenLabs API](https://elevenlabs.io/docs/api-reference)
- [Google Cloud Speech-to-Text](https://cloud.google.com/speech-to-text)
- [Google Cloud Text-to-Speech](https://cloud.google.com/text-to-speech)
- [Web Speech API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API)

## 改訂履歴

- 2025-10-04: 初版作成
