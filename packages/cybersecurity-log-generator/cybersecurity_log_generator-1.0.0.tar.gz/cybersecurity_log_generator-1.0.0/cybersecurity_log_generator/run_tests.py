#!/usr/bin/env python3
"""
Test runner for the Cybersecurity Log Generator.
"""

import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a command and return success status."""
    print(f"\n=== {description} ===")
    print(f"Running: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print("✓ Success")
        if result.stdout:
            print(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed with exit code {e.returncode}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        return False

def main():
    """Main test runner."""
    print("Cybersecurity Log Generator - Test Runner")
    print("=" * 50)
    
    # Change to the project directory
    project_dir = Path(__file__).parent
    print(f"Project directory: {project_dir}")
    
    # Test basic functionality
    print("\n1. Testing basic functionality...")
    basic_test = run_command(
        f"cd {project_dir} && python test_generator.py",
        "Basic Generator Test"
    )
    
    # Test examples
    print("\n2. Testing examples...")
    example_test = run_command(
        f"cd {project_dir} && python examples/basic_usage.py",
        "Basic Usage Example"
    )
    
    # Test MCP server (if available)
    print("\n3. Testing MCP server...")
    try:
        mcp_test = run_command(
            f"cd {project_dir} && python -c \"from mcp.server import create_mcp_server; print('MCP server import successful')\"",
            "MCP Server Import Test"
        )
    except Exception as e:
        print(f"MCP server test skipped: {e}")
        mcp_test = True
    
    # Summary
    print("\n=== Test Summary ===")
    tests = [
        ("Basic Functionality", basic_test),
        ("Examples", example_test),
        ("MCP Server", mcp_test),
    ]
    
    passed = sum(1 for _, result in tests if result)
    total = len(tests)
    
    for name, result in tests:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
