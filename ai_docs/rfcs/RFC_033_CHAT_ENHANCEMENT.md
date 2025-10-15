# RFC-033: Chat Enhancement - Intelligent & Self-Expanding Chat System

**ステータス**: Draft
**作成日**: 2025-10-15
**優先度**: ⭐️⭐️ Very High (UX & Capability Critical)
**関連Issue**: TBD
**依存RFC**: RFC-005 (Meta Agent), RFC-032 (MCP Integration)

---

## 📋 概要

### 問題

現在の`kagura chat`は機能が限定的：

1. **エージェント選択が手動**
   - プリセット（translate/summarize/review）のみ
   - ユーザー定義エージェントが使えない
   - 最適なエージェント自動選択なし

2. **動的拡張不可**
   - YouTube動画サマライズ → 専用エージェント必要だが、手動作成
   - CSV分析 → pandasインストール＆エージェント作成が必要
   - Docker操作 → 対応不可

3. **生成エージェント管理なし**
   - 生成したエージェントが再利用されない
   - 同じタスクで毎回生成

4. **UX問題**
   - サジェスト機能なし
   - Ctrl+Pでコマンド履歴が出ない
   - マークダウン表示が不完全
   - マルチバイト文字の表示崩れ
   - リンククリック不可

### 解決策

**Intelligent & Self-Expanding Chat System** - 賢く、自己拡張するチャットシステム

---

## 🎯 目標

### 成功指標

1. **自動エージェント選択**
   - ✅ ユーザー入力 → 最適なagent/tool自動選択
   - ✅ 登録済みエージェント全てを利用可能

2. **自動エージェント生成**
   - ✅ 対応エージェントがない → Meta Agent自動生成
   - ✅ YouTube、CSV、Docker等に対応
   - ✅ 依存関係（pip、Docker）自動インストール

3. **エージェント管理**
   - ✅ 生成エージェントをDB保存・再利用
   - ✅ `~/.kagura/agents/`に永続化
   - ✅ 世代管理（v1、v2...）

4. **UX向上**
   - ✅ サジェスト機能（Tab補完）
   - ✅ Ctrl+P: コマンド履歴
   - ✅ Markdown表示改善（コードブロック、リンク）
   - ✅ マルチバイト文字正しく表示
   - ✅ クリック可能リンク

---

## 🏗️ アーキテクチャ

### 現在の構成（限定的）

```
User Input
   ↓
Preset Detection (/translate, /summarize, /review)
   ↓
Fixed Preset Agents
   ↓
Response
```

### 改善後の構成（自己拡張型）

```
User Input
   ↓
┌─────────────────────────────────────┐
│   Intent Analyzer (LLM-based)       │
│   - Task classification             │
│   - Required capabilities detection │
└───────────┬─────────────────────────┘
            │
    ┌───────▼────────┐
    │ Agent Selector │
    └───────┬────────┘
            │
    ┌───────▼──────────────────────────┐
    │ Registry Lookup                  │
    │ - agent_registry.get_all()       │
    │ - tool_registry.get_all()        │
    │ - custom_agents DB               │
    └───┬──────────────────────────┬───┘
        │ Found                    │ Not Found
        ↓                          ↓
    Execute                  ┌──────────────┐
                            │ Meta Agent    │
                            │ Auto-Generate │
                            └──────┬────────┘
                                   │
                            ┌──────▼────────────────┐
                            │ Dependency Installer   │
                            │ - pip packages        │
                            │ - Docker images       │
                            └──────┬────────────────┘
                                   │
                            ┌──────▼────────────────┐
                            │ Agent DB Storage      │
                            │ - Save for reuse      │
                            │ - Version management  │
                            └──────┬────────────────┘
                                   │
                                Execute
```

---

## 📦 Phase 1: Auto-Discovery & Selection (Week 1)

### 実装内容

#### 1.1 Agent/Tool Registry Integration

