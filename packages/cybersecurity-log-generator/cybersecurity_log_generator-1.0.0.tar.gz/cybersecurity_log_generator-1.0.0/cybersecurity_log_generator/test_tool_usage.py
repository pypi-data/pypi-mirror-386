#!/usr/bin/env python3
"""
Test correct tool usage patterns for MCP tools
"""

import requests
import json

def test_correct_tool_usage():
    """Test the correct way to use MCP tools."""
    print("🧪 Testing Correct MCP Tool Usage Patterns")
    print("=" * 60)
    
    base_url = "http://localhost:8003/mcp"
    
    # Test 1: Generate logs correctly
    print("\n1️⃣ Testing generate_logs tool:")
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "generate_logs",
            "arguments": {
                "log_type": "ids",
                "count": 2,
                "time_range": "1h"
            }
        }
    }
    
    try:
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/event-stream'
        }
        response = requests.post(base_url, json=payload, headers=headers, timeout=10)
        result = response.json()
        print(f"✅ generate_logs result: {result.get('result', {}).get('success', False)}")
        
        # Extract the logs for analysis
        if result.get('result', {}).get('success'):
            logs_data = result['result']['logs']
            logs_json = json.dumps(logs_data)
            print(f"📊 Generated {len(logs_data)} logs")
            
            # Test 2: Analyze logs correctly
            print("\n2️⃣ Testing analyze_log_patterns tool:")
            analyze_payload = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "analyze_log_patterns",
                    "arguments": {
                        "events_json": logs_json,  # Pass the JSON string
                        "analysis_type": "security"  # Correct parameter
                    }
                }
            }
            
            analyze_response = requests.post(base_url, json=analyze_payload, headers=headers, timeout=10)
            analyze_result = analyze_response.json()
            print(f"✅ analyze_log_patterns result: {analyze_result.get('result', {}).get('success', False)}")
            
            if analyze_result.get('result', {}).get('success'):
                print("📈 Analysis completed successfully!")
            else:
                print(f"❌ Analysis failed: {analyze_result.get('error', 'Unknown error')}")
                
    except Exception as e:
        print(f"❌ Error: {e}")

    # Test 3: Generate correlated events correctly
    print("\n3️⃣ Testing generate_correlated_events tool:")
    correlated_payload = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "generate_correlated_events",
            "arguments": {
                "log_types": "ids,firewall",  # Correct parameter
                "count": 10,  # Correct parameter
                "correlation_strength": 0.7  # Correct parameter
            }
        }
    }
    
    try:
        correlated_response = requests.post(base_url, json=correlated_payload, headers=headers, timeout=10)
        correlated_result = correlated_response.json()
        print(f"✅ generate_correlated_events result: {correlated_result.get('result', {}).get('success', False)}")
        
        if correlated_result.get('result', {}).get('success'):
            print("🔗 Correlated events generated successfully!")
        else:
            print(f"❌ Correlated events failed: {correlated_result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_correct_tool_usage()
