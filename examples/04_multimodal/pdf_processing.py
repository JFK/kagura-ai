"""PDF Processing - Extract and analyze PDF content

This example demonstrates:
- Extracting text from PDFs
- Using AI to analyze PDF content
- Multimodal document processing
"""

import asyncio
from pathlib import Path
from kagura import agent


@agent
async def pdf_summarizer(pdf_path: str) -> str:
    """
    Summarize the PDF document at: {{ pdf_path }}

    Provide:
    - Main topic/theme
    - Key points (3-5 bullets)
    - Document type (article, report, etc.)
    """
    pass


@agent
async def pdf_qa(pdf_path: str, question: str) -> str:
    """
    Based on the PDF at {{ pdf_path }}, answer this question:
    {{ question }}

    Provide a clear, factual answer based on the document.
    """
    pass


@agent
async def pdf_extractor(pdf_path: str, extract_type: str) -> str:
    """
    Extract {{ extract_type }} from PDF: {{ pdf_path }}

    Types: titles, dates, names, technical_terms, statistics
    Return as a structured list.
    """
    pass


async def main():
    print("PDF Processing Demo")
    print("-" * 50)
    print("Note: This example requires actual PDF files")
    print("Place test PDFs in ./test_pdfs/ directory")
    print()

    # Example PDF path
    test_pdf = "./test_pdfs/sample.pdf"

    # Check if PDF exists
    if not Path(test_pdf).exists():
        print(f"⚠️  PDF not found: {test_pdf}")
        print("Please add test PDFs to run this example")
        return

    # Summarize PDF
    print("=== PDF Summary ===")
    summary = await pdf_summarizer(test_pdf)
    print(f"{summary}\n")

    # Ask questions about PDF
    print("=== Q&A ===")
    questions = [
        "What is the main conclusion?",
        "Who are the authors?",
        "What methodology was used?"
    ]

    for question in questions:
        answer = await pdf_qa(test_pdf, question)
        print(f"Q: {question}")
        print(f"A: {answer}\n")

    # Extract specific information
    print("=== Information Extraction ===")
    extractions = ["titles", "dates", "technical_terms"]

    for extract_type in extractions:
        result = await pdf_extractor(test_pdf, extract_type)
        print(f"{extract_type.title()}:")
        print(f"{result}\n")


if __name__ == "__main__":
    asyncio.run(main())
