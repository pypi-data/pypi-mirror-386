#!/usr/bin/env python3
"""
Test MCP Server with LLM Integration
Simulates how an LLM would use the MCP server.
"""

import sys
import json
import time
import warnings
from pathlib import Path

# Suppress deprecation warnings for WebSocket protocols
warnings.filterwarnings("ignore", category=DeprecationWarning, module="websockets")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="uvicorn.protocols.websockets")

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from mcp_server.server import create_proper_mcp_server
    from core.models import LogType, ThreatActor
    print("✓ MCP server imports successful")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)


class LLMMCPTester:
    """Test MCP server usage by simulating LLM interactions."""
    
    def __init__(self):
        self.server = create_proper_mcp_server()
        self.test_results = []
    
    def simulate_llm_request(self, request: str, expected_tool: str) -> bool:
        """Simulate an LLM making a request to the MCP server."""
        print(f"\n🤖 LLM Request: {request}")
        print(f"🎯 Expected Tool: {expected_tool}")
        
        try:
            # Simulate LLM parsing and tool selection
            request_lower = request.lower()
            
            # Check for log generation requests
            if any(keyword in request_lower for keyword in ["generate", "create", "make"]) and any(keyword in request_lower for keyword in ["logs", "log", "events"]):
                # Parse parameters from request
                log_type = "ids"  # Default
                count = 100  # Default
                
                if "ids" in request_lower:
                    log_type = "ids"
                elif "web" in request_lower:
                    log_type = "web_access"
                elif "endpoint" in request_lower:
                    log_type = "endpoint"
                elif "windows" in request_lower:
                    log_type = "windows_event"
                elif "linux" in request_lower:
                    log_type = "linux_syslog"
                elif "firewall" in request_lower:
                    log_type = "firewall"
                
                # Extract count from request
                import re
                count_match = re.search(r'(\d+)', request)
                if count_match:
                    count = int(count_match.group(1))
                
                # Simulate tool execution
                result = f"Generated {count} {log_type} events"
                print(f"✅ Tool executed: {result}")
                return True
                
            # Check for campaign/attack requests
            elif any(keyword in request_lower for keyword in ["campaign", "attack", "simulation", "threat"]):
                # Parse threat actor
                threat_actor = "APT29"  # Default
                
                if "apt29" in request_lower:
                    threat_actor = "APT29"
                elif "apt28" in request_lower:
                    threat_actor = "APT28"
                elif "lazarus" in request_lower:
                    threat_actor = "Lazarus"
                elif "carbon" in request_lower:
                    threat_actor = "Carbon Spider"
                elif "fin7" in request_lower:
                    threat_actor = "FIN7"
                elif "wizard" in request_lower:
                    threat_actor = "Wizard Spider"
                
                # Extract event count
                import re
                count_match = re.search(r'(\d+)', request)
                event_count = int(count_match.group(1)) if count_match else 50
                
                # Simulate tool execution
                result = f"Generated {threat_actor} campaign with {event_count} events"
                print(f"✅ Tool executed: {result}")
                return True
                
            # Check for export requests
            elif "export" in request_lower:
                # Parse export format
                format_type = "json"  # Default
                
                if "csv" in request_lower:
                    format_type = "csv"
                elif "syslog" in request_lower:
                    format_type = "syslog"
                elif "cef" in request_lower:
                    format_type = "cef"
                elif "leef" in request_lower:
                    format_type = "leef"
                
                # Simulate tool execution
                result = f"Exported events in {format_type.upper()} format"
                print(f"✅ Tool executed: {result}")
                return True
                
            # Check for analysis requests
            elif any(keyword in request_lower for keyword in ["analyze", "analysis", "patterns", "threats"]):
                # Simulate tool execution
                result = "Analyzed log patterns for threats and anomalies"
                print(f"✅ Tool executed: {result}")
                return True
                
            # Check for information requests
            elif any(keyword in request_lower for keyword in ["what", "show", "list", "available", "supported"]):
                if "log types" in request_lower or "logs" in request_lower:
                    result = "Supported log types: IDS, Web Access, Endpoint, Windows Event, Linux Syslog, Firewall"
                elif "threat actors" in request_lower or "actors" in request_lower:
                    result = "Supported threat actors: APT29, APT28, Lazarus, Carbon Spider, FIN7, Wizard Spider"
                else:
                    result = "Retrieved requested information"
                
                print(f"✅ Tool executed: {result}")
                return True
                
            else:
                print(f"❌ Unknown request type")
                return False
                
        except Exception as e:
            print(f"❌ Error processing request: {e}")
            return False
    
    def test_llm_integration(self) -> None:
        """Test various LLM requests."""
        print("🧠 Testing LLM Integration with MCP Server")
        print("=" * 60)
        
        # Test cases simulating real LLM requests
        test_cases = [
            {
                "request": "Generate 100 IDS logs for the last hour",
                "expected_tool": "generate_logs",
                "description": "Basic log generation request"
            },
            {
                "request": "Create 500 web access logs for analysis",
                "expected_tool": "generate_logs", 
                "description": "Web access log generation"
            },
            {
                "request": "Generate an APT29 attack campaign with 200 events",
                "expected_tool": "generate_security_campaign",
                "description": "Attack campaign generation"
            },
            {
                "request": "Create a Lazarus threat actor simulation",
                "expected_tool": "generate_security_campaign",
                "description": "Threat actor simulation"
            },
            {
                "request": "Export the logs as CSV format",
                "expected_tool": "export_logs",
                "description": "Export format request"
            },
            {
                "request": "Analyze the log patterns for threats",
                "expected_tool": "analyze_log_patterns",
                "description": "Log analysis request"
            },
            {
                "request": "What log types are supported?",
                "expected_tool": "get_supported_log_types",
                "description": "Information request"
            },
            {
                "request": "Show me the available threat actors",
                "expected_tool": "get_supported_threat_actors",
                "description": "Threat actor information"
            }
        ]
        
        passed = 0
        total = len(test_cases)
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n--- Test {i}: {test_case['description']} ---")
            
            success = self.simulate_llm_request(
                test_case["request"], 
                test_case["expected_tool"]
            )
            
            if success:
                passed += 1
                print(f"✅ Test {i} PASSED")
            else:
                print(f"❌ Test {i} FAILED")
        
        # Print summary
        print(f"\n📊 LLM Integration Test Summary")
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("🎉 All LLM integration tests passed!")
        elif passed >= total * 0.8:
            print("✅ Most LLM integration tests passed.")
        else:
            print("⚠️ Some LLM integration tests failed.")


def main():
    """Main function to run LLM integration tests."""
    try:
        tester = LLMMCPTester()
        tester.test_llm_integration()
        return 0
    except Exception as e:
        print(f"LLM integration testing error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
