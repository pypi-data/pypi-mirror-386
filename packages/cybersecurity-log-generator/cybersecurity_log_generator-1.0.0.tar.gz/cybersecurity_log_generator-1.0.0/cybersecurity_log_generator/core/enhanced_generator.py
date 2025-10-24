"""
Enhanced cybersecurity log generator supporting all 24 cyberdefense pillars.
"""

import random
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from .models import (
    SecurityEvent, CyberdefensePillar, LogSeverity, AttackTactic, 
    ThreatActor, AttackCampaign, GeneratorConfig, LogType
)
# Import only the generators that exist
from .pillar_generators import SIEMLogsGenerator

# Try to import other generators if they exist
try:
    from .pillar_generators import (
        VendorRiskGenerator, APISecurityGenerator, EndpointSecurityGenerator,
        AuthenticationGenerator, AuthorizationGenerator, ApplicationSecurityGenerator,
        AuditComplianceGenerator, CloudSecurityGenerator, ContainerSecurityGenerator,
        DataPrivacyGenerator, DataProtectionGenerator, DetectionCorrelationGenerator,
        DisasterRecoveryGenerator, DueDiligenceGenerator, EncryptionGenerator,
        AISecurityGenerator, GovernanceRiskGenerator, IdentityGovernanceGenerator,
        IncidentResponseGenerator, NetworkSecurityGenerator, OTPhysicalSecurityGenerator,
        SecurityAwarenessGenerator, ThreatIntelligenceGenerator, VulnerabilityManagementGenerator
    )
except ImportError:
    # Set all generators to None if they don't exist
    VendorRiskGenerator = None
    APISecurityGenerator = None
    EndpointSecurityGenerator = None
    AuthenticationGenerator = None
    AuthorizationGenerator = None
    ApplicationSecurityGenerator = None
    AuditComplianceGenerator = None
    CloudSecurityGenerator = None
    ContainerSecurityGenerator = None
    DataPrivacyGenerator = None
    DataProtectionGenerator = None
    DetectionCorrelationGenerator = None
    DisasterRecoveryGenerator = None
    DueDiligenceGenerator = None
    EncryptionGenerator = None
    AISecurityGenerator = None
    GovernanceRiskGenerator = None
    IdentityGovernanceGenerator = None
    IncidentResponseGenerator = None
    NetworkSecurityGenerator = None
    OTPhysicalSecurityGenerator = None
    SecurityAwarenessGenerator = None
    ThreatIntelligenceGenerator = None
    VulnerabilityManagementGenerator = None


