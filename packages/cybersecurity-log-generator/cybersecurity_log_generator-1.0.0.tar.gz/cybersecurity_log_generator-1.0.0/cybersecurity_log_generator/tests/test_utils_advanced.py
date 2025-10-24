"""
Advanced tests for utility functions.
"""

import pytest
import json
import csv
import os
from cybersecurity_log_generator.utils import (
    export_logs, validate_logs, analyze_log_patterns,
    export_json, export_csv, export_syslog, export_cef, export_leef,
    get_syslog_priority, format_cef_message, format_leef_message
)


def test_export_json_advanced():
    """Test advanced JSON export functionality."""
    logs = [
        {"timestamp": "2024-01-01T00:00:00Z", "event_type": "login", "severity": "INFO", "user": "test_user"},
        {"timestamp": "2024-01-01T00:01:00Z", "event_type": "failed_login", "severity": "WARNING", "user": "test_user"},
        {"timestamp": "2024-01-01T00:02:00Z", "event_type": "logout", "severity": "INFO", "user": "test_user"}
    ]
    
    file_path = export_json(logs, "test_advanced_json")
    assert file_path == "test_advanced_json.json"
    
    # Verify file content
    with open(file_path, 'r') as f:
        loaded_logs = json.load(f)
    
    assert len(loaded_logs) == 3
    assert loaded_logs[0]["event_type"] == "login"
    assert loaded_logs[1]["event_type"] == "failed_login"
    assert loaded_logs[2]["event_type"] == "logout"
    
    # Clean up
    os.remove(file_path)


def test_export_csv_advanced():
    """Test advanced CSV export functionality."""
    logs = [
        {"timestamp": "2024-01-01T00:00:00Z", "event_type": "login", "severity": "INFO", "user": "test_user"},
        {"timestamp": "2024-01-01T00:01:00Z", "event_type": "failed_login", "severity": "WARNING", "user": "test_user"},
        {"timestamp": "2024-01-01T00:02:00Z", "event_type": "logout", "severity": "INFO", "user": "test_user"}
    ]
    
    file_path = export_csv(logs, "test_advanced_csv")
    assert file_path == "test_advanced_csv.csv"
    
    # Verify file content
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    assert len(rows) == 3
    assert rows[0]["event_type"] == "login"
    assert rows[1]["event_type"] == "failed_login"
    assert rows[2]["event_type"] == "logout"
    
    # Clean up
    os.remove(file_path)


def test_export_syslog_advanced():
    """Test advanced Syslog export functionality."""
    logs = [
        {"timestamp": "2024-01-01T00:00:00Z", "event_type": "login", "severity": "INFO", "hostname": "server1", "program": "auth"},
        {"timestamp": "2024-01-01T00:01:00Z", "event_type": "failed_login", "severity": "WARNING", "hostname": "server1", "program": "auth"}
    ]
    
    file_path = export_syslog(logs, "test_advanced_syslog")
    assert file_path == "test_advanced_syslog.syslog"
    
    # Verify file content
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    assert len(lines) == 2
    assert "CEF:" in lines[0] or "<" in lines[0]  # Should be syslog format
    
    # Clean up
    os.remove(file_path)


def test_export_cef_advanced():
    """Test advanced CEF export functionality."""
    logs = [
        {"timestamp": "2024-01-01T00:00:00Z", "event_type": "login", "severity": "INFO", "user": "test_user", "source_ip": "192.168.1.1"},
        {"timestamp": "2024-01-01T00:01:00Z", "event_type": "failed_login", "severity": "WARNING", "user": "test_user", "source_ip": "192.168.1.2"}
    ]
    
    file_path = export_cef(logs, "test_advanced_cef")
    assert file_path == "test_advanced_cef.cef"
    
    # Verify file content
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    assert len(lines) == 2
    assert all("CEF:" in line for line in lines)
    assert all("CybersecurityLogGenerator" in line for line in lines)
    
    # Clean up
    os.remove(file_path)


def test_export_leef_advanced():
    """Test advanced LEEF export functionality."""
    logs = [
        {"timestamp": "2024-01-01T00:00:00Z", "event_type": "login", "severity": "INFO", "user": "test_user", "source_ip": "192.168.1.1"},
        {"timestamp": "2024-01-01T00:01:00Z", "event_type": "failed_login", "severity": "WARNING", "user": "test_user", "source_ip": "192.168.1.2"}
    ]
    
    file_path = export_leef(logs, "test_advanced_leef")
    assert file_path == "test_advanced_leef.leef"
    
    # Verify file content
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    assert len(lines) == 2
    assert all("LEEF:" in line for line in lines)
    assert all("CybersecurityLogGenerator" in line for line in lines)
    
    # Clean up
    os.remove(file_path)


