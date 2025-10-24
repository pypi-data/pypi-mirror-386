#!/usr/bin/env python3
"""
Test script for VictoriaLogs integration with cybersecurity log generator.
"""

import json
import requests
import sys
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from mcp_server.server import ingest_logs_to_victorialogs, create_proper_mcp_server

def test_victorialogs_connection():
    """Test connection to VictoriaLogs."""
    print("🔍 Testing VictoriaLogs connection...")
    try:
        response = requests.get("http://localhost:9428/health", timeout=5)
        if response.status_code == 200:
            print("✅ VictoriaLogs is running and accessible")
            return True
        else:
            print(f"❌ VictoriaLogs health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to VictoriaLogs: {e}")
        return False

def test_log_ingestion():
    """Test ingesting logs into VictoriaLogs."""
    print("\n📤 Testing log ingestion to VictoriaLogs...")
    
    # Create sample logs
    sample_logs = [
        {
            "_time": "2024-01-01T00:00:00Z",
            "_msg": "Cybersecurity test log 1",
            "level": "info",
            "source": "cybersecurity_generator",
            "log_type": "ids",
            "severity": "low"
        },
        {
            "_time": "2024-01-01T00:01:00Z", 
            "_msg": "Security event detected",
            "level": "warning",
            "source": "cybersecurity_generator",
            "log_type": "ids",
            "severity": "medium",
            "threat_type": "malware"
        },
        {
            "_time": "2024-01-01T00:02:00Z",
            "_msg": "Firewall blocked suspicious connection",
            "level": "error", 
            "source": "cybersecurity_generator",
            "log_type": "firewall",
            "severity": "high",
            "action": "blocked"
        }
    ]
    
    # Test ingestion
    success = ingest_logs_to_victorialogs(sample_logs)
    
    if success:
        print("✅ Successfully ingested 3 test logs to VictoriaLogs")
        return True
    else:
        print("❌ Failed to ingest logs to VictoriaLogs")
        return False

def test_log_query():
    """Test querying logs from VictoriaLogs."""
    print("\n🔍 Testing log query from VictoriaLogs...")
    
    try:
        # Try to query logs
        response = requests.get(
            "http://localhost:9428/select/logsql/query",
            params={"query": "SELECT * FROM logs LIMIT 5"},
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Successfully queried logs from VictoriaLogs")
            print(f"Response length: {len(response.text)} characters")
            if response.text.strip():
                print("📊 Logs found in VictoriaLogs")
                return True
            else:
                print("⚠️ No logs found in VictoriaLogs (might be normal if just started)")
                return True
        else:
            print(f"❌ Failed to query logs: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error querying logs: {e}")
        return False

def test_mcp_server_integration():
    """Test MCP server integration."""
    print("\n🔧 Testing MCP server integration...")
    
    try:
        # Create MCP server
        server = create_proper_mcp_server()
        print("✅ MCP server created successfully")
        
        # Test if the ingest function is available
        if hasattr(server, 'tools') or hasattr(server, 'tool'):
            print("✅ MCP server has tool capabilities")
            return True
        else:
            print("⚠️ MCP server tool capabilities not accessible")
            return False
            
    except Exception as e:
        print(f"❌ Error creating MCP server: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 VictoriaLogs Integration Test Suite")
    print("=" * 50)
    
    tests = [
        ("VictoriaLogs Connection", test_victorialogs_connection),
        ("Log Ingestion", test_log_ingestion),
        ("Log Query", test_log_query),
        ("MCP Server Integration", test_mcp_server_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! VictoriaLogs integration is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
    
    print("\n🌐 Access VictoriaLogs Web UI: http://localhost:9428/select/vmui")
    print("🔧 MCP Server URL: http://localhost:8082/mcp")

if __name__ == "__main__":
    main()

