"""Email Automation Example - AI-Powered Email Processing

This example demonstrates how to build an email automation system using
Kagura AI agents for classification, response generation, and routing.

Usage:
    # No extra dependencies needed (uses standard library)
    python examples/09_sdk_integration/email_automation.py
"""

import asyncio
from datetime import datetime
from enum import Enum

from kagura import agent
from pydantic import BaseModel

# ============================================
# Data Models
# ============================================


class EmailCategory(str, Enum):
    """Email category types"""

    SUPPORT = "support"
    SALES = "sales"
    BILLING = "billing"
    FEEDBACK = "feedback"
    SPAM = "spam"


class Priority(str, Enum):
    """Priority levels"""

    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EmailAnalysis(BaseModel):
    """Complete email analysis"""

    category: EmailCategory
    priority: Priority
    sentiment: str  # positive/neutral/negative
    key_topics: list[str]
    requires_human: bool
    estimated_response_time: str  # e.g., "within 1 hour"


class AutoResponse(BaseModel):
    """Auto-generated email response"""

    subject: str
    body: str
    send_now: bool  # True if safe to send, False if needs review
    confidence: float  # 0.0-1.0


# ============================================
# AI Agents
# ============================================


@agent(model="gpt-4o-mini")
async def email_analyzer(
    subject: str, body: str, sender: str
) -> EmailAnalysis:
    """Analyze incoming email

    From: {{ sender }}
    Subject: {{ subject }}
    Body: {{ body }}

    Analyze and determine:
    1. Category (support/sales/billing/feedback/spam)
    2. Priority (urgent/high/medium/low)
    3. Sentiment (positive/neutral/negative)
    4. Key topics discussed
    5. Whether human review is needed
    6. Estimated response time based on priority

    Return as JSON matching EmailAnalysis model.
    """
    pass


@agent(model="gpt-4o-mini")
async def response_generator(
    original_subject: str,
    original_body: str,
    category: str,
    sender_name: str,
) -> AutoResponse:
    """Generate email response

    Original email:
    Subject: {{ original_subject }}
    Body: {{ original_body }}
    Category: {{ category }}
    From: {{ sender_name }}

    Generate a professional, helpful response:
    1. Appropriate subject line (Re: ...)
    2. Personalized greeting
    3. Address the question/concern
    4. Provide next steps if applicable
    5. Professional closing

    Determine if safe to send automatically or needs human review.
    Provide confidence score (0.0-1.0).

    Return as JSON matching AutoResponse model.
    """
    pass


@agent(model="gpt-4o-mini")
async def email_summarizer(emails: list[str]) -> str:
    """Summarize multiple emails into daily digest

    Emails to summarize:
    {% for email in emails %}
    ---
    {{ email }}
    {% endfor %}

    Create a concise daily digest:
    1. Group by category
    2. Highlight urgent items
    3. Summarize key themes
    4. List action items

    Return formatted markdown summary.
    """
    pass


# ============================================
# Email Automation Workflows
# ============================================


async def process_incoming_email(
    subject: str, body: str, sender: str
) -> dict:
    """
    Process single incoming email with AI

    Args:
        subject: Email subject
        body: Email body
        sender: Sender email address

    Returns:
        Processing results with analysis and suggested response
    """
    print(f"\n📧 Processing email from: {sender}")
    print(f"   Subject: {subject}")

    # Step 1: Analyze email
    analysis = await email_analyzer(subject, body, sender)
    print("\n📊 Analysis:")
    print(f"   Category: {analysis.category.value}")
    print(f"   Priority: {analysis.priority.value}")
    print(f"   Sentiment: {analysis.sentiment}")
    print(f"   Topics: {', '.join(analysis.key_topics)}")

    # Step 2: Generate response (if not spam)
    response = None
    if analysis.category != EmailCategory.SPAM:
        sender_name = sender.split("@")[0]  # Simple name extraction
        response = await response_generator(
            original_subject=subject,
            original_body=body,
            category=analysis.category.value,
            sender_name=sender_name,
        )

        print("\n✉️ Generated Response:")
        print(f"   Subject: {response.subject}")
        print(f"   Auto-send: {response.send_now}")
        print(f"   Confidence: {response.confidence:.2%}")

    return {
        "analysis": analysis,
        "response": response,
        "timestamp": datetime.now().isoformat(),
    }


async def batch_process_emails(emails: list[dict]) -> dict:
    """
    Process multiple emails in batch

    Args:
        emails: List of email dicts with subject, body, sender

    Returns:
        Batch processing results
    """
    print(f"\n🔄 Processing {len(emails)} emails in batch...")

    # Process all emails concurrently
    tasks = [
        process_incoming_email(e["subject"], e["body"], e["sender"])
        for e in emails
    ]
    results = await asyncio.gather(*tasks)

    # Categorize results
    urgent = [r for r in results if r["analysis"].priority == Priority.URGENT]
    spam = [r for r in results if r["analysis"].category == EmailCategory.SPAM]
    auto_send = [
        r for r in results if r["response"] and r["response"].send_now
    ]

    print("\n📊 Batch Processing Complete:")
    print(f"   Total: {len(results)}")
    print(f"   Urgent: {len(urgent)}")
    print(f"   Spam: {len(spam)}")
    print(f"   Auto-sendable: {len(auto_send)}")

    return {
        "total": len(results),
        "results": results,
        "urgent": urgent,
        "spam": spam,
        "auto_send": auto_send,
    }


async def create_daily_digest(emails: list[dict]) -> str:
    """
    Create daily email digest

    Args:
        emails: List of processed emails

    Returns:
        Formatted digest text
    """
    # Format emails for summarization
    email_texts = [
        f"From: {e['sender']}\nSubject: {e['subject']}\n{e['body']}"
        for e in emails
    ]

    digest = await email_summarizer(email_texts)
    return digest


# ============================================
# Example Usage
# ============================================


async def main():
    """Run email automation examples"""
    print("=" * 60)
    print("Kagura AI - Email Automation Examples")
    print("=" * 60)

    # Sample emails
    test_emails = [
        {
            "subject": "URGENT: Production server down",
            "body": "Our main server crashed 10 minutes ago. Customers cannot access the service. Need immediate help!",
            "sender": "ops@company.com",
        },
        {
            "subject": "Question about Enterprise pricing",
            "body": "Hi, we're a team of 50 looking to upgrade. What's the best plan for us? Can we schedule a demo?",
            "sender": "sales@prospect.com",
        },
        {
            "subject": "Love your product!",
            "body": "Just wanted to say your tool saved me hours today. The new feature is amazing. Keep up the great work!",
            "sender": "happy@user.com",
        },
        {
            "subject": "Invoice #12345 question",
            "body": "I see a duplicate charge on invoice #12345. Can you clarify what happened?",
            "sender": "billing@customer.com",
        },
    ]

    # Example 1: Process single email
    print("\n" + "=" * 60)
    print("Example 1: Single Email Processing")
    print("=" * 60)
    result = await process_incoming_email(
        subject=test_emails[0]["subject"],
        body=test_emails[0]["body"],
        sender=test_emails[0]["sender"],
    )

    # Example 2: Batch processing
    print("\n" + "=" * 60)
    print("Example 2: Batch Email Processing")
    print("=" * 60)
    batch_results = await batch_process_emails(test_emails)

    # Example 3: Daily digest
    print("\n" + "=" * 60)
    print("Example 3: Daily Email Digest")
    print("=" * 60)
    digest = await create_daily_digest(test_emails)
    print("\n📰 Daily Digest:")
    print(digest)

    print("\n" + "=" * 60)
    print("✅ All examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
