#!/usr/bin/env python3
"""
Comprehensive Test Suite for Deployed MCP Server
Tests all endpoints, tools, and functionality of the remote MCP server.
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://127.0.0.1:8001"
MCP_URL = f"{BASE_URL}/mcp"
HEALTH_URL = f"{BASE_URL}/health"
DOCS_URL = f"{BASE_URL}/docs"

class MCPTester:
    def __init__(self):
        self.session_id = None
        self.test_results = []
        
    def log_test(self, test_name, success, details=""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        
    def test_server_connectivity(self):
        """Test basic server connectivity"""
        print("🔍 Testing Server Connectivity...")
        print("=" * 50)
        
        # Test 1: Root endpoint
        try:
            response = requests.get(BASE_URL, timeout=10)
            if response.status_code == 200:
                self.log_test("Root Endpoint", True, f"Status: {response.status_code}")
            else:
                self.log_test("Root Endpoint", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Root Endpoint", False, f"Error: {e}")
            
        # Test 2: Health endpoint
        try:
            response = requests.get(HEALTH_URL, timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log_test("Health Check", True, f"Status: {data.get('status', 'unknown')}")
            else:
                self.log_test("Health Check", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Health Check", False, f"Error: {e}")
            
        # Test 3: API Documentation
        try:
            response = requests.get(DOCS_URL, timeout=10)
            if response.status_code == 200:
                self.log_test("API Documentation", True, f"Status: {response.status_code}")
            else:
                self.log_test("API Documentation", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("API Documentation", False, f"Error: {e}")
            
    def test_mcp_protocol(self):
        """Test MCP protocol initialization and communication"""
        print("\n🔧 Testing MCP Protocol...")
        print("=" * 50)
        
        # Test 1: MCP Initialize
        try:
            response = requests.post(MCP_URL, json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "mcp/initialize",
                "params": {}
            }, headers={
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json"
            }, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "result" in data:
                    self.log_test("MCP Initialize", True, "Protocol initialized successfully")
                    # Store session info if available
                    if "sessionId" in data.get("result", {}):
                        self.session_id = data["result"]["sessionId"]
                else:
                    self.log_test("MCP Initialize", False, f"Unexpected response: {data}")
            else:
                self.log_test("MCP Initialize", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("MCP Initialize", False, f"Error: {e}")
            
        # Test 2: List Tools
        try:
            response = requests.post(MCP_URL, json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }, headers={
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json"
            }, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "result" in data and "tools" in data["result"]:
                    tools = data["result"]["tools"]
                    self.log_test("List Tools", True, f"Found {len(tools)} tools")
                    # Log available tools
                    for tool in tools[:5]:  # Show first 5 tools
                        print(f"    📋 {tool.get('name', 'Unknown')}: {tool.get('description', 'No description')[:50]}...")
                else:
                    self.log_test("List Tools", False, f"Unexpected response: {data}")
            else:
                self.log_test("List Tools", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("List Tools", False, f"Error: {e}")
            
    def test_log_generation_tools(self):
        """Test core log generation tools"""
        print("\n📊 Testing Log Generation Tools...")
        print("=" * 50)
        
        # Test 1: Generate Basic Logs
        try:
            response = requests.post(MCP_URL, json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "generate_logs",
                    "arguments": {
                        "log_type": "ids",
                        "count": 5,
                        "time_range": "1h"
                    }
                }
            }, headers={
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json"
            }, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if "result" in data:
                    result = data["result"]
                    if "content" in result:
                        self.log_test("Generate IDS Logs", True, f"Generated {len(result['content'])} logs")
                    else:
                        self.log_test("Generate IDS Logs", False, f"Unexpected result: {result}")
                else:
                    self.log_test("Generate IDS Logs", False, f"Unexpected response: {data}")
            else:
                self.log_test("Generate IDS Logs", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Generate IDS Logs", False, f"Error: {e}")
            
        # Test 2: Generate SIEM Priority Logs
        try:
            response = requests.post(MCP_URL, json={
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "generate_siem_priority_logs",
                    "arguments": {
                        "category": "endpoint",
                        "count": 3,
                        "time_range": "1h"
                    }
                }
            }, headers={
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json"
            }, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if "result" in data:
                    result = data["result"]
                    if "content" in result:
                        self.log_test("Generate SIEM Priority Logs", True, f"Generated {len(result['content'])} logs")
                    else:
                        self.log_test("Generate SIEM Priority Logs", False, f"Unexpected result: {result}")
                else:
                    self.log_test("Generate SIEM Priority Logs", False, f"Unexpected response: {data}")
            else:
                self.log_test("Generate SIEM Priority Logs", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Generate SIEM Priority Logs", False, f"Error: {e}")
            
    def test_export_functionality(self):
        """Test log export functionality"""
        print("\n📤 Testing Export Functionality...")
        print("=" * 50)
        
        # Test 1: Export Logs (JSON format)
        try:
            # First generate some logs
            generate_response = requests.post(MCP_URL, json={
                "jsonrpc": "2.0",
                "id": 5,
                "method": "tools/call",
                "params": {
                    "name": "generate_logs",
                    "arguments": {
                        "log_type": "firewall",
                        "count": 3,
                        "time_range": "1h"
                    }
                }
            }, headers={
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json"
            }, timeout=30)
            
            if generate_response.status_code == 200:
                generate_data = generate_response.json()
                if "result" in generate_data and "content" in generate_data["result"]:
                    logs = generate_data["result"]["content"]
                    
                    # Now test export
                    export_response = requests.post(MCP_URL, json={
                        "jsonrpc": "2.0",
                        "id": 6,
                        "method": "tools/call",
                        "params": {
                            "name": "export_logs",
                            "arguments": {
                                "events_json": json.dumps(logs),
                                "format": "json",
                                "output_path": "/tmp/test_export.json"
                            }
                        }
                    }, headers={
                        "Accept": "application/json, text/event-stream",
                        "Content-Type": "application/json"
                    }, timeout=30)
                    
                    if export_response.status_code == 200:
                        export_data = export_response.json()
                        if "result" in export_data:
                            self.log_test("Export Logs (JSON)", True, "Export completed successfully")
                        else:
                            self.log_test("Export Logs (JSON)", False, f"Unexpected response: {export_data}")
                    else:
                        self.log_test("Export Logs (JSON)", False, f"Status: {export_response.status_code}")
                else:
                    self.log_test("Export Logs (JSON)", False, "Failed to generate logs for export")
            else:
                self.log_test("Export Logs (JSON)", False, "Failed to generate logs for export")
        except Exception as e:
            self.log_test("Export Logs (JSON)", False, f"Error: {e}")
            
    def test_pillar_generation(self):
        """Test cyberdefense pillar log generation"""
        print("\n🛡️ Testing Cyberdefense Pillar Generation...")
        print("=" * 50)
        
        # Test 1: Generate Pillar Logs
        try:
            response = requests.post(MCP_URL, json={
                "jsonrpc": "2.0",
                "id": 7,
                "method": "tools/call",
                "params": {
                    "name": "generate_pillar_logs",
                    "arguments": {
                        "pillar": "endpoint_security",
                        "count": 3,
                        "time_range": "1h"
                    }
                }
            }, headers={
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json"
            }, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if "result" in data:
                    result = data["result"]
                    if "content" in result:
                        self.log_test("Generate Pillar Logs", True, f"Generated {len(result['content'])} logs")
                    else:
                        self.log_test("Generate Pillar Logs", False, f"Unexpected result: {result}")
                else:
                    self.log_test("Generate Pillar Logs", False, f"Unexpected response: {data}")
            else:
                self.log_test("Generate Pillar Logs", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Generate Pillar Logs", False, f"Error: {e}")
            
    def test_server_performance(self):
        """Test server performance and response times"""
        print("\n⚡ Testing Server Performance...")
        print("=" * 50)
        
        # Test response times for different endpoints
        endpoints = [
            ("Health Check", HEALTH_URL, "GET"),
            ("Root Endpoint", BASE_URL, "GET"),
            ("MCP Initialize", MCP_URL, "POST")
        ]
        
        for name, url, method in endpoints:
            try:
                start_time = time.time()
                if method == "GET":
                    response = requests.get(url, timeout=10)
                else:
                    response = requests.post(url, json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "mcp/initialize",
                        "params": {}
                    }, headers={
                        "Accept": "application/json, text/event-stream",
                        "Content-Type": "application/json"
                    }, timeout=10)
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # Convert to milliseconds
                
                if response.status_code == 200:
                    self.log_test(f"{name} Performance", True, f"Response time: {response_time:.2f}ms")
                else:
                    self.log_test(f"{name} Performance", False, f"Status: {response.status_code}, Time: {response_time:.2f}ms")
            except Exception as e:
                self.log_test(f"{name} Performance", False, f"Error: {e}")
                
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n📊 COMPREHENSIVE TEST REPORT")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"📈 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📊 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  • {result['test']}: {result['details']}")
        
        print(f"\n🎯 Server Status: {'✅ HEALTHY' if failed_tests == 0 else '⚠️ ISSUES DETECTED'}")
        print(f"🔗 Server URL: {BASE_URL}")
        print(f"📚 API Docs: {DOCS_URL}")
        print(f"❤️ Health: {HEALTH_URL}")
        print(f"🔧 MCP Endpoint: {MCP_URL}")
        
        return failed_tests == 0

def main():
    """Main test execution"""
    print("🧪 COMPREHENSIVE MCP SERVER TEST SUITE")
    print("=" * 60)
    print(f"🎯 Target Server: {BASE_URL}")
    print(f"⏰ Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    tester = MCPTester()
    
    # Run all test suites
    tester.test_server_connectivity()
    tester.test_mcp_protocol()
    tester.test_log_generation_tools()
    tester.test_export_functionality()
    tester.test_pillar_generation()
    tester.test_server_performance()
    
    # Generate final report
    success = tester.generate_report()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ALL TESTS PASSED! Server is fully functional!")
    else:
        print("⚠️ SOME TESTS FAILED! Check the details above.")
    print("=" * 60)
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
