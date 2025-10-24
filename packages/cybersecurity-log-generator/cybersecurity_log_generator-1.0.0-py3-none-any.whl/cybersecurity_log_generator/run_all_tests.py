#!/usr/bin/env python3
"""
Master Test Runner for Cybersecurity Log Generator
Orchestrates all test suites and provides comprehensive testing coverage.
"""

import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple
import json

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))


class MasterTestRunner:
    """Master test runner that orchestrates all test suites."""
    
    def __init__(self):
        self.test_suites = []
        self.results = {}
        self.start_time = None
        self.end_time = None
    
    def run_command(self, command: str, description: str) -> Tuple[bool, str, float]:
        """Run a command and return success status, output, and duration."""
        print(f"\n{'='*60}")
        print(f"🧪 {description}")
        print(f"{'='*60}")
        print(f"Running: {command}")
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                check=True, 
                capture_output=True, 
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            duration = time.time() - start_time
            return True, result.stdout, duration
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return False, "Test timed out after 5 minutes", duration
            
        except subprocess.CalledProcessError as e:
            duration = time.time() - start_time
            error_output = f"Exit code {e.returncode}\nSTDOUT: {e.stdout}\nSTDERR: {e.stderr}"
            return False, error_output, duration
            
        except Exception as e:
            duration = time.time() - start_time
            return False, f"Exception: {str(e)}", duration
    
    def run_basic_functionality_tests(self) -> Dict[str, Any]:
        """Run basic functionality tests."""
        print("\n🔧 BASIC FUNCTIONALITY TESTS")
        print("=" * 50)
        
        # Test imports
        success, output, duration = self.run_command(
            "python -c \"from core.generator import LogGenerator; from core.models import LogType; print('Imports successful')\"",
            "Import Test"
        )
        
        # Test basic generation
        success, output, duration = self.run_command(
            "python test_generator.py",
            "Basic Generator Test"
        )
        
        return {
            'name': 'Basic Functionality',
            'success': success,
            'output': output,
            'duration': duration,
            'details': 'Core functionality and imports'
        }
    
    def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run comprehensive test suite."""
        print("\n🧪 COMPREHENSIVE TEST SUITE")
        print("=" * 50)
        
        success, output, duration = self.run_command(
            "python comprehensive_test_suite.py",
            "Comprehensive Test Suite"
        )
        
        return {
            'name': 'Comprehensive Tests',
            'success': success,
            'output': output,
            'duration': duration,
            'details': 'All core functionality, generators, MCP server, edge cases'
        }
    
    def run_scenario_tests(self) -> Dict[str, Any]:
        """Run cybersecurity scenario tests."""
        print("\n🛡️ CYBERSECURITY SCENARIO TESTS")
        print("=" * 50)
        
        success, output, duration = self.run_command(
            "python test_log_scenarios.py",
            "Cybersecurity Scenario Tests"
        )
        
        return {
            'name': 'Scenario Tests',
            'success': success,
            'output': output,
            'duration': duration,
            'details': 'Attack scenarios, threat actors, security patterns'
        }
    
    def run_performance_tests(self) -> Dict[str, Any]:
        """Run performance and stress tests."""
        print("\n⚡ PERFORMANCE TESTS")
        print("=" * 50)
        
        success, output, duration = self.run_command(
            "python test_performance.py",
            "Performance and Stress Tests"
        )
        
        return {
            'name': 'Performance Tests',
            'success': success,
            'output': output,
            'duration': duration,
            'details': 'Performance benchmarks, memory usage, stress testing'
        }
    
    def run_example_tests(self) -> Dict[str, Any]:
        """Run example tests."""
        print("\n📚 EXAMPLE TESTS")
        print("=" * 50)
        
        success, output, duration = self.run_command(
            "python examples/basic_usage.py",
            "Basic Usage Examples"
        )
        
        return {
            'name': 'Example Tests',
            'success': success,
            'output': output,
            'duration': duration,
            'details': 'Usage examples and documentation'
        }
    
    def run_mcp_server_tests(self) -> Dict[str, Any]:
        """Run MCP server tests."""
        print("\n🌐 MCP SERVER TESTS")
        print("=" * 50)
        
        # Test MCP server creation
        success, output, duration = self.run_command(
            "python -c \"from mcp.server import create_mcp_server; server = create_mcp_server(); print('MCP server created successfully')\"",
            "MCP Server Creation Test"
        )
        
        return {
            'name': 'MCP Server Tests',
            'success': success,
            'output': output,
            'duration': duration,
            'details': 'MCP server functionality and tools'
        }
    
    def run_export_tests(self) -> Dict[str, Any]:
        """Run export format tests."""
        print("\n📤 EXPORT TESTS")
        print("=" * 50)
        
        # Test all export formats
        export_script = """
