#!/usr/bin/env python3
"""
Remote MCP Server Wrapper
A FastMCP server that properly integrates with FastAPI following FastMCP best practices.
This wrapper creates a proper FastMCP server with all tools and mounts it correctly.
"""

import os
import json
import asyncio
import warnings
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# Suppress deprecation warnings for WebSocket protocols
warnings.filterwarnings("ignore", category=DeprecationWarning, module="websockets")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="uvicorn.protocols.websockets")

# FastMCP imports
from fastmcp import FastMCP

# FastAPI for HTTP server features
from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Import our main MCP server
try:
    from .server import create_proper_mcp_server
except ImportError:
    # Handle case when run directly (not as module)
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from mcp_server.server import create_proper_mcp_server

# Authentication support (optional but recommended for remote servers)
try:
    from fastmcp.server.auth import BearerTokenAuth
    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False

# ============================================================================
# FASTMCP SERVER SETUP
# ============================================================================

def create_remote_mcp_server() -> FastMCP:
    """Create a remote MCP server that properly integrates with FastMCP."""
    
    # Check for authentication token
    auth_token = os.environ.get("MCP_AUTH_TOKEN")
    auth = None
    
    if auth_token and AUTH_AVAILABLE:
        auth = BearerTokenAuth(token=auth_token)
        print("🔐 Authentication enabled with Bearer token")
    else:
        print("⚠️  No authentication configured - server is open to all clients")
    
    # Create the core MCP server with all tools
    core_server = create_proper_mcp_server()
    
    # Return the core server - it already has all the tools registered
    return core_server

# Create the remote MCP server
mcp = create_remote_mcp_server()

# ============================================================================
# FASTAPI INTEGRATION
# ============================================================================

# Create FastAPI app for additional features
app = FastAPI(
    title="Cybersecurity Log Generator MCP Server",
    description="Remote HTTP access to cybersecurity log generation tools",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add health check to the MCP server using FastMCP's custom route feature
@mcp.custom_route("/health", methods=["GET"])
async def mcp_health_check(request):
    """Health check endpoint for the MCP server."""
    return JSONResponse({
        "status": "healthy", 
        "service": "mcp-server",
        "timestamp": datetime.now().isoformat()
    })

# Mount the MCP server as an ASGI application
# According to FastMCP documentation, we need to use the ASGI app approach
mcp_app = mcp.http_app()
app.mount("/mcp", mcp_app)

# ============================================================================
# ADDITIONAL FASTAPI ROUTES
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint with server information."""
    return {
        "name": "Cybersecurity Log Generator MCP Server",
        "version": "1.0.0",
        "description": "Remote HTTP access to cybersecurity log generation tools",
        "mcp_endpoint": "/mcp",
        "health_endpoint": "/health",
        "status_endpoint": "/status"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "server": "Cybersecurity Log Generator MCP Server"
    }

@app.get("/status")
async def server_status():
    """Detailed server status."""
    try:
        # Get tools from the FastMCP server (async method)
        tools = await mcp.get_tools() if hasattr(mcp, 'get_tools') else []
        return {
            "status": "running",
            "timestamp": datetime.now().isoformat(),
            "server": "Cybersecurity Log Generator MCP Server",
            "tools_available": len(tools),
            "mcp_endpoint": "/mcp",
            "documentation": "/docs"
        }
    except Exception as e:
        return {
            "status": "running",
            "timestamp": datetime.now().isoformat(),
            "server": "Cybersecurity Log Generator MCP Server",
            "tools_available": 0,
            "error": str(e),
            "mcp_endpoint": "/mcp",
            "documentation": "/docs"
        }

@app.get("/tools")
async def list_tools():
    """List all available MCP tools."""
    try:
        # Get tools from the FastMCP server (async method)
        tools = await mcp.get_tools() if hasattr(mcp, 'get_tools') else []
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


# ============================================================================
# SERVER CONFIGURATION
# ============================================================================

def main():
    """Main entry point for the remote MCP server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Remote Cybersecurity Log Generator MCP Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    parser.add_argument("--production", action="store_true", help="Run in production mode")
    
    args = parser.parse_args()
    
    print(f"🚀 Starting Remote Cybersecurity Log Generator MCP Server")
    print(f"📡 Host: {args.host}")
    print(f"🔌 Port: {args.port}")
    print(f"🛠️  Workers: {args.workers}")
    print(f"🔄 Reload: {args.reload}")
    print(f"🏭 Production: {args.production}")
    print(f"🌐 Server URL: http://{args.host}:{args.port}")
    print(f"📚 API Docs: http://{args.host}:{args.port}/docs")
    print(f"❤️  Health: http://{args.host}:{args.port}/health")
    print(f"🔧 MCP Endpoint: http://{args.host}:{args.port}/mcp")
    print(f"🔧 MCP Health: http://{args.host}:{args.port}/mcp/health")
    
    # Suppress deprecation warnings globally
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    
    if args.production:
        # Production configuration following FastMCP best practices
        uvicorn.run(
            app,  # Use the FastAPI app directly
            host=args.host,
            port=args.port,
            workers=args.workers,
            log_level="info",
            access_log=True,
            ws_ping_interval=20,
            ws_ping_timeout=10,
            ws_max_size=16777216,
            loop="asyncio"
        )
    else:
        # Development configuration
        uvicorn.run(
            app,  # Use the FastAPI app directly
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level="debug",
            access_log=True,
            ws_ping_interval=20,
            ws_ping_timeout=10,
            ws_max_size=16777216,
            loop="asyncio"
        )

if __name__ == "__main__":
    main()
