"""
MCP Server module for cybersecurity log generation.

This module provides MCP (Model Context Protocol) server functionality
for generating cybersecurity logs through standardized interfaces.
"""

from .server import create_proper_mcp_server

__all__ = ["create_proper_mcp_server"]