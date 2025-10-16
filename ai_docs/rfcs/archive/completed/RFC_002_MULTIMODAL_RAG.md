# RFC-002: Multimodal RAG Chat with Google Workspace & MCP support

**ステータス**: 提案中
**作成日**: 2025-10-03
**対象バージョン**: v2.1.0 - v2.2.0
**関連Issue**: #62

---

## 📋 概要

Kagura AIに以下の機能を追加します：

1. **マルチモーダルRAGチャット** - 画像・音声・動画・PDFを含むディレクトリデータの対話的探索
2. **Google Workspace連携** - Drive/Calendar/Gmail統合
3. **ハイブリッドツールシステム** - Kagura独自 `@tool` + MCP互換レイヤー

---

## 🎯 目標

### ユーザー視点
- `kagura chat` 一発で、プロジェクト全体を理解できる
- 画像の中身を質問できる（「この図の内容は？」）
- 音声ファイルを文字起こし・要約できる
- Googleカレンダーの予定と関連資料を自動で紐付け
- 日本語で自然に会話できる

### 開発者視点
- シンプルな `@tool` デコレータでツール作成
- 型安全（Python型ヒント完全活用）
- MCP互換で既存エコシステム活用可能
- Gemini APIで低コスト・高性能なマルチモーダル

---

## 🏗️ アーキテクチャ

### 全体構成

```
┌─────────────────────────────────────────────┐
│         Kagura AI Application               │
│                                             │
│  ┌───────────────────────────────────┐     │
│  │  @agent decorated functions       │     │
│  │                                   │     │
│  │  Native @tool (Kagura Core)      │     │
│  │    ✅ Simple decorator           │     │
│  │    ✅ Type-safe                  │     │
│  │    ✅ Fast (no IPC overhead)     │     │
│  └──────────┬────────────────────────┘     │
│             │                               │
│             ▼                               │
│  ┌───────────────────────────────────┐     │
│  │  MCP Adapter (Optional)           │     │
│  │    - Load external MCP servers    │     │
│  │    - Convert to Kagura tools      │     │
│  │    - Expose Kagura tools as MCP   │     │
│  └──────────┬────────────────────────┘     │
└─────────────┼───────────────────────────────┘
              │
              ▼
    ┌──────────────────────┐
    │  External Resources  │
    │  - MCP Servers       │
    │  - Google Workspace  │
    │  - Web URLs          │
    │  - Vector DB         │
    └──────────────────────┘
```

### なぜハイブリッド？

#### Kagura独自実装（コア）

**優先する理由**:
1. **シンプル**: Kaguraの設計思想「Python-First」に一致
2. **高速**: プロセス間通信のオーバーヘッドなし
3. **型安全**: Python型ヒントをフル活用
4. **学習コスト低**: Pythonのデコレータ知識だけで使える

**実装例**:
```python
from kagura import agent, tool

@tool
def calculate(expression: str) -> float:
    """Calculate mathematical expression"""
    import math
    return eval(expression, {"__builtins__": {}, "math": math})

@agent(tools=[calculate])
async def assistant(task: str) -> str:
    """{{ task }}"""
    pass
```

#### MCP互換レイヤー（拡張）

**追加する理由**:
1. **エコシステム**: 既存MCPサーバー（filesystem, github等）を活用
2. **標準化**: Anthropic提唱の業界標準
3. **相互運用性**: Claude Desktop等との連携

**実装例**:
```python
from kagura.mcp import MCPClient

# 既存MCPサーバーを読み込み
mcp = MCPClient()
await mcp.connect("filesystem", command="npx", args=[...])

# Kaguraエージェントで使用
@agent(tools=mcp.get_tools())
async def file_assistant(task: str) -> str:
    """{{ task }}"""
    pass
```

---

## 🎨 主要機能詳細

### 1. マルチモーダル対応

#### 対応フォーマット

| 種類 | 拡張子 | API | 処理 |
|------|--------|-----|------|
| **画像** | .png, .jpg, .jpeg, .gif, .webp | Gemini Vision | ネイティブ |
| **音声** | .mp3, .wav, .m4a | Gemini Audio | ネイティブ |
| **動画** | .mp4, .mov, .avi | Gemini Video | ネイティブ |
| **PDF** | .pdf | Gemini PDF | ネイティブ |
| **テキスト** | .py, .md, .txt, .json | 直接読み込み | - |
| **データ** | .csv, .xlsx, .parquet | Pandas | テキスト化 |

#### Gemini 1.5を選ぶ理由