```python
# src/kagura/chat/discovery.py

from kagura.core.registry import agent_registry
from kagura.core.tool_registry import tool_registry

class AgentDiscovery:
    """Discover and select agents/tools for user tasks"""

    def __init__(self):
        self.agents = agent_registry.get_all()
        self.tools = tool_registry.get_all()

    async def find_best_match(self, user_input: str) -> tuple[str, callable]:
        """Find best agent/tool for user input

        Returns:
            (type, callable) - ("agent", agent_func) or ("tool", tool_func)
        """
        # LLM-based intent detection
        intent_prompt = f"""Analyze this user request and select the best agent/tool.

Available agents: {list(self.agents.keys())}
Available tools: {list(self.tools.keys())}

User request: {user_input}

Which agent/tool is most suitable? Return just the name.
"""

        from kagura.core.llm import call_llm, LLMConfig

        config = LLMConfig(model="gpt-4o-mini", temperature=0.3)
        selected_name = str(await call_llm(intent_prompt, config)).strip()

        if selected_name in self.agents:
            return ("agent", self.agents[selected_name])
        elif selected_name in self.tools:
            return ("tool", self.tools[selected_name])
        else:
            return ("none", None)
```

#### 1.2 Chat Session Integration

```python
# src/kagura/chat/session.py (enhanced)

from .discovery import AgentDiscovery

class ChatSession:
    def __init__(self, ...):
        # ... existing code ...
        self.discovery = AgentDiscovery()
        self.enable_auto_discovery = True

    async def chat(self, user_input: str):
        """Enhanced chat with auto-discovery"""

        # Try auto-discovery first
        if self.enable_auto_discovery:
            agent_type, agent_func = await self.discovery.find_best_match(user_input)

            if agent_func:
                self.console.print(f"💡 Using {agent_type}: {agent_func.__name__}")
                result = await agent_func(user_input)
                self.console.print(Markdown(str(result)))
                return

        # Fall back to default chat agent
        # ... existing code ...
```

### テスト

```python
# tests/chat/test_discovery.py

import pytest
from kagura import agent, tool
from kagura.chat.discovery import AgentDiscovery

@agent
async def youtube_summarizer(url: str) -> str:
    '''Summarize YouTube video: {{ url }}'''
    pass

@tool
def calculator(x: float, y: float) -> float:
    '''Add numbers'''
    return x + y

@pytest.mark.asyncio
async def test_discovery_finds_agent():
    discovery = AgentDiscovery()

    agent_type, agent_func = await discovery.find_best_match(
        "Summarize https://youtu.be/xxx"
    )

    assert agent_type == "agent"
    assert agent_func.__name__ == "youtube_summarizer"

@pytest.mark.asyncio
async def test_discovery_finds_tool():
    discovery = AgentDiscovery()

    agent_type, tool_func = await discovery.find_best_match(
        "Calculate 10 + 5"
    )

    assert agent_type == "tool"
    assert tool_func.__name__ == "calculator"
```

---

## 📦 Phase 2: Meta Agent Auto-Generation (Week 2)

### 実装内容

#### 2.1 Task Analyzer

```python
# src/kagura/chat/task_analyzer.py

from dataclasses import dataclass
from typing import List

@dataclass
class TaskAnalysis:
    """Task analysis result"""
    description: str
    required_packages: List[str]  # pip packages
    required_tools: List[str]     # Docker, etc.
    agent_spec: str               # Generated spec

class TaskAnalyzer:
    """Analyze user tasks and determine requirements"""

    async def analyze(self, user_input: str) -> TaskAnalysis:
        """Analyze user task

        Returns:
            TaskAnalysis with requirements
        """
        analysis_prompt = f"""Analyze this task and list requirements:

Task: {user_input}

Return JSON:
{{
  "description": "Brief description",
  "required_packages": ["pandas", "matplotlib"],  // pip packages
  "required_tools": ["docker"],  // Docker, curl, etc.
  "agent_spec": "Agent that analyzes CSV and creates charts"
}}
"""

        from kagura.core.llm import call_llm, LLMConfig
        from kagura.core.parser import parse_response

        config = LLMConfig(model="gpt-4o-mini", temperature=0.3)
        response = await call_llm(analysis_prompt, config)

        return parse_response(str(response), TaskAnalysis)
```

#### 2.2 Package Manager

