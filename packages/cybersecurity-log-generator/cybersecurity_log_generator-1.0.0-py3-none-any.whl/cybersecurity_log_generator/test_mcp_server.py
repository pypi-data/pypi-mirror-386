#!/usr/bin/env python3
"""
Test MCP Server - Simple working example
"""

import warnings

# Suppress deprecation warnings for WebSocket protocols
warnings.filterwarnings("ignore", category=DeprecationWarning, module="websockets")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="uvicorn.protocols.websockets")

from fastmcp import FastMCP
import uvicorn

# Create FastMCP server
mcp = FastMCP("Test Server")

@mcp.tool
def hello(name: str) -> str:
    """Say hello to someone."""
    return f"Hello, {name}!"

@mcp.tool
def generate_test_logs(count: int = 10) -> str:
    """Generate test cybersecurity logs."""
    import json
    from datetime import datetime
    
    logs = []
    for i in range(count):
        logs.append({
            "id": f"test-{i}",
            "timestamp": datetime.now().isoformat(),
            "message": f"Test security event {i}",
            "severity": "medium"
        })
    
    return json.dumps(logs, indent=2)

if __name__ == "__main__":
    print("🚀 Starting Test MCP Server")
    print("📍 Server will be available at: http://127.0.0.1:8000/mcp/")

    # Use the direct HTTP server approach
    mcp.run(transport="http", host="127.0.0.1", port=8000)