"""FastAPI Integration Example - AI-Powered REST API

This example demonstrates how to integrate Kagura AI agents into a FastAPI
application to create intelligent REST API endpoints.

Usage:
    # Install dependencies
    pip install -e "examples/[sdk]"

    # Run server
    uvicorn examples.09_sdk_integration.fastapi_endpoint:app --reload

    # Test endpoint
    curl -X POST http://localhost:8000/api/support \
         -H "Content-Type: application/json" \
         -d '{"question": "How do I reset my password?"}'
"""


from fastapi import FastAPI, HTTPException
from kagura import agent
from pydantic import BaseModel

# ============================================
# FastAPI App Setup
# ============================================

app = FastAPI(
    title="AI Support API",
    description="Customer support API powered by Kagura AI",
    version="3.0.0",
)


# ============================================
# Request/Response Models
# ============================================


class SupportRequest(BaseModel):
    """Customer support question"""

    question: str
    context: str | None = None


class SupportResponse(BaseModel):
    """AI-generated support response"""

    answer: str
    confidence: str
    helpful_links: list[str]


# ============================================
# AI Agents
# ============================================


@agent(model="gpt-4o-mini")
async def support_agent(question: str, context: str | None = None) -> SupportResponse:
    """Answer customer support question: {{ question }}

    {% if context %}
    Additional context: {{ context }}
    {% endif %}

    Provide:
    1. Clear, helpful answer
    2. Confidence level (high/medium/low)
    3. Relevant help documentation links

    Return as JSON matching SupportResponse model.
    """
    pass


@agent(model="gpt-4o-mini", enable_memory=True)
async def sentiment_analyzer(text: str) -> dict[str, str | float]:
    """Analyze sentiment of text: {{ text }}

    Return JSON with:
    - sentiment: positive/negative/neutral
    - score: confidence score (0.0-1.0)
    - keywords: list of important keywords
    """
    pass


# ============================================
# API Endpoints
# ============================================


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "service": "AI Support API", "version": "3.0.0"}


@app.post("/api/support", response_model=SupportResponse)
async def handle_support(request: SupportRequest):
    """
    Handle customer support question with AI

    Args:
        request: Support question with optional context

    Returns:
        AI-generated support response with confidence and links
    """
    try:
        response = await support_agent(
            question=request.question, context=request.context
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI processing failed: {str(e)}")


@app.post("/api/sentiment")
async def analyze_sentiment(text: str):
    """
    Analyze sentiment of customer feedback

    Args:
        text: Text to analyze

    Returns:
        Sentiment analysis results
    """
    try:
        result = await sentiment_analyzer(text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


# ============================================
# Example Usage (if run directly)
# ============================================

if __name__ == "__main__":
    import uvicorn

    print("Starting AI Support API...")
    print("Open http://localhost:8000/docs for interactive API documentation")

    uvicorn.run(app, host="0.0.0.0", port=8000)
