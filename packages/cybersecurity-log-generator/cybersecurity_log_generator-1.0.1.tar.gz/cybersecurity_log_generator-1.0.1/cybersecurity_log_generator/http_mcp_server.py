#!/usr/bin/env python3
"""
Standalone HTTP MCP Server
A simple HTTP server that provides MCP tools via REST API
"""

import os
import sys
import json
import asyncio
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# FastAPI imports
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Import our MCP server
from mcp_server.server import create_proper_mcp_server

# Create the MCP server instance
mcp_server = create_proper_mcp_server()

# Create FastAPI app
app = FastAPI(
    title="Cybersecurity Log Generator MCP Server",
    description="HTTP API for cybersecurity log generation tools",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the MCP server as an ASGI application
mcp_app = mcp_server.http_app()
app.mount("/mcp", mcp_app)

@app.get("/")
async def root():
    """Root endpoint with server information."""
    return {
        "name": "Cybersecurity Log Generator MCP Server",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "mcp": "/mcp",
            "docs": "/docs",
            "tools": "/tools"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "server": "Cybersecurity Log Generator MCP Server"
    }

@app.get("/tools")
async def list_tools():
    """List all available MCP tools."""
    try:
        # Get tools from the FastMCP server (async method)
        tools = await mcp_server.get_tools() if hasattr(mcp_server, 'get_tools') else []
        # Handle both tool objects and string names
        if tools:
            tool_names = []
            for tool in tools:
                if hasattr(tool, 'name'):
                    tool_names.append(tool.name)
                elif isinstance(tool, str):
                    tool_names.append(tool)
                else:
                    tool_names.append(str(tool))
        else:
            tool_names = []
        return {
            "tools": tool_names,
            "count": len(tool_names),
            "server": "Cybersecurity Log Generator MCP Server"
        }
    except Exception as e:
        return {
            "tools": [],
            "count": 0,
            "error": str(e),
            "server": "Cybersecurity Log Generator MCP Server"
        }

# Note: MCP endpoint is automatically handled by FastMCP when mounted at /mcp
# FastMCP provides the proper MCP protocol implementation

def main():
    """Main function to start the HTTP server."""
    parser = argparse.ArgumentParser(description='HTTP MCP Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8000, help='Port to bind to')
    parser.add_argument('--reload', action='store_true', help='Enable auto-reload')
    
    args = parser.parse_args()
    
    print("🚀 Starting HTTP MCP Server")
    print(f"📍 Host: {args.host}")
    print(f"🔌 Port: {args.port}")
    print(f"📚 Docs: http://{args.host}:{args.port}/docs")
    print(f"🔧 MCP: http://{args.host}:{args.port}/mcp")
    print(f"❤️  Health: http://{args.host}:{args.port}/health")
    
    uvicorn.run(
        "http_mcp_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )

if __name__ == "__main__":
    main()
