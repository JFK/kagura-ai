"""Data Pipeline Integration Example - AI-Powered ETL

This example demonstrates how to use Kagura AI agents in data processing
pipelines for data enrichment, cleaning, and transformation.

Usage:
    # Install dependencies
    pip install -e "examples/[sdk]"

    # Run pipeline
    python examples/09_sdk_integration/data_pipeline.py
"""

import asyncio

import pandas as pd
from kagura import agent
from pydantic import BaseModel

# ============================================
# Data Models
# ============================================


class CompanyProfile(BaseModel):
    """Enriched company profile"""

    name: str
    industry: str
    size: str  # small/medium/large/enterprise
    location: str
    description: str
    founded_year: int | None = None
    employee_count: str | None = None


class EmailClassification(BaseModel):
    """Email classification result"""

    category: str  # support/sales/billing/spam
    priority: str  # high/medium/low
    sentiment: str  # positive/neutral/negative
    requires_human: bool
    suggested_response: str | None = None


# ============================================
# AI Agents for Data Processing
# ============================================


@agent(model="gpt-4o-mini", tools=["web_search"])
async def company_enricher(company_name: str) -> CompanyProfile:
    """Enrich company data for: {{ company_name }}

    Use web_search(query) to find current information about the company.

    Extract and return:
    - Industry sector
    - Company size (small/medium/large/enterprise)
    - Headquarters location
    - Brief description
    - Founded year (if available)
    - Approximate employee count

    Return as structured JSON matching CompanyProfile model.
    """
    pass


@agent(model="gpt-4o-mini")
async def email_classifier(email_body: str, subject: str) -> EmailClassification:
    """Classify customer email

    Subject: {{ subject }}
    Body: {{ email_body }}

    Categorize into: support/sales/billing/spam
    Assess priority: high/medium/low
    Analyze sentiment: positive/neutral/negative
    Determine if human review is needed
    Suggest automated response if appropriate

    Return as JSON matching EmailClassification model.
    """
    pass


@agent(model="gpt-4o-mini")
async def data_cleaner(text: str, field_type: str) -> str:
    """Clean and standardize data field: {{ text }}

    Field type: {{ field_type }}

    Rules:
    - Remove unnecessary whitespace
    - Fix common typos
    - Standardize format (e.g., phone numbers, emails)
    - Handle missing/null values appropriately

    Return cleaned text only.
    """
    pass


# ============================================
# Pipeline Functions
# ============================================


async def enrich_companies(company_names: list[str]) -> pd.DataFrame:
    """
    Enrich company data using AI web search

    Args:
        company_names: List of company names to enrich

    Returns:
        DataFrame with enriched company profiles
    """
    print(f"\n🔍 Enriching {len(company_names)} companies...")

    # Process in parallel for speed
    tasks = [company_enricher(name) for name in company_names]
    profiles = await asyncio.gather(*tasks)

    # Convert to DataFrame
    df = pd.DataFrame([p.model_dump() for p in profiles])
    print(f"✅ Enrichment complete: {len(df)} profiles")

    return df


async def classify_emails(emails: list[dict[str, str]]) -> pd.DataFrame:
    """
    Classify customer emails in bulk

    Args:
        emails: List of dicts with 'subject' and 'body'

    Returns:
        DataFrame with classification results
    """
    print(f"\n📧 Classifying {len(emails)} emails...")

    # Classify each email
    tasks = [
        email_classifier(email["body"], email["subject"]) for email in emails
    ]
    classifications = await asyncio.gather(*tasks)

    # Convert to DataFrame
    df = pd.DataFrame([c.model_dump() for c in classifications])
    print("✅ Classification complete")

    return df


async def clean_dataset(df: pd.DataFrame, field_mappings: dict[str, str]) -> pd.DataFrame:
    """
    Clean dataset fields using AI

    Args:
        df: DataFrame to clean
        field_mappings: Dict mapping column names to field types

    Returns:
        Cleaned DataFrame
    """
    print(f"\n🧹 Cleaning {len(df)} rows, {len(field_mappings)} fields...")

    cleaned_df = df.copy()

    for column, field_type in field_mappings.items():
        if column not in df.columns:
            continue

        print(f"  Cleaning: {column} ({field_type})")

        # Clean each value
        tasks = [
            data_cleaner(str(value), field_type)
            for value in df[column]
        ]
        cleaned_values = await asyncio.gather(*tasks)

        cleaned_df[column] = cleaned_values

    print("✅ Cleaning complete")
    return cleaned_df


# ============================================
# Example Pipeline Execution
# ============================================


async def run_company_enrichment_pipeline():
    """Example: Enrich company data for lead scoring"""
    companies = [
        "Anthropic",
        "OpenAI",
        "Google DeepMind",
    ]

    enriched_df = await enrich_companies(companies)
    print("\n📊 Enriched Company Data:")
    print(enriched_df.to_string())

    # Save to CSV
    enriched_df.to_csv("enriched_companies.csv", index=False)
    print("\n💾 Saved to: enriched_companies.csv")


async def run_email_classification_pipeline():
    """Example: Classify customer emails for routing"""
    emails = [
        {
            "subject": "Urgent: Cannot access my account",
            "body": "I've been locked out for 2 hours. This is critical!",
        },
        {
            "subject": "Interested in Enterprise plan",
            "body": "Our company is looking to upgrade. Can we schedule a call?",
        },
        {
            "subject": "Invoice question",
            "body": "I see a duplicate charge on my latest invoice. Can you clarify?",
        },
    ]

    classified_df = await classify_emails(emails)
    print("\n📊 Email Classifications:")
    print(classified_df.to_string())

    # Filter high-priority items
    urgent = classified_df[classified_df["priority"] == "high"]
    print(f"\n⚠️ {len(urgent)} urgent emails require immediate attention")


async def run_data_cleaning_pipeline():
    """Example: Clean messy user data"""
    # Sample messy data
    data = {
        "name": ["  John  Doe ", "jane   smith", "Bob  WILSON  "],
        "email": ["john@example.com  ", "  jane@test.com", "bob@COMPANY.COM"],
        "phone": ["555-1234", "(555) 5678", "555.9012"],
    }

    df = pd.DataFrame(data)
    print("\n📊 Original Data:")
    print(df.to_string())

    # Clean with AI
    field_mappings = {
        "name": "person_name",
        "email": "email_address",
        "phone": "phone_number",
    }

    cleaned_df = await clean_dataset(df, field_mappings)
    print("\n📊 Cleaned Data:")
    print(cleaned_df.to_string())


async def main():
    """Run all pipeline examples"""
    print("=" * 60)
    print("Kagura AI - Data Pipeline Integration Examples")
    print("=" * 60)

    # Run pipelines
    await run_company_enrichment_pipeline()
    print("\n" + "=" * 60 + "\n")

    await run_email_classification_pipeline()
    print("\n" + "=" * 60 + "\n")

    await run_data_cleaning_pipeline()
    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
