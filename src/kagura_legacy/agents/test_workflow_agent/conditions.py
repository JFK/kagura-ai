# kagura/agents/test_orchestrator_agent/conditions.py
from typing import Any, Dict


async def check_conversion(state: Dict[str, Any]) -> str:
    """Check the status of content conversion and determine next step.

    Returns:
        str: Next step to execute ('success', 'retry', or 'failure')
    """
    if not state.get("converted_content"):
        if state.get("retry_count", 0) < 3:
            return "retry"
        return "failure"
    return "success"
