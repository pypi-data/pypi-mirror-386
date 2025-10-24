"""
Tests for the basic log generator.
"""

import pytest
from cybersecurity_log_generator.core.generator import LogGenerator
from cybersecurity_log_generator.core.models import LogType


def test_log_generator_initialization():
    """Test that LogGenerator initializes correctly."""
    generator = LogGenerator()
    assert generator is not None


def test_generate_logs():
    """Test basic log generation."""
    generator = LogGenerator()
    logs = generator.generate_logs(LogType.IDS, count=10)
    
    assert len(logs) == 10
    assert all(hasattr(log, 'timestamp') for log in logs)
    assert all(hasattr(log, 'event_type') for log in logs)


def test_generate_logs_with_time_range():
    """Test log generation with custom time range."""
    generator = LogGenerator()
    logs = generator.generate_logs(LogType.WEB_ACCESS, count=5, time_range="1h")
    
    assert len(logs) == 5
    # Verify logs are within the specified time range
    # This would need more sophisticated time validation in a real test


def test_all_log_types():
    """Test that all log types can be generated."""
    generator = LogGenerator()
    
    for log_type in LogType:
        logs = generator.generate_logs(log_type, count=1)
        assert len(logs) == 1
        assert logs[0].event_type is not None


def test_log_structure():
    """Test that generated logs have the expected structure."""
    generator = LogGenerator()
    logs = generator.generate_logs(LogType.ENDPOINT, count=3)
    
    for log in logs:
        # Check required fields exist
        assert hasattr(log, 'timestamp')
        assert hasattr(log, 'event_type')
        assert hasattr(log, 'severity')
        
        # Check field types
        assert isinstance(log.timestamp, str)
        assert isinstance(log.event_type, str)
        assert isinstance(log.severity, str)
