#!/usr/bin/env python3
"""
Test CrewAI with Working HTTP MCP Server
This test uses the working HTTP MCP server on port 8009 with CrewAI and Ollama.
"""

import sys
import os
import warnings
import asyncio
import httpx
from pathlib import Path

# Suppress specific warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="uvicorn.protocols.websockets")

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from crewai import Agent, Task, Crew, Process
    from crewai_tools import MCPServerAdapter
    from langchain_ollama import ChatOllama
    print("✓ CrewAI, MCP, and Ollama imports successful")
except ImportError as e:
    print(f"✗ Import error: {e}")
    print("Please install: pip install 'crewai-tools[mcp]' langchain-ollama")
    sys.exit(1)

# --- Helper Functions for Server Health Checks ---
async def check_server_health(url):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{url}/health", timeout=5)
            response.raise_for_status()
            return response.status_code, response.json()
    except httpx.HTTPStatusError as e:
        return e.response.status_code, {"error": str(e)}
    except httpx.RequestError as e:
        return 0, {"error": f"Request failed: {e}"}

async def check_server_tools(url):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{url}/tools", timeout=5)
            response.raise_for_status()
            return response.status_code, response.json()
    except httpx.HTTPStatusError as e:
        return e.response.status_code, {"error": str(e)}
    except httpx.RequestError as e:
        return 0, {"error": f"Request failed: {e}"}

async def check_mcp_endpoint(url):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{url}/mcp", timeout=5)
            return response.status_code, response.text
    except httpx.HTTPStatusError as e:
        return e.response.status_code, {"error": str(e)}
    except httpx.RequestError as e:
        return 0, {"error": f"Request failed: {e}"}

async def test_mcp_initialize(url):
    """Test MCP initialize protocol."""
    try:
        async with httpx.AsyncClient() as client:
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "test-client",
                        "version": "1.0.0"
                    }
                }
            }
            response = await client.post(f"{url}/mcp", json=payload, timeout=10)
            return response.status_code, response.json()
    except httpx.HTTPStatusError as e:
        return e.response.status_code, {"error": str(e)}
    except httpx.RequestError as e:
        return 0, {"error": f"Request failed: {e}"}

async def test_mcp_tools_list(url):
    """Test MCP tools/list protocol."""
    try:
        async with httpx.AsyncClient() as client:
            payload = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }
            response = await client.post(f"{url}/mcp", json=payload, timeout=10)
            return response.status_code, response.json()
    except httpx.HTTPStatusError as e:
        return e.response.status_code, {"error": str(e)}
    except httpx.RequestError as e:
        return 0, {"error": f"Request failed: {e}"}

# --- Test Functions ---
async def test_working_http_mcp_with_ollama(server_url, ollama_base_url, ollama_model):
    """Test Working HTTP MCP server with Ollama using CrewAI."""
    print("\n🧪 Testing Working HTTP MCP Server with Ollama...")
    print(f"Testing Working HTTP MCP server with CrewAI and Ollama")
    print(f"This tests the working HTTP MCP server with Ollama as the LLM")
    print(f"================================================================================\n")

    print("🔍 Testing Working HTTP Server Endpoints...")
    
    # Test /health
    status, data = await check_server_health(server_url)
    print(f"🔍 Testing Health Check (/health)...")
    print(f"  Status: {status}")
    if status == 200:
        print(f"  ✓ Health Check data: {str(data)[:100]}...")
    else:
        print(f"  ✗ Health Check failed: {data}")

    # Test /tools
    status, data = await check_server_tools(server_url)
    print(f"\n🔍 Testing Tools List (/tools)...")
    print(f"  Status: {status}")
    if status == 200:
        print(f"  ✓ Tools List data: {str(data)[:100]}...")
    else:
        print(f"  ✗ Tools List failed: {data}")

    # Test /mcp
    status, data = await check_mcp_endpoint(server_url)
    print(f"\n🔍 Testing MCP Endpoint (/mcp)...")
    print(f"  Status: {status}")
    if status == 200:
        print(f"  ✓ MCP Endpoint data: {str(data)[:100]}...")
    else:
        print(f"  ✗ MCP Endpoint failed: {status}")

    # Test MCP initialize protocol
    status, data = await test_mcp_initialize(server_url)
    print(f"\n🔍 Testing MCP Initialize Protocol...")
    print(f"  Status: {status}")
    if status == 200:
        print(f"  ✓ MCP Initialize data: {str(data)[:100]}...")
    else:
        print(f"  ✗ MCP Initialize failed: {data}")

    # Test MCP tools/list protocol
    status, data = await test_mcp_tools_list(server_url)
    print(f"\n🔍 Testing MCP Tools List Protocol...")
    print(f"  Status: {status}")
    if status == 200:
        print(f"  ✓ MCP Tools List data: {str(data)[:100]}...")
    else:
        print(f"  ✗ MCP Tools List failed: {data}")

    print("\n🧪 Testing Working HTTP MCP Server with Ollama...")
    server_params = {
        "url": f"{server_url}/mcp",
        "transport": "streamable-http"
    }
    print(f"🔧 Working HTTP MCP Configuration:\n  URL: {server_params['url']}\n  Transport: {server_params['transport']}")

    # Configure Ollama LLM
    llm = ChatOllama(
        model=f"ollama/{ollama_model}",
        base_url=ollama_base_url,
        temperature=0.1
    )
    print(f"🔧 Ollama Configuration:\n  Model: {ollama_model}\n  Base URL: {ollama_base_url}")

    try:
        with MCPServerAdapter(server_params, connect_timeout=30) as tools:
            print(f"✓ Available tools from Working HTTP MCP server: {[tool.name for tool in tools]}")

            working_agent = Agent(
                role="Cybersecurity Analyst",
                goal="Analyze cybersecurity logs and identify threats using MCP tools.",
                backstory="An expert in cybersecurity analysis, skilled in using various tools to detect and respond to threats.",
                tools=tools,
                llm=llm,
                verbose=True,
            )

            working_task = Task(
                description="Generate 2 IDS logs for the last hour and analyze them for potential threats.",
                expected_output="A summary of potential threats found in the IDS logs.",
                agent=working_agent,
            )

            working_crew = Crew(
                agents=[working_agent],
                tasks=[working_task],
                verbose=True,
                process=Process.sequential
            )
            
            print("✓ Working HTTP MCP server with Ollama test setup completed successfully")
            print("🚀 Starting CrewAI task execution...")
            
            result = working_crew.kickoff() 
            print("\nCrew Task Result (Working HTTP MCP + Ollama):", result)

    except Exception as e:
        print(f"✗ Working HTTP MCP server with Ollama test failed: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()

async def main():
    server_url = os.getenv("WORKING_MCP_URL", "http://localhost:8009")
    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

    print(f"\n================================================================================")
    print(f"🧪 CrewAI Working HTTP MCP Server Test")
    print(f"Testing working HTTP MCP server with CrewAI and Ollama")
    print(f"Server URL: {server_url}")
    print(f"Ollama URL: {ollama_base_url}")
    print(f"Ollama Model: {ollama_model}")
    print(f"================================================================================\n")

    await test_working_http_mcp_with_ollama(server_url, ollama_base_url, ollama_model)

    print(f"\n🎉 All tests completed!")
    print(f"\n📝 Summary:")
    print(f"   ✓ CrewAI Working HTTP MCP server test completed")
    print(f"   ✓ Testing working HTTP MCP server on port {server_url.split(':')[-1]}")
    print(f"   ✓ Using Ollama as the LLM for CrewAI")

if __name__ == "__main__":
    asyncio.run(main())
