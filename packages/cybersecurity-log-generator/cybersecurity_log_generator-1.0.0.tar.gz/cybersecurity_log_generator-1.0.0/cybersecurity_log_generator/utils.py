"""
Utility functions for cybersecurity-log-generator.
"""

import json
import csv
import syslog
from typing import List, Dict, Any, Union
from datetime import datetime
from pathlib import Path


def export_logs(logs: List[Dict[str, Any]], format: str = "json", output_path: str = "exported_logs") -> str:
    """
    Export logs in various formats.
    
    Args:
        logs: List of log dictionaries
        format: Export format (json, csv, syslog, cef, leef)
        output_path: Output file path
        
    Returns:
        Path to exported file
    """
    if format.lower() == "json":
        return export_json(logs, output_path)
    elif format.lower() == "csv":
        return export_csv(logs, output_path)
    elif format.lower() == "syslog":
        return export_syslog(logs, output_path)
    elif format.lower() == "cef":
        return export_cef(logs, output_path)
    elif format.lower() == "leef":
        return export_leef(logs, output_path)
    else:
        raise ValueError(f"Unsupported format: {format}")


def export_json(logs: List[Dict[str, Any]], output_path: str) -> str:
    """Export logs to JSON format."""
    file_path = f"{output_path}.json"
    with open(file_path, 'w') as f:
        json.dump(logs, f, indent=2, default=str)
    return file_path


def export_csv(logs: List[Dict[str, Any]], output_path: str) -> str:
    """Export logs to CSV format."""
    file_path = f"{output_path}.csv"
    
    if not logs:
        return file_path
    
    # Get all unique keys from all logs
    all_keys = set()
    for log in logs:
        all_keys.update(log.keys())
    
    with open(file_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=sorted(all_keys))
        writer.writeheader()
        writer.writerows(logs)
    
    return file_path


def export_syslog(logs: List[Dict[str, Any]], output_path: str) -> str:
    """Export logs to Syslog format."""
    file_path = f"{output_path}.syslog"
    
    with open(file_path, 'w') as f:
        for log in logs:
            # Format as syslog message
            timestamp = log.get('timestamp', datetime.now().isoformat())
            severity = log.get('severity', 'INFO')
            message = log.get('message', str(log))
            
            syslog_line = f"<{get_syslog_priority(severity)}>1 {timestamp} {log.get('hostname', 'localhost')} {log.get('program', 'cybersecurity-log-gen')} - - {message}\n"
            f.write(syslog_line)
    
    return file_path


def export_cef(logs: List[Dict[str, Any]], output_path: str) -> str:
    """Export logs to CEF (Common Event Format) format."""
    file_path = f"{output_path}.cef"
    
    with open(file_path, 'w') as f:
        for log in logs:
            cef_line = format_cef_message(log)
            f.write(cef_line + "\n")
    
    return file_path


def export_leef(logs: List[Dict[str, Any]], output_path: str) -> str:
    """Export logs to LEEF (Log Event Extended Format) format."""
    file_path = f"{output_path}.leef"
    
    with open(file_path, 'w') as f:
        for log in logs:
            leef_line = format_leef_message(log)
            f.write(leef_line + "\n")
    
    return file_path


def get_syslog_priority(severity: str) -> int:
    """Get syslog priority number for severity level."""
    severity_map = {
        'DEBUG': 7,
        'INFO': 6,
        'WARNING': 4,
        'ERROR': 3,
        'CRITICAL': 2,
        'ALERT': 1,
        'EMERGENCY': 0
    }
    return severity_map.get(severity.upper(), 6)


def format_cef_message(log: Dict[str, Any]) -> str:
    """Format a log entry as CEF message."""
    # CEF:Version|Device Vendor|Device Product|Device Version|Device Event Class ID|Name|Severity|Extension
    version = "0"
    vendor = "CybersecurityLogGenerator"
    product = "LogGenerator"
    device_version = "1.0"
    event_class_id = log.get('event_id', '1001')
    name = log.get('event_type', 'Security Event')
    severity = log.get('severity', '5')
    
    # Build extension fields
    extensions = []
    for key, value in log.items():
        if key not in ['event_id', 'event_type', 'severity']:
            extensions.append(f"{key}={value}")
    
    extension_str = " ".join(extensions)
    
    return f"CEF:{version}|{vendor}|{product}|{device_version}|{event_class_id}|{name}|{severity}|{extension_str}"


