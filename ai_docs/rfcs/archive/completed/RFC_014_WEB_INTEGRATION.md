# RFC-014: Web Integration - Web検索とスクレイピング

## ステータス
- **状態**: Draft
- **作成日**: 2025-10-04
- **関連Issue**: #75
- **優先度**: High

## 概要

Kagura AIにWeb情報取得機能を追加します。リアルタイムのWeb検索、Webスクレイピング、ブラウザ自動化により、最新情報にアクセスできるようにします。

### 目標
- Web検索機能（Brave Search、DuckDuckGo）
- Webスクレイピング（BeautifulSoup）
- ブラウザ自動化（Playwright、オプション）
- エージェントへの簡単な統合（`@web.enable`）

### 非目標
- 違法なスクレイピング（robots.txt遵守）
- 完全なWebブラウザ機能

## モチベーション

### 現在の課題
1. **リアルタイム情報がない**
   - ニュース、天気、株価など最新情報が取得できない
   - LLMの知識カットオフ日以降の情報がない

2. **Web情報の活用不可**
   - 公式ドキュメントを参照できない
   - 競合分析ができない
   - 技術記事を検索できない

3. **手動コピペが必要**
   - Web情報を手動でコピーして貼り付け
   - 効率が悪い

### 解決するユースケース
- **最新ニュース**: 「今日のAIニュースは？」→リアルタイムWeb検索
- **技術調査**: 「FastAPIのOAuth2実装方法」→公式ドキュメント検索
- **競合分析**: 指定URLをスクレイピングして分析
- **価格比較**: 複数サイトから価格情報を収集

### なぜ今実装すべきか
- LLMとWeb情報の組み合わせは強力
- Brave Search API（無料枠あり）が利用可能
- RFC-002（Multimodal RAG）の基盤となる

## 設計

### 基本機能

#### 1. Web Search

```python
from kagura import web

# Web検索
results = await web.search("Python tutorial", max_results=5)

for r in results:
    print(f"{r.title}: {r.url}")
    print(f"  {r.snippet}")
```

#### 2. Web Scraping

```python
from kagura import web

# URLからコンテンツ取得
content = await web.fetch("https://example.com")

# CSS Selectorで抽出
articles = await web.scrape(
    url="https://news.example.com",
    selector="article.post"
)
```

#### 3. エージェント統合

```python
from kagura import agent, web

@agent(model="gpt-4o-mini")
@web.enable(search_engine="brave")
async def research_agent(topic: str) -> str:
    """
    Research {{ topic }} using web search.

    Available tools:
    - web.search(query, max_results=10)
    - web.fetch(url)
    """
    pass

result = await research_agent("AI trends 2025")
```

### 使用例

#### 例1: ニュース要約

```python
from kagura import agent, web

@agent(model="gpt-4o-mini")
@web.enable
async def news_summary(topic: str) -> str:
    """
    Search news about {{ topic }} and create summary.
    """
    # Web検索
    results = await web.search(f"{topic} news today", max_results=5)

    # 各記事を取得して要約
    articles = []
    for r in results:
        content = await web.fetch(r.url)
        articles.append({
            "title": r.title,
            "url": r.url,
            "content": content[:1000]
        })

    # 要約生成
    return f"Summarize these articles: {articles}"

# 使用
summary = await news_summary("AI research")
```

#### 例2: 技術ドキュメント検索

```python
@agent(model="gpt-4o")
@web.enable
async def tech_doc_search(framework: str, question: str) -> str:
    """
    Search {{ framework }} documentation for: {{ question }}
    """
    # 公式ドキュメント検索
    results = await web.search(
        f"{framework} documentation {question}",
        max_results=3
    )

    # 最も関連性の高いページを取得
    doc = await web.fetch(results[0].url)

    return f"""
    Found in {framework} documentation:
    {doc[:2000]}

    Answer to your question:
    """

# 使用
answer = await tech_doc_search("FastAPI", "OAuth2 authentication")
```

#### 例3: 競合分析

```python
@agent(model="gpt-4o")
@web.enable
async def competitor_analysis(url: str) -> dict:
    """
    Analyze competitor website: {{ url }}

    Extract:
    1. Products/Services
    2. Pricing
    3. Key features
    """
    # Webページ取得
    content = await web.fetch(url)

    # 構造化データ抽出
    products = await web.scrape(
        url=url,
        selector=".product-card"
    )

    return f"""
    Website: {url}
    Products found: {len(products)}
    Content: {content[:3000]}

    Provide competitive analysis.
    """
```

## 実装計画

### Phase 1: Web Search (v2.4.0)
- [ ] Brave Search API統合
- [ ] DuckDuckGo統合
- [ ] `web.search()` API
- [ ] `@web.enable` デコレータ
- [ ] 検索結果のキャッシング

