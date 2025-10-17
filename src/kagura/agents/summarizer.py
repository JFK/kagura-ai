"""Summarizer agent for text summarization"""

from kagura import agent


@agent(model="gpt-5-mini", temperature=0.5)
async def SummarizeAgent(text: str, max_sentences: int = 3) -> str:
    """
    Summarize the following text in {{ max_sentences }} sentences or less:

    {{ text }}

    Provide a concise summary.
    """
    ...
