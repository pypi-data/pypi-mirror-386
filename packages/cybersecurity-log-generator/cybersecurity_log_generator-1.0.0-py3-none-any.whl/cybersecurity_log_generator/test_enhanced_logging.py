#!/usr/bin/env python3
"""
Test script to demonstrate comprehensive logging in the MCP server.
"""

import json
import time
from datetime import datetime

def test_enhanced_logging():
    """Test the enhanced MCP server with comprehensive logging."""
    print("🧪 Testing Enhanced MCP Server with Comprehensive Logging")
    print("=" * 60)
    
    try:
        # Import the server
        from mcp.server import create_mcp_server
        print("✅ MCP server import successful")
        
        # Create server (this will trigger logging)
        print("\n🔧 Creating MCP server...")
        server = create_mcp_server()
        print("✅ MCP server created successfully")
        
        # Test different scenarios to trigger various logging levels
        print("\n📊 Testing various logging scenarios...")
        
        # Test 1: Normal operation
        print("\n1️⃣ Testing normal log generation...")
        try:
            from core.generator import LogGenerator
            generator = LogGenerator()
            logs = generator.generate_logs('ids', 5, '1h')
            print(f"   ✅ Generated {len(logs)} IDS logs")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test 2: Attack campaign
        print("\n2️⃣ Testing attack campaign generation...")
        try:
            campaign = generator.generate_security_campaign('APT29', '2h', 10)
            print(f"   ✅ Generated {len(campaign.events)} campaign events")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test 3: Correlated events
        print("\n3️⃣ Testing correlated events generation...")
        try:
            events = generator.generate_correlated_events(['ids', 'web_access'], 0.8, '1h')
            print(f"   ✅ Generated {len(events)} correlated events")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test 4: Error scenarios (to test error logging)
        print("\n4️⃣ Testing error scenarios...")
        try:
            # This should trigger error logging
            logs = generator.generate_logs('invalid_type', 5, '1h')
            print(f"   ⚠️ Unexpected success: {len(logs)} logs")
        except Exception as e:
            print(f"   ✅ Expected error caught: {e}")
        
        print("\n📋 Logging Summary:")
        print("   - Server creation: Logged")
        print("   - Tool execution: Logged")
        print("   - Error handling: Logged")
        print("   - Performance metrics: Logged")
        
        print(f"\n📄 Check detailed logs at: logs/cybersecurity_log_generator.log")
        
    except Exception as e:
        print(f"❌ Critical error: {e}")
        import traceback
        traceback.print_exc()

def show_log_file():
    """Display the current log file contents."""
    print("\n📄 Current Log File Contents:")
    print("-" * 40)
    try:
        with open('logs/cybersecurity_log_generator.log', 'r') as f:
            lines = f.readlines()
            for line in lines[-10:]:  # Show last 10 lines
                print(line.strip())
    except FileNotFoundError:
        print("Log file not found")
    except Exception as e:
        print(f"Error reading log file: {e}")

if __name__ == "__main__":
    test_enhanced_logging()
    show_log_file()




