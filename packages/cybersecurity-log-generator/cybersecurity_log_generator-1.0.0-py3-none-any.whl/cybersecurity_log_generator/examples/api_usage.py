#!/usr/bin/env python3
"""
API usage examples for cybersecurity-log-generator.
"""

import requests
import json
import time


def test_api_endpoints():
    """Test all API endpoints."""
    base_url = "http://localhost:9021"
    
    print("=== Testing Cybersecurity Log Generator API ===")
    
    # Test root endpoint
    print("\n1. Testing root endpoint...")
    try:
        response = requests.get(f"{base_url}/")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to API server. Make sure it's running on localhost:9021")
        return False
    
    # Test health check
    print("\n2. Testing health check...")
    response = requests.get(f"{base_url}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test get supported types
    print("\n3. Testing get supported types...")
    response = requests.get(f"{base_url}/types")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Supported log types: {data['log_types'][:5]}...")  # Show first 5
    
    # Test get supported pillars
    print("\n4. Testing get supported pillars...")
    response = requests.get(f"{base_url}/pillars")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Supported pillars: {data['pillars'][:5]}...")  # Show first 5
    
    return True


def test_log_generation():
    """Test log generation endpoints."""
    base_url = "http://localhost:9021"
    
    print("\n=== Testing Log Generation ===")
    
    # Test basic log generation
    print("\n1. Testing basic log generation...")
    payload = {
        "log_type": "ids",
        "count": 5,
        "time_range": "1h"
    }
    
    response = requests.post(f"{base_url}/generate", json=payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Success: {data['success']}")
        print(f"Count: {data['count']}")
        print(f"Message: {data['message']}")
        print(f"Sample log: {data['logs'][0] if data['logs'] else 'No logs'}")
    else:
        print(f"Error: {response.text}")
    
    # Test pillar log generation
    print("\n2. Testing pillar log generation...")
    payload = {
        "pillar": "authentication",
        "count": 3,
        "time_range": "30m"
    }
    
    response = requests.post(f"{base_url}/pillar", json=payload)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Success: {data['success']}")
        print(f"Count: {data['count']}")
        print(f"Message: {data['message']}")
        print(f"Sample log: {data['logs'][0] if data['logs'] else 'No logs'}")
    else:
        print(f"Error: {response.text}")


def test_error_handling():
    """Test error handling."""
    base_url = "http://localhost:9021"
    
    print("\n=== Testing Error Handling ===")
    
    # Test invalid log type
    print("\n1. Testing invalid log type...")
    payload = {
        "log_type": "invalid_type",
        "count": 5
    }
    
    response = requests.post(f"{base_url}/generate", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test invalid pillar
    print("\n2. Testing invalid pillar...")
    payload = {
        "pillar": "invalid_pillar",
        "count": 5
    }
    
    response = requests.post(f"{base_url}/pillar", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test missing required fields
    print("\n3. Testing missing required fields...")
    payload = {
        "count": 5
    }
    
    response = requests.post(f"{base_url}/generate", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")


def test_performance():
    """Test API performance."""
    base_url = "http://localhost:9021"
    
    print("\n=== Testing API Performance ===")
    
    # Test with different log counts
    test_cases = [10, 50, 100]
    
    for count in test_cases:
        print(f"\nTesting with {count} logs...")
        
        payload = {
            "log_type": "ids",
            "count": count,
            "time_range": "1h"
        }
        
        start_time = time.time()
        response = requests.post(f"{base_url}/generate", json=payload)
        end_time = time.time()
        
        if response.status_code == 200:
            data = response.json()
            generation_time = end_time - start_time
            logs_per_second = count / generation_time
            
            print(f"Status: {response.status_code}")
            print(f"Generation time: {generation_time:.2f} seconds")
            print(f"Logs per second: {logs_per_second:.2f}")
            print(f"Actual count: {data['count']}")
        else:
            print(f"Error: {response.status_code} - {response.text}")


def main():
    """Run all API tests."""
    print("Cybersecurity Log Generator - API Usage Examples")
    print("=" * 60)
    
    # Test basic endpoints
    if not test_api_endpoints():
        print("\nSkipping other tests due to connection error.")
        return 1
    
    # Test log generation
    test_log_generation()
    
    # Test error handling
    test_error_handling()
    
    # Test performance
    test_performance()
    
    print("\n=== API Testing Complete ===")
    print("All API tests completed!")
    
    return 0


if __name__ == "__main__":
    exit(main())
