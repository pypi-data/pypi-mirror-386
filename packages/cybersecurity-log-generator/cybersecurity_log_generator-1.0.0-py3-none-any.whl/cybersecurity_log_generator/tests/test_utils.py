"""
Tests for utility functions.
"""

import pytest
from cybersecurity_log_generator.utils import export_logs, validate_logs, analyze_log_patterns


def test_export_logs_json():
    """Test JSON export functionality."""
    logs = [
        {"timestamp": "2024-01-01T00:00:00Z", "event_type": "login", "severity": "INFO"},
        {"timestamp": "2024-01-01T00:01:00Z", "event_type": "failed_login", "severity": "WARNING"}
    ]
    
    file_path = export_logs(logs, format="json", output_path="test_logs")
    assert file_path == "test_logs.json"
    
    # Clean up
    import os
    if os.path.exists(file_path):
        os.remove(file_path)


def test_export_logs_csv():
    """Test CSV export functionality."""
    logs = [
        {"timestamp": "2024-01-01T00:00:00Z", "event_type": "login", "severity": "INFO"},
        {"timestamp": "2024-01-01T00:01:00Z", "event_type": "failed_login", "severity": "WARNING"}
    ]
    
    file_path = export_logs(logs, format="csv", output_path="test_logs")
    assert file_path == "test_logs.csv"
    
    # Clean up
    import os
    if os.path.exists(file_path):
        os.remove(file_path)


def test_validate_logs():
    """Test log validation functionality."""
    valid_logs = [
        {"timestamp": "2024-01-01T00:00:00Z", "event_type": "login", "severity": "INFO"},
        {"timestamp": "2024-01-01T00:01:00Z", "event_type": "failed_login", "severity": "WARNING"}
    ]
    
    result = validate_logs(valid_logs)
    assert result["valid"] is True
    assert result["count"] == 2
    assert len(result["errors"]) == 0


def test_validate_logs_invalid():
    """Test log validation with invalid logs."""
    invalid_logs = [
        {"event_type": "login"},  # Missing timestamp
        {"timestamp": "2024-01-01T00:00:00Z", "severity": "INFO"}  # Missing event_type
    ]
    
    result = validate_logs(invalid_logs)
    assert result["valid"] is False
    assert len(result["errors"]) > 0


def test_analyze_log_patterns():
    """Test log pattern analysis."""
    logs = [
        {"timestamp": "2024-01-01T00:00:00Z", "event_type": "login", "severity": "INFO", "source": "auth_server"},
        {"timestamp": "2024-01-01T00:01:00Z", "event_type": "failed_login", "severity": "WARNING", "source": "auth_server"},
        {"timestamp": "2024-01-01T00:02:00Z", "event_type": "login", "severity": "INFO", "source": "auth_server"}
    ]
    
    result = analyze_log_patterns(logs)
    assert result["total_logs"] == 3
    assert result["unique_event_types"] == 2
    assert result["unique_severities"] == 2
    assert result["unique_sources"] == 1
    assert result["most_common_event_type"] == "login"
    assert result["most_common_severity"] == "INFO"


def test_analyze_log_patterns_empty():
    """Test log pattern analysis with empty logs."""
    result = analyze_log_patterns([])
    assert "error" in result
    assert result["error"] == "No logs to analyze"
