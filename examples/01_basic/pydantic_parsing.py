"""Pydantic Parsing - Structured data extraction

This example demonstrates:
- Using Pydantic models as return types
- Automatic JSON parsing and validation
- Type-safe AI responses
"""

import asyncio
from pydantic import BaseModel, Field
from kagura import agent


class Person(BaseModel):
    """Structured person information"""
    name: str = Field(description="Full name")
    age: int = Field(description="Age in years")
    occupation: str = Field(description="Job or profession")
    hobbies: list[str] = Field(description="List of hobbies")


class Sentiment(BaseModel):
    """Sentiment analysis result"""
    sentiment: str = Field(description="positive, negative, or neutral")
    confidence: float = Field(description="Confidence score 0-1")
    reasoning: str = Field(description="Brief explanation")


@agent
async def extract_person_info(text: str) -> Person:
    """
    Extract person information from this text:
    {{ text }}

    Return structured JSON with name, age, occupation, and hobbies.
    """
    pass


@agent
async def analyze_sentiment(text: str) -> Sentiment:
    """
    Analyze the sentiment of this text:
    "{{ text }}"

    Return JSON with sentiment (positive/negative/neutral),
    confidence (0-1), and reasoning.
    """
    pass


async def main():
    # Extract structured person information
    bio = """
    John Smith is a 32-year-old software engineer living in San Francisco.
    In his free time, he enjoys hiking, photography, and playing guitar.
    """

    person = await extract_person_info(bio)
    print("Extracted Person Info:")
    print(f"  Name: {person.name}")
    print(f"  Age: {person.age}")
    print(f"  Occupation: {person.occupation}")
    print(f"  Hobbies: {', '.join(person.hobbies)}")
    print()

    # Analyze sentiment
    review = "This product is amazing! It exceeded all my expectations."
    sentiment = await analyze_sentiment(review)
    print(f"Sentiment Analysis:")
    print(f"  Sentiment: {sentiment.sentiment}")
    print(f"  Confidence: {sentiment.confidence:.1%}")
    print(f"  Reasoning: {sentiment.reasoning}")


if __name__ == "__main__":
    asyncio.run(main())
