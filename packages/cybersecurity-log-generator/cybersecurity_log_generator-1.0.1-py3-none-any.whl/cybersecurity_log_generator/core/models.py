"""
Enhanced models for the 24-pillar cybersecurity log generator.
"""

import uuid
from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class LogSeverity(str, Enum):
    """Log severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class LogType(str, Enum):
    """Supported log types."""
    IDS = "ids"
    WEB_ACCESS = "web_access"
    ENDPOINT = "endpoint"
    WINDOWS_EVENT = "windows_event"
    LINUX_SYSLOG = "linux_syslog"
    FIREWALL = "firewall"
    VPN = "vpn"
    PROXY = "proxy"
    DNS = "dns"
    DHCP = "dhcp"


class CyberdefensePillar(str, Enum):
    """The 24 cyberdefense pillars."""
    VENDOR_RISK = "vendor_risk"
    API_SECURITY = "api_security"
    APPLICATION_SECURITY = "application_security"
    AUDIT_COMPLIANCE = "audit_compliance"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    CLOUD_SECURITY = "cloud_security"
    CONTAINER_SECURITY = "container_security"
    DATA_PRIVACY = "data_privacy"
    DATA_PROTECTION = "data_protection"
    DETECTION_CORRELATION = "detection_correlation"
    DISASTER_RECOVERY = "disaster_recovery"
    DUE_DILIGENCE = "due_diligence"
    ENCRYPTION = "encryption"
    ENDPOINT_SECURITY = "endpoint_security"
    AI_SECURITY = "ai_security"
    GOVERNANCE_RISK = "governance_risk"
    IDENTITY_GOVERNANCE = "identity_governance"
    INCIDENT_RESPONSE = "incident_response"
    NETWORK_SECURITY = "network_security"
    OT_PHYSICAL_SECURITY = "ot_physical_security"
    SECURITY_AWARENESS = "security_awareness"
    THREAT_INTELLIGENCE = "threat_intelligence"
    VULNERABILITY_MANAGEMENT = "vulnerability_management"
    SIEM_LOGS = "siem_logs"


class AttackTactic(str, Enum):
    """MITRE ATT&CK tactics."""
    INITIAL_ACCESS = "initial_access"
    EXECUTION = "execution"
    PERSISTENCE = "persistence"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DEFENSE_EVASION = "defense_evasion"
    CREDENTIAL_ACCESS = "credential_access"
    DISCOVERY = "discovery"
    LATERAL_MOVEMENT = "lateral_movement"
    COLLECTION = "collection"
    COMMAND_AND_CONTROL = "command_and_control"
    EXFILTRATION = "exfiltration"
    IMPACT = "impact"
    RECONNAISSANCE = "reconnaissance"
    ABUSE = "abuse"


class ThreatActor(str, Enum):
    """Known threat actors for simulation."""
    APT29 = "APT29"
    APT28 = "APT28"
    LAZARUS = "Lazarus"
    CARBON_SPIDER = "Carbon Spider"
    FIN7 = "FIN7"
    UNC2452 = "UNC2452"
    WIZARD_SPIDER = "Wizard Spider"
    RYUK = "Ryuk"
    CONTI = "Conti"
    MAZE = "Maze"


class LogEvent(BaseModel):
    """Base log event model."""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)
    log_type: Optional[str] = None
    severity: Optional[LogSeverity] = None
    source: Optional[Any] = None  # Allow any type including NetworkEndpoint
    destination: Optional[Any] = None  # Allow any type including NetworkEndpoint
    user: Optional[str] = None
    message: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = Field(default_factory=list)


class SecurityEvent(LogEvent):
    """Enhanced security event with pillar-specific data."""
    pillar: Optional[CyberdefensePillar] = None
    threat_actor: Optional[ThreatActor] = None
    attack_tactic: Optional[AttackTactic] = None
    attack_technique: Optional[str] = None
    ioc_type: Optional[str] = None
    ioc_value: Optional[str] = None
    confidence_score: Optional[float] = None
    false_positive_probability: Optional[float] = None
    correlation_id: Optional[str] = None
    campaign_id: Optional[str] = None


class AttackCampaign(BaseModel):
    """Attack campaign across multiple pillars."""
    campaign_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    threat_actor: Optional[ThreatActor] = None
    start_time: Optional[datetime] = Field(default_factory=datetime.utcnow)
    duration: Optional[str] = "24h"
    target_count: Optional[int] = 50
    events: Optional[List[SecurityEvent]] = Field(default_factory=list)
    description: Optional[str] = ""
    objectives: Optional[List[str]] = Field(default_factory=list)


class PillarAttackPattern(BaseModel):
    """Attack pattern for a specific pillar."""
    pillar: Optional[CyberdefensePillar] = None
    attack_type: Optional[str] = None
    severity: Optional[LogSeverity] = None
    description: Optional[str] = None
    tactic: Optional[AttackTactic] = None
    weight: Optional[float] = 0.1
    indicators: Optional[List[str]] = Field(default_factory=list)
    log_sources: Optional[List[str]] = Field(default_factory=list)
    mitigation_controls: Optional[List[str]] = Field(default_factory=list)


class NetworkEndpoint(BaseModel):
    """Network endpoint configuration."""
    ip_address: Optional[str] = None
    hostname: Optional[str] = None
    port: Optional[int] = None
    protocol: Optional[str] = "tcp"
    service: Optional[str] = None


class NetworkTopology(BaseModel):
    """Network topology configuration."""
    name: Optional[str] = None
    subnets: Optional[List[str]] = Field(default_factory=list)
    gateways: Optional[List[str]] = Field(default_factory=list)
    dns_servers: Optional[List[str]] = Field(default_factory=list)


class UserProfile(BaseModel):
    """User profile for log generation."""
    username: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None
    access_level: Optional[str] = None
    location: Optional[str] = None


class GeneratorConfig(BaseModel):
    """Configuration for the enhanced log generator."""
    enable_all_pillars: Optional[bool] = True
    pillar_weights: Optional[Dict[CyberdefensePillar, float]] = Field(default_factory=dict)
    attack_frequency: Optional[float] = 0.15  # 15% chance of attack events
    correlation_enabled: Optional[bool] = True
    campaign_mode: Optional[bool] = False
    threat_actor_distribution: Optional[Dict[ThreatActor, float]] = Field(default_factory=dict)
    time_range: Optional[str] = "24h"
    output_format: Optional[str] = "json"
    enable_mitre_attack: Optional[bool] = True
    enable_correlation: Optional[bool] = True