```python
# src/kagura/core/package_manager.py

import subprocess
import sys
from typing import List
from pathlib import Path

class PackageManager:
    """Manage pip and Docker dependencies"""

    SAFE_PACKAGES = [
        # Data science
        "pandas", "numpy", "matplotlib", "seaborn",
        "scipy", "scikit-learn", "statsmodels",
        # Web
        "requests", "beautifulsoup4", "selenium",
        "httpx", "aiohttp",
        # File processing
        "openpyxl", "python-docx", "pypdf2",
        "pillow", "opencv-python",
        # YouTube
        "yt-dlp", "youtube-transcript-api",
        # Utils
        "tqdm", "rich", "click",
    ]

    async def check_package(self, package: str) -> bool:
        """Check if package is installed"""
        try:
            __import__(package.replace("-", "_"))
            return True
        except ImportError:
            return False

    async def install_package(
        self,
        package: str,
        user_approval: bool = True,
        force: bool = False
    ) -> bool:
        """Install pip package with safety check"""

        # Safety check
        if not force and package not in self.SAFE_PACKAGES:
            print(f"⚠️  Package '{package}' not in safe list")
            if user_approval:
                response = input(f"Install anyway? [y/N]: ")
                if response.lower() != 'y':
                    return False

        # User approval for safe packages too
        if user_approval:
            response = input(f"📦 Install {package}? [Y/n]: ")
            if response.lower() == 'n':
                return False

        # Install
        print(f"📦 Installing {package}...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", package],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(f"✓ {package} installed")
            return True
        else:
            print(f"✗ Failed to install {package}: {result.stderr}")
            return False

    async def check_docker(self) -> bool:
        """Check if Docker is available"""
        result = subprocess.run(
            ["docker", "version"],
            capture_output=True
        )
        return result.returncode == 0

    async def pull_docker_image(
        self,
        image: str,
        user_approval: bool = True
    ) -> bool:
        """Pull Docker image"""

        if user_approval:
            response = input(f"🐳 Pull Docker image '{image}'? [Y/n]: ")
            if response.lower() == 'n':
                return False

        print(f"🐳 Pulling {image}...")
        result = subprocess.run(
            ["docker", "pull", image],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(f"✓ {image} pulled")
            return True
        else:
            print(f"✗ Failed to pull {image}")
            return False
```

#### 2.3 Auto-Generating Chat

```python
# src/kagura/chat/session.py (enhanced)

from .task_analyzer import TaskAnalyzer
from kagura.core.package_manager import PackageManager
from kagura.meta import MetaAgent

class ChatSession:
    def __init__(self, enable_auto_agent: bool = True, ...):
        # ... existing ...
        self.enable_auto_agent = enable_auto_agent
        self.task_analyzer = TaskAnalyzer()
        self.package_mgr = PackageManager()
        self.meta_agent = MetaAgent()
        self.agent_db = AgentDatabase()  # Phase 3

    async def chat(self, user_input: str):
        """Enhanced chat with auto-generation"""

        # 1. Try existing agents/tools
        if self.enable_auto_discovery:
            agent_type, agent_func = await self.discovery.find_best_match(user_input)

            if agent_func:
                self.console.print(f"💡 Using {agent_type}: {agent_func.__name__}")
                result = await self._execute_agent_or_tool(agent_type, agent_func, user_input)
                self.console.print(Markdown(str(result)))
                return

        # 2. Try auto-generation
        if self.enable_auto_agent:
            self.console.print("💡 No suitable agent found")
            self.console.print("💡 Analyzing task...")

            # Analyze task
            analysis = await self.task_analyzer.analyze(user_input)

            # Install dependencies
            if analysis.required_packages:
                self.console.print(f"📦 Required packages: {', '.join(analysis.required_packages)}")
                for pkg in analysis.required_packages:
                    if not await self.package_mgr.check_package(pkg):
                        await self.package_mgr.install_package(pkg, user_approval=True)

            if analysis.required_tools:
                # Docker check
                if "docker" in analysis.required_tools:
                    if not await self.package_mgr.check_docker():
                        self.console.print("⚠️  Docker not available")
                        return

            # Generate agent
            self.console.print("💡 Generating agent...")
            code = await self.meta_agent.generate(analysis.agent_spec)

            # Save agent
            agent_name = self._extract_agent_name(code)
            await self.agent_db.save(agent_name, code, analysis)

            # Execute agent
            self.console.print(f"✓ Agent '{agent_name}' created")
            exec(code)  # Dynamic execution

            # Get generated agent from locals
            agent_func = locals()[agent_name]
            result = await agent_func(user_input)

            self.console.print(Markdown(str(result)))
            return

        # 3. Fall back to default chat
        # ... existing code ...
```

