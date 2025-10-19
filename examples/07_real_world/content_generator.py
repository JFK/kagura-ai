"""Content Generator - Blog and article generation system

This example demonstrates:
- Multi-stage content creation
- SEO optimization
- Outline generation
- Content expansion
- Editing and refinement
"""

import asyncio
from pydantic import BaseModel, Field
from kagura import agent, LLMConfig
from kagura.core.memory import MemoryRAG


# Content models
class ContentOutline(BaseModel):
    """Article outline"""
    title: str = Field(description="Article title")
    hook: str = Field(description="Opening hook/intro")
    sections: list[str] = Field(description="Section titles")
    conclusion: str = Field(description="Conclusion summary")
    target_word_count: int = Field(description="Target words")


class SEOAnalysis(BaseModel):
    """SEO analysis"""
    keywords: list[str] = Field(description="Primary keywords")
    meta_description: str = Field(description="Meta description")
    slug: str = Field(description="URL slug")
    readability_score: str = Field(description="easy, medium, advanced")
    suggestions: list[str] = Field(description="SEO improvements")


class Article(BaseModel):
    """Complete article"""
    title: str
    content: str
    word_count: int
    seo: SEOAnalysis
    tags: list[str]


# Config
config = LLMConfig(model="gpt-4o-mini", temperature=0.7)

# Content memory for research
content_research = MemoryRAG(collection_name="content_generator")


# Content agents
@agent(config=config)
async def idea_generator(topic: str, angle: str) -> list[str]:
    """
    Generate 5 article ideas for:
    Topic: {{ topic }}
    Angle: {{ angle }}

    Return list of creative, engaging article titles.
    """
    pass


@agent(config=config)
async def outline_creator(title: str, target_words: int) -> ContentOutline:
    """
    Create detailed outline for: "{{ title }}"
    Target word count: {{ target_words }}

    IMPORTANT: sections must be a list of STRING titles ONLY, not objects.
    Example: ["Introduction to Topic", "Key Concepts", "Practical Examples", "Conclusion"]

    Return JSON with:
    - title: string
    - hook: string (opening sentence)
    - sections: list of STRING section titles (3-5 items)
    - conclusion: string (summary)
    - target_word_count: integer
    """
    pass


@agent(config=config)
async def section_writer(section_title: str, context: str) -> str:
    """
    Write section: "{{ section_title }}"

    Context:
    {{ context }}

    Write 2-3 engaging paragraphs (200-300 words).
    Include specific examples and actionable insights.
    """
    pass


@agent(config=config)
async def intro_writer(title: str, hook: str, outline: str) -> str:
    """
    Write engaging introduction for: "{{ title }}"

    Hook: {{ hook }}
    Outline: {{ outline }}

    Write compelling intro (100-150 words) that:
    - Grabs attention
    - Sets up the article
    - Makes reader want to continue
    """
    pass


@agent(config=config)
async def conclusion_writer(title: str, summary: str) -> str:
    """
    Write conclusion for: "{{ title }}"

    Summary: {{ summary }}

    Write strong conclusion (100-150 words) that:
    - Summarizes key points
    - Provides call-to-action
    - Leaves lasting impression
    """
    pass


@agent(config=config)
async def seo_optimizer(title: str, content: str) -> SEOAnalysis:
    """
    Optimize for SEO:

    Title: {{ title }}
    Content: {{ content[:500] }}...

    Return SEO analysis with:
    - Primary keywords (5-7)
    - Meta description (150-160 chars)
    - URL slug
    - Readability score
    - Improvement suggestions
    """
    pass


@agent(config=config)
async def editor(content: str) -> str:
    """
    Edit and improve this content:

    {{ content }}

    Fix:
    - Grammar and spelling
    - Flow and transitions
    - Clarity and conciseness
    - Tone consistency

    Return polished version.
    """
    pass


