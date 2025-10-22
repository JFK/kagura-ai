"""
Fact-checking tools for Kagura AI (MCP Built-in)

Web-based fact-checking capabilities using Brave Search.
"""

import json

from kagura import tool


@tool
async def fact_check_claim(claim: str, sources: list[str] | None = None) -> str:
    """Verify the accuracy of a specific claim using multiple web sources.

    Use this tool when:
    - User explicitly asks to fact-check a statement
    - A claim seems dubious and needs verification
    - Multiple sources are needed to confirm information
    - User asks "is this true?" or "verify this"
    - Checking controversial or disputed information

    Do NOT use for:
    - Simple factual questions (use brave_web_search instead)
    - Personal opinions or subjective matters
    - Future predictions
    - Questions with no factual answer

    Searches for evidence from multiple sources and provides
    a verdict with confidence level.

    Args:
        claim: The specific claim to fact-check (be precise and clear)
        sources: Optional list of source URLs for additional verification

    Returns:
        Fact-check result with verdict (TRUE/FALSE/MIXED/UNVERIFIED),
        confidence level, evidence, and summary

    Example:
        # Verify a factual claim
        claim="The Earth revolves around the Sun"

        # Check a disputed claim
        claim="Coffee prevents cancer"

        # With additional sources
        claim="Python 3.12 was released in 2023",
        sources=["https://www.python.org/downloads/"]
    """
    try:
        from kagura.core.llm import LLMConfig, call_llm
        from kagura.tools import brave_web_search
    except ImportError as e:
        return json.dumps(
            {
                "error": "Required dependencies not available",
                "details": str(e),
            },
            indent=2,
        )

    try:
        # Search for evidence
        search_results = await brave_web_search(claim, count=7)

        # Fetch additional sources if provided
        source_context = ""
        if sources:
            source_context = "\n\nAdditional sources provided:\n"
            for i, url in enumerate(sources, 1):
                source_context += f"{i}. {url}\n"

        # Use LLM to analyze
        config = LLMConfig(model="gpt-4o-mini", temperature=0.2)

        prompt = f"""Fact-check this claim using the provided web search results.

Claim: "{claim}"

Web search results:
{search_results}
{source_context}

Analyze the claim and provide a structured response:

1. **Verdict**: Choose one:
   - TRUE: Claim is supported by strong evidence
   - FALSE: Claim is contradicted by strong evidence
   - MIXED: Claim is partially true or context-dependent
   - UNVERIFIED: Insufficient evidence to determine

2. **Confidence**: 0-100% (how confident you are in the verdict)

3. **Evidence**: List 3-5 key facts that support your verdict.
   Include source URLs where possible.

4. **Summary**: 2-3 sentence explanation of your verdict.

Format your response as Markdown.
"""

        response = await call_llm(prompt, config)
        return str(response)

    except Exception as e:
        return json.dumps(
            {
                "error": f"Fact-check failed: {str(e)}",
                "claim": claim,
            },
            indent=2,
        )
