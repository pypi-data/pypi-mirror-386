#!/usr/bin/env python3
"""
Test CrewAI with Docker MCP Server and Ollama
Test the Docker MCP server (port 8003) using CrewAI with Ollama.
This tests the remote HTTP MCP server with Ollama as the LLM.
"""

import os
import sys
import json
import warnings
from pathlib import Path
from datetime import datetime

# Suppress deprecation warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="websockets")
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

def test_docker_mcp_with_ollama():
    """Test Docker MCP server with Ollama using CrewAI."""
    print("🧪 Testing Docker MCP Server with Ollama...")
    
    try:
        # Configure Docker MCP server parameters (port 8003)
        server_params = {
            "url": "http://localhost:8003/mcp",  # Docker server on port 8003
            "transport": "streamable-http"  # Use streamable-http transport
        }
        
        print(f"🔧 Docker MCP Configuration:")
        print(f"  URL: {server_params['url']}")
        print(f"  Transport: {server_params['transport']}")
        
        # Configure Ollama LLM
        llm = ChatOllama(
            model="llama3.2:3b",  # Use a lightweight model
            base_url="http://localhost:11434",  # Ollama default port
            temperature=0.1
        )
        
        print(f"🔧 Ollama Configuration:")
        print(f"  Model: llama3.2:3b")
        print(f"  Base URL: http://localhost:11434")
        
        # Use managed connection with Docker MCP server
        with MCPServerAdapter(server_params, connect_timeout=30) as tools:
            print(f"✓ Connected to Docker MCP server (Managed)")
            print(f"✓ Available tools: {[tool.name for tool in tools]}")
            
            # Create cybersecurity analyst agent with Ollama
            analyst_agent = Agent(
                role="Cybersecurity Analyst",
                goal="Generate and analyze cybersecurity logs using MCP tools",
                backstory="An expert cybersecurity analyst with access to advanced log generation and analysis tools",
                tools=tools,
                llm=llm,  # Use Ollama as LLM
                verbose=True
            )
            
            # Create log generation task
            log_task = Task(
                description="Generate IDS logs and analyze them for security patterns using the MCP tools",
                expected_output="Generated IDS logs and analysis results",
                agent=analyst_agent
            )
            
            # Create crew with Ollama
            security_crew = Crew(
                agents=[analyst_agent],
                tasks=[log_task],
                process=Process.sequential,
                verbose=True
            )
            
            print("🚀 Starting CrewAI execution with Docker MCP server and Ollama...")
            result = security_crew.kickoff()
            
            print("✓ Docker MCP server with Ollama test completed successfully")
            print(f"📊 Result: {str(result)[:200]}...")
            
            return result
            
    except Exception as e:
        print(f"✗ Docker MCP server with Ollama test failed: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise

def test_docker_mcp_manual_with_ollama():
    """Test Docker MCP server with manual connection and Ollama."""
    print("\n🧪 Testing Docker MCP Server with Manual Connection and Ollama...")
    
    try:
        # Configure Docker MCP server parameters (port 8003)
        server_params = {
            "url": "http://localhost:8003/mcp",  # Docker server on port 8003
            "transport": "streamable-http"  # Use streamable-http transport
        }
        
        print(f"🔧 Docker MCP Configuration:")
        print(f"  URL: {server_params['url']}")
        print(f"  Transport: {server_params['transport']}")
        
        # Configure Ollama LLM
        llm = ChatOllama(
            model="llama3.2:3b",  # Use a lightweight model
            base_url="http://localhost:11434",  # Ollama default port
            temperature=0.1
        )
        
        print(f"🔧 Ollama Configuration:")
        print(f"  Model: llama3.2:3b")
        print(f"  Base URL: http://localhost:11434")
        
        # Manual connection lifecycle
        mcp_server_adapter = None
        try:
            mcp_server_adapter = MCPServerAdapter(server_params, connect_timeout=30)
            mcp_server_adapter.start()
            tools = mcp_server_adapter.tools
            print(f"✓ Connected to Docker MCP server (Manual)")
            print(f"✓ Available tools: {[tool.name for tool in tools]}")
            
            # Create advanced cybersecurity agent with Ollama
            advanced_agent = Agent(
                role="Advanced Cybersecurity Specialist",
                goal="Use MCP tools for comprehensive cybersecurity analysis",
                backstory="A senior cybersecurity specialist with deep expertise in log analysis and threat detection",
                tools=tools,
                llm=llm,  # Use Ollama as LLM
                verbose=True
            )
            
            # Create comprehensive analysis task
            analysis_task = Task(
                description="Perform comprehensive cybersecurity analysis using multiple MCP tools",
                expected_output="Detailed cybersecurity analysis and recommendations",
                agent=advanced_agent
            )
            
            # Create crew with Ollama
            analysis_crew = Crew(
                agents=[advanced_agent],
                tasks=[analysis_task],
                process=Process.sequential,
                verbose=True
            )
            
            print("🚀 Starting CrewAI execution with Docker MCP server and Ollama (Manual)...")
            result = analysis_crew.kickoff()
            
            print("✓ Docker MCP server manual connection with Ollama test completed successfully")
            print(f"📊 Result: {str(result)[:200]}...")
            
            return result
            
        finally:
            if mcp_server_adapter and mcp_server_adapter.is_connected:
                print("Stopping Docker MCP server connection (manual)...")
                mcp_server_adapter.stop()  # Crucial: Ensure stop is called
            elif mcp_server_adapter:
                print("Docker MCP server adapter was not connected. No stop needed or start failed.")
                
    except Exception as e:
        print(f"✗ Docker MCP server manual connection with Ollama test failed: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        raise

def test_docker_server_endpoints():
    """Test the Docker server endpoints to verify it's working."""
    print("\n🔍 Testing Docker Server Endpoints (Port 8003)...")
    
    import requests
    
    base_url = "http://localhost:8003"
    endpoints = [
        ("/health", "Health Check"),
        ("/tools", "Tools List"),
        ("/mcp", "MCP Endpoint"),
        ("/docs", "API Documentation")
    ]
    
    for endpoint, description in endpoints:
        try:
            print(f"\n🔍 Testing {description} ({endpoint})...")
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                if endpoint in ["/docs"]:
                    print(f"  ✓ {description} accessible (HTML content)")
                else:
                    try:
                        data = response.json()
                        print(f"  ✓ {description} data: {json.dumps(data, indent=2)[:200]}...")
                    except:
                        print(f"  ✓ {description} accessible (non-JSON content)")
            elif response.status_code == 307:
                print(f"  ↻ {description} redirects (likely to {endpoint}/)")
            else:
                print(f"  ✗ {description} failed: {response.status_code}")
        except Exception as e:
            print(f"  ✗ {description} error: {e}")

def main():
    """Main entry point."""
    print("🧪 CrewAI Docker MCP Server with Ollama Test")
    print("Testing Docker MCP server (port 8003) with CrewAI and Ollama")
    print("This tests the remote HTTP MCP server with Ollama as the LLM")
    print("=" * 80)
    
    # Test Docker server endpoints first
    test_docker_server_endpoints()
    
    # Test Docker MCP server with Ollama
    try:
        test_docker_mcp_with_ollama()
    except Exception as e:
        print(f"❌ Docker MCP server with Ollama test failed: {e}")
    
    # Test Docker MCP server manual connection with Ollama
    try:
        test_docker_mcp_manual_with_ollama()
    except Exception as e:
        print(f"❌ Docker MCP server manual connection with Ollama test failed: {e}")
    
    print("\n🎉 All tests completed!")
    print("\n📝 Summary:")
    print("   ✓ CrewAI Docker MCP server with Ollama test completed")
    print("   ✓ Testing remote HTTP MCP server on port 8003")
    print("   ✓ Using Ollama as the LLM for CrewAI")

if __name__ == "__main__":
    main()
