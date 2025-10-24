"""
Base pillar generator for the 24 cyberdefense pillars.
"""

import random
import uuid
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from ..models import (
    SecurityEvent, CyberdefensePillar, LogSeverity, AttackTactic, 
    ThreatActor, PillarAttackPattern, LogType
)


class BasePillarGenerator(ABC):
    """Base class for pillar-specific log generators."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.pillar = self.get_pillar()
        self.attack_patterns = self._setup_attack_patterns()
        self.threat_actors = self._setup_threat_actors()
        self.faker = self._setup_faker()
    
    @abstractmethod
    def get_pillar(self) -> CyberdefensePillar:
        """Return the pillar this generator handles."""
        pass
    
    @abstractmethod
    def _setup_attack_patterns(self) -> Dict[str, PillarAttackPattern]:
        """Setup attack patterns specific to this pillar."""
        pass
    
    def _setup_threat_actors(self) -> Dict[ThreatActor, Dict[str, Any]]:
        """Setup threat actors and their characteristics."""
        return {
            ThreatActor.APT29: {
                'sophistication': 'high',
                'tactics': [AttackTactic.INITIAL_ACCESS, AttackTactic.PERSISTENCE, AttackTactic.EXFILTRATION],
                'targets': ['government', 'healthcare', 'finance']
            },
            ThreatActor.APT28: {
                'sophistication': 'high',
                'tactics': [AttackTactic.EXECUTION, AttackTactic.LATERAL_MOVEMENT, AttackTactic.COLLECTION],
                'targets': ['government', 'military', 'energy']
            },
            ThreatActor.LAZARUS: {
                'sophistication': 'medium',
                'tactics': [AttackTactic.INITIAL_ACCESS, AttackTactic.EXFILTRATION],
                'targets': ['finance', 'cryptocurrency']
            },
            ThreatActor.CARBON_SPIDER: {
                'sophistication': 'medium',
                'tactics': [AttackTactic.CREDENTIAL_ACCESS, AttackTactic.IMPACT],
                'targets': ['finance', 'retail']
            },
            ThreatActor.FIN7: {
                'sophistication': 'medium',
                'tactics': [AttackTactic.CREDENTIAL_ACCESS, AttackTactic.COLLECTION],
                'targets': ['finance', 'retail']
            }
        }
    
    def _setup_faker(self):
        """Setup faker for generating realistic data."""
        try:
            from faker import Faker
            return Faker()
        except ImportError:
            return None
    
    def generate_event(self, **kwargs) -> SecurityEvent:
        """Generate a single security event for this pillar."""
        # Determine if this is an attack or normal event
        is_attack = random.random() < self.config.get('attack_frequency', 0.15)
        
        if is_attack:
            return self._generate_attack_event(**kwargs)
        else:
            return self._generate_normal_event(**kwargs)
    
    def _generate_attack_event(self, **kwargs) -> SecurityEvent:
        """Generate an attack event for this pillar."""
        # Select attack pattern based on weights
        attack_types = list(self.attack_patterns.keys())
        weights = [self.attack_patterns[at].weight for at in attack_types]
        attack_type = random.choices(attack_types, weights=weights)[0]
        
        pattern = self.attack_patterns[attack_type]
        
        # Generate source and destination
        source = self._generate_source()
        destination = self._generate_destination()
        
        # Generate threat actor (optional)
        threat_actor = None
        if random.random() < 0.3:  # 30% chance of attributed attack
            threat_actor = random.choice(list(self.threat_actors.keys()))
        
        # Create event message
        message = self._create_attack_message(pattern, source, destination)
        
        # Generate raw data
        raw_data = self._generate_attack_raw_data(pattern, source, destination)
        
        # Generate IOCs
        ioc_type, ioc_value = self._generate_ioc()
        
        return SecurityEvent(
            pillar=self.pillar,
            log_type=self.pillar.value,
            severity=LogSeverity(pattern.severity),
            source=source,
            destination=destination,
            user=self._generate_user(),
            message=message,
            raw_data=raw_data,
            threat_actor=threat_actor,
            attack_tactic=pattern.tactic,
            attack_technique=attack_type,
            ioc_type=ioc_type,
            ioc_value=ioc_value,
            confidence_score=random.uniform(0.7, 1.0),
            false_positive_probability=random.uniform(0.0, 0.1),
            tags=['attack', 'security', attack_type, self.pillar.value]
        )
    
    def _generate_normal_event(self, **kwargs) -> SecurityEvent:
        """Generate a normal event for this pillar."""
        source = self._generate_source()
        destination = self._generate_destination()
        
        # Normal activities for this pillar
        normal_activities = self._get_normal_activities()
        activity = random.choice(normal_activities)
        
        message = f"Normal {self.pillar.value} activity: {activity}"
        
        raw_data = self._generate_normal_raw_data(source, destination)
        
        return SecurityEvent(
            pillar=self.pillar,
            log_type=self.pillar.value,
            severity=LogSeverity.LOW,
            source=source,
            destination=destination,
            user=self._generate_user(),
            message=message,
            raw_data=raw_data,
            tags=['normal', self.pillar.value]
        )
    
    def _generate_source(self) -> Dict[str, Any]:
        """Generate source information."""
        if self.faker:
            return {
                'ip_address': self.faker.ipv4(),
                'hostname': self.faker.hostname(),
                'port': random.randint(1024, 65535),
                'user_agent': self.faker.user_agent() if random.random() < 0.5 else None
            }
        else:
            return {
                'ip_address': f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}",
                'hostname': f"host-{random.randint(1000, 9999)}.corp.com",
                'port': random.randint(1024, 65535)
            }
    
    def _generate_destination(self) -> Dict[str, Any]:
        """Generate destination information."""
        if self.faker:
            return {
                'ip_address': self.faker.ipv4(),
                'hostname': self.faker.hostname(),
                'port': random.randint(1024, 65535),
                'service': random.choice(['http', 'https', 'ssh', 'ftp', 'smtp'])
            }
        else:
            return {
                'ip_address': f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}",
                'hostname': f"server-{random.randint(1000, 9999)}.corp.com",
                'port': random.randint(1024, 65535)
            }
    
    def _generate_user(self) -> str:
        """Generate user information."""
        if self.faker:
            return self.faker.user_name()
        else:
            return f"user{random.randint(1000, 9999)}"
    
    def _generate_ioc(self) -> tuple:
        """Generate indicators of compromise."""
        ioc_types = ['ip_address', 'domain', 'file_hash', 'email', 'url']
        ioc_type = random.choice(ioc_types)
        
        if ioc_type == 'ip_address':
            ioc_value = f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
        elif ioc_type == 'domain':
            ioc_value = f"malicious-{random.randint(1000, 9999)}.evil.com"
        elif ioc_type == 'file_hash':
            ioc_value = f"{random.randint(0, 0xFFFFFFFF):08x}{random.randint(0, 0xFFFFFFFF):08x}"
        elif ioc_type == 'email':
            ioc_value = f"attacker{random.randint(1000, 9999)}@evil.com"
        else:  # url
            ioc_value = f"https://evil-{random.randint(1000, 9999)}.com/malware"
        
        return ioc_type, ioc_value
    
    def _create_attack_message(self, pattern: PillarAttackPattern, source: Dict, destination: Dict) -> str:
        """Create attack message based on pattern."""
        return f"{pattern.description} from {source.get('ip_address', 'unknown')} to {destination.get('ip_address', 'unknown')}"
    
    def _generate_attack_raw_data(self, pattern: PillarAttackPattern, source: Dict, destination: Dict) -> Dict[str, Any]:
        """Generate raw data for attack events."""
        return {
            'attack_type': pattern.attack_type,
            'severity': pattern.severity,
            'indicators': pattern.indicators,
            'log_sources': pattern.log_sources,
            'mitigation_controls': pattern.mitigation_controls,
            'timestamp': datetime.utcnow().isoformat(),
            'pillar': self.pillar.value
        }
    
    def _generate_normal_raw_data(self, source: Dict, destination: Dict) -> Dict[str, Any]:
        """Generate raw data for normal events."""
        return {
            'event_type': 'normal',
            'timestamp': datetime.utcnow().isoformat(),
            'pillar': self.pillar.value
        }
    
    @abstractmethod
    def _get_normal_activities(self) -> List[str]:
        """Return list of normal activities for this pillar."""
        pass
    
    def generate_campaign_events(self, threat_actor: ThreatActor, duration_hours: int = 24) -> List[SecurityEvent]:
        """Generate a coordinated attack campaign for this pillar."""
        events = []
        start_time = datetime.utcnow()
        
        # Get threat actor characteristics
        actor_info = self.threat_actors.get(threat_actor, {})
        tactics = actor_info.get('tactics', [])
        
        # Generate events over time
        for tactic in tactics:
            event_count = random.randint(3, 10)
            for i in range(event_count):
                event_time = start_time + timedelta(
                    hours=random.uniform(0, duration_hours)
                )
                
                event = self._generate_attack_event()
                event.timestamp = event_time
                event.threat_actor = threat_actor
                event.attack_tactic = tactic
                event.campaign_id = str(uuid.uuid4())
                events.append(event)
        
        return sorted(events, key=lambda x: x.timestamp)