from core.generator import LogGenerator
from core.models import LogType

generator = LogGenerator()
events = generator.generate_logs(LogType.IDS, count=100)

formats = ['json', 'csv', 'syslog', 'cef', 'leef']
for fmt in formats:
    result = generator.export_logs(events, format=fmt)
    print(f'{fmt.upper()}: {len(result)} characters')

print('All export formats tested successfully')
"""
        
        success, output, duration = self.run_command(
            f"python -c \"{export_script}\"",
            "Export Format Tests"
        )
        
        return {
            'name': 'Export Tests',
            'success': success,
            'output': output,
            'duration': duration,
            'details': 'All export formats (JSON, CSV, Syslog, CEF, LEEF)'
        }
    
    def run_integration_tests(self) -> Dict[str, Any]:
        """Run integration tests."""
        print("\n🔗 INTEGRATION TESTS")
        print("=" * 50)
        
        # Test full workflow
        integration_script = """
from core.generator import LogGenerator
from core.models import LogType, ThreatActor

# Initialize generator
generator = LogGenerator()

# Test 1: Generate different log types
log_types = [LogType.IDS, LogType.WEB_ACCESS, LogType.ENDPOINT]
for log_type in log_types:
    events = generator.generate_logs(log_type, count=50)
    print(f'Generated {len(events)} {log_type.value} events')

# Test 2: Generate attack campaign
campaign = generator.generate_security_campaign(
    threat_actor=ThreatActor.APT29,
    duration='1h',
    target_count=100
)
print(f'Generated {len(campaign.events)} campaign events')

# Test 3: Generate correlated events
correlated = generator.generate_correlated_events(
    log_types=[LogType.IDS, LogType.ENDPOINT],
    correlation_strength=0.8,
    time_window='1h'
)
print(f'Generated {len(correlated)} correlated events')

# Test 4: Export in different formats
json_result = generator.export_logs(events, format='json')
csv_result = generator.export_logs(events, format='csv')
print(f'JSON export: {len(json_result)} chars, CSV export: {len(csv_result)} chars')

