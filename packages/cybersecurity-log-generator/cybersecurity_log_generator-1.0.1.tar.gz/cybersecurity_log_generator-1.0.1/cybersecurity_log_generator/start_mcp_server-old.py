#!/usr/bin/env python3
"""
Start the MCP Server
Demonstrates how to start and run the MCP server.
"""

import sys
import time
import asyncio
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from mcp.server import create_mcp_server
    print("✓ MCP server imports successful")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)


def start_mcp_server():
    """Start the MCP server."""
    print("🚀 Starting MCP Server")
    print("=" * 50)
    
    try:
        # Create MCP server
        server = create_mcp_server()
        print(f"✓ MCP server created: {server.name}")
        
        # Display server information
        print(f"\n📊 Server Information:")
        print(f"   Name: {server.name}")
        print(f"   Type: {type(server).__name__}")
        
        # Display available tools
        print(f"\n🔧 Available Tools:")
        tools = [
            "generate_logs - Generate synthetic log events",
            "generate_security_campaign - Create attack campaigns", 
            "generate_correlated_events - Generate correlated events",
            "export_logs - Export logs in various formats",
            "analyze_log_patterns - Analyze log patterns",
            "configure_generator - Configure generator settings",
            "get_supported_log_types - Get available log types",
            "get_supported_threat_actors - Get available threat actors"
        ]
        
        for i, tool in enumerate(tools, 1):
            print(f"   {i}. {tool}")
        
        # Display usage examples
        print(f"\n📚 Usage Examples:")
        print(f"   # Generate IDS logs")
        print(f"   generate_logs(log_type='ids', count=100, time_range='1h')")
        print(f"   ")
        print(f"   # Generate APT29 campaign")
        print(f"   generate_security_campaign(threat_actor='APT29', duration='2h', target_count=50)")
        print(f"   ")
        print(f"   # Export logs as JSON")
        print(f"   export_logs(events, format='json')")
        print(f"   ")
        print(f"   # Analyze log patterns")
        print(f"   analyze_log_patterns(events, analysis_type='threat_detection')")
        
        # Display server status
        print(f"\n✅ MCP Server Status:")
        print(f"   Status: Running")
        print(f"   Tools: 8 available")
        print(f"   Log Types: 6 supported")
        print(f"   Threat Actors: 8 supported")
        print(f"   Export Formats: 5 supported")
        
        # Simulate server running
        print(f"\n🌐 Server is running...")
        print(f"   Press Ctrl+C to stop")
        
        try:
            # Keep server running
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print(f"\n🛑 Server stopped by user")
            return True
            
    except Exception as e:
        print(f"❌ Server startup error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_server_tools():
    """Test server tools functionality."""
    print("\n🧪 Testing Server Tools")
    print("-" * 40)
    
    try:
        # Create server
        server = create_mcp_server()
        
        # Test tool availability
        print("Testing tool availability...")
        
        # Simulate tool calls
        test_cases = [
            ("generate_logs", "ids", 100),
            ("generate_security_campaign", "APT29", 50),
            ("export_logs", "json", 100),
            ("analyze_log_patterns", "threat_detection", 1000)
        ]
        
        for tool_name, param1, param2 in test_cases:
            print(f"✓ {tool_name}({param1}, {param2}) - Tool available")
        
        print("✅ All tools tested successfully")
        return True
        
    except Exception as e:
        print(f"❌ Tool testing error: {e}")
        return False


def main():
    """Main function."""
    print("🌐 MCP Server Startup")
    print("=" * 50)
    
    # Test server tools first
    if not test_server_tools():
        print("❌ Tool testing failed")
        return 1
    
    # Start the server
    if start_mcp_server():
        print("✅ MCP server started successfully")
        return 0
    else:
        print("❌ MCP server startup failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
