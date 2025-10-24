#!/usr/bin/env python3
"""
Performance and Stress Testing Script for Cybersecurity Log Generator
Tests system performance under various loads and conditions.
"""

import sys
import time
import psutil
import threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import traceback
import json

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from core.generator import LogGenerator
    from core.models import LogType, ThreatActor, NetworkTopology
    print("✓ Imports successful")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)


class PerformanceTester:
    """Performance and stress tester for the cybersecurity log generator."""
    
    def __init__(self):
        self.generator = LogGenerator()
        self.results = []
        self.memory_usage = []
        self.cpu_usage = []
    
    def log_performance(self, test_name: str, duration: float, events: int, 
                       memory_mb: float, cpu_percent: float, details: str = ""):
        """Log performance metrics."""
        events_per_second = events / duration if duration > 0 else 0
        memory_per_event = memory_mb / events if events > 0 else 0
        
        result = {
            'test_name': test_name,
            'duration': duration,
            'events': events,
            'events_per_second': events_per_second,
            'memory_mb': memory_mb,
            'memory_per_event': memory_per_event,
            'cpu_percent': cpu_percent,
            'details': details
        }
        
        self.results.append(result)
        
        print(f"📊 {test_name}")
        print(f"   Duration: {duration:.2f}s")
        print(f"   Events: {events:,}")
        print(f"   Events/sec: {events_per_second:.0f}")
        print(f"   Memory: {memory_mb:.1f} MB ({memory_per_event:.3f} MB/event)")
        print(f"   CPU: {cpu_percent:.1f}%")
        if details:
            print(f"   Details: {details}")
        print()
    
    def get_system_metrics(self) -> Tuple[float, float]:
        """Get current system metrics."""
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        cpu_percent = process.cpu_percent()
        return memory_mb, cpu_percent
    
    def test_single_log_type_performance(self, log_type: LogType, count: int) -> Dict[str, Any]:
        """Test performance for a single log type."""
        test_name = f"Single {log_type.value} Generation"
        
        # Get initial metrics
        initial_memory, initial_cpu = self.get_system_metrics()
        
        # Generate events
        start_time = time.time()
        events = self.generator.generate_logs(log_type, count=count)
        end_time = time.time()
        
        # Get final metrics
        final_memory, final_cpu = self.get_system_metrics()
        
        duration = end_time - start_time
        memory_used = final_memory - initial_memory
        
        self.log_performance(
            test_name, duration, len(events), memory_used, final_cpu,
            f"Generated {len(events)} {log_type.value} events"
        )
        
        return {
            'log_type': log_type.value,
            'count': count,
            'duration': duration,
            'events_per_second': len(events) / duration,
            'memory_used': memory_used
        }
    
    def test_all_log_types_performance(self) -> None:
        """Test performance for all log types."""
        print("🚀 Testing All Log Types Performance")
        print("=" * 50)
        
        log_types = [
            LogType.IDS,
            LogType.WEB_ACCESS,
            LogType.ENDPOINT,
            LogType.WINDOWS_EVENT,
            LogType.LINUX_SYSLOG,
            LogType.FIREWALL
        ]
        
        test_count = 1000
        
        for log_type in log_types:
            try:
                self.test_single_log_type_performance(log_type, test_count)
            except Exception as e:
                print(f"✗ Error testing {log_type.value}: {e}")
    
    def test_scaling_performance(self) -> None:
        """Test performance scaling with different event counts."""
        print("\n📈 Testing Performance Scaling")
        print("=" * 50)
        
        test_counts = [100, 500, 1000, 5000, 10000]
        log_type = LogType.IDS
        
        for count in test_counts:
            try:
                self.test_single_log_type_performance(log_type, count)
            except Exception as e:
                print(f"✗ Error testing count {count}: {e}")
    
    def test_memory_efficiency(self) -> None:
        """Test memory efficiency with large datasets."""
        print("\n💾 Testing Memory Efficiency")
        print("=" * 50)
        
        # Test with increasing dataset sizes
        test_counts = [1000, 5000, 10000, 20000]
        log_type = LogType.IDS
        
        for count in test_counts:
            try:
                # Get initial memory
                initial_memory, _ = self.get_system_metrics()
                
                # Generate events
                start_time = time.time()
                events = self.generator.generate_logs(log_type, count=count)
                end_time = time.time()
                
                # Get final memory
                final_memory, final_cpu = self.get_system_metrics()
                
                duration = end_time - start_time
                memory_used = final_memory - initial_memory
                memory_per_event = memory_used / len(events)
                
                self.log_performance(
                    f"Memory Test ({count:,} events)", duration, len(events), 
                    memory_used, final_cpu,
                    f"Memory per event: {memory_per_event:.3f} MB"
                )
                
                # Check for memory leaks
                if memory_per_event > 0.1:  # 100KB per event threshold
                    print(f"⚠️  High memory usage detected: {memory_per_event:.3f} MB per event")
                
            except Exception as e:
                print(f"✗ Error in memory test for count {count}: {e}")
    
    def test_concurrent_generation(self) -> None:
        """Test concurrent log generation."""
        print("\n🔄 Testing Concurrent Generation")
        print("=" * 50)
        
        def generate_logs_worker(log_type: LogType, count: int, results: List):
            """Worker function for concurrent generation."""
            try:
                start_time = time.time()
                events = self.generator.generate_logs(log_type, count=count)
                end_time = time.time()
                
                results.append({
                    'log_type': log_type.value,
                    'count': len(events),
                    'duration': end_time - start_time,
                    'success': True
                })
            except Exception as e:
                results.append({
                    'log_type': log_type.value,
                    'count': 0,
                    'duration': 0,
                    'success': False,
                    'error': str(e)
                })
        
        # Test concurrent generation
        threads = []
        results = []
        
        log_types = [LogType.IDS, LogType.WEB_ACCESS, LogType.ENDPOINT]
        count_per_thread = 500
        
        start_time = time.time()
        
        for log_type in log_types:
            thread = threading.Thread(
                target=generate_logs_worker,
                args=(log_type, count_per_thread, results)
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Analyze results
        successful_results = [r for r in results if r['success']]
        total_events = sum(r['count'] for r in successful_results)
        total_events_per_second = total_events / total_duration
        
        print(f"📊 Concurrent Generation Results:")
        print(f"   Total Duration: {total_duration:.2f}s")
        print(f"   Total Events: {total_events:,}")
        print(f"   Events/sec: {total_events_per_second:.0f}")
        print(f"   Successful Threads: {len(successful_results)}/{len(results)}")
        
        for result in results:
            if result['success']:
                events_per_second = result['count'] / result['duration']
                print(f"   {result['log_type']}: {result['count']} events in {result['duration']:.2f}s ({events_per_second:.0f} events/sec)")
            else:
                print(f"   {result['log_type']}: FAILED - {result.get('error', 'Unknown error')}")
    
    def test_attack_campaign_performance(self) -> None:
        """Test attack campaign generation performance."""
        print("\n🎯 Testing Attack Campaign Performance")
        print("=" * 50)
        
        threat_actors = [ThreatActor.APT29, ThreatActor.APT28, ThreatActor.LAZARUS]
        durations = ["1h", "6h", "24h"]
        target_counts = [50, 200, 500]
        
        for threat_actor in threat_actors:
            for duration in durations:
                for target_count in target_counts:
                    try:
                        # Get initial metrics
                        initial_memory, initial_cpu = self.get_system_metrics()
                        
                        # Generate campaign
                        start_time = time.time()
                        campaign = self.generator.generate_security_campaign(
                            threat_actor=threat_actor,
                            duration=duration,
                            target_count=target_count
                        )
                        end_time = time.time()
                        
                        # Get final metrics
                        final_memory, final_cpu = self.get_system_metrics()
                        
                        duration_seconds = end_time - start_time
                        memory_used = final_memory - initial_memory
                        
                        self.log_performance(
                            f"Campaign {threat_actor.value} ({duration}, {target_count} targets)",
                            duration_seconds, len(campaign.events), memory_used, final_cpu,
                            f"Generated {len(campaign.events)} events for {threat_actor.value}"
                        )
                        
                    except Exception as e:
                        print(f"✗ Error testing campaign {threat_actor.value}: {e}")
    
    def test_export_performance(self) -> None:
        """Test export performance for different formats."""
        print("\n📤 Testing Export Performance")
        print("=" * 50)
        
        # Generate test events
        events = self.generator.generate_logs(LogType.IDS, count=5000)
        formats = ['json', 'csv', 'syslog', 'cef', 'leef']
        
        for format_type in formats:
            try:
                start_time = time.time()
                result = self.generator.export_logs(events, format=format_type)
                end_time = time.time()
                
                duration = end_time - start_time
                output_size = len(result)
                size_mb = output_size / 1024 / 1024
                
                self.log_performance(
                    f"Export {format_type.upper()}", duration, len(events), 
                    size_mb, 0, f"Output size: {size_mb:.2f} MB"
                )
                
            except Exception as e:
                print(f"✗ Error testing {format_type} export: {e}")
    
    def test_correlation_performance(self) -> None:
        """Test correlation performance."""
        print("\n🔗 Testing Correlation Performance")
        print("=" * 50)
        
        correlation_strengths = [0.3, 0.5, 0.8, 0.95]
        time_windows = ["30m", "1h", "2h", "4h"]
        
        for strength in correlation_strengths:
            for time_window in time_windows:
                try:
                    # Get initial metrics
                    initial_memory, initial_cpu = self.get_system_metrics()
                    
                    # Generate correlated events
                    start_time = time.time()
                    events = self.generator.generate_correlated_events(
                        log_types=[LogType.IDS, LogType.ENDPOINT, LogType.WEB_ACCESS],
                        correlation_strength=strength,
                        time_window=time_window
                    )
                    end_time = time.time()
                    
                    # Get final metrics
                    final_memory, final_cpu = self.get_system_metrics()
                    
                    duration = end_time - start_time
                    memory_used = final_memory - initial_memory
                    
                    # Count correlated events
                    correlated_count = len([e for e in events if 'correlated' in e.tags])
                    
                    self.log_performance(
                        f"Correlation (strength={strength}, window={time_window})",
                        duration, len(events), memory_used, final_cpu,
                        f"Correlated events: {correlated_count}"
                    )
                    
                except Exception as e:
                    print(f"✗ Error testing correlation: {e}")
    
    def test_stress_conditions(self) -> None:
        """Test system under stress conditions."""
        print("\n💪 Testing Stress Conditions")
        print("=" * 50)
        
        # Test with very large dataset
        try:
            print("Testing large dataset generation (50,000 events)...")
            start_time = time.time()
            events = self.generator.generate_logs(LogType.IDS, count=50000)
            end_time = time.time()
            
            duration = end_time - start_time
            events_per_second = len(events) / duration
            
            print(f"✓ Large dataset: {len(events):,} events in {duration:.2f}s ({events_per_second:.0f} events/sec)")
            
            if events_per_second < 1000:
                print("⚠️  Performance below expected threshold (1000 events/sec)")
            
        except Exception as e:
            print(f"✗ Large dataset test failed: {e}")
        
        # Test memory under stress
        try:
            print("Testing memory stress...")
            initial_memory, _ = self.get_system_metrics()
            
            # Generate multiple large datasets
            for i in range(5):
                events = self.generator.generate_logs(LogType.IDS, count=10000)
                current_memory, _ = self.get_system_metrics()
                memory_used = current_memory - initial_memory
                
                print(f"  Batch {i+1}: {len(events):,} events, {memory_used:.1f} MB used")
                
                if memory_used > 1000:  # 1GB threshold
                    print("⚠️  High memory usage detected")
                    break
            
        except Exception as e:
            print(f"✗ Memory stress test failed: {e}")
    
    def generate_performance_report(self) -> None:
        """Generate comprehensive performance report."""
        print("\n📊 PERFORMANCE REPORT")
        print("=" * 60)
        
        if not self.results:
            print("No performance data available")
            return
        
        # Calculate statistics
        events_per_second = [r['events_per_second'] for r in self.results if 'events_per_second' in r]
        memory_usage = [r['memory_mb'] for r in self.results if 'memory_mb' in r]
        
        if events_per_second:
            avg_eps = sum(events_per_second) / len(events_per_second)
            max_eps = max(events_per_second)
            min_eps = min(events_per_second)
            
            print(f"Events per Second:")
            print(f"  Average: {avg_eps:.0f}")
            print(f"  Maximum: {max_eps:.0f}")
            print(f"  Minimum: {min_eps:.0f}")
        
        if memory_usage:
            avg_memory = sum(memory_usage) / len(memory_usage)
            max_memory = max(memory_usage)
            
            print(f"\nMemory Usage:")
            print(f"  Average: {avg_memory:.1f} MB")
            print(f"  Maximum: {max_memory:.1f} MB")
        
        # Performance recommendations
        print(f"\n🎯 PERFORMANCE RECOMMENDATIONS:")
        
        if events_per_second:
            if max_eps > 10000:
                print("✅ Excellent performance - system can handle high loads")
            elif max_eps > 5000:
                print("✅ Good performance - suitable for most use cases")
            elif max_eps > 1000:
                print("⚠️  Moderate performance - consider optimization for high loads")
            else:
                print("❌ Low performance - system needs optimization")
        
        if memory_usage:
            if max_memory > 1000:
                print("⚠️  High memory usage detected - consider streaming for large datasets")
            else:
                print("✅ Memory usage is reasonable")
        
        # Save detailed report
        report_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'results': self.results,
            'summary': {
                'total_tests': len(self.results),
                'avg_events_per_second': avg_eps if events_per_second else 0,
                'max_events_per_second': max_eps if events_per_second else 0,
                'avg_memory_mb': avg_memory if memory_usage else 0,
                'max_memory_mb': max_memory if memory_usage else 0
            }
        }
        
        with open('performance_report.json', 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: performance_report.json")
    
    def run_all_performance_tests(self) -> None:
        """Run all performance tests."""
        print("🚀 Cybersecurity Log Generator - Performance Testing")
        print("=" * 60)
        
        try:
            # Run all performance tests
            self.test_all_log_types_performance()
            self.test_scaling_performance()
            self.test_memory_efficiency()
            self.test_concurrent_generation()
            self.test_attack_campaign_performance()
            self.test_export_performance()
            self.test_correlation_performance()
            self.test_stress_conditions()
            
            # Generate report
            self.generate_performance_report()
            
        except Exception as e:
            print(f"Performance testing error: {e}")
            traceback.print_exc()


def main():
    """Main function to run performance tests."""
    try:
        tester = PerformanceTester()
        tester.run_all_performance_tests()
        return 0
    except Exception as e:
        print(f"Performance testing error: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
