"""Code Review Agent - Automated code review system

This example demonstrates:
- Multi-aspect code review
- Security analysis
- Performance suggestions
- Best practices checking
"""

import asyncio

from kagura import LLMConfig, agent
from kagura.core.parallel import parallel_gather
from pydantic import BaseModel, Field


# Review models
class SecurityIssue(BaseModel):
    """Security issue found in code"""
    severity: str = Field(description="critical, high, medium, low")
    line_number: int = Field(description="Line number")
    description: str = Field(description="Issue description")
    fix_suggestion: str = Field(description="How to fix")


class PerformanceIssue(BaseModel):
    """Performance issue"""
    impact: str = Field(description="high, medium, low")
    location: str = Field(description="Where in code")
    description: str = Field(description="Issue description")
    optimization: str = Field(description="Optimization suggestion")


class CodeReview(BaseModel):
    """Complete code review"""
    overall_quality: str = Field(description="excellent, good, fair, poor")
    security_issues: list[SecurityIssue]
    performance_issues: list[PerformanceIssue]
    style_suggestions: list[str]
    best_practices: list[str]
    summary: str = Field(description="Overall review summary")


# Config
config = LLMConfig(model="gpt-4o-mini", temperature=0.3)  # Low temp for consistency


# Review agents
@agent(config=config)
async def security_reviewer(code: str) -> list[SecurityIssue]:
    """
    Review this code for security issues:

    ```python
    {{ code }}
    ```

    Find vulnerabilities like:
    - SQL injection
    - XSS vulnerabilities
    - Insecure data handling
    - Authentication issues

    Return list of SecurityIssues (empty list if none found).
    """
    pass


@agent(config=config)
async def performance_reviewer(code: str) -> list[PerformanceIssue]:
    """
    Review this code for performance issues:

    ```python
    {{ code }}
    ```

    Look for:
    - Inefficient algorithms
    - Unnecessary loops
    - Memory leaks
    - Database query issues

    Return list of PerformanceIssues (empty list if none found).
    """
    pass


@agent(config=config)
async def style_reviewer(code: str) -> list[str]:
    """
    Review this code for style issues:

    ```python
    {{ code }}
    ```

    Check for:
    - PEP 8 compliance
    - Naming conventions
    - Code organization
    - Documentation

    Return list of style suggestions (empty list if none).
    """
    pass


@agent(config=config)
async def best_practices_reviewer(code: str) -> list[str]:
    """
    Review this code for best practices:

    ```python
    {{ code }}
    ```

    Check for:
    - Error handling
    - Type hints
    - Function decomposition
    - Design patterns

    Return list of best practice recommendations.
    """
    pass


@agent(config=config)
async def quality_assessor(code: str) -> str:
    """
    Assess overall code quality of:

    ```python
    {{ code }}
    ```

    Return: excellent, good, fair, or poor with brief reasoning.
    """
    pass


async def review_code(code: str, file_name: str) -> CodeReview:
    """Perform comprehensive code review"""
    print(f"\n{'=' * 60}")
    print(f"Reviewing: {file_name}")
    print(f"{'=' * 60}")
    print("\nCode:")
    print(code)
    print(f"\n{'─' * 60}")

    # Parallel review (all aspects simultaneously)
    print("\n[Analyzing code in parallel...]")

    (
        security_issues,
        performance_issues,
        style_suggestions,
        best_practices,
        quality
    ) = await parallel_gather(
        security_reviewer(code),
        performance_reviewer(code),
        style_reviewer(code),
        best_practices_reviewer(code),
        quality_assessor(code)
    )

    print("✓ Review complete")

    # Extract quality string from LLMResponse
    quality_str = str(quality).split(',')[0].strip() if ',' in str(quality) else str(quality).strip()

    # Generate summary
    summary = f"Overall quality: {quality_str}. "
    if security_issues:
        summary += f"Found {len(security_issues)} security issues. "
    if performance_issues:
        summary += f"Found {len(performance_issues)} performance issues. "

    # Create review object
    review = CodeReview(
        overall_quality=quality_str,
        security_issues=security_issues,
        performance_issues=performance_issues,
        style_suggestions=style_suggestions,
        best_practices=best_practices,
        summary=summary
    )

    return review


def print_review(review: CodeReview):
    """Print formatted review"""
    print(f"\n{'=' * 60}")
    print("CODE REVIEW RESULTS")
    print(f"{'=' * 60}")

    print(f"\nOverall Quality: {review.overall_quality.upper()}")
    print(f"\n{review.summary}")

    if review.security_issues:
        print(f"\n⚠️  Security Issues ({len(review.security_issues)}):")
        for issue in review.security_issues:
            print(f"\n  [{issue.severity.upper()}] Line {issue.line_number}")
            print(f"  Issue: {issue.description}")
            print(f"  Fix: {issue.fix_suggestion}")

    if review.performance_issues:
        print(f"\n🐌 Performance Issues ({len(review.performance_issues)}):")
        for issue in review.performance_issues:
            print(f"\n  [{issue.impact.upper()}] {issue.location}")
            print(f"  Issue: {issue.description}")
            print(f"  Optimization: {issue.optimization}")

    if review.style_suggestions:
        print(f"\n📝 Style Suggestions ({len(review.style_suggestions)}):")
        for suggestion in review.style_suggestions:
            print(f"  - {suggestion}")

    if review.best_practices:
        print(f"\n✨ Best Practices ({len(review.best_practices)}):")
        for practice in review.best_practices:
            print(f"  - {practice}")


async def main():
    print("Code Review Agent - Automated Review System")
    print("=" * 60)

    # Code samples to review
    code_samples = [
        {
            "file": "auth.py",
            "code": """
def login(username, password):
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    result = db.execute(query)
    return result
"""
        },
        {
            "file": "process_data.py",
            "code": """
def process_items(items):
    result = []
    for item in items:
        for i in range(len(items)):
            if items[i] == item:
                result.append(item * 2)
    return result
"""
        },
        {
            "file": "calculator.py",
            "code": """
def calculate_average(numbers: list[float]) -> float:
    '''Calculate average of a list of numbers'''
    if not numbers:
        raise ValueError("Empty list")

    total = sum(numbers)
    return total / len(numbers)
"""
        }
    ]

    # Review each sample
    for sample in code_samples:
        review = await review_code(sample["code"], sample["file"])
        print_review(review)

    print("\n" + "=" * 60)
    print("Code Review Agent Features:")
    print("- Parallel review (security, performance, style)")
    print("- Security vulnerability detection")
    print("- Performance optimization suggestions")
    print("- Style and best practices checking")
    print("- Structured, actionable feedback")


if __name__ == "__main__":
    asyncio.run(main())