---

## 📦 Phase 3: Agent Database & Management (Week 3)

### 実装内容

#### 3.1 Agent Database

```python
# src/kagura/chat/agent_db.py

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List

class AgentDatabase:
    """Manage generated agents with versioning"""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_path = Path.home() / ".kagura" / "agents.db"

        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize database schema"""
        conn = sqlite3.connect(str(self.db_path))

        conn.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                version INTEGER NOT NULL,
                code TEXT NOT NULL,
                description TEXT,
                required_packages TEXT,  -- JSON array
                required_tools TEXT,     -- JSON array
                created_at TEXT NOT NULL,
                last_used TEXT,
                usage_count INTEGER DEFAULT 0,
                UNIQUE(name, version)
            )
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_name_version
            ON agents(name, version DESC)
        """)

        conn.commit()
        conn.close()

    async def save(
        self,
        name: str,
        code: str,
        analysis,
        version: Optional[int] = None
    ) -> int:
        """Save generated agent

        Returns:
            Version number
        """
        conn = sqlite3.connect(str(self.db_path))

        # Get latest version
        if version is None:
            cursor = conn.execute(
                "SELECT MAX(version) FROM agents WHERE name = ?",
                (name,)
            )
            result = cursor.fetchone()[0]
            version = (result + 1) if result else 1

        # Save
        conn.execute("""
            INSERT INTO agents
            (name, version, code, description, required_packages, required_tools, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            version,
            code,
            analysis.description,
            json.dumps(analysis.required_packages),
            json.dumps(analysis.required_tools),
            datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()

        # Also save to file
        agent_file = Path.home() / ".kagura" / "agents" / f"{name}_v{version}.py"
        agent_file.parent.mkdir(parents=True, exist_ok=True)
        agent_file.write_text(code)

        return version

    def get_latest(self, name: str) -> Optional[dict]:
        """Get latest version of agent"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row

        cursor = conn.execute("""
            SELECT * FROM agents
            WHERE name = ?
            ORDER BY version DESC
            LIMIT 1
        """, (name,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def list_agents(self) -> List[dict]:
        """List all agents (latest versions only)"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row

        cursor = conn.execute("""
            SELECT DISTINCT ON (name) *
            FROM agents
            ORDER BY name, version DESC
        """)

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def increment_usage(self, name: str, version: int):
        """Increment usage count"""
        conn = sqlite3.connect(str(self.db_path))

        conn.execute("""
            UPDATE agents
            SET usage_count = usage_count + 1,
                last_used = ?
            WHERE name = ? AND version = ?
        """, (datetime.now().isoformat(), name, version))

        conn.commit()
        conn.close()
```

### CLI拡張

```bash
# List generated agents
$ kagura chat --list-agents

Generated Agents:
  • youtube_summarizer (v2) - Last used: 2025-10-15 15:30
  • csv_analyzer (v1) - Last used: 2025-10-15 14:20
  • docker_manager (v1) - Never used

# Clean old agents
$ kagura chat --clean-agents --older-than 30d
```

---

## 📦 Phase 4: UX Improvements (Week 4)

### 実装内容

#### 4.1 Suggest/Autocomplete

```python
# src/kagura/chat/completer.py

from prompt_toolkit.completion import Completer, Completion

class KaguraCompleter(Completer):
    """Smart autocomplete for kagura chat"""

    def __init__(self, session):
        self.session = session

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor

        # Slash commands
        if text.startswith('/'):
            commands = [
                '/translate', '/summarize', '/review',
                '/help', '/exit', '/clear', '/agents', '/tools'
            ]
            for cmd in commands:
                if cmd.startswith(text):
                    yield Completion(cmd, start_position=-len(text))

        # Agent names
        elif text.startswith('@'):
            for agent_name in self.session.discovery.agents.keys():
                suggestion = f"@{agent_name}"
                if suggestion.startswith(text):
                    yield Completion(suggestion, start_position=-len(text))

        # Tool names
        elif text.startswith('!'):
            for tool_name in self.session.discovery.tools.keys():
                suggestion = f"!{tool_name}"
                if suggestion.startswith(text):
                    yield Completion(suggestion, start_position=-len(text))
```