### Phase 2: Web Scraping (v2.5.0)
- [ ] BeautifulSoup統合
- [ ] `web.fetch()` API
- [ ] `web.scrape()` API（CSS Selector）
- [ ] robots.txt遵守
- [ ] レート制限

### Phase 3: Browser Automation (v2.6.0)
- [ ] Playwright統合（オプション）
- [ ] Headlessブラウザ
- [ ] スクリーンショット
- [ ] JavaScript実行

## 技術的詳細

### 依存関係

```toml
[project.optional-dependencies]
web = [
    "httpx>=0.25.0",
    "beautifulsoup4>=4.12.0",
    "lxml>=4.9.3",
    "duckduckgo-search>=4.1.0",
]

browser = [
    "playwright>=1.40.0",  # オプション
]
```

### Web Search実装

```python
# src/kagura/web/search.py
from dataclasses import dataclass
import httpx

@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    source: str

class BraveSearch:
    """Brave Search API client"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("BRAVE_API_KEY")
        self.base_url = "https://api.search.brave.com/res/v1"

    async def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/web/search",
                headers={"X-Subscription-Token": self.api_key},
                params={"q": query, "count": max_results}
            )

            data = response.json()
            results = []

            for item in data.get("web", {}).get("results", []):
                results.append(SearchResult(
                    title=item["title"],
                    url=item["url"],
                    snippet=item["description"],
                    source="brave"
                ))

            return results

class DuckDuckGoSearch:
    """DuckDuckGo (no API key required)"""

    async def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        from duckduckgo_search import DDGS

        with DDGS() as ddgs:
            results = []
            for r in ddgs.text(query, max_results=max_results):
                results.append(SearchResult(
                    title=r["title"],
                    url=r["href"],
                    snippet=r["body"],
                    source="duckduckgo"
                ))

            return results

# 統合API
async def search(query: str, max_results: int = 10) -> list[SearchResult]:
    """Search the web (auto-select engine)"""
    if os.getenv("BRAVE_API_KEY"):
        engine = BraveSearch()
    else:
        engine = DuckDuckGoSearch()

    return await engine.search(query, max_results)
```

### Web Scraping実装

```python
# src/kagura/web/scraper.py
import httpx
from bs4 import BeautifulSoup

class WebScraper:
    """Web scraping with BeautifulSoup"""

    def __init__(self):
        self.user_agent = "Kagura-AI/2.0 (+https://github.com/user/kagura-ai)"

    async def fetch(self, url: str) -> str:
        """Fetch webpage content"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={"User-Agent": self.user_agent},
                follow_redirects=True
            )
            return response.text

    async def fetch_text(self, url: str) -> str:
        """Fetch and extract text content"""
        html = await self.fetch(url)
        soup = BeautifulSoup(html, 'lxml')

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        return soup.get_text(separator='\n', strip=True)

    async def scrape(self, url: str, selector: str) -> list:
        """Scrape with CSS selector"""
        html = await self.fetch(url)
        soup = BeautifulSoup(html, 'lxml')

        elements = soup.select(selector)
        return [elem.get_text(strip=True) for elem in elements]
```

### 設定

`~/.kagura/config.toml`:

```toml
[web]
default_search_engine = "brave"
cache_ttl = 3600  # 1 hour

[web.brave]
api_key = "${BRAVE_API_KEY}"

[web.scraping]
respect_robots_txt = true
user_agent = "Kagura-AI/2.0"
rate_limit_delay = 1.0  # seconds
max_retries = 3
```

## セキュリティ考慮事項

1. **robots.txt遵守**
   - スクレイピング前にrobots.txtをチェック
   - Disallowパスは回避

2. **レート制限**
   - デフォルト1秒の遅延
   - 連続アクセスの制限

3. **User-Agent**
   - 明示的なUser-Agent設定
   - 連絡先情報を含める

## テスト戦略

```python
# tests/web/test_search.py
@pytest.mark.asyncio
async def test_web_search():
    from kagura import web

    results = await web.search("Python programming", max_results=5)

    assert len(results) > 0
    assert all(r.url.startswith("http") for r in results)

# tests/web/test_scraper.py
@pytest.mark.asyncio
async def test_fetch_text():
    from kagura.web import WebScraper

    scraper = WebScraper()
    text = await scraper.fetch_text("https://example.com")

    assert "Example Domain" in text
```

## マイグレーション

既存ユーザーへの影響なし。新機能として追加：

```bash
# Web機能インストール
pip install kagura-ai[web]

# オプション: ブラウザ自動化
pip install kagura-ai[web,browser]
```

## ドキュメント

### 必要なドキュメント
1. Web Search Tutorial
2. Web Scraping Best Practices
3. Browser Automation Guide
4. robots.txt遵守ガイド

## 参考資料

- [Brave Search API](https://brave.com/search/api/)
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)
- [Playwright](https://playwright.dev/python/)

## 改訂履歴

- 2025-10-04: 初版作成（RFC-013から分離）