**比較**:
- **GPT-4o**: 画像・音声のみ、動画非対応
- **Claude 3.5 Sonnet**: 画像のみ
- **Gemini 1.5 Pro/Flash**: 画像・音声・動画・PDF全対応

**Gemini優位点**:
1. ✅ **2M context**: 長文PDF、長時間動画も一発
2. ✅ **ネイティブ動画**: フレーム抽出不要
3. ✅ **低コスト**: Flash版は非常に安価
4. ✅ **Google連携**: Drive直接アクセス可能

**実装**:
```python
# src/kagura/loaders/multimodal.py
from pathlib import Path
import google.generativeai as genai

class GeminiLoader:
    def __init__(self, model: str = "gemini-1.5-flash"):
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel(model)

    async def analyze_image(self, image_path: Path, prompt: str) -> str:
        """Analyze image with Gemini Vision"""
        image = genai.upload_file(image_path)
        response = await self.model.generate_content([prompt, image])
        return response.text

    async def transcribe_audio(self, audio_path: Path) -> str:
        """Transcribe audio with Gemini"""
        audio = genai.upload_file(audio_path)
        response = await self.model.generate_content([
            "Transcribe this audio in Japanese",
            audio
        ])
        return response.text

    async def analyze_video(self, video_path: Path, prompt: str) -> str:
        """Analyze video with Gemini"""
        video = genai.upload_file(video_path)
        response = await self.model.generate_content([prompt, video])
        return response.text
```

### 2. Google Workspace連携

#### 認証フロー

```python
# src/kagura/integrations/google_auth.py
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pickle

SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/gmail.readonly',
]

def authenticate():
    """OAuth 2.0 authentication flow"""
    creds = None

    # トークンキャッシュ
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # 期限切れ or 未認証
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        # キャッシュ保存
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return creds
```

#### Drive統合

```python
from kagura import tool
from googleapiclient.discovery import build

class GoogleDrive:
    def __init__(self, creds):
        self.service = build('drive', 'v3', credentials=creds)

    @tool
    async def search_files(
        self,
        query: str,
        max_results: int = 10,
        file_types: list[str] = None
    ) -> list[dict]:
        """
        Search Google Drive files

        Args:
            query: Search query (e.g., "name contains 'report'")
            max_results: Maximum number of results
            file_types: Filter by MIME types

        Returns:
            List of file metadata (id, name, link, modified time)
        """
        # クエリ構築
        q = query
        if file_types:
            mime_queries = [f"mimeType='{ft}'" for ft in file_types]
            q += f" and ({' or '.join(mime_queries)})"

        results = self.service.files().list(
            q=q,
            pageSize=max_results,
            fields="files(id, name, mimeType, modifiedTime, webViewLink)"
        ).execute()

        return results.get('files', [])

    @tool
    async def read_file(self, file_id: str) -> str:
        """
        Read Google Drive file content

        Args:
            file_id: Google Drive file ID

        Returns:
            File content as text
        """
        # ファイルメタデータ取得
        file = self.service.files().get(fileId=file_id).execute()
        mime_type = file['mimeType']

        # Google Docs/Sheets/Slides
        if 'google-apps' in mime_type:
            export_mime = 'text/plain'
            content = self.service.files().export(
                fileId=file_id,
                mimeType=export_mime
            ).execute()
        else:
            # 通常ファイル
            content = self.service.files().get_media(
                fileId=file_id
            ).execute()

        return content.decode('utf-8')
```

#### Calendar統合

```python
class GoogleCalendar:
    def __init__(self, creds):
        self.service = build('calendar', 'v3', credentials=creds)

    @tool
    async def get_events(
        self,
        days_ahead: int = 7,
        calendar_id: str = 'primary'
    ) -> list[dict]:
        """
        Get upcoming calendar events

        Args:
            days_ahead: Number of days to look ahead
            calendar_id: Calendar ID (default: primary)

        Returns:
            List of events with summary, start, end, attendees
        """
        from datetime import datetime, timedelta

        now = datetime.utcnow()
        time_min = now.isoformat() + 'Z'
        time_max = (now + timedelta(days=days_ahead)).isoformat() + 'Z'

        events_result = self.service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        return events_result.get('items', [])

    @tool
    async def create_event(
        self,
        summary: str,
        start_time: str,
        end_time: str,
        attendees: list[str] = None,
        description: str = ""
    ) -> dict:
        """
        Create a new calendar event

        Args:
            summary: Event title
            start_time: ISO format (e.g., "2024-10-15T14:00:00")
            end_time: ISO format
            attendees: List of email addresses
            description: Event description

        Returns:
            Created event metadata
        """
        event = {
            'summary': summary,
            'description': description,
            'start': {'dateTime': start_time, 'timeZone': 'Asia/Tokyo'},
            'end': {'dateTime': end_time, 'timeZone': 'Asia/Tokyo'},
        }

        if attendees:
            event['attendees'] = [{'email': email} for email in attendees]

        created = self.service.events().insert(
            calendarId='primary',
            body=event
        ).execute()

        return created
```

