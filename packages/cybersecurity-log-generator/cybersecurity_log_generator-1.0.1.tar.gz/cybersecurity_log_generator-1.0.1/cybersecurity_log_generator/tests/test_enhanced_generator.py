"""
Tests for the enhanced log generator.
"""

import pytest
from cybersecurity_log_generator.core.enhanced_generator import EnhancedLogGenerator
from cybersecurity_log_generator.core.models import CyberdefensePillar


def test_enhanced_generator_initialization():
    """Test that EnhancedLogGenerator initializes correctly."""
    generator = EnhancedLogGenerator()
    assert generator is not None


def test_generate_pillar_logs():
    """Test pillar-specific log generation."""
    generator = EnhancedLogGenerator()
    logs = generator.generate_logs(CyberdefensePillar.AUTHENTICATION, count=10)
    
    assert len(logs) == 10
    assert all(hasattr(log, 'timestamp') for log in logs)
    assert all(hasattr(log, 'event_type') for log in logs)


def test_all_pillars():
    """Test that all cyberdefense pillars can generate logs."""
    generator = EnhancedLogGenerator()
    
    for pillar in CyberdefensePillar:
        logs = generator.generate_logs(pillar, count=1)
        assert len(logs) == 1
        assert logs[0].event_type is not None


def test_pillar_log_structure():
    """Test that pillar logs have the expected structure."""
    generator = EnhancedLogGenerator()
    logs = generator.generate_logs(CyberdefensePillar.NETWORK_SECURITY, count=3)
    
    for log in logs:
        # Check required fields exist
        assert hasattr(log, 'timestamp')
        assert hasattr(log, 'event_type')
        assert hasattr(log, 'severity')
        
        # Check field types
        assert isinstance(log.timestamp, str)
        assert isinstance(log.event_type, str)
        assert isinstance(log.severity, str)


def test_correlated_events():
    """Test generation of correlated events."""
    generator = EnhancedLogGenerator()
    logs = generator.generate_correlated_events(
        pillars=[CyberdefensePillar.AUTHENTICATION, CyberdefensePillar.NETWORK_SECURITY],
        count=10,
        correlation_strength=0.8
    )
    
    assert len(logs) == 10
    # Verify correlation IDs exist
    correlation_ids = [log.correlation_id for log in logs if hasattr(log, 'correlation_id')]
    assert len(correlation_ids) > 0


def test_campaign_logs():
    """Test generation of campaign logs."""
    generator = EnhancedLogGenerator()
    logs = generator.generate_campaign_logs(
        threat_actor="APT29",
        duration="24h",
        target_count=20
    )
    
    assert len(logs) == 20
    # Verify campaign attributes
    campaign_ids = [log.campaign_id for log in logs if hasattr(log, 'campaign_id')]
    assert len(campaign_ids) > 0
