#!/usr/bin/env python3
"""
CLI usage examples for cybersecurity-log-generator.
"""

import subprocess
import sys
import os


def run_cli_command(cmd):
    """Run a CLI command and return the result."""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=30
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)


def test_basic_commands():
    """Test basic CLI commands."""
    print("=== Testing Basic CLI Commands ===")
    
    # Test help
    print("\n1. Testing help command...")
    returncode, stdout, stderr = run_cli_command("cybersecurity-log-gen --help")
    print(f"Return code: {returncode}")
    print(f"Output: {stdout[:200]}...")
    if stderr:
        print(f"Error: {stderr}")
    
    # Test list types
    print("\n2. Testing list types command...")
    returncode, stdout, stderr = run_cli_command("cybersecurity-log-gen list-types")
    print(f"Return code: {returncode}")
    print(f"Output: {stdout[:200]}...")
    if stderr:
        print(f"Error: {stderr}")


def test_log_generation():
    """Test log generation commands."""
    print("\n=== Testing Log Generation Commands ===")
    
    # Test basic log generation
    print("\n1. Testing basic log generation...")
    returncode, stdout, stderr = run_cli_command("cybersecurity-log-gen generate --type ids --count 5")
    print(f"Return code: {returncode}")
    if returncode == 0:
        print(f"Output: {stdout[:200]}...")
    else:
        print(f"Error: {stderr}")
    
    # Test pillar log generation
    print("\n2. Testing pillar log generation...")
    returncode, stdout, stderr = run_cli_command("cybersecurity-log-gen pillar --pillar authentication --count 3")
    print(f"Return code: {returncode}")
    if returncode == 0:
        print(f"Output: {stdout[:200]}...")
    else:
        print(f"Error: {stderr}")


def test_output_files():
    """Test output file generation."""
    print("\n=== Testing Output File Generation ===")
    
    # Test JSON output
    print("\n1. Testing JSON output...")
    returncode, stdout, stderr = run_cli_command("cybersecurity-log-gen generate --type ids --count 3 --output test_output.json")
    print(f"Return code: {returncode}")
    print(f"Output: {stdout}")
    
    if returncode == 0 and os.path.exists("test_output.json"):
        print("JSON file created successfully!")
        with open("test_output.json", 'r') as f:
            content = f.read()
            print(f"File content: {content[:200]}...")
        os.remove("test_output.json")
        print("Test file cleaned up.")
    else:
        print(f"Error: {stderr}")
    
    # Test pillar output
    print("\n2. Testing pillar output...")
    returncode, stdout, stderr = run_cli_command("cybersecurity-log-gen pillar --pillar authentication --count 2 --output test_pillar.json")
    print(f"Return code: {returncode}")
    print(f"Output: {stdout}")
    
    if returncode == 0 and os.path.exists("test_pillar.json"):
        print("Pillar file created successfully!")
        with open("test_pillar.json", 'r') as f:
            content = f.read()
            print(f"File content: {content[:200]}...")
        os.remove("test_pillar.json")
        print("Test file cleaned up.")
    else:
        print(f"Error: {stderr}")


def test_error_handling():
    """Test error handling."""
    print("\n=== Testing Error Handling ===")
    
    # Test invalid log type
    print("\n1. Testing invalid log type...")
    returncode, stdout, stderr = run_cli_command("cybersecurity-log-gen generate --type invalid_type --count 5")
    print(f"Return code: {returncode}")
    print(f"Output: {stdout}")
    print(f"Error: {stderr}")
    
    # Test invalid pillar
    print("\n2. Testing invalid pillar...")
    returncode, stdout, stderr = run_cli_command("cybersecurity-log-gen pillar --pillar invalid_pillar --count 5")
    print(f"Return code: {returncode}")
    print(f"Output: {stdout}")
    print(f"Error: {stderr}")
    
    # Test missing required arguments
    print("\n3. Testing missing required arguments...")
    returncode, stdout, stderr = run_cli_command("cybersecurity-log-gen generate --count 5")
    print(f"Return code: {returncode}")
    print(f"Output: {stdout}")
    print(f"Error: {stderr}")


def test_different_log_types():
    """Test different log types."""
    print("\n=== Testing Different Log Types ===")
    
    log_types = ["ids", "web_access", "endpoint", "windows_event", "linux_syslog", "firewall"]
    
    for log_type in log_types:
        print(f"\nTesting {log_type}...")
        returncode, stdout, stderr = run_cli_command(f"cybersecurity-log-gen generate --type {log_type} --count 2")
        print(f"Return code: {returncode}")
        if returncode == 0:
            print(f"Success: {stdout[:100]}...")
        else:
            print(f"Error: {stderr}")


def test_different_pillars():
    """Test different pillars."""
    print("\n=== Testing Different Pillars ===")
    
    pillars = ["authentication", "network_security", "endpoint_security", "cloud_security", "data_protection"]
    
    for pillar in pillars:
        print(f"\nTesting {pillar}...")
        returncode, stdout, stderr = run_cli_command(f"cybersecurity-log-gen pillar --pillar {pillar} --count 2")
        print(f"Return code: {returncode}")
        if returncode == 0:
            print(f"Success: {stdout[:100]}...")
        else:
            print(f"Error: {stderr}")


def main():
    """Run all CLI tests."""
    print("Cybersecurity Log Generator - CLI Usage Examples")
    print("=" * 60)
    
    # Test basic commands
    test_basic_commands()
    
    # Test log generation
    test_log_generation()
    
    # Test output files
    test_output_files()
    
    # Test error handling
    test_error_handling()
    
    # Test different log types
    test_different_log_types()
    
    # Test different pillars
    test_different_pillars()
    
    print("\n=== CLI Testing Complete ===")
    print("All CLI tests completed!")
    
    return 0


if __name__ == "__main__":
    exit(main())
