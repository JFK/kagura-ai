"""Customer Support Bot - Full support system

This example demonstrates:
- Multi-agent support system
- Ticket routing and classification
- Memory-enabled conversations
- Knowledge base integration
"""

import asyncio
from enum import Enum
from pydantic import BaseModel, Field
from kagura import agent, tool, LLMConfig
from kagura.core.memory import MemoryManager, WorkingMemory, MemoryRAG


# Support ticket classification
class TicketType(str, Enum):
    TECHNICAL = "technical"
    BILLING = "billing"
    GENERAL = "general"
    URGENT = "urgent"


class TicketClassification(BaseModel):
    """Ticket classification result"""
    ticket_type: TicketType = Field(description="Type of support ticket")
    priority: str = Field(description="high, medium, or low")
    summary: str = Field(description="Brief summary of issue")
    suggested_action: str = Field(description="Recommended next step")


# Knowledge base
knowledge_base = MemoryRAG(collection_name="support_kb")


# Support tools
@tool
async def search_knowledge_base(query: str) -> str:
    """Search support knowledge base for solutions"""
    results = knowledge_base.recall(query, top_k=3)
    if not results:
        return "No matching articles found"

    articles = "\n".join([
        f"- {r.get('content', '')}"
        for r in results
    ])
    return f"Knowledge Base Results:\n{articles}"


@tool
async def create_ticket(
    customer_id: str,
    issue: str,
    priority: str
) -> str:
    """Create a support ticket"""
    ticket_id = f"TICKET-{hash(customer_id + issue) % 10000:04d}"
    return f"Created ticket {ticket_id} with {priority} priority"


@tool
async def check_account_status(customer_id: str) -> str:
    """Check customer account status"""
    # Simulated account lookup
    return f"Account {customer_id}: Active, Premium Plan, No outstanding issues"


# Agents
config = LLMConfig(model="gpt-4o-mini", temperature=0.7, enable_cache=True)


@agent(config=config)
async def ticket_classifier(message: str) -> TicketClassification:
    """
    Classify this support request:
    "{{ message }}"

    Return structured classification with type, priority, summary, and action.
    """
    pass


@agent(config=config, tools=[search_knowledge_base, check_account_status])
async def technical_support(issue: str, customer_id: str) -> str:
    """
    Technical support specialist.
    Customer ID: {{ customer_id }}
    Issue: {{ issue }}

    Search knowledge base and provide step-by-step solution.
    """
    pass


@agent(config=config, tools=[check_account_status])
async def billing_support(issue: str, customer_id: str) -> str:
    """
    Billing specialist.
    Customer ID: {{ customer_id }}
    Issue: {{ issue }}

    Check account status and provide billing assistance.
    """
    pass


@agent(config=config, tools=[search_knowledge_base])
async def general_support(question: str) -> str:
    """
    General support agent.
    Question: {{ question }}

    Search knowledge base and provide helpful answer.
    """
    pass


# Main support system
async def initialize_knowledge_base():
    """Populate knowledge base with articles"""
    articles = [
        "How to reset password: Go to Settings > Security > Reset Password",
        "Installation guide: Run 'pip install kagura-ai' to install",
        "Billing FAQ: Subscriptions auto-renew monthly, cancel anytime",
        "API rate limits: Free tier allows 100 requests/day",
        "Troubleshooting crashes: Check logs in ~/.kagura/logs/",
        "Upgrade to premium: Visit account.example.com/upgrade",
        "Contact support: Email support@example.com or use live chat"
    ]

    for article in articles:
        knowledge_base.store(
            content=article,
            metadata={"type": "support_article"}
        )


async def handle_support_request(message: str, customer_id: str):
    """Handle a support request through the full system"""
    print(f"\n{'=' * 60}")
    print(f"Customer {customer_id}: {message}")
    print(f"{'=' * 60}")

    # 1. Classify ticket
    classification = await ticket_classifier(message)
    print(f"\n[Classification]")
    print(f"  Type: {classification.ticket_type.value}")
    print(f"  Priority: {classification.priority}")
    print(f"  Summary: {classification.summary}")
    print(f"  Action: {classification.suggested_action}")

    # 2. Route to appropriate agent
    print(f"\n[Routing to {classification.ticket_type.value} support...]")

    if classification.ticket_type == TicketType.TECHNICAL:
        response = await technical_support(message, customer_id)
    elif classification.ticket_type == TicketType.BILLING:
        response = await billing_support(message, customer_id)
    else:
        response = await general_support(message)

    print(f"\n[Response]")
    print(response)

    # 3. Create ticket if high priority
    if classification.priority == "high":
        ticket_result = await create_ticket(
            customer_id,
            message,
            classification.priority
        )
        print(f"\n[Ticket] {ticket_result}")


async def main():
    print("Customer Support Bot - Full System Demo")
    print("=" * 60)

    # Initialize
    await initialize_knowledge_base()
    print("✓ Knowledge base initialized\n")

    # Test scenarios
    scenarios = [
        ("CUST001", "My application keeps crashing when I start it"),
        ("CUST002", "I was charged twice this month"),
        ("CUST003", "How do I install Kagura AI?"),
        ("CUST004", "I can't access my account, getting authentication errors"),
        ("CUST005", "What are the differences between free and premium plans?")
    ]

    for customer_id, message in scenarios:
        await handle_support_request(message, customer_id)
        await asyncio.sleep(0.5)  # Spacing

    print("\n" + "=" * 60)
    print("Support System Features:")
    print("- Automatic ticket classification")
    print("- Intelligent routing")
    print("- Knowledge base search")
    print("- Multi-agent specialization")
    print("- Priority handling")


if __name__ == "__main__":
    asyncio.run(main())
