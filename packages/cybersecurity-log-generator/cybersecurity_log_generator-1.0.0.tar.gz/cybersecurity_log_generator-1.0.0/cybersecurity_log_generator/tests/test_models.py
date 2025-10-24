"""
Tests for data models.
"""

import pytest
from cybersecurity_log_generator.core.models import LogType, ThreatActor, CyberdefensePillar


def test_log_type_enum():
    """Test LogType enum values."""
    assert LogType.IDS.value == "ids"
    assert LogType.WEB_ACCESS.value == "web_access"
    assert LogType.ENDPOINT.value == "endpoint"
    assert LogType.WINDOWS_EVENT.value == "windows_event"
    assert LogType.LINUX_SYSLOG.value == "linux_syslog"
    assert LogType.FIREWALL.value == "firewall"


def test_threat_actor_enum():
    """Test ThreatActor enum values."""
    assert ThreatActor.APT29.value == "APT29"
    assert ThreatActor.APT28.value == "APT28"
    assert ThreatActor.LAZARUS.value == "Lazarus"
    assert ThreatActor.FIN7.value == "FIN7"
    assert ThreatActor.UNC2452.value == "UNC2452"
    assert ThreatActor.WIZARD_SPIDER.value == "Wizard Spider"
    assert ThreatActor.RYUK.value == "Ryuk"
    assert ThreatActor.CONTI.value == "Conti"
    assert ThreatActor.MAZE.value == "Maze"


def test_cyberdefense_pillar_enum():
    """Test CyberdefensePillar enum values."""
    assert CyberdefensePillar.VENDOR_RISK.value == "vendor_risk"
    assert CyberdefensePillar.API_SECURITY.value == "api_security"
    assert CyberdefensePillar.ENDPOINT_SECURITY.value == "endpoint_security"
    assert CyberdefensePillar.AUTHENTICATION.value == "authentication"
    assert CyberdefensePillar.AUTHORIZATION.value == "authorization"
    assert CyberdefensePillar.APPLICATION_SECURITY.value == "application_security"
    assert CyberdefensePillar.AUDIT_COMPLIANCE.value == "audit_compliance"
    assert CyberdefensePillar.CLOUD_SECURITY.value == "cloud_security"
    assert CyberdefensePillar.CONTAINER_SECURITY.value == "container_security"
    assert CyberdefensePillar.DATA_PRIVACY.value == "data_privacy"
    assert CyberdefensePillar.DATA_PROTECTION.value == "data_protection"
    assert CyberdefensePillar.DETECTION_CORRELATION.value == "detection_correlation"
    assert CyberdefensePillar.DISASTER_RECOVERY.value == "disaster_recovery"
    assert CyberdefensePillar.DUE_DILIGENCE.value == "due_diligence"
    assert CyberdefensePillar.ENCRYPTION.value == "encryption"
    assert CyberdefensePillar.AI_SECURITY.value == "ai_security"
    assert CyberdefensePillar.GOVERNANCE_RISK.value == "governance_risk"
    assert CyberdefensePillar.IDENTITY_GOVERNANCE.value == "identity_governance"
    assert CyberdefensePillar.INCIDENT_RESPONSE.value == "incident_response"
    assert CyberdefensePillar.NETWORK_SECURITY.value == "network_security"
    assert CyberdefensePillar.OT_PHYSICAL_SECURITY.value == "ot_physical_security"
    assert CyberdefensePillar.SECURITY_AWARENESS.value == "security_awareness"
    assert CyberdefensePillar.THREAT_INTELLIGENCE.value == "threat_intelligence"
    assert CyberdefensePillar.VULNERABILITY_MANAGEMENT.value == "vulnerability_management"


def test_enum_iteration():
    """Test that enums can be iterated over."""
    log_types = list(LogType)
    assert len(log_types) > 0
    assert all(isinstance(lt, LogType) for lt in log_types)
    
    threat_actors = list(ThreatActor)
    assert len(threat_actors) > 0
    assert all(isinstance(ta, ThreatActor) for ta in threat_actors)
    
    pillars = list(CyberdefensePillar)
    assert len(pillars) > 0
    assert all(isinstance(p, CyberdefensePillar) for p in pillars)


def test_enum_string_conversion():
    """Test string conversion of enums."""
    log_type = LogType.IDS
    assert str(log_type) == "ids"
    assert log_type.value == "ids"
    
    threat_actor = ThreatActor.APT29
    assert str(threat_actor) == "APT29"
    assert threat_actor.value == "APT29"
    
    pillar = CyberdefensePillar.AUTHENTICATION
    assert str(pillar) == "authentication"
    assert pillar.value == "authentication"


def test_enum_comparison():
    """Test enum comparison."""
    log_type1 = LogType.IDS
    log_type2 = LogType.IDS
    log_type3 = LogType.WEB_ACCESS
    
    assert log_type1 == log_type2
    assert log_type1 != log_type3
    assert log_type1 is log_type2


def test_enum_from_string():
    """Test creating enums from string values."""
    # Test LogType
    log_type = LogType("ids")
    assert log_type == LogType.IDS
    
    # Test ThreatActor
    threat_actor = ThreatActor("APT29")
    assert threat_actor == ThreatActor.APT29
    
    # Test CyberdefensePillar
    pillar = CyberdefensePillar("authentication")
    assert pillar == CyberdefensePillar.AUTHENTICATION


def test_enum_invalid_string():
    """Test creating enums from invalid string values."""
    with pytest.raises(ValueError):
        LogType("invalid_type")
    
    with pytest.raises(ValueError):
        ThreatActor("InvalidActor")
    
    with pytest.raises(ValueError):
        CyberdefensePillar("invalid_pillar")
