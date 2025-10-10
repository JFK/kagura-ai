"""
MCP (Model Context Protocol) integration for Kagura AI

This module enables Kagura agents to be exposed as MCP tools,
allowing integration with Claude Code, Cline, and other MCP clients.
"""

from .schema import generate_json_schema
from .server import create_mcp_server

__all__ = ["generate_json_schema", "create_mcp_server"]
