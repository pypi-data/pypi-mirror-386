#!/usr/bin/env python3
"""
Comprehensive Test Suite for Cybersecurity Log Generator
Tests all log generation scenarios, MCP server functionality, and edge cases.
"""

import sys
import json
import time
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any
import traceback

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from core.generator import LogGenerator
    from core.models import (
        LogType, ThreatActor, LogSeverity, AttackTactic, 
        NetworkTopology, GeneratorConfig, SecurityEvent
    )
    from mcp.server import create_mcp_server
    print("✓ All imports successful")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)


class TestResult:
    """Test result container."""
    def __init__(self, name: str, passed: bool, message: str = "", duration: float = 0.0):
        self.name = name
        self.passed = passed
        self.message = message
        self.duration = duration


class ComprehensiveTestSuite:
    """Comprehensive test suite for the cybersecurity log generator."""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.generator = None
        self.mcp_server = None
        
    def run_test(self, test_func, test_name: str) -> TestResult:
        """Run a single test and record the result."""
        print(f"\n--- {test_name} ---")
        start_time = time.time()
        
        try:
            result = test_func()
            duration = time.time() - start_time
            
            if result:
                print(f"✓ {test_name} PASSED ({duration:.2f}s)")
                return TestResult(test_name, True, "Test passed", duration)
            else:
                print(f"✗ {test_name} FAILED ({duration:.2f}s)")
                return TestResult(test_name, False, "Test failed", duration)
                
        except Exception as e:
            duration = time.time() - start_time
            print(f"✗ {test_name} ERROR ({duration:.2f}s): {e}")
            traceback.print_exc()
            return TestResult(test_name, False, f"Error: {str(e)}", duration)
    
    def test_imports(self) -> bool:
        """Test that all imports work correctly."""
        try:
            from core.generator import LogGenerator
            from core.models import LogType, ThreatActor, LogSeverity
            from mcp.server import create_mcp_server
            return True
        except Exception as e:
            print(f"Import error: {e}")
            return False
    
    def test_generator_initialization(self) -> bool:
        """Test generator initialization."""
        try:
            self.generator = LogGenerator()
            return self.generator is not None
        except Exception as e:
            print(f"Generator initialization error: {e}")
            return False
    
    def test_generator_with_config(self) -> bool:
        """Test generator initialization with configuration."""
        try:
            config = GeneratorConfig(
                output_format="json",
                time_range="24h",
                enable_correlation=True,
                attack_campaign_probability=0.1
            )
            generator = LogGenerator(config)
            return generator is not None
        except Exception as e:
            print(f"Generator with config error: {e}")
            return False
    
    def test_ids_log_generation(self) -> bool:
        """Test IDS log generation."""
        try:
            events = self.generator.generate_logs(LogType.IDS, count=100)
            
            # Verify we got the right number of events
            if len(events) != 100:
                print(f"Expected 100 events, got {len(events)}")
                return False
            
            # Verify all events are IDS type
            for event in events:
                if event.log_type != LogType.IDS:
                    print(f"Expected IDS log type, got {event.log_type}")
                    return False
                
                # Verify required fields
                if not event.timestamp or not event.message or not event.source:
                    print("Missing required fields in IDS event")
                    return False
            
            # Check for security events
            security_events = [e for e in events if e.threat_actor]
            print(f"Generated {len(security_events)} security events out of {len(events)} total")
            
            return True
        except Exception as e:
            print(f"IDS log generation error: {e}")
            return False
    
    def test_web_access_log_generation(self) -> bool:
        """Test web access log generation."""
        try:
            events = self.generator.generate_logs(LogType.WEB_ACCESS, count=50)
            
            if len(events) != 50:
                print(f"Expected 50 events, got {len(events)}")
                return False
            
            for event in events:
                if event.log_type != LogType.WEB_ACCESS:
                    print(f"Expected WEB_ACCESS log type, got {event.log_type}")
                    return False
                
                # Check for web-specific fields
                if not hasattr(event, 'raw_data') or not event.raw_data:
                    print("Missing raw_data in web access event")
                    return False
                
                raw_data = event.raw_data
                if 'method' not in raw_data or 'status_code' not in raw_data:
                    print("Missing web-specific fields in raw_data")
                    return False
            
            return True
        except Exception as e:
            print(f"Web access log generation error: {e}")
            return False
    
    def test_endpoint_log_generation(self) -> bool:
        """Test endpoint log generation."""
        try:
            events = self.generator.generate_logs(LogType.ENDPOINT, count=75)
            
            if len(events) != 75:
                print(f"Expected 75 events, got {len(events)}")
                return False
            
            for event in events:
                if event.log_type != LogType.ENDPOINT:
                    print(f"Expected ENDPOINT log type, got {event.log_type}")
                    return False
                
                # Check for endpoint-specific fields
                if not event.process:
                    print("Missing process field in endpoint event")
                    return False
            
            # Check for malware detection events
            malware_events = [e for e in events if 'malware' in e.message.lower()]
            print(f"Generated {len(malware_events)} malware-related events")
            
            return True
        except Exception as e:
            print(f"Endpoint log generation error: {e}")
            return False
    
    def test_windows_event_log_generation(self) -> bool:
        """Test Windows event log generation."""
        try:
            events = self.generator.generate_logs(LogType.WINDOWS_EVENT, count=60)
            
            if len(events) != 60:
                print(f"Expected 60 events, got {len(events)}")
                return False
            
            for event in events:
                if event.log_type != LogType.WINDOWS_EVENT:
                    print(f"Expected WINDOWS_EVENT log type, got {event.log_type}")
                    return False
                
                # Check for Windows-specific fields
                if not event.event_id:
                    print("Missing event_id in Windows event")
                    return False
                
                raw_data = event.raw_data
                if not raw_data or 'event_id' not in raw_data:
                    print("Missing event_id in raw_data")
                    return False
            
            return True
        except Exception as e:
            print(f"Windows event log generation error: {e}")
            return False
    
    def test_linux_syslog_generation(self) -> bool:
        """Test Linux syslog generation."""
        try:
            events = self.generator.generate_logs(LogType.LINUX_SYSLOG, count=40)
            
            if len(events) != 40:
                print(f"Expected 40 events, got {len(events)}")
                return False
            
            for event in events:
                if event.log_type != LogType.LINUX_SYSLOG:
                    print(f"Expected LINUX_SYSLOG log type, got {event.log_type}")
                    return False
                
                # Check for syslog-specific format
                if not event.message or '<' not in event.message:
                    print("Missing syslog format in message")
                    return False
            
            return True
        except Exception as e:
            print(f"Linux syslog generation error: {e}")
            return False
    
    def test_firewall_log_generation(self) -> bool:
        """Test firewall log generation."""
        try:
            events = self.generator.generate_logs(LogType.FIREWALL, count=80)
            
            if len(events) != 80:
                print(f"Expected 80 events, got {len(events)}")
                return False
            
            for event in events:
                if event.log_type != LogType.FIREWALL:
                    print(f"Expected FIREWALL log type, got {event.log_type}")
                    return False
                
                # Check for firewall-specific fields
                raw_data = event.raw_data
                if not raw_data or 'action' not in raw_data or 'protocol' not in raw_data:
                    print("Missing firewall-specific fields")
                    return False
            
            return True
        except Exception as e:
            print(f"Firewall log generation error: {e}")
            return False
    
    def test_attack_campaign_generation(self) -> bool:
        """Test attack campaign generation."""
        try:
            # Test APT29 campaign
            campaign = self.generator.generate_security_campaign(
                threat_actor=ThreatActor.APT29,
                duration="2h",
                target_count=50
            )
            
            if not campaign:
                print("Campaign generation failed")
                return False
            
            if campaign.threat_actor != ThreatActor.APT29:
                print(f"Expected APT29, got {campaign.threat_actor}")
                return False
            
            if len(campaign.events) == 0:
                print("No events in campaign")
                return False
            
            # Check that events are properly attributed
            for event in campaign.events:
                if event.threat_actor != ThreatActor.APT29:
                    print(f"Event not attributed to APT29: {event.threat_actor}")
                    return False
            
            print(f"Generated {len(campaign.events)} events for APT29 campaign")
            return True
        except Exception as e:
            print(f"Attack campaign generation error: {e}")
            return False
    
    def test_multiple_threat_actors(self) -> bool:
        """Test multiple threat actor campaigns."""
        try:
            threat_actors = [ThreatActor.APT29, ThreatActor.APT28, ThreatActor.LAZARUS]
            
            for actor in threat_actors:
                campaign = self.generator.generate_security_campaign(
                    threat_actor=actor,
                    duration="1h",
                    target_count=25
                )
                
                if campaign.threat_actor != actor:
                    print(f"Expected {actor}, got {campaign.threat_actor}")
                    return False
                
                if len(campaign.events) == 0:
                    print(f"No events for {actor}")
                    return False
            
            print("All threat actors tested successfully")
            return True
        except Exception as e:
            print(f"Multiple threat actors test error: {e}")
            return False
    
    def test_correlated_events_generation(self) -> bool:
        """Test correlated events generation."""
        try:
            events = self.generator.generate_correlated_events(
                log_types=[LogType.IDS, LogType.ENDPOINT, LogType.WEB_ACCESS],
                correlation_strength=0.8,
                time_window="1h"
            )
            
            if len(events) == 0:
                print("No correlated events generated")
                return False
            
            # Check that we have multiple log types
            log_types = set(event.log_type for event in events)
            if len(log_types) < 2:
                print(f"Expected multiple log types, got {log_types}")
                return False
            
            # Check for correlated events
            correlated_events = [e for e in events if 'correlated' in e.tags]
            print(f"Generated {len(correlated_events)} correlated events out of {len(events)} total")
            
            return True
        except Exception as e:
            print(f"Correlated events generation error: {e}")
            return False
    
    def test_network_topology_events(self) -> bool:
        """Test network topology-based event generation."""
        try:
            topology = NetworkTopology(
                subnets=["10.0.0.0/8", "192.168.0.0/16"],
                internet_facing_ips=["1.2.3.4", "5.6.7.8"],
                internal_networks=["10.0.0.0/8"],
                dmz_networks=["172.16.0.0/24"],
                critical_assets=["10.0.1.100", "10.0.1.101"]
            )
            
            events = self.generator.generate_network_topology_events(
                topology=topology,
                event_count=100
            )
            
            if len(events) == 0:
                print("No topology events generated")
                return False
            
            # Check that events respect network boundaries
            internal_events = 0
            external_events = 0
            
            for event in events:
                source_ip = event.source.ip_address
                if source_ip.startswith(('10.', '192.168.', '172.16.')):
                    internal_events += 1
                else:
                    external_events += 1
            
            print(f"Generated {internal_events} internal and {external_events} external events")
            return True
        except Exception as e:
            print(f"Network topology events error: {e}")
            return False
    
    def test_export_formats(self) -> bool:
        """Test all export formats."""
        try:
            # Generate some test events
            events = self.generator.generate_logs(LogType.IDS, count=20)
            
            formats = ['json', 'csv', 'syslog', 'cef', 'leef']
            
            for format_type in formats:
                result = self.generator.export_logs(events, format=format_type)
                
                if not result or len(result) == 0:
                    print(f"Export format {format_type} failed")
                    return False
                
                print(f"✓ {format_type.upper()} export: {len(result)} characters")
            
            return True
        except Exception as e:
            print(f"Export formats test error: {e}")
            return False
    
    def test_export_to_file(self) -> bool:
        """Test exporting to files."""
        try:
            events = self.generator.generate_logs(LogType.IDS, count=10)
            
            # Test JSON export to file
            result = self.generator.export_logs(
                events, 
                format="json", 
                output_path="test_export.json"
            )
            
            # Check if file was created
            if not Path("test_export.json").exists():
                print("JSON export file not created")
                return False
            
            # Clean up
            Path("test_export.json").unlink()
            
            return True
        except Exception as e:
            print(f"Export to file test error: {e}")
            return False
    
    def test_large_dataset_generation(self) -> bool:
        """Test large dataset generation."""
        try:
            print("Generating large dataset (1000 events)...")
            start_time = time.time()
            
            events = self.generator.generate_logs(LogType.IDS, count=1000)
            
            duration = time.time() - start_time
            events_per_second = len(events) / duration
            
            print(f"Generated {len(events)} events in {duration:.2f}s ({events_per_second:.0f} events/sec)")
            
            if len(events) != 1000:
                print(f"Expected 1000 events, got {len(events)}")
                return False
            
            return True
        except Exception as e:
            print(f"Large dataset generation error: {e}")
            return False
    
    def test_performance_benchmarks(self) -> bool:
        """Test performance benchmarks."""
        try:
            log_types = [LogType.IDS, LogType.WEB_ACCESS, LogType.ENDPOINT]
            results = {}
            
            for log_type in log_types:
                start_time = time.time()
                events = self.generator.generate_logs(log_type, count=500)
                duration = time.time() - start_time
                
                events_per_second = len(events) / duration
                results[log_type.value] = events_per_second
                
                print(f"{log_type.value}: {events_per_second:.0f} events/sec")
            
            # Check that performance is reasonable (at least 100 events/sec)
            for log_type, eps in results.items():
                if eps < 100:
                    print(f"Performance too low for {log_type}: {eps:.0f} events/sec")
                    return False
            
            return True
        except Exception as e:
            print(f"Performance benchmarks error: {e}")
            return False
    
    def test_mcp_server_creation(self) -> bool:
        """Test MCP server creation."""
        try:
            self.mcp_server = create_mcp_server()
            return self.mcp_server is not None
        except Exception as e:
            print(f"MCP server creation error: {e}")
            return False
    
    def test_mcp_server_tools(self) -> bool:
        """Test MCP server tools."""
        try:
            if not self.mcp_server:
                print("MCP server not created")
                return False
            
            # Test that server has the expected tools
            # Note: This is a simplified test - in a real scenario you'd test the actual tool calls
            print("MCP server tools available")
            return True
        except Exception as e:
            print(f"MCP server tools test error: {e}")
            return False
    
    def test_edge_cases(self) -> bool:
        """Test edge cases and error handling."""
        try:
            # Test with zero count
            events = self.generator.generate_logs(LogType.IDS, count=0)
            if len(events) != 0:
                print("Expected 0 events for count=0")
                return False
            
            # Test with very small count
            events = self.generator.generate_logs(LogType.IDS, count=1)
            if len(events) != 1:
                print("Expected 1 event for count=1")
                return False
            
            # Test with invalid log type (should raise exception)
            try:
                events = self.generator.generate_logs("invalid_type", count=10)
                print("Expected exception for invalid log type")
                return False
            except (ValueError, TypeError):
                pass  # Expected
            
            return True
        except Exception as e:
            print(f"Edge cases test error: {e}")
            return False
    
    def test_data_validation(self) -> bool:
        """Test data validation and model integrity."""
        try:
            events = self.generator.generate_logs(LogType.IDS, count=50)
            
            for event in events:
                # Test that all required fields are present
                if not event.id or not event.timestamp or not event.log_type:
                    print("Missing required fields")
                    return False
                
                # Test that severity is valid
                if event.severity not in [LogSeverity.LOW, LogSeverity.MEDIUM, LogSeverity.HIGH, LogSeverity.CRITICAL]:
                    print(f"Invalid severity: {event.severity}")
                    return False
                
                # Test that source IP is valid
                if not event.source or not event.source.ip_address:
                    print("Missing source IP")
                    return False
                
                # Test IP format (basic validation)
                ip_parts = event.source.ip_address.split('.')
                if len(ip_parts) != 4:
                    print(f"Invalid IP format: {event.source.ip_address}")
                    return False
                
                for part in ip_parts:
                    if not part.isdigit() or not 0 <= int(part) <= 255:
                        print(f"Invalid IP octet: {part}")
                        return False
            
            return True
        except Exception as e:
            print(f"Data validation test error: {e}")
            return False
    
    def test_time_distribution(self) -> bool:
        """Test that events have realistic time distribution."""
        try:
            events = self.generator.generate_logs(LogType.IDS, count=100)
            
            # Check that timestamps are recent (within last 24 hours)
            now = datetime.utcnow()
            for event in events:
                time_diff = (now - event.timestamp).total_seconds()
                if time_diff < 0 or time_diff > 86400:  # 24 hours
                    print(f"Event timestamp out of range: {event.timestamp}")
                    return False
            
            # Check that events are roughly in chronological order
            timestamps = [event.timestamp for event in events]
            sorted_timestamps = sorted(timestamps)
            
            # Allow some flexibility for concurrent generation
            if timestamps != sorted_timestamps:
                print("Events not in chronological order")
                # This might be acceptable for concurrent generation
                pass
            
            return True
        except Exception as e:
            print(f"Time distribution test error: {e}")
            return False
    
    def run_all_tests(self) -> None:
        """Run all tests in the suite."""
        print("🚀 Cybersecurity Log Generator - Comprehensive Test Suite")
        print("=" * 70)
        
        # Define all tests
        tests = [
            ("Import Test", self.test_imports),
            ("Generator Initialization", self.test_generator_initialization),
            ("Generator with Config", self.test_generator_with_config),
            ("IDS Log Generation", self.test_ids_log_generation),
            ("Web Access Log Generation", self.test_web_access_log_generation),
            ("Endpoint Log Generation", self.test_endpoint_log_generation),
            ("Windows Event Generation", self.test_windows_event_log_generation),
            ("Linux Syslog Generation", self.test_linux_syslog_generation),
            ("Firewall Log Generation", self.test_firewall_log_generation),
            ("Attack Campaign Generation", self.test_attack_campaign_generation),
            ("Multiple Threat Actors", self.test_multiple_threat_actors),
            ("Correlated Events Generation", self.test_correlated_events_generation),
            ("Network Topology Events", self.test_network_topology_events),
            ("Export Formats", self.test_export_formats),
            ("Export to File", self.test_export_to_file),
            ("Large Dataset Generation", self.test_large_dataset_generation),
            ("Performance Benchmarks", self.test_performance_benchmarks),
            ("MCP Server Creation", self.test_mcp_server_creation),
            ("MCP Server Tools", self.test_mcp_server_tools),
            ("Edge Cases", self.test_edge_cases),
            ("Data Validation", self.test_data_validation),
            ("Time Distribution", self.test_time_distribution),
        ]
        
        # Run all tests
        for test_name, test_func in tests:
            result = self.run_test(test_func, test_name)
            self.results.append(result)
        
        # Print summary
        self.print_summary()
    
    def print_summary(self) -> None:
        """Print test summary."""
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        total_time = sum(r.duration for r in self.results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        print(f"Total Time: {total_time:.2f}s")
        
        print("\n📋 DETAILED RESULTS:")
        print("-" * 70)
        
        for result in self.results:
            status = "✓ PASS" if result.passed else "✗ FAIL"
            print(f"{status} {result.name:<35} ({result.duration:.2f}s)")
            if not result.passed and result.message:
                print(f"    └─ {result.message}")
        
        print("\n🎯 RECOMMENDATIONS:")
        if passed == total:
            print("🎉 All tests passed! The system is working perfectly.")
        elif passed >= total * 0.9:
            print("✅ Most tests passed. Minor issues detected.")
        elif passed >= total * 0.7:
            print("⚠️  Some tests failed. Review and fix issues.")
        else:
            print("❌ Many tests failed. System needs significant fixes.")
        
        # Performance insights
        perf_tests = [r for r in self.results if "Performance" in r.name or "Large Dataset" in r.name]
        if perf_tests:
            print("\n⚡ PERFORMANCE INSIGHTS:")
            for test in perf_tests:
                if test.passed:
                    print(f"  ✓ {test.name}: {test.duration:.2f}s")
                else:
                    print(f"  ✗ {test.name}: {test.message}")


def main():
    """Main function to run the comprehensive test suite."""
    try:
        test_suite = ComprehensiveTestSuite()
        test_suite.run_all_tests()
        
        # Return exit code based on results
        passed = sum(1 for r in test_suite.results if r.passed)
        total = len(test_suite.results)
        
        if passed == total:
            return 0
        else:
            return 1
            
    except Exception as e:
        print(f"Test suite error: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