#### 4.2 History with Ctrl+P

```python
# src/kagura/chat/session.py

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings

class ChatSession:
    def __init__(self, ...):
        # Enable history
        history_file = Path.home() / ".kagura" / "chat_history.txt"
        self.prompt_session = PromptSession(
            history=FileHistory(str(history_file)),
            completer=KaguraCompleter(self),
            enable_history_search=True,  # Ctrl+R
            key_bindings=self._create_keybindings()
        )

    def _create_keybindings(self):
        kb = KeyBindings()

        # Ctrl+P: Previous command (like shell)
        @kb.add('c-p')
        def _(event):
            event.current_buffer.history_backward()

        # Ctrl+N: Next command
        @kb.add('c-n')
        def _(event):
            event.current_buffer.history_forward()

        return kb
```

#### 4.3 Rich Markdown Display

```python
# src/kagura/chat/session.py

from rich.markdown import Markdown
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

class ChatSession:
    def display_response(self, response: str):
        """Enhanced markdown display"""

        # Detect and highlight code blocks
        if "```" in response:
            # Use Syntax for code blocks
            self._display_with_syntax(response)
        else:
            # Regular markdown
            self.console.print(Markdown(response))

        # Make links clickable (using Rich)
        # Rich automatically makes URLs clickable in terminals that support it

    def _display_with_syntax(self, response: str):
        """Display with syntax highlighting"""
        parts = response.split("```")

        for i, part in enumerate(parts):
            if i % 2 == 0:
                # Regular text
                if part.strip():
                    self.console.print(Markdown(part))
            else:
                # Code block
                lines = part.split("\n")
                lang = lines[0].strip() if lines else "python"
                code = "\n".join(lines[1:])

                syntax = Syntax(code, lang, theme="monokai", line_numbers=True)
                self.console.print(Panel(syntax, title=f"Code ({lang})"))
```

#### 4.4 Multibyte Character Fix

```python
# src/kagura/chat/session.py

from prompt_toolkit.formatted_text import FormattedText
from wcwidth import wcswidth

class ChatSession:
    def _calculate_display_width(self, text: str) -> int:
        """Calculate display width for multibyte characters"""
        return wcswidth(text)

    def format_prompt(self) -> FormattedText:
        """Format prompt with proper multibyte handling"""
        return FormattedText([
            ('class:prompt', '[You] > '),
        ])
```

---

## 📦 Phase 5: Docker Integration (Week 5)

### 実装内容

#### 5.1 Docker Tool

```python
# src/kagura/mcp/builtin/docker_ops.py

from kagura import tool
import subprocess
import json

@tool
async def docker_run(
    image: str,
    command: str,
    volumes: dict[str, str] = None
) -> str:
    """Run Docker container

    Args:
        image: Docker image name
        command: Command to run
        volumes: Volume mounts {host: container}

    Returns:
        Container output
    """
    cmd = ["docker", "run", "--rm"]

    if volumes:
        for host, container in volumes.items():
            cmd.extend(["-v", f"{host}:{container}"])

    cmd.extend([image, "sh", "-c", command])

    result = subprocess.run(cmd, capture_output=True, text=True)

    return result.stdout if result.returncode == 0 else result.stderr

@tool
def docker_list_images() -> str:
    """List available Docker images"""
    result = subprocess.run(
        ["docker", "images", "--format", "json"],
        capture_output=True,
        text=True
    )
    return result.stdout

@tool
async def docker_build(dockerfile_path: str, tag: str) -> str:
    """Build Docker image from Dockerfile"""
    result = subprocess.run(
        ["docker", "build", "-t", tag, dockerfile_path],
        capture_output=True,
        text=True
    )
    return result.stdout
```

#### 5.2 Docker-Aware Agent Generation

```python
# src/kagura/meta/templates/agent_with_docker.py.j2

from kagura import agent
import subprocess

@agent(tools=[docker_run])
async def {{ name }}({{ input_param }}: {{ input_type }}) -> {{ output_type }}:
    """{{ system_prompt }}

    Input: {{ '{{' }} {{ input_param }} {{ '}}' }}

    Available tools:
    - docker_run(image, command, volumes): Run Docker container
    """
    pass