def test_get_syslog_priority():
    """Test syslog priority mapping."""
    assert get_syslog_priority("DEBUG") == 7
    assert get_syslog_priority("INFO") == 6
    assert get_syslog_priority("WARNING") == 4
    assert get_syslog_priority("ERROR") == 3
    assert get_syslog_priority("CRITICAL") == 2
    assert get_syslog_priority("ALERT") == 1
    assert get_syslog_priority("EMERGENCY") == 0
    assert get_syslog_priority("UNKNOWN") == 6  # Default


def test_format_cef_message():
    """Test CEF message formatting."""
    log = {
        "event_id": "1001",
        "event_type": "Security Event",
        "severity": "5",
        "user": "test_user",
        "source_ip": "192.168.1.1"
    }
    
    cef_message = format_cef_message(log)
    
    assert "CEF:" in cef_message
    assert "CybersecurityLogGenerator" in cef_message
    assert "LogGenerator" in cef_message
    assert "1001" in cef_message
    assert "Security Event" in cef_message
    assert "5" in cef_message
    assert "user=test_user" in cef_message
    assert "source_ip=192.168.1.1" in cef_message


def test_format_leef_message():
    """Test LEEF message formatting."""
    log = {
        "event_id": "1001",
        "event_type": "Security Event",
        "severity": "5",
        "user": "test_user",
        "source_ip": "192.168.1.1"
    }
    
    leef_message = format_leef_message(log)
    
    assert "LEEF:" in leef_message
    assert "CybersecurityLogGenerator" in leef_message
    assert "LogGenerator" in leef_message
    assert "1001" in leef_message
    assert "Security Event" in leef_message
    assert "5" in leef_message
    assert "user=test_user" in leef_message
    assert "source_ip=192.168.1.1" in leef_message


def test_validate_logs_advanced():
    """Test advanced log validation."""
    # Valid logs
    valid_logs = [
        {"timestamp": "2024-01-01T00:00:00Z", "event_type": "login", "severity": "INFO"},
        {"timestamp": "2024-01-01T00:01:00Z", "event_type": "failed_login", "severity": "WARNING"},
        {"timestamp": "2024-01-01T00:02:00Z", "event_type": "logout", "severity": "INFO"}
    ]
    
    result = validate_logs(valid_logs)
    assert result["valid"] is True
    assert result["count"] == 3
    assert len(result["errors"]) == 0
    assert result["unique_event_types"] == 3
    assert result["unique_severities"] == 2
    
    # Invalid logs
    invalid_logs = [
        {"event_type": "login"},  # Missing timestamp
        {"timestamp": "2024-01-01T00:00:00Z", "severity": "INFO"},  # Missing event_type
        {"timestamp": "2024-01-01T00:00:00Z", "event_type": "login", "severity": "INVALID"}  # Invalid severity
    ]
    
    result = validate_logs(invalid_logs)
    assert result["valid"] is False
    assert len(result["errors"]) > 0
    assert len(result["warnings"]) > 0


def test_analyze_log_patterns_advanced():
    """Test advanced log pattern analysis."""
    logs = [
        {"timestamp": "2024-01-01T00:00:00Z", "event_type": "login", "severity": "INFO", "source": "auth_server", "user": "user1"},
        {"timestamp": "2024-01-01T00:01:00Z", "event_type": "failed_login", "severity": "WARNING", "source": "auth_server", "user": "user2"},
        {"timestamp": "2024-01-01T00:02:00Z", "event_type": "login", "severity": "INFO", "source": "auth_server", "user": "user1"},
        {"timestamp": "2024-01-01T00:03:00Z", "event_type": "logout", "severity": "INFO", "source": "auth_server", "user": "user1"},
        {"timestamp": "2024-01-01T00:04:00Z", "event_type": "failed_login", "severity": "WARNING", "source": "auth_server", "user": "user3"}
    ]
    
    result = analyze_log_patterns(logs)
    
    assert result["total_logs"] == 5
    assert result["unique_event_types"] == 3
    assert result["unique_severities"] == 2
    assert result["unique_sources"] == 1
    assert result["most_common_event_type"] == "login"
    assert result["most_common_severity"] == "INFO"
    
    # Check event type distribution
    assert result["event_types"]["login"] == 2
    assert result["event_types"]["failed_login"] == 2
    assert result["event_types"]["logout"] == 1
    
    # Check severity distribution
    assert result["severities"]["INFO"] == 3
    assert result["severities"]["WARNING"] == 2


def test_analyze_log_patterns_empty():
    """Test log pattern analysis with empty logs."""
    result = analyze_log_patterns([])
    assert "error" in result
    assert result["error"] == "No logs to analyze"


def test_analyze_log_patterns_single_log():
    """Test log pattern analysis with single log."""
    logs = [
        {"timestamp": "2024-01-01T00:00:00Z", "event_type": "login", "severity": "INFO", "source": "auth_server"}
    ]
    
    result = analyze_log_patterns(logs)
    
    assert result["total_logs"] == 1
    assert result["unique_event_types"] == 1
    assert result["unique_severities"] == 1
    assert result["unique_sources"] == 1
    assert result["most_common_event_type"] == "login"
    assert result["most_common_severity"] == "INFO"