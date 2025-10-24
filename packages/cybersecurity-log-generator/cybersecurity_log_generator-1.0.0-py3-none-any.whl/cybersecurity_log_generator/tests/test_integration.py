"""
Integration tests for the cybersecurity-log-generator package.
"""

import pytest
from cybersecurity_log_generator.core.generator import LogGenerator
from cybersecurity_log_generator.core.enhanced_generator import EnhancedLogGenerator
from cybersecurity_log_generator.core.models import LogType, CyberdefensePillar
from cybersecurity_log_generator.utils import export_logs, validate_logs, analyze_log_patterns


def test_end_to_end_basic_generation():
    """Test end-to-end basic log generation workflow."""
    # Generate logs
    generator = LogGenerator()
    logs = generator.generate_logs(LogType.IDS, count=10, time_range="1h")
    
    # Validate logs
    logs_data = [log.dict() if hasattr(log, 'dict') else log for log in logs]
    validation_result = validate_logs(logs_data)
    
    assert validation_result["valid"] is True
    assert validation_result["count"] == 10
    
    # Analyze patterns
    analysis_result = analyze_log_patterns(logs_data)
    assert analysis_result["total_logs"] == 10
    assert analysis_result["unique_event_types"] > 0


def test_end_to_end_pillar_generation():
    """Test end-to-end pillar log generation workflow."""
    # Generate pillar logs
    enhanced_generator = EnhancedLogGenerator()
    logs = enhanced_generator.generate_logs(CyberdefensePillar.AUTHENTICATION, count=15, time_range="2h")
    
    # Validate logs
    logs_data = [log.dict() if hasattr(log, 'dict') else log for log in logs]
    validation_result = validate_logs(logs_data)
    
    assert validation_result["valid"] is True
    assert validation_result["count"] == 15
    
    # Analyze patterns
    analysis_result = analyze_log_patterns(logs_data)
    assert analysis_result["total_logs"] == 15
    assert analysis_result["unique_event_types"] > 0


def test_end_to_end_export_workflow():
    """Test end-to-end export workflow."""
    # Generate logs
    generator = LogGenerator()
    logs = generator.generate_logs(LogType.WEB_ACCESS, count=5, time_range="30m")
    
    # Convert to dictionary format
    logs_data = [log.dict() if hasattr(log, 'dict') else log for log in logs]
    
    # Export in different formats
    json_file = export_logs(logs_data, format="json", output_path="test_integration")
    csv_file = export_logs(logs_data, format="csv", output_path="test_integration")
    
    # Verify files were created
    import os
    assert os.path.exists(json_file)
    assert os.path.exists(csv_file)
    
    # Clean up
    if os.path.exists(json_file):
        os.remove(json_file)
    if os.path.exists(csv_file):
        os.remove(csv_file)


def test_correlated_events_workflow():
    """Test correlated events generation workflow."""
    enhanced_generator = EnhancedLogGenerator()
    
    # Generate correlated events
    logs = enhanced_generator.generate_correlated_events(
        pillars=[CyberdefensePillar.AUTHENTICATION, CyberdefensePillar.NETWORK_SECURITY],
        count=20,
        correlation_strength=0.7
    )
    
    # Validate logs
    logs_data = [log.dict() if hasattr(log, 'dict') else log for log in logs]
    validation_result = validate_logs(logs_data)
    
    assert validation_result["valid"] is True
    assert validation_result["count"] == 20
    
    # Check for correlation IDs
    correlation_ids = [log.get('correlation_id') for log in logs_data if 'correlation_id' in log]
    assert len(correlation_ids) > 0


def test_campaign_logs_workflow():
    """Test campaign logs generation workflow."""
    enhanced_generator = EnhancedLogGenerator()
    
    # Generate campaign logs
    logs = enhanced_generator.generate_campaign_logs(
        threat_actor="APT29",
        duration="12h",
        target_count=25
    )
    
    # Validate logs
    logs_data = [log.dict() if hasattr(log, 'dict') else log for log in logs]
    validation_result = validate_logs(logs_data)
    
    assert validation_result["valid"] is True
    assert validation_result["count"] == 25
    
    # Check for campaign attributes
    campaign_ids = [log.get('campaign_id') for log in logs_data if 'campaign_id' in log]
    threat_actors = [log.get('threat_actor') for log in logs_data if 'threat_actor' in log]
    
    assert len(campaign_ids) > 0
    assert len(threat_actors) > 0
    assert all(actor == "APT29" for actor in threat_actors if actor)


def test_multi_pillar_generation():
    """Test generating logs from multiple pillars."""
    enhanced_generator = EnhancedLogGenerator()
    
    # Generate logs from different pillars
    pillars = [
        CyberdefensePillar.AUTHENTICATION,
        CyberdefensePillar.NETWORK_SECURITY,
        CyberdefensePillar.ENDPOINT_SECURITY
    ]
    
    all_logs = []
    for pillar in pillars:
        logs = enhanced_generator.generate_logs(pillar, count=5, time_range="1h")
        all_logs.extend(logs)
    
    # Validate all logs
    logs_data = [log.dict() if hasattr(log, 'dict') else log for log in all_logs]
    validation_result = validate_logs(logs_data)
    
    assert validation_result["valid"] is True
    assert validation_result["count"] == 15  # 5 logs per pillar * 3 pillars
    
    # Analyze patterns across all pillars
    analysis_result = analyze_log_patterns(logs_data)
    assert analysis_result["total_logs"] == 15
    assert analysis_result["unique_event_types"] > 0