```

---

## 📦 Phase 6: Advanced Features (Week 6)

### 実装内容

#### 6.1 YouTube統合

```python
# src/kagura/mcp/builtin/youtube.py

from kagura import tool
import subprocess
import json

@tool
async def youtube_get_transcript(url: str, lang: str = "en") -> str:
    """Get YouTube video transcript

    Args:
        url: YouTube URL
        lang: Language code (default: en)

    Returns:
        Video transcript text
    """
    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        # Extract video ID
        if "youtu.be/" in url:
            video_id = url.split("youtu.be/")[1].split("?")[0]
        else:
            video_id = url.split("v=")[1].split("&")[0]

        # Get transcript
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=[lang])

        # Combine text
        text = " ".join([t["text"] for t in transcript_list])

        return text
    except ImportError:
        return "Error: youtube-transcript-api required. Install with: pip install youtube-transcript-api"
    except Exception as e:
        return f"Error: {e}"

@tool
async def youtube_get_metadata(url: str) -> str:
    """Get YouTube video metadata

    Args:
        url: YouTube URL

    Returns:
        JSON string with title, author, duration, views
    """
    try:
        import yt_dlp

        ydl_opts = {'quiet': True, 'no_warnings': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            metadata = {
                "title": info.get("title"),
                "author": info.get("uploader"),
                "duration": info.get("duration"),
                "views": info.get("view_count"),
                "upload_date": info.get("upload_date")
            }

            return json.dumps(metadata, indent=2)
    except ImportError:
        return json.dumps({"error": "yt-dlp required. Install with: pip install yt-dlp"})
    except Exception as e:
        return json.dumps({"error": str(e)})
```

#### 6.2 Pre-built Agent Templates

```python
# src/kagura/chat/templates.py

YOUTUBE_SUMMARIZER = """
from kagura import agent

@agent(tools=[youtube_get_transcript, youtube_get_metadata])
async def youtube_summarizer(url: str) -> str:
    '''Summarize YouTube video: {{ url }}

    Available tools:
    - youtube_get_transcript(url, lang): Get video transcript
    - youtube_get_metadata(url): Get video info
    '''
    pass
"""

CSV_ANALYZER = """
from kagura import agent

@agent
async def csv_analyzer(file_path: str, question: str) -> str:
    '''Analyze CSV file {{ file_path }} and answer: {{ question }}

    Use Python code execution to:
    1. Load CSV with pandas
    2. Analyze data
    3. Answer the question
    '''
    pass
"""

DOCKER_MANAGER = """
from kagura import agent

@agent(tools=[docker_run, docker_list_images])
async def docker_manager(task: str) -> str:
    '''Manage Docker: {{ task }}

    Available tools:
    - docker_run(image, command, volumes)
    - docker_list_images()
    '''
    pass
"""
```

---

## 📊 成功指標

### Phase 1完了時
- ✅ 全登録agent/toolを自動選択
- ✅ LLMベースのIntent Detection
- ✅ 20+ tests全パス

### Phase 2完了時
- ✅ Meta Agent自動生成動作
- ✅ pip依存関係自動インストール
- ✅ YouTube/CSV/Docker対応
- ✅ 15+ tests全パス

### Phase 3完了時
- ✅ 生成エージェントDB保存・再利用
- ✅ バージョン管理
- ✅ `kagura chat --list-agents`
- ✅ 10+ tests全パス

### Phase 4完了時
- ✅ Tab補完動作
- ✅ Ctrl+P: 履歴
- ✅ Markdown表示改善
- ✅ マルチバイト文字正しく表示
- ✅ 5+ UXテスト全パス

### Phase 5完了時
- ✅ Docker操作可能
- ✅ docker_run/build/list tools動作
- ✅ 10+ tests全パス

### Phase 6完了時
- ✅ YouTube transcript取得
- ✅ YouTube metadata取得
- ✅ Pre-built templates動作
- ✅ 10+ tests全パス

---

## 🚀 実装順序

### Week 1: Auto-Discovery & Selection
- AgentDiscovery実装
- LLMベースIntent Detection
- Chat Session統合
- 20+ tests

### Week 2: Meta Agent Auto-Generation
- TaskAnalyzer実装
- PackageManager実装
- Auto-generation flow
- 15+ tests

### Week 3: Agent Database
- AgentDatabase実装
- Version management
- CLI commands
- 10+ tests

### Week 4: UX Improvements
- Autocomplete
- Keybindings (Ctrl+P/N/R)
- Rich Markdown
- Multibyte fix
- 5+ UX tests

### Week 5: Docker Integration
- Docker tools (run/build/list)
- Docker-aware agent generation
- Safety checks
- 10+ tests

### Week 6: YouTube & Templates
- YouTube tools (transcript/metadata)
- Pre-built templates
- Integration tests
- 10+ tests

---

## 📋 チェックリスト

### Phase 1 完了条件
- [ ] AgentDiscovery実装
- [ ] LLM-based intent detection
- [ ] Chat session integration
- [ ] 20+ tests全パス
- [ ] ドキュメント

### Phase 2 完了条件
- [ ] TaskAnalyzer実装
- [ ] PackageManager実装（pip）
- [ ] Auto-generation flow
- [ ] 15+ tests全パス
- [ ] ドキュメント

### Phase 3 完了条件
- [ ] AgentDatabase実装
- [ ] Version management
- [ ] CLI: list/clean agents
- [ ] 10+ tests全パス
- [ ] ドキュメント

### Phase 4 完了条件
- [ ] Autocomplete (Tab)
- [ ] Keybindings (Ctrl+P/N/R)
- [ ] Rich Markdown improvements
- [ ] Multibyte character fix
- [ ] 5+ UX tests
- [ ] ドキュメント

### Phase 5 完了条件
- [ ] Docker tools (run/build/list)
- [ ] Docker integration in Meta Agent
- [ ] Safety checks
- [ ] 10+ tests全パス
- [ ] ドキュメント

### Phase 6 完了条件
- [ ] YouTube tools (transcript/metadata)
- [ ] Pre-built agent templates
- [ ] Integration tests
- [ ] 10+ tests全パス
- [ ] ドキュメント

---

## 🎓 参考資料

### YouTube API
- [youtube-transcript-api](https://github.com/jdepoix/youtube-transcript-api)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)

### Docker
- [Docker Python SDK](https://docker-py.readthedocs.io/)
- [Docker CLI](https://docs.docker.com/engine/reference/commandline/cli/)

### UX Libraries
- [prompt_toolkit](https://python-prompt-toolkit.readthedocs.io/)
- [Rich](https://rich.readthedocs.io/)
- [wcwidth](https://github.com/jquast/wcwidth)

---

## 🔒 セキュリティ考慮

### Package Installation
1. **Whitelist**: 安全なパッケージリスト（SAFE_PACKAGES）
2. **User Approval**: 全インストールで確認
3. **Dry Run**: `--dry-run`でインストール内容確認

### Docker Execution
1. **Read-only**: デフォルトで`--read-only`
2. **No privileged**: `--privileged`禁止
3. **Resource limits**: CPU/Memoryリミット

### Code Generation
1. **AST Validation**: 既存のASTValidator使用
2. **Sandbox**: CodeExecutor内で実行
3. **Review**: 生成コードをユーザーに表示

---

## 💡 追加提案

### 1. Smart Suggestions

```bash
[You] > I want to analyze sales.csv

💡 Suggestions:
  1. Create CSV analyzer agent (auto-install pandas)
  2. Use existing data_analyzer (if available)
  3. Manual analysis

Select [1]: _
```

### 2. Agent Marketplace Preview

```bash
[You] > Translate this to Japanese

💡 No translator found
💡 Options:
  1. Generate translator agent
  2. Search community agents (kagura-ai/community)
  3. Use default chat

Select [1]: _
```

### 3. Conversation Context

```bash
[You] > Analyze sales.csv
[AI] > (Creates csv_analyzer, shows results)

[You] > Create a chart
💡 Context: Previous task was CSV analysis
💡 Using csv_analyzer with chart generation
[AI] > (Chart created)
```

### 4. Batch Mode

```bash
$ kagura chat --batch tasks.txt

# tasks.txt:
# 1. Summarize https://youtu.be/xxx
# 2. Analyze data.csv
# 3. Deploy to Docker

# Auto-generates and executes all tasks
```

---

**このRFCにより、kagura chatは世界最強の自己拡張型AIチャットシステムになります！**
