#!/usr/bin/env python3
"""
Test MCP Client - Test the remote MCP server
"""

import requests
import json

def test_mcp_server():
    """Test the MCP server endpoints."""
    base_url = "http://127.0.0.1:8000/mcp/"
    
    print("🧪 Testing MCP Server")
    print("=" * 50)
    
    # Test 1: List tools
    print("1. Testing tools/list...")
    try:
        response = requests.post(base_url, json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }, headers={
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json"
        })
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Tools list successful")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    print("\n" + "-" * 50)
    
    # Test 2: Call generate_logs tool
    print("2. Testing generate_logs tool...")
    try:
        response = requests.post(base_url, json={
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "generate_logs",
                "arguments": {
                    "log_type": "ids",
                    "count": 3
                }
            }
        }, headers={
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json"
        })
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Generate logs successful")
            result = response.json()
            if "result" in result:
                logs = json.loads(result["result"]["content"][0]["text"])
                print(f"Generated {len(logs)} logs")
                print("Sample log:", json.dumps(logs[0], indent=2))
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    print("\n" + "-" * 50)
    
    # Test 3: Call get_supported_log_types
    print("3. Testing get_supported_log_types tool...")
    try:
        response = requests.post(base_url, json={
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "get_supported_log_types",
                "arguments": {}
            }
        }, headers={
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json"
        })
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Get supported log types successful")
            result = response.json()
            if "result" in result:
                print(result["result"]["content"][0]["text"])
        else:
            print(f"❌ Error: {response.text}")
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_mcp_server()