def format_leef_message(log: Dict[str, Any]) -> str:
    """Format a log entry as LEEF message."""
    # LEEF:Version|Vendor|Product|Version|EventID|Name|Severity|Extension
    version = "2.0"
    vendor = "CybersecurityLogGenerator"
    product = "LogGenerator"
    device_version = "1.0"
    event_id = log.get('event_id', '1001')
    name = log.get('event_type', 'Security Event')
    severity = log.get('severity', '5')
    
    # Build extension fields
    extensions = []
    for key, value in log.items():
        if key not in ['event_id', 'event_type', 'severity']:
            extensions.append(f"{key}={value}")
    
    extension_str = " ".join(extensions)
    
    return f"LEEF:{version}|{vendor}|{product}|{device_version}|{event_id}|{name}|{severity}|{extension_str}"


def validate_logs(logs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Validate generated logs and return statistics.
    
    Args:
        logs: List of log dictionaries
        
    Returns:
        Validation statistics
    """
    if not logs:
        return {"valid": False, "count": 0, "errors": ["No logs provided"]}
    
    errors = []
    warnings = []
    
    # Check required fields
    required_fields = ['timestamp', 'event_type', 'severity']
    for i, log in enumerate(logs):
        for field in required_fields:
            if field not in log:
                errors.append(f"Log {i}: Missing required field '{field}'")
    
    # Check data types
    for i, log in enumerate(logs):
        if 'timestamp' in log and not isinstance(log['timestamp'], (str, datetime)):
            warnings.append(f"Log {i}: Invalid timestamp format")
        
        if 'severity' in log and log['severity'] not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            warnings.append(f"Log {i}: Invalid severity level")
    
    # Calculate statistics
    event_types = {}
    severities = {}
    for log in logs:
        event_type = log.get('event_type', 'Unknown')
        severity = log.get('severity', 'Unknown')
        
        event_types[event_type] = event_types.get(event_type, 0) + 1
        severities[severity] = severities.get(severity, 0) + 1
    
    return {
        "valid": len(errors) == 0,
        "count": len(logs),
        "errors": errors,
        "warnings": warnings,
        "event_types": event_types,
        "severities": severities,
        "unique_event_types": len(event_types),
        "unique_severities": len(severities)
    }


def analyze_log_patterns(logs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze log patterns and provide insights.
    
    Args:
        logs: List of log dictionaries
        
    Returns:
        Analysis results
    """
    if not logs:
        return {"error": "No logs to analyze"}
    
    # Time analysis
    timestamps = [log.get('timestamp') for log in logs if 'timestamp' in log]
    time_span = None
    if timestamps:
        try:
            start_time = min(timestamps)
            end_time = max(timestamps)
            time_span = str(end_time - start_time) if start_time != end_time else "0"
        except:
            pass
    
    # Event type analysis
    event_types = {}
    for log in logs:
        event_type = log.get('event_type', 'Unknown')
        event_types[event_type] = event_types.get(event_type, 0) + 1
    
    # Severity analysis
    severities = {}
    for log in logs:
        severity = log.get('severity', 'Unknown')
        severities[severity] = severities.get(severity, 0) + 1
    
    # Source analysis
    sources = {}
    for log in logs:
        source = log.get('source', 'Unknown')
        sources[source] = sources.get(source, 0) + 1
    
    return {
        "total_logs": len(logs),
        "time_span": time_span,
        "event_types": event_types,
        "severities": severities,
        "sources": sources,
        "unique_event_types": len(event_types),
        "unique_severities": len(severities),
        "unique_sources": len(sources),
        "most_common_event_type": max(event_types.items(), key=lambda x: x[1])[0] if event_types else None,
        "most_common_severity": max(severities.items(), key=lambda x: x[1])[0] if severities else None
    }