### 3. Directory RAG Chat

#### 実装

```python
# src/kagura/cli/chat.py
from kagura import agent, memory, tool
from kagura.loaders import GeminiLoader
from kagura.integrations import GoogleWorkspace
import chromadb

class DirectoryRAGChat:
    def __init__(self, directory: str = ".", lang: str = "ja"):
        self.directory = Path(directory)
        self.lang = lang
        self.gemini = GeminiLoader()
        self.google = GoogleWorkspace()
        self.chroma = chromadb.Client()
        self.collection = self.chroma.create_collection("directory_data")

    async def start(self):
        """Start interactive chat"""
        # 1. ディレクトリスキャン
        files = await self._scan_directory()
        print(f"\nLoaded {len(files)} files:")

        # ファイルタイプ別に集計
        file_types = {}
        for f in files:
            ext = f.suffix[1:] if f.suffix else "no_ext"
            file_types[ext] = file_types.get(ext, 0) + 1

        for ext, count in sorted(file_types.items()):
            print(f"  - {count} {ext} files")

        # 2. ベクトルDB構築
        print("\nBuilding vector database...")
        await self._build_vectordb(files)

        # 3. チャットループ
        chat_id = str(uuid.uuid4())
        print(f"\n{'='*50}")
        print("Kagura AI Chat - Type 'exit' to quit")
        print(f"{'='*50}\n")

        while True:
            try:
                user_input = input("You: ")
                if user_input.lower() in ['exit', 'quit', 'q']:
                    break

                response = await self.chat(user_input, chat_id)
                print(f"\nAI: {response}\n")

            except KeyboardInterrupt:
                break

    async def _scan_directory(self) -> list[Path]:
        """Scan directory for all files"""
        files = []
        for path in self.directory.rglob('*'):
            if path.is_file() and not self._is_ignored(path):
                files.append(path)
        return files

    def _is_ignored(self, path: Path) -> bool:
        """Check if file should be ignored"""
        ignore_patterns = [
            '__pycache__',
            '.git',
            'node_modules',
            '.venv',
            'venv',
            '.egg-info',
        ]
        return any(pattern in str(path) for pattern in ignore_patterns)

    async def _build_vectordb(self, files: list[Path]):
        """Build vector database from files"""
        for file in files:
            try:
                content = await self._load_file(file)

                # ベクトルDBに追加
                self.collection.add(
                    documents=[content],
                    metadatas=[{
                        "path": str(file),
                        "type": file.suffix[1:] if file.suffix else "unknown"
                    }],
                    ids=[str(file)]
                )
            except Exception as e:
                print(f"Warning: Failed to load {file}: {e}")

    async def _load_file(self, file: Path) -> str:
        """Load file content"""
        # テキストファイル
        if file.suffix in ['.py', '.md', '.txt', '.json', '.yaml', '.toml']:
            with open(file, 'r', encoding='utf-8') as f:
                return f.read()

        # 画像
        elif file.suffix in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
            return await self.gemini.analyze_image(
                file,
                "この画像の内容を日本語で詳しく説明してください"
            )

        # 音声
        elif file.suffix in ['.mp3', '.wav', '.m4a']:
            return await self.gemini.transcribe_audio(file)

        # 動画
        elif file.suffix in ['.mp4', '.mov', '.avi']:
            return await self.gemini.analyze_video(
                file,
                "この動画の内容を日本語で要約してください"
            )

        # PDF
        elif file.suffix == '.pdf':
            # Gemini PDFサポート使用
            pass

        return ""

    @agent(model="gemini/gemini-1.5-flash")
    @memory.session(key="chat_id")
    async def chat(self, message: str, chat_id: str) -> str:
        """
        ユーザーの質問に{{ lang }}で回答してください。

        ユーザー: {{ message }}

        関連するファイル:
        {% for doc in retrieved_docs %}
        ファイル: {{ doc.metadata.path }}
        種類: {{ doc.metadata.type }}
        内容: {{ doc.document[:500] }}...
        {% endfor %}

        利用可能なツール:
        - search_drive: Google Driveを検索
        - get_calendar_events: カレンダーの予定を取得
        - read_gmail: Gmailを読む
        - generate_file: 新しいファイルを生成
        """
        # ベクトル検索
        results = self.collection.query(
            query_texts=[message],
            n_results=5
        )

        # コンテキストに追加
        retrieved_docs = []
        for i, doc_id in enumerate(results['ids'][0]):
            retrieved_docs.append({
                "metadata": results['metadatas'][0][i],
                "document": results['documents'][0][i]
            })

        # エージェント実行（プロンプトテンプレートに自動注入）
        pass

    @tool
    async def generate_file(self, path: str, content: str) -> str:
        """
        新しいファイルを生成

        Args:
            path: ファイルパス
            content: ファイル内容

        Returns:
            成功メッセージ
        """
        file_path = self.directory / path
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return f"Generated {path}"
```