print('Integration tests completed successfully')
"""
        
        success, output, duration = self.run_command(
            f"python -c \"{integration_script}\"",
            "Integration Tests"
        )
        
        return {
            'name': 'Integration Tests',
            'success': success,
            'output': output,
            'duration': duration,
            'details': 'End-to-end workflow testing'
        }
    
    def run_all_tests(self) -> None:
        """Run all test suites."""
        print("🚀 CYBERSECURITY LOG GENERATOR - MASTER TEST RUNNER")
        print("=" * 70)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        self.start_time = time.time()
        
        # Define all test suites
        test_suites = [
            ("Basic Functionality", self.run_basic_functionality_tests),
            ("Comprehensive Tests", self.run_comprehensive_tests),
            ("Scenario Tests", self.run_scenario_tests),
            ("Performance Tests", self.run_performance_tests),
            ("Example Tests", self.run_example_tests),
            ("MCP Server Tests", self.run_mcp_server_tests),
            ("Export Tests", self.run_export_tests),
            ("Integration Tests", self.run_integration_tests),
        ]
        
        # Run all test suites
        for suite_name, test_func in test_suites:
            try:
                result = test_func()
                self.results[suite_name] = result
                
                status = "✅ PASSED" if result['success'] else "❌ FAILED"
                print(f"\n{status} {suite_name} ({result['duration']:.2f}s)")
                
                if not result['success'] and result['output']:
                    print(f"Error details: {result['output'][:200]}...")
                    
            except Exception as e:
                print(f"\n❌ ERROR {suite_name}: {e}")
                self.results[suite_name] = {
                    'name': suite_name,
                    'success': False,
                    'output': str(e),
                    'duration': 0,
                    'details': 'Test suite execution failed'
                }
        
        self.end_time = time.time()
        self.print_summary()
        self.save_report()
    
    def print_summary(self) -> None:
        """Print comprehensive test summary."""
        print("\n" + "=" * 70)
        print("📊 MASTER TEST SUMMARY")
        print("=" * 70)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results.values() if r['success'])
        failed_tests = total_tests - passed_tests
        total_duration = self.end_time - self.start_time
        
        print(f"Total Test Suites: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print(f"Total Duration: {total_duration:.2f}s")
        
        print("\n📋 DETAILED RESULTS:")
        print("-" * 70)
        
        for suite_name, result in self.results.items():
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            duration = result['duration']
            details = result['details']
            
            print(f"{status} {suite_name:<25} ({duration:>6.2f}s) - {details}")
            
            if not result['success'] and result['output']:
                # Show first few lines of error output
                error_lines = result['output'].split('\n')[:3]
                for line in error_lines:
                    if line.strip():
                        print(f"    └─ {line.strip()}")
        
        print("\n🎯 SYSTEM ASSESSMENT:")
        if passed_tests == total_tests:
            print("🎉 EXCELLENT - All test suites passed! System is fully functional.")
            print("   ✅ Core functionality working")
            print("   ✅ All log types generating correctly")
            print("   ✅ Attack scenarios realistic")
            print("   ✅ Performance meets requirements")
            print("   ✅ MCP server operational")
            print("   ✅ Export formats working")
            print("   ✅ Integration tests passing")
        elif passed_tests >= total_tests * 0.8:
            print("✅ GOOD - Most test suites passed. Minor issues detected.")
            print("   🔧 Review failed tests and address issues")
            print("   📈 System is largely functional")
        elif passed_tests >= total_tests * 0.6:
            print("⚠️  MODERATE - Some test suites failed. System needs attention.")
            print("   🔧 Multiple issues need to be addressed")
            print("   📊 Review failed tests for patterns")
        else:
            print("❌ POOR - Many test suites failed. System needs significant work.")
            print("   🚨 Major issues detected")
            print("   🔧 Comprehensive fixes required")
        
        # Performance insights
        performance_result = self.results.get('Performance Tests', {})
        if performance_result.get('success'):
            print("\n⚡ PERFORMANCE INSIGHTS:")
            print("   📊 Performance tests completed successfully")
            print("   📄 Check performance_report.json for detailed metrics")
        else:
            print("\n⚠️  PERFORMANCE WARNING:")
            print("   📊 Performance tests failed - check system resources")
        
        # Security insights
        scenario_result = self.results.get('Scenario Tests', {})
        if scenario_result.get('success'):
            print("\n🛡️ SECURITY INSIGHTS:")
            print("   🎯 Attack scenarios generating correctly")
            print("   🔍 Threat actors properly simulated")
            print("   📈 Security patterns realistic")
        else:
            print("\n⚠️  SECURITY WARNING:")
            print("   🎯 Attack scenarios need review")
            print("   🔍 Check threat actor simulation")
    
    def save_report(self) -> None:
        """Save detailed test report."""
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_tests': len(self.results),
                'passed_tests': sum(1 for r in self.results.values() if r['success']),
                'failed_tests': sum(1 for r in self.results.values() if not r['success']),
                'total_duration': self.end_time - self.start_time,
                'success_rate': (sum(1 for r in self.results.values() if r['success']) / len(self.results)) * 100
            },
            'results': self.results
        }
        
        # Save JSON report
        with open('master_test_report.json', 'w') as f:
            json.dump(report_data, f, indent=2)
        
        # Save text report
        with open('master_test_report.txt', 'w') as f:
            f.write("CYBERSECURITY LOG GENERATOR - MASTER TEST REPORT\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Duration: {self.end_time - self.start_time:.2f}s\n\n")
            
            f.write("SUMMARY:\n")
            f.write(f"Total Test Suites: {len(self.results)}\n")
            f.write(f"Passed: {sum(1 for r in self.results.values() if r['success'])}\n")
            f.write(f"Failed: {sum(1 for r in self.results.values() if not r['success'])}\n\n")
            
            f.write("DETAILED RESULTS:\n")
            for suite_name, result in self.results.items():
                status = "PASS" if result['success'] else "FAIL"
                f.write(f"{status} {suite_name} ({result['duration']:.2f}s)\n")
                if not result['success'] and result['output']:
                    f.write(f"  Error: {result['output'][:500]}...\n")
        
        print(f"\n📄 Detailed reports saved:")
        print(f"   📊 JSON: master_test_report.json")
        print(f"   📝 Text: master_test_report.txt")


def main():
    """Main function to run all tests."""
    try:
        runner = MasterTestRunner()
        runner.run_all_tests()
        
        # Return exit code based on results
        passed = sum(1 for r in runner.results.values() if r['success'])
        total = len(runner.results)
        
        if passed == total:
            return 0
        else:
            return 1
            
    except Exception as e:
        print(f"Master test runner error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
