"""
Preset agents for common tasks in Chat REPL
"""

from kagura import agent


@agent(model="gpt-4o-mini", temperature=0.3)
async def TranslateAgent(text: str, target_language: str = "ja") -> str:
    """
    Translate the following text to {{ target_language }}:

    {{ text }}

    Provide only the translation, without explanations.
    """
    ...


@agent(model="gpt-4o-mini", temperature=0.5)
async def SummarizeAgent(text: str, max_sentences: int = 3) -> str:
    """
    Summarize the following text in {{ max_sentences }} sentences or less:

    {{ text }}

    Provide a concise summary.
    """
    ...


@agent(model="gpt-4o", temperature=0.3)
async def CodeReviewAgent(code: str, language: str = "python") -> str:
    """
    Review the following {{ language }} code and provide feedback:

    ```{{ language }}
    {{ code }}
    ```

    Provide:
    1. Issues found (bugs, anti-patterns, potential errors)
    2. Suggestions for improvement
    3. Best practices recommendations

    Format your response in markdown.
    """
    ...
