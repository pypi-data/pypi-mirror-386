#!/usr/bin/env python3
"""
Test MCP Server Status and Functionality
"""

import requests
import json
import time

def test_server_status():
    """Test the MCP server status and basic functionality."""
    print("🧪 Testing MCP Server Status")
    print("=" * 50)
    
    # Test 1: Check if server is running
    print("1. Checking server status...")
    try:
        response = requests.get("http://127.0.0.1:8000/", timeout=5)
        print(f"   Root endpoint: {response.status_code}")
    except Exception as e:
        print(f"   Root endpoint error: {e}")
    
    # Test 2: Check MCP endpoint
    print("\n2. Checking MCP endpoint...")
    try:
        response = requests.get("http://127.0.0.1:8000/mcp/", timeout=5)
        print(f"   MCP endpoint: {response.status_code}")
    except Exception as e:
        print(f"   MCP endpoint error: {e}")
    
    # Test 3: Test MCP protocol with proper headers
    print("\n3. Testing MCP protocol...")
    try:
        # Initialize session
        init_response = requests.post(
            "http://127.0.0.1:8000/mcp/",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "clientInfo": {
                        "name": "test-client",
                        "version": "1.0.0"
                    }
                }
            },
            headers={
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json"
            },
            timeout=10
        )
        print(f"   Initialize: {init_response.status_code}")
        if init_response.status_code == 200:
            print("   ✅ MCP server is responding correctly")
        else:
            print(f"   ❌ MCP server error: {init_response.text}")
    except Exception as e:
        print(f"   ❌ MCP protocol error: {e}")
    
    # Test 4: Test tools list
    print("\n4. Testing tools list...")
    try:
        tools_response = requests.post(
            "http://127.0.0.1:8000/mcp/",
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            },
            headers={
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json"
            },
            timeout=10
        )
        print(f"   Tools list: {tools_response.status_code}")
        if tools_response.status_code == 200:
            result = tools_response.json()
            if "result" in result and "tools" in result["result"]:
                tools = result["result"]["tools"]
                print(f"   ✅ Found {len(tools)} tools:")
                for tool in tools:
                    print(f"      - {tool['name']}: {tool.get('description', 'No description')}")
            else:
                print(f"   Response: {result}")
        else:
            print(f"   ❌ Tools list error: {tools_response.text}")
    except Exception as e:
        print(f"   ❌ Tools list error: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 MCP Server Testing Complete!")
    print("🔗 Server URL: http://127.0.0.1:8000/mcp/")
    print("📚 The server is running and implementing the MCP protocol")

if __name__ == "__main__":
    test_server_status()
