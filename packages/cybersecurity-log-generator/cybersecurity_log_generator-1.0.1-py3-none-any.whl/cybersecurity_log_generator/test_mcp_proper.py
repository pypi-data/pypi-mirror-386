#!/usr/bin/env python3
"""
Proper MCP Client Test - Using MCP protocol correctly
"""

import asyncio
import json
import warnings

# Suppress deprecation warnings for WebSocket protocols
warnings.filterwarnings("ignore", category=DeprecationWarning, module="websockets")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="uvicorn.protocols.websockets")

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_mcp_server():
    """Test the MCP server using proper MCP client."""
    print("🧪 Testing MCP Server with Proper MCP Client")
    print("=" * 60)
    
    # Create server parameters for HTTP MCP server
    server_params = StdioServerParameters(
        command="curl",
        args=["-X", "POST", "-H", "Accept: application/json, text/event-stream", 
              "-H", "Content-Type: application/json", 
              "http://127.0.0.1:8000/mcp/"]
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                print("✅ Connected to MCP server")
                
                # Test 1: List tools
                print("\n1. Testing tools/list...")
                try:
                    tools = await session.list_tools()
                    print(f"✅ Found {len(tools.tools)} tools:")
                    for tool in tools.tools:
                        print(f"   - {tool.name}: {tool.description}")
                except Exception as e:
                    print(f"❌ Error listing tools: {e}")
                
                # Test 2: Call generate_logs tool
                print("\n2. Testing generate_logs tool...")
                try:
                    result = await session.call_tool("generate_logs", {
                        "log_type": "ids",
                        "count": 3
                    })
                    print("✅ Generate logs successful")
                    if result.content:
                        logs = json.loads(result.content[0].text)
                        print(f"   Generated {len(logs)} logs")
                        print(f"   Sample log: {json.dumps(logs[0], indent=2)}")
                except Exception as e:
                    print(f"❌ Error calling generate_logs: {e}")
                
                # Test 3: Call get_supported_log_types
                print("\n3. Testing get_supported_log_types tool...")
                try:
                    result = await session.call_tool("get_supported_log_types", {})
                    print("✅ Get supported log types successful")
                    if result.content:
                        print(f"   Result: {result.content[0].text}")
                except Exception as e:
                    print(f"❌ Error calling get_supported_log_types: {e}")
                
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("💡 Make sure the MCP server is running on http://127.0.0.1:8000/mcp/")

if __name__ == "__main__":
    asyncio.run(test_mcp_server())