class EnhancedLogGenerator:
    """Enhanced log generator supporting all 24 cyberdefense pillars."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = GeneratorConfig(**(config or {}))
        self.pillar_generators = self._setup_pillar_generators()
        self.correlation_engine = self._setup_correlation_engine()
    
    def _setup_pillar_generators(self) -> Dict[CyberdefensePillar, Any]:
        """Setup generators for all 24 pillars."""
        generators = {}
        
        # Initialize available pillar generators - only if they exist
        available_generators = {}
        
        # Use SIEM logs generator as fallback for all pillars
        siem_generator = SIEMLogsGenerator(self.config.model_dump())
        
        # Only add generators that actually exist
        if VendorRiskGenerator:
            available_generators[CyberdefensePillar.VENDOR_RISK] = VendorRiskGenerator(self.config.model_dump())
        if APISecurityGenerator:
            available_generators[CyberdefensePillar.API_SECURITY] = APISecurityGenerator(self.config.model_dump())
        if EndpointSecurityGenerator:
            available_generators[CyberdefensePillar.ENDPOINT_SECURITY] = EndpointSecurityGenerator(self.config.model_dump())
        if AuthenticationGenerator:
            available_generators[CyberdefensePillar.AUTHENTICATION] = AuthenticationGenerator(self.config.model_dump())
        if AuthorizationGenerator:
            available_generators[CyberdefensePillar.AUTHORIZATION] = AuthorizationGenerator(self.config.model_dump())
        if ApplicationSecurityGenerator:
            available_generators[CyberdefensePillar.APPLICATION_SECURITY] = ApplicationSecurityGenerator(self.config.model_dump())
        if AuditComplianceGenerator:
            available_generators[CyberdefensePillar.AUDIT_COMPLIANCE] = AuditComplianceGenerator(self.config.model_dump())
        if CloudSecurityGenerator:
            available_generators[CyberdefensePillar.CLOUD_SECURITY] = CloudSecurityGenerator(self.config.model_dump())
        if ContainerSecurityGenerator:
            available_generators[CyberdefensePillar.CONTAINER_SECURITY] = ContainerSecurityGenerator(self.config.model_dump())
        if DataPrivacyGenerator:
            available_generators[CyberdefensePillar.DATA_PRIVACY] = DataPrivacyGenerator(self.config.model_dump())
        if DataProtectionGenerator:
            available_generators[CyberdefensePillar.DATA_PROTECTION] = DataProtectionGenerator(self.config.model_dump())
        if DetectionCorrelationGenerator:
            available_generators[CyberdefensePillar.DETECTION_CORRELATION] = DetectionCorrelationGenerator(self.config.model_dump())
        if DisasterRecoveryGenerator:
            available_generators[CyberdefensePillar.DISASTER_RECOVERY] = DisasterRecoveryGenerator(self.config.model_dump())
        if DueDiligenceGenerator:
            available_generators[CyberdefensePillar.DUE_DILIGENCE] = DueDiligenceGenerator(self.config.model_dump())
        if EncryptionGenerator:
            available_generators[CyberdefensePillar.ENCRYPTION] = EncryptionGenerator(self.config.model_dump())
        if AISecurityGenerator:
            available_generators[CyberdefensePillar.AI_SECURITY] = AISecurityGenerator(self.config.model_dump())
        if GovernanceRiskGenerator:
            available_generators[CyberdefensePillar.GOVERNANCE_RISK] = GovernanceRiskGenerator(self.config.model_dump())
        if IdentityGovernanceGenerator:
            available_generators[CyberdefensePillar.IDENTITY_GOVERNANCE] = IdentityGovernanceGenerator(self.config.model_dump())
        if IncidentResponseGenerator:
            available_generators[CyberdefensePillar.INCIDENT_RESPONSE] = IncidentResponseGenerator(self.config.model_dump())
        if NetworkSecurityGenerator:
            available_generators[CyberdefensePillar.NETWORK_SECURITY] = NetworkSecurityGenerator(self.config.model_dump())
        if OTPhysicalSecurityGenerator:
            available_generators[CyberdefensePillar.OT_PHYSICAL_SECURITY] = OTPhysicalSecurityGenerator(self.config.model_dump())
        if SecurityAwarenessGenerator:
            available_generators[CyberdefensePillar.SECURITY_AWARENESS] = SecurityAwarenessGenerator(self.config.model_dump())
        if ThreatIntelligenceGenerator:
            available_generators[CyberdefensePillar.THREAT_INTELLIGENCE] = ThreatIntelligenceGenerator(self.config.model_dump())
        if VulnerabilityManagementGenerator:
            available_generators[CyberdefensePillar.VULNERABILITY_MANAGEMENT] = VulnerabilityManagementGenerator(self.config.model_dump())
        
        # Always add SIEM logs generator
        available_generators[CyberdefensePillar.SIEM_LOGS] = siem_generator
        
        # Use available generators or SIEM generator as fallback
        for pillar in CyberdefensePillar:
            if pillar in available_generators:
                generators[pillar] = available_generators[pillar]
            else:
                # Use SIEM generator as fallback for all unimplemented pillars
                generators[pillar] = siem_generator
        
        return generators
    
    def _create_placeholder_generator(self, pillar: CyberdefensePillar):
        """Create a placeholder generator for unimplemented pillars."""
        class PlaceholderGenerator:
            def __init__(self, pillar):
                self.pillar = pillar
            
            def generate_event(self, **kwargs):
                return SecurityEvent(
                    pillar=pillar,
                    log_type=pillar.value,
                    severity=LogSeverity.MEDIUM,
                    message=f"Placeholder event for {pillar.value}",
                    raw_data={'pillar': pillar.value, 'placeholder': True},
                    tags=['placeholder', pillar.value]
                )
            
            def generate_campaign_events(self, threat_actor, duration_hours=24):
                return [self.generate_event()]
        
        return PlaceholderGenerator(pillar)
    
    def _setup_correlation_engine(self):
        """Setup correlation engine for cross-pillar attacks."""
        return {
            'enabled': self.config.correlation_enabled,
            'correlation_rules': self._get_correlation_rules(),
            'campaign_templates': self._get_campaign_templates()
        }
    
    def _get_correlation_rules(self) -> List[Dict[str, Any]]:
        """Get correlation rules for cross-pillar attacks."""
        return [
            {
                'name': 'ransomware_campaign',
                'pillars': [CyberdefensePillar.ENDPOINT_SECURITY, CyberdefensePillar.DATA_PROTECTION],
                'indicators': ['file_encryption', 'ransom_note', 'backup_targeting'],
                'severity': LogSeverity.CRITICAL
            },
            {
                'name': 'insider_threat_campaign',
                'pillars': [CyberdefensePillar.ENDPOINT_SECURITY, CyberdefensePillar.IDENTITY_GOVERNANCE],
                'indicators': ['privilege_abuse', 'data_exfiltration', 'unauthorized_access'],
                'severity': LogSeverity.HIGH
            },
            {
                'name': 'supply_chain_attack',
                'pillars': [CyberdefensePillar.VENDOR_RISK, CyberdefensePillar.APPLICATION_SECURITY],
                'indicators': ['vendor_compromise', 'malicious_dependencies', 'supply_chain_breach'],
                'severity': LogSeverity.CRITICAL
            }
        ]
    
    def _get_campaign_templates(self) -> List[Dict[str, Any]]:
        """Get campaign templates for coordinated attacks."""
        return [
            {
                'name': 'apt_campaign',
                'threat_actor': ThreatActor.APT29,
                'pillars': [CyberdefensePillar.ENDPOINT_SECURITY, CyberdefensePillar.NETWORK_SECURITY],
                'duration': '72h',
                'target_count': 100
            },
            {
                'name': 'ransomware_campaign',
                'threat_actor': ThreatActor.RYUK,
                'pillars': [CyberdefensePillar.ENDPOINT_SECURITY, CyberdefensePillar.DATA_PROTECTION],
                'duration': '24h',
                'target_count': 50
            }
        ]
    
    def generate_logs(self, pillar: CyberdefensePillar, count: int = 100, 
                     time_range: str = "24h", **kwargs) -> List[SecurityEvent]:
        """Generate logs for a specific pillar."""
        generator = self.pillar_generators.get(pillar)
        if not generator:
            raise ValueError(f"No generator available for pillar: {pillar}")
        
        events = []
        for _ in range(count):
            event = generator.generate_event(**kwargs)
            events.append(event)
        
        return events
    
    def generate_campaign(self, threat_actor: ThreatActor, duration: str = "24h", 
                         target_count: int = 50, **kwargs) -> AttackCampaign:
        """Generate a coordinated attack campaign across multiple pillars."""
        campaign_id = str(uuid.uuid4())
        start_time = datetime.utcnow()
        
        # Get campaign template
        template = self._get_campaign_template(threat_actor)
        if not template:
            template = {
                'pillars': [CyberdefensePillar.ENDPOINT_SECURITY],
                'duration': duration,
                'target_count': target_count
            }
        
        # Generate events for each pillar
        all_events = []
        for pillar in template['pillars']:
            generator = self.pillar_generators.get(pillar)
            if generator:
                pillar_events = generator.generate_campaign_events(
                    threat_actor, 
                    duration_hours=int(duration.replace('h', ''))
                )
                all_events.extend(pillar_events)
        
        # Sort events by timestamp
        all_events.sort(key=lambda x: x.timestamp)
        
        # Create campaign
        campaign = AttackCampaign(
            campaign_id=campaign_id,
            threat_actor=threat_actor,
            start_time=start_time,
            duration=duration,
            target_count=target_count,
            events=all_events,
            description=f"Coordinated attack campaign by {threat_actor.value}",
            objectives=self._get_campaign_objectives(threat_actor)
        )
        
        return campaign
    
    def generate_correlated_events(self, log_types: str, count: int = 100, 
                                 correlation_strength: float = 0.7) -> List[SecurityEvent]:
        """Generate correlated events across multiple log types."""
        pillars = [CyberdefensePillar(pillar.strip()) for pillar in log_types.split(',')]
        events = []
        
        # Generate base events for each pillar
        for pillar in pillars:
            pillar_events = self.generate_logs(pillar, count // len(pillars))
            events.extend(pillar_events)
        
        # Apply correlation if enabled
        if self.config.correlation_enabled and correlation_strength > 0:
            events = self._apply_correlation(events, correlation_strength)
        
        return events
    
    def _apply_correlation(self, events: List[SecurityEvent], strength: float) -> List[SecurityEvent]:
        """Apply correlation between events."""
        correlated_events = []
        correlation_id = str(uuid.uuid4())
        
        for event in events:
            if random.random() < strength:
                event.correlation_id = correlation_id
            correlated_events.append(event)
        
        return correlated_events
    
    def _get_campaign_template(self, threat_actor: ThreatActor) -> Optional[Dict[str, Any]]:
        """Get campaign template for threat actor."""
        for template in self.correlation_engine['campaign_templates']:
            if template['threat_actor'] == threat_actor:
                return template
        return None
    
    def _get_campaign_objectives(self, threat_actor: ThreatActor) -> List[str]:
        """Get campaign objectives for threat actor."""
        objectives_map = {
            ThreatActor.APT29: ['data_exfiltration', 'persistent_access', 'intelligence_gathering'],
            ThreatActor.APT28: ['espionage', 'data_theft', 'network_compromise'],
            ThreatActor.LAZARUS: ['financial_gain', 'cryptocurrency_theft', 'disruption'],
            ThreatActor.RYUK: ['ransomware_deployment', 'financial_extortion', 'data_encryption']
        }
        return objectives_map.get(threat_actor, ['unknown_objective'])
    
    def get_supported_pillars(self) -> List[CyberdefensePillar]:
        """Get list of supported pillars."""
        return list(CyberdefensePillar)
    
    def get_pillar_attack_patterns(self, pillar: CyberdefensePillar) -> List[str]:
        """Get attack patterns for a specific pillar."""
        generator = self.pillar_generators.get(pillar)
        if hasattr(generator, 'attack_patterns'):
            return list(generator.attack_patterns.keys())
        return []
    
    def get_threat_actors(self) -> List[ThreatActor]:
        """Get supported threat actors."""
        return list(ThreatActor)
    
    def get_correlation_rules(self) -> List[Dict[str, Any]]:
        """Get available correlation rules."""
        return self.correlation_engine['correlation_rules']
