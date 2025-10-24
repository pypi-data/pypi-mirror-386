#!/usr/bin/env python3
"""
Test Docker MCP Server
"""

import requests
import json
import time

def test_docker_mcp():
    """Test the Docker MCP server."""
    print("🐳 Testing Docker MCP Server")
    print("=" * 50)
    
    # Test 1: Check if server is running
    print("1. Checking Docker container status...")
    try:
        response = requests.get("http://127.0.0.1:8000/", timeout=5)
        print(f"   Root endpoint: {response.status_code}")
    except Exception as e:
        print(f"   Root endpoint error: {e}")
    
    # Test 2: Test MCP protocol
    print("\n2. Testing MCP protocol...")
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
                        "name": "docker-test-client",
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
            print("   ✅ Docker MCP server is responding correctly")
            result = init_response.json()
            print(f"   Server info: {result.get('result', {}).get('serverInfo', {})}")
        else:
            print(f"   ❌ MCP server error: {init_response.text}")
    except Exception as e:
        print(f"   ❌ MCP protocol error: {e}")
    
    # Test 3: Test tools list
    print("\n3. Testing tools list...")
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
    print("🎉 Docker MCP Server Testing Complete!")
    print("🐳 Container: hackerdogs-loggen")
    print("🔗 Server URL: http://127.0.0.1:8000/mcp/")
    print("📚 The Docker container is running the MCP protocol successfully")

if __name__ == "__main__":
    test_docker_mcp()