# Content generation workflow
async def generate_article(
    topic: str,
    angle: str,
    target_words: int = 800
) -> Article:
    """Generate complete article"""
    print(f"\n{'=' * 60}")
    print(f"Generating article on: {topic}")
    print(f"Angle: {angle}")
    print(f"{'=' * 60}")

    # Step 1: Generate ideas
    print("\n[Step 1] Generating ideas...")
    ideas = await idea_generator(topic, angle)
    selected_title = ideas[0]
    print(f"✓ Selected: {selected_title}")

    # Step 2: Create outline
    print("\n[Step 2] Creating outline...")
    outline = await outline_creator(selected_title, target_words)
    print(f"✓ Outline with {len(outline.sections)} sections")

    # Step 3: Write introduction
    print("\n[Step 3] Writing introduction...")
    outline_text = "\n".join(f"- {s}" for s in outline.sections)
    intro = await intro_writer(selected_title, outline.hook, outline_text)
    print("✓ Introduction written")

    # Step 4: Write sections
    print("\n[Step 4] Writing sections...")
    sections = []
    for i, section_title in enumerate(outline.sections, 1):
        context = f"Article: {selected_title}\nPrevious sections: {', '.join(sections)}"
        section_content = await section_writer(section_title, context)
        sections.append(section_content)
        print(f"✓ Section {i}/{len(outline.sections)} written")

    # Step 5: Write conclusion
    print("\n[Step 5] Writing conclusion...")
    conclusion = await conclusion_writer(selected_title, outline.conclusion)
    print("✓ Conclusion written")

    # Step 6: Combine and edit
    print("\n[Step 6] Editing content...")
    full_content = f"{intro}\n\n"
    for i, (title, content) in enumerate(zip(outline.sections, sections)):
        full_content += f"## {title}\n\n{content}\n\n"
    full_content += f"## Conclusion\n\n{conclusion}"

    edited_content = await editor(full_content)
    print("✓ Content edited")

    # Step 7: SEO optimization
    print("\n[Step 7] Optimizing for SEO...")
    seo = await seo_optimizer(selected_title, edited_content)
    print(f"✓ SEO optimized ({len(seo.keywords)} keywords)")

    # Create article
    article = Article(
        title=selected_title,
        content=edited_content,
        word_count=len(edited_content.split()),
        seo=seo,
        tags=seo.keywords[:5]
    )

    return article


def print_article(article: Article):
    """Print formatted article"""
    print(f"\n{'=' * 60}")
    print(f"GENERATED ARTICLE")
    print(f"{'=' * 60}")

    print(f"\nTitle: {article.title}")
    print(f"Word Count: {article.word_count}")
    print(f"Tags: {', '.join(article.tags)}")

    print(f"\n{'─' * 60}")
    print("SEO ANALYSIS")
    print(f"{'─' * 60}")
    print(f"Keywords: {', '.join(article.seo.keywords)}")
    print(f"Slug: {article.seo.slug}")
    print(f"Meta: {article.seo.meta_description}")
    print(f"Readability: {article.seo.readability_score}")

    print(f"\n{'─' * 60}")
    print("CONTENT (Preview)")
    print(f"{'─' * 60}")
    # Show first 500 characters
    preview = article.content[:500]
    print(preview + "...\n")


async def main():
    print("Content Generator - Blog/Article Generation System")
    print("=" * 60)

    # Content requests
    requests = [
        {
            "topic": "Python programming",
            "angle": "beginners guide",
            "words": 800
        },
        {
            "topic": "AI agent frameworks",
            "angle": "comparison and best practices",
            "words": 1000
        }
    ]

    # Generate articles
    for req in requests:
        article = await generate_article(
            req["topic"],
            req["angle"],
            req["words"]
        )
        print_article(article)

    print("\n" + "=" * 60)
    print("Content Generator Features:")
    print("- Multi-stage content creation")
    print("- SEO optimization")
    print("- Automated editing")
    print("- Structured workflow")
    print("- Professional quality output")


if __name__ == "__main__":
    asyncio.run(main())
