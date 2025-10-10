"""Conditional Workflow Example

This example demonstrates conditional branching in workflows based on
agent outputs, user input, or runtime conditions.
"""

import asyncio
from kagura import agent, workflow, conditional


# Define workflow agents
@agent(model="gpt-4o-mini")
async def sentiment_analyzer(text: str) -> str:
    """Analyze sentiment of: {{ text }}. Return only 'positive', 'negative', or 'neutral'."""
    pass


@agent(model="gpt-4o-mini")
async def positive_responder(text: str) -> str:
    """Respond positively to: {{ text }}"""
    pass


@agent(model="gpt-4o-mini")
async def negative_responder(text: str) -> str:
    """Respond empathetically to: {{ text }}"""
    pass


@agent(model="gpt-4o-mini")
async def neutral_responder(text: str) -> str:
    """Respond neutrally to: {{ text }}"""
    pass


@agent(model="gpt-4o-mini")
async def content_classifier(text: str) -> str:
    """Classify content type: {{ text }}. Return 'question', 'statement', or 'request'."""
    pass


@agent(model="gpt-4o-mini")
async def question_handler(question: str) -> str:
    """Answer question: {{ question }}"""
    pass


@agent(model="gpt-4o-mini")
async def statement_handler(statement: str) -> str:
    """Acknowledge statement: {{ statement }}"""
    pass


@agent(model="gpt-4o-mini")
async def request_handler(request: str) -> str:
    """Process request: {{ request }}"""
    pass


async def main():
    """Demonstrate conditional workflows."""
    print("=== Conditional Workflow Examples ===\n")

    # Example 1: Simple sentiment-based branching
    print("1. Sentiment-Based Branching")
    print("-" * 50)

    @workflow
    async def sentiment_workflow(text: str) -> str:
        """Process text based on sentiment."""
        # Analyze sentiment
        sentiment = await sentiment_analyzer(text)
        sentiment = sentiment.strip().lower()

        # Branch based on sentiment
        if "positive" in sentiment:
            return await positive_responder(text)
        elif "negative" in sentiment:
            return await negative_responder(text)
        else:
            return await neutral_responder(text)

    test_texts = [
        "I love this product!",
        "This is terrible.",
        "The sky is blue.",
    ]

    for text in test_texts:
        result = await sentiment_workflow(text)
        print(f"Input: {text}")
        print(f"Response: {result}\n")

    # Example 2: Content type classification
    print("2. Content Type Classification")
    print("-" * 50)

    @workflow
    async def content_workflow(text: str) -> str:
        """Route content based on type."""
        # Classify content
        content_type = await content_classifier(text)
        content_type = content_type.strip().lower()

        # Route to appropriate handler
        if "question" in content_type:
            return await question_handler(text)
        elif "statement" in content_type:
            return await statement_handler(text)
        elif "request" in content_type:
            return await request_handler(text)
        else:
            return "Unable to process content"

    test_contents = [
        "What is Python?",
        "I think AI is fascinating.",
        "Please translate this to French.",
    ]

    for content in test_contents:
        result = await content_workflow(content)
        print(f"Input: {content}")
        print(f"Response: {result}\n")

    # Example 3: Multi-level conditional
    print("3. Multi-Level Conditional Logic")
    print("-" * 50)

    @agent(model="gpt-4o-mini")
    async def length_checker(text: str) -> str:
        """Return 'short' if text < 50 chars, 'medium' if < 150, else 'long'."""
        if len(text) < 50:
            return "short"
        elif len(text) < 150:
            return "medium"
        else:
            return "long"

    @agent(model="gpt-4o-mini")
    async def short_summarizer(text: str) -> str:
        """Briefly respond to: {{ text }}"""
        pass

    @agent(model="gpt-4o-mini")
    async def detailed_analyzer(text: str) -> str:
        """Provide detailed analysis of: {{ text }}"""
        pass

    @workflow
    async def adaptive_workflow(text: str) -> str:
        """Adapt processing based on input length and sentiment."""
        # Check length
        length = await length_checker(text)
        length = length.strip().lower()

        # For short text, quick response
        if "short" in length:
            return await short_summarizer(text)

        # For longer text, analyze sentiment first
        sentiment = await sentiment_analyzer(text)
        sentiment = sentiment.strip().lower()

        if "positive" in sentiment:
            return await positive_responder(text)
        elif "negative" in sentiment:
            return await negative_responder(text)
        else:
            return await detailed_analyzer(text)

    test_inputs = [
        "Hi!",
        "I really enjoyed reading this book. It was fantastic and well-written.",
        "This product disappointed me. The quality was poor and it broke after one use. Very unsatisfied with my purchase.",
    ]

    for text in test_inputs:
        result = await adaptive_workflow(text)
        print(f"Input: {text[:50]}...")
        print(f"Response: {result}\n")

    # Example 4: Conditional with shared context
    print("4. Conditional with Shared Context")
    print("-" * 50)

    @workflow
    async def context_aware_workflow(user_input: str, user_level: str) -> str:
        """Provide response appropriate to user level."""
        if user_level == "beginner":
            @agent(model="gpt-4o-mini")
            async def simple_explainer(query: str) -> str:
                """Explain in simple terms: {{ query }}"""
                pass
            return await simple_explainer(user_input)

        elif user_level == "advanced":
            @agent(model="gpt-4o-mini")
            async def technical_explainer(query: str) -> str:
                """Provide technical explanation: {{ query }}"""
                pass
            return await technical_explainer(user_input)

        else:  # intermediate
            @agent(model="gpt-4o-mini")
            async def balanced_explainer(query: str) -> str:
                """Explain with balanced detail: {{ query }}"""
                pass
            return await balanced_explainer(user_input)

    query = "What is machine learning?"

    for level in ["beginner", "intermediate", "advanced"]:
        result = await context_aware_workflow(query, level)
        print(f"User level: {level}")
        print(f"Response: {result}\n")

    # Example 5: Error handling with conditionals
    print("5. Conditional Error Handling")
    print("-" * 50)

    @workflow
    async def robust_workflow(text: str) -> str:
        """Workflow with error handling."""
        try:
            # Try primary path
            sentiment = await sentiment_analyzer(text)

            if not sentiment or len(sentiment.strip()) == 0:
                # Fallback for empty response
                return await neutral_responder(text)

            # Normal processing
            sentiment = sentiment.strip().lower()
            if "positive" in sentiment:
                return await positive_responder(text)
            elif "negative" in sentiment:
                return await negative_responder(text)
            else:
                return await neutral_responder(text)

        except Exception as e:
            # Error fallback
            print(f"Error in workflow: {e}")
            return f"Unable to process: {text}"

    result = await robust_workflow("This is a test")
    print(f"Robust workflow result: {result}\n")

    # Example 6: Conditional composition
    print("6. Conditional Workflow Composition")
    print("-" * 50)

    @workflow
    async def preprocessing_workflow(text: str) -> dict:
        """Preprocess and classify input."""
        sentiment = await sentiment_analyzer(text)
        content_type = await content_classifier(text)

        return {
            "text": text,
            "sentiment": sentiment.strip().lower(),
            "type": content_type.strip().lower()
        }

    @workflow
    async def composed_workflow(text: str) -> str:
        """Composed workflow using preprocessing."""
        # Preprocess
        analysis = await preprocessing_workflow(text)

        # Branch based on both sentiment and type
        if "positive" in analysis["sentiment"] and "question" in analysis["type"]:
            return await question_handler(text) + " (Positive tone detected)"
        elif "negative" in analysis["sentiment"]:
            return await negative_responder(text)
        else:
            return await neutral_responder(text)

    result = await composed_workflow("What's your favorite feature?")
    print(f"Composed workflow: {result}\n")


