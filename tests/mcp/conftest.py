"""
pytest configuration for MCP tests.

This conftest.py ensures that all MCP tools are registered before test collection.
"""

# Register all MCP tools before pytest collects tests
# This must happen here (not in individual test files) to ensure tools are
# available during test collection phase
import kagura.mcp.builtin  # noqa: F401
