"""
IDS (Intrusion Detection System) log generator.
Enhanced version of the original Security-Log-Generator with advanced capabilities.
"""

import random
from typing import Dict, Any, Optional, List
from datetime import datetime

from .base import BaseLogGenerator
from ..models import LogEvent, SecurityEvent, LogType, LogSeverity, AttackTactic, ThreatActor


class IDSLogGenerator(BaseLogGenerator):
    """Advanced IDS log generator with realistic attack patterns."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._setup_attack_patterns()
    
    def _setup_attack_patterns(self):
        """Setup attack patterns and threat intelligence."""
        self.protocols = {
            'TCP': 0.4, 'UDP': 0.3, 'ICMP': 0.1, 'HTTP': 0.1, 
            'HTTPS': 0.05, 'FTP': 0.02, 'SMTP': 0.02, 'DNS': 0.01
        }
        
        self.attack_types = {
            'port_scan': {
                'severity': 'medium',
                'description': 'Port scanning detected',
                'tactic': AttackTactic.RECONNAISSANCE,
                'weight': 0.3
            },
            'dos_attack': {
                'severity': 'high', 
                'description': 'Denial of service attack',
                'tactic': AttackTactic.IMPACT,
                'weight': 0.15
            },
            'malware_traffic': {
                'severity': 'high',
                'description': 'Malicious traffic detected',
                'tactic': AttackTactic.EXECUTION,
                'weight': 0.2
            },
            'sql_injection': {
                'severity': 'critical',
                'description': 'SQL injection attempt',
                'tactic': AttackTactic.INITIAL_ACCESS,
                'weight': 0.1
            },
            'xss_attack': {
                'severity': 'high',
                'description': 'Cross-site scripting attempt',
                'tactic': AttackTactic.INITIAL_ACCESS,
                'weight': 0.1
            },
            'brute_force': {
                'severity': 'medium',
                'description': 'Brute force attack',
                'tactic': AttackTactic.CREDENTIAL_ACCESS,
                'weight': 0.1
            },
            'data_exfiltration': {
                'severity': 'critical',
                'description': 'Potential data exfiltration',
                'tactic': AttackTactic.EXFILTRATION,
                'weight': 0.05
            }
        }
        
        self.threat_actors = {
            ThreatActor.APT29: {'sophistication': 'high', 'tactics': [AttackTactic.INITIAL_ACCESS, AttackTactic.PERSISTENCE]},
            ThreatActor.APT28: {'sophistication': 'high', 'tactics': [AttackTactic.EXECUTION, AttackTactic.LATERAL_MOVEMENT]},
            ThreatActor.LAZARUS: {'sophistication': 'medium', 'tactics': [AttackTactic.INITIAL_ACCESS, AttackTactic.EXFILTRATION]},
            ThreatActor.FIN7: {'sophistication': 'medium', 'tactics': [AttackTactic.CREDENTIAL_ACCESS, AttackTactic.COLLECTION]}
        }
    
    def generate_event(self, **kwargs) -> SecurityEvent:
        """Generate a single IDS event."""
        # Determine if this is a normal or attack event
        is_attack = random.random() < 0.15  # 15% chance of attack event
        
        if is_attack:
            return self._generate_attack_event(**kwargs)
        else:
            return self._generate_normal_event(**kwargs)
    
    def _generate_attack_event(self, **kwargs) -> SecurityEvent:
        """Generate an attack event."""
        # Select attack type based on weights
        attack_types = list(self.attack_types.keys())
        weights = [self.attack_types[at]['weight'] for at in attack_types]
        attack_type = random.choices(attack_types, weights=weights)[0]
        
        attack_info = self.attack_types[attack_type]
        
        # Generate source and destination
        source = self.generate_network_endpoint("external")
        destination = self.generate_network_endpoint("internal")
        
        # Generate protocol
        protocol = random.choices(list(self.protocols.keys()), 
                                weights=list(self.protocols.values()))[0]
        
        # Generate ports based on protocol
        source_port = self.generate_port(protocol)
        dest_port = self.generate_port(protocol)
        
        # Generate threat actor (optional)
        threat_actor = None
        if random.random() < 0.3:  # 30% chance of attributed attack
            threat_actor = random.choice(list(self.threat_actors.keys()))
        
        # Create event message
        message = f"{attack_info['description']} from {source.ip_address}:{source_port} to {destination.ip_address}:{dest_port} via {protocol}"
        
        # Generate raw data
        raw_data = {
            'protocol': protocol,
            'source_port': source_port,
            'destination_port': dest_port,
            'flags': self._generate_tcp_flags(),
            'packet_size': random.randint(64, 1500),
            'attack_signature': f"SIG-{random.randint(1000, 9999)}",
            'rule_id': f"IDS-{random.randint(100, 999)}"
        }
        
        return SecurityEvent(
            log_type=LogType.IDS,
            severity=LogSeverity(attack_info['severity']),
            source=source,
            destination=destination,
            message=message,
            raw_data=raw_data,
            threat_actor=threat_actor,
            attack_tactic=attack_info['tactic'],
            attack_technique=attack_type,
            confidence_score=random.uniform(0.7, 1.0),
            false_positive_probability=random.uniform(0.0, 0.1),
            tags=['attack', 'security', attack_type]
        )
    
    def _generate_normal_event(self, **kwargs) -> SecurityEvent:
        """Generate a normal network event."""
        source = self.generate_network_endpoint("internal")
        destination = self.generate_network_endpoint("external")
        
        protocol = random.choices(list(self.protocols.keys()), 
                               weights=list(self.protocols.values()))[0]
        
        source_port = self.generate_port(protocol)
        dest_port = self.generate_port(protocol)
        
        # Normal network activities
        normal_activities = [
            "HTTP request to external website",
            "DNS query for domain resolution", 
            "HTTPS connection established",
            "Email client connecting to SMTP server",
            "FTP file transfer initiated",
            "SSH connection to remote server"
        ]
        
        activity = random.choice(normal_activities)
        message = f"Normal network activity: {activity} from {source.ip_address}:{source_port} to {destination.ip_address}:{dest_port}"
        
        raw_data = {
            'protocol': protocol,
            'source_port': source_port,
            'destination_port': dest_port,
            'flags': self._generate_tcp_flags(),
            'packet_size': random.randint(64, 1500),
            'connection_state': 'established'
        }
        
        return SecurityEvent(
            log_type=LogType.IDS,
            severity=LogSeverity.LOW,
            source=source,
            destination=destination,
            message=message,
            raw_data=raw_data,
            tags=['normal', 'network']
        )
    
    def _generate_tcp_flags(self) -> str:
        """Generate realistic TCP flags."""
        flags = ['SYN', 'ACK', 'FIN', 'RST', 'PSH', 'URG']
        # Most connections have SYN and ACK
        if random.random() < 0.8:
            return 'SYN,ACK'
        else:
            return random.choice(flags)
    
    def generate_attack_campaign(self, threat_actor: ThreatActor, 
                                duration_hours: int = 24) -> List[SecurityEvent]:
        """Generate a coordinated attack campaign."""
        events = []
        start_time = datetime.utcnow()
        
        # Get threat actor characteristics
        actor_info = self.threat_actors[threat_actor]
        tactics = actor_info['tactics']
        
        # Generate events over time with realistic timing
        for tactic in tactics:
            # Generate 5-20 events per tactic
            event_count = random.randint(5, 20)
            for i in range(event_count):
                # Spread events over the duration
                event_time = start_time + timedelta(
                    hours=random.uniform(0, duration_hours)
                )
                
                event = self._generate_attack_event()
                event.timestamp = event_time
                event.threat_actor = threat_actor
                event.attack_tactic = tactic
                events.append(event)
        
        return sorted(events, key=lambda x: x.timestamp)