---

## 📦 依存関係

```toml
[project.optional-dependencies]
# マルチモーダル + Google連携
multimodal = [
    "google-generativeai>=0.3.0",      # Gemini API
    "google-auth>=2.0.0",              # Google認証
    "google-auth-oauthlib>=1.0.0",     # OAuth 2.0
    "google-api-python-client>=2.0.0", # Workspace API
    "chromadb>=0.4.0",                 # ベクトルDB
    "pillow>=10.0.0",                  # 画像処理
    "beautifulsoup4>=4.12.0",          # Web scraping
    "playwright>=1.40.0",              # 動的ページ
]

# MCP互換レイヤー（オプション）
mcp = [
    "mcp>=0.1.0",  # Model Context Protocol SDK
]
```

---

## 📅 実装スケジュール

### Phase 2.1: コアツールシステム（v2.1.0）
**Week 1-2** (2025-10-07 〜 2025-10-20):
- [ ] `@tool` デコレータ実装
- [ ] JSON Schema変換
- [ ] ツール実行エンジン
- [ ] ユニットテスト
- [ ] ドキュメント

### Phase 2.2: Google Workspace連携（v2.1.0）
**Week 3-4** (2025-10-21 〜 2025-11-03):
- [ ] OAuth 2.0認証フロー
- [ ] Google Drive API統合
- [ ] Google Calendar API統合
- [ ] Gmail API統合
- [ ] 統合テスト

### Phase 2.3: マルチモーダルRAG（v2.2.0）
**Week 5-6** (2025-11-04 〜 2025-11-17):
- [ ] Gemini API統合
- [ ] マルチモーダルローダー
- [ ] ディレクトリスキャナー
- [ ] ChromaDB統合
- [ ] `kagura chat` コマンド

### Phase 2.4: MCP互換レイヤー（v2.2.0 - オプション）
**Week 7-8** (2025-11-18 〜 2025-12-01):
- [ ] MCPクライアント実装
- [ ] MCPサーバー実装
- [ ] 既存MCPサーバー統合
- [ ] Claude Desktop連携確認

---

## ⚠️ リスクと対策

### リスク1: コスト増加
**問題**: Gemini API利用でコストが発生
**対策**:
- デフォルトはGemini 1.5 Flash（低コスト版）
- ローカルキャッシュで重複呼び出し防止
- ユーザーに事前警告（`--estimate-cost`オプション）

### リスク2: プライバシー懸念
**問題**: ローカルファイルをGeminiに送信
**対策**:
- `.gitignore` ファイルは自動除外
- `--exclude` オプションで除外パターン指定
- ドキュメントで明示的に注意喚起

### リスク3: MCP複雑性
**問題**: MCP実装が複雑
**対策**:
- Phase 2.4をオプション化
- コアは独自実装のみで完結
- MCP需要が高まってから実装

---

## 🎓 学習リソース

### ユーザー向け
- チュートリアル: `kagura chat` の使い方
- サンプル: Google Workspace連携の実例
- FAQ: コスト、プライバシー、対応形式

### 開発者向け
- `@tool` デコレータの作り方
- カスタムローダーの実装
- MCP互換レイヤーの拡張

---

## 📝 まとめ

このRFCは、Kagura AIを「単なるAIエージェントフレームワーク」から「インテリジェントなデータ探索ツール」へと進化させます。

**キーポイント**:
1. ✅ **Gemini 1.5でマルチモーダル対応**（低コスト・高性能）
2. ✅ **Google Workspace統合**（Drive/Calendar/Gmail）
3. ✅ **ハイブリッド設計**（独自実装コア + MCP互換拡張）
4. ✅ **日本語ネイティブ**（完全対応）
5. ✅ **シンプルなAPI**（`kagura chat`一発）

コミュニティのフィードバックを歓迎します！
