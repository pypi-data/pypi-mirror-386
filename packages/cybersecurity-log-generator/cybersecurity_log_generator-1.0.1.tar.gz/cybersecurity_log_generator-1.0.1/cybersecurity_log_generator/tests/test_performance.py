"""
Performance tests for the cybersecurity-log-generator package.
"""

import pytest
import time
from cybersecurity_log_generator.core.generator import LogGenerator
from cybersecurity_log_generator.core.enhanced_generator import EnhancedLogGenerator
from cybersecurity_log_generator.core.models import LogType, CyberdefensePillar


def test_basic_generation_performance():
    """Test performance of basic log generation."""
    generator = LogGenerator()
    
    # Test with different log counts
    test_cases = [100, 500, 1000]
    
    for count in test_cases:
        start_time = time.time()
        logs = generator.generate_logs(LogType.IDS, count=count)
        end_time = time.time()
        
        generation_time = end_time - start_time
        logs_per_second = count / generation_time
        
        # Should generate at least 100 logs per second
        assert logs_per_second >= 100, f"Performance too slow: {logs_per_second:.2f} logs/sec"
        assert len(logs) == count


def test_enhanced_generation_performance():
    """Test performance of enhanced log generation."""
    enhanced_generator = EnhancedLogGenerator()
    
    # Test with different pillar counts
    test_cases = [50, 200, 500]
    
    for count in test_cases:
        start_time = time.time()
        logs = enhanced_generator.generate_logs(CyberdefensePillar.AUTHENTICATION, count=count)
        end_time = time.time()
        
        generation_time = end_time - start_time
        logs_per_second = count / generation_time
        
        # Should generate at least 50 logs per second for enhanced generation
        assert logs_per_second >= 50, f"Performance too slow: {logs_per_second:.2f} logs/sec"
        assert len(logs) == count


def test_correlated_events_performance():
    """Test performance of correlated events generation."""
    enhanced_generator = EnhancedLogGenerator()
    
    start_time = time.time()
    logs = enhanced_generator.generate_correlated_events(
        pillars=[CyberdefensePillar.AUTHENTICATION, CyberdefensePillar.NETWORK_SECURITY],
        count=200,
        correlation_strength=0.8
    )
    end_time = time.time()
    
    generation_time = end_time - start_time
    logs_per_second = 200 / generation_time
    
    # Should generate at least 30 logs per second for correlated events
    assert logs_per_second >= 30, f"Performance too slow: {logs_per_second:.2f} logs/sec"
    assert len(logs) == 200


def test_campaign_logs_performance():
    """Test performance of campaign logs generation."""
    enhanced_generator = EnhancedLogGenerator()
    
    start_time = time.time()
    logs = enhanced_generator.generate_campaign_logs(
        threat_actor="APT29",
        duration="24h",
        target_count=100
    )
    end_time = time.time()
    
    generation_time = end_time - start_time
    logs_per_second = 100 / generation_time
    
    # Should generate at least 20 logs per second for campaign logs
    assert logs_per_second >= 20, f"Performance too slow: {logs_per_second:.2f} logs/sec"
    assert len(logs) == 100


def test_memory_usage():
    """Test memory usage during log generation."""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    generator = LogGenerator()
    logs = generator.generate_logs(LogType.IDS, count=1000)
    
    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_increase = final_memory - initial_memory
    
    # Memory increase should be reasonable (less than 100MB for 1000 logs)
    assert memory_increase < 100, f"Memory usage too high: {memory_increase:.2f}MB increase"
    assert len(logs) == 1000


def test_concurrent_generation():
    """Test concurrent log generation."""
    import threading
    import queue
    
    def generate_logs_thread(generator, log_type, count, results_queue):
        """Thread function for generating logs."""
        logs = generator.generate_logs(log_type, count=count)
        results_queue.put(len(logs))
    
    generator = LogGenerator()
    results_queue = queue.Queue()
    
    # Start multiple threads
    threads = []
    for i in range(5):
        thread = threading.Thread(
            target=generate_logs_thread,
            args=(generator, LogType.IDS, 100, results_queue)
        )
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Collect results
    results = []
    while not results_queue.empty():
        results.append(results_queue.get())
    
    # All threads should have generated 100 logs
    assert len(results) == 5
    assert all(result == 100 for result in results)


def test_large_dataset_generation():
    """Test generation of large datasets."""
    generator = LogGenerator()
    
    # Generate a large dataset
    start_time = time.time()
    logs = generator.generate_logs(LogType.WEB_ACCESS, count=5000, time_range="7d")
    end_time = time.time()
    
    generation_time = end_time - start_time
    logs_per_second = 5000 / generation_time
    
    # Should generate at least 200 logs per second for large datasets
    assert logs_per_second >= 200, f"Performance too slow: {logs_per_second:.2f} logs/sec"
    assert len(logs) == 5000
    
    # Verify log quality
    logs_data = [log.dict() if hasattr(log, 'dict') else log for log in logs]
    unique_event_types = len(set(log.get('event_type', '') for log in logs_data))
    assert unique_event_types > 1  # Should have variety in event types
