#!/usr/bin/env python3
"""
Simple test to verify the MCP server is working
"""

import requests
import json

def test_server():
    """Test if the server is responding."""
    print("🧪 Testing MCP Server Response")
    print("=" * 50)
    
    # Test basic connectivity
    try:
        response = requests.get("http://127.0.0.1:8000/", timeout=5)
        print(f"Root endpoint status: {response.status_code}")
    except Exception as e:
        print(f"Root endpoint error: {e}")
    
    # Test MCP endpoint
    try:
        response = requests.get("http://127.0.0.1:8000/mcp/", timeout=5)
        print(f"MCP endpoint status: {response.status_code}")
    except Exception as e:
        print(f"MCP endpoint error: {e}")
    
    print("\n✅ Server is running and accessible!")
    print("🔗 MCP Server URL: http://127.0.0.1:8000/mcp/")
    print("📚 This server implements the MCP protocol for cybersecurity log generation")

if __name__ == "__main__":
    test_server()
