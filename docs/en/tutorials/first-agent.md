# Building Your First Agent: Review Analyzer

This tutorial guides you through creating a review analysis agent that processes customer reviews to extract sentiment, key points, and suggestions.

## Project Setup

1. Create the agent directory:
```bash
mkdir -p ~/.config/kagura/agents/review_analyzer
```

2. Initialize agent files:
```bash
touch ~/.config/kagura/agents/review_analyzer/agent.yml
touch ~/.config/kagura/agents/review_analyzer/state_model.yml
```

## State Model Configuration

Create state_model.yml:
```yaml
custom_models:
  - name: Sentiment
    fields:
      - name: score
        type: float
        description:
          - language: en
            text: Sentiment score from -1.0 (negative) to 1.0 (positive)
      - name: confidence
        type: float
        description:
          - language: en
            text: Confidence level of sentiment analysis (0.0 to 1.0)

  - name: ReviewPoint
    fields:
      - name: category
        type: str
        description:
          - language: en
            text: Category of the point (positive, negative, suggestion)
      - name: text
        type: str
        description:
          - language: en
            text: Description of the point
      - name: importance
        type: float
        description:
          - language: en
            text: Importance score (0.0 to 1.0)

  - name: AnalysisResult
    fields:
      - name: sentiment
        type: Sentiment
        description:
          - language: en
            text: Overall sentiment analysis
      - name: key_points
        type: List[ReviewPoint]
        description:
          - language: en
            text: List of extracted key points
      - name: suggestions
        type: List[str]
        description:
          - language: en
            text: Improvement suggestions based on the review

state_fields:
  - name: review_text
    type: str
    description:
      - language: en
        text: Input review text to analyze
  - name: analysis
    type: AnalysisResult
    description:
      - language: en
        text: Complete analysis result
```

## Agent Configuration

Create agent.yml:
```yaml
type: atomic
description:
  - language: en
    text: Analyzes customer reviews to extract sentiment, key points, and actionable suggestions

instructions:
  - language: en
    description: |
      Analyze customer reviews to:
      1. Determine overall sentiment with confidence score
      2. Extract key positive and negative points
      3. Generate actionable suggestions
      4. Assign importance scores to findings

      Maintain objectivity and focus on constructive feedback.

prompt:
  - language: en
    template: |
      Analyze this customer review:
      {review_text}

      Provide a structured analysis including:
      1. Overall sentiment (score and confidence)
      2. Key points (positive and negative)
      3. Actionable suggestions
      4. Importance scores for each point

      Focus on specific, actionable insights rather than general observations.

llm:
  model: openai/gpt-4o-mini
  max_tokens: 1024
  retry_count: 3

response_fields:
  - analysis
input_fields:
  - review_text
```

## Using the Agent

```python
from kagura.core.agent import Agent

async def analyze_review():
    # Create agent instance
    agent = Agent.assigner("review_analyzer")

    # Sample review
    review = """
    The product has great build quality and the battery life is impressive.
    However, the software is a bit confusing and customer support took too
    long to respond. Would be better with clearer documentation and faster
    support response times.
    """

    # Execute analysis
    result = await agent.execute({"review_text": review})

    # Access results
    analysis = result.analysis
    print(f"Sentiment Score: {analysis.sentiment.score}")
    print("\nKey Points:")
    for point in analysis.key_points:
        print(f"- [{point.category}] {point.text} (Importance: {point.importance})")
    print("\nSuggestions:")
    for suggestion in analysis.suggestions:
        print(f"- {suggestion}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(analyze_review())
```

## Testing

```python
import pytest
from kagura.core.agent import Agent

@pytest.mark.asyncio
async def test_review_analyzer():
    agent = Agent.assigner("review_analyzer")
    test_review = "Good product but needs improvement in user interface..."

    result = await agent.execute({"review_text": test_review})

    assert result.SUCCESS
    assert -1.0 <= result.analysis.sentiment.score <= 1.0
    assert 0.0 <= result.analysis.sentiment.confidence <= 1.0
    assert len(result.analysis.key_points) > 0
    assert len(result.analysis.suggestions) > 0

@pytest.mark.asyncio
async def test_empty_review():
    agent = Agent.assigner("review_analyzer")

    result = await agent.execute({"review_text": ""})
    assert not result.SUCCESS
    assert result.ERROR_MESSAGE
```