async def advanced_patterns():
    """Demonstrate advanced conditional patterns."""
    print("\n" + "=" * 60)
    print("=== Advanced Conditional Patterns ===\n")

    # Pattern 1: State machine workflow
    print("1. State Machine Workflow")
    print("-" * 50)

    @workflow
    async def state_machine_workflow(state: str, input_text: str) -> tuple:
        """Simple state machine."""
        if state == "init":
            sentiment = await sentiment_analyzer(input_text)
            new_state = "analyzed"
            return new_state, sentiment

        elif state == "analyzed":
            response = await positive_responder(input_text)
            new_state = "complete"
            return new_state, response

        else:
            return "complete", "Done"

    state = "init"
    text = "Great day!"

    for i in range(3):
        state, output = await state_machine_workflow(state, text)
        print(f"Step {i+1}: State={state}, Output={output}")

        if state == "complete":
            break

    print()

    # Pattern 2: Priority-based routing
    print("2. Priority-Based Routing")
    print("-" * 50)

    @workflow
    async def priority_workflow(text: str, priority: str) -> str:
        """Route based on priority."""
        if priority == "urgent":
            # Fast path
            return await positive_responder(text)
        elif priority == "normal":
            # Standard path
            sentiment = await sentiment_analyzer(text)
            if "negative" in sentiment.lower():
                return await negative_responder(text)
            return await positive_responder(text)
        else:  # low priority
            # Detailed path
            sentiment = await sentiment_analyzer(text)
            content_type = await content_classifier(text)
            return f"Analyzed: {sentiment}, Type: {content_type}"

    for priority in ["urgent", "normal", "low"]:
        result = await priority_workflow("Need help!", priority)
        print(f"Priority {priority}: {result}")

    print()


if __name__ == "__main__":
    # Run main examples
    asyncio.run(main())

    # Run advanced patterns
    asyncio.run(advanced_patterns())

    print("=" * 60)
    print("Conditional workflow examples complete! 🎉")
