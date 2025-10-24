"""
Firewall log generator.
Generates realistic firewall and network security events.
"""

import random
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from .base import BaseLogGenerator
from ..models import LogEvent, SecurityEvent, LogType, LogSeverity, AttackTactic


class FirewallLogGenerator(BaseLogGenerator):
    """Firewall log generator with network security events."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._setup_firewall_patterns()
    
    def _setup_firewall_patterns(self):
        """Setup firewall patterns and security events."""
        self.actions = {
            'ALLOW': 0.7,
            'DENY': 0.2,
            'DROP': 0.05,
            'REJECT': 0.05
        }
        
        self.protocols = {
            'TCP': 0.5,
            'UDP': 0.3,
            'ICMP': 0.1,
            'GRE': 0.05,
            'ESP': 0.05
        }
        
        self.security_events = {
            'port_scan': {
                'severity': 'medium',
                'description': 'Port scanning detected',
                'action': 'DENY',
                'weight': 0.1
            },
            'dos_attack': {
                'severity': 'high',
                'description': 'Denial of service attack',
                'action': 'DROP',
                'weight': 0.05
            },
            'suspicious_connection': {
                'severity': 'medium',
                'description': 'Suspicious connection pattern',
                'action': 'DENY',
                'weight': 0.1
            },
            'malicious_ip': {
                'severity': 'high',
                'description': 'Connection from known malicious IP',
                'action': 'DROP',
                'weight': 0.05
            },
            'policy_violation': {
                'severity': 'medium',
                'description': 'Firewall policy violation',
                'action': 'DENY',
                'weight': 0.1
            }
        }
    
    def generate_event(self, **kwargs) -> SecurityEvent:
        """Generate a single firewall event."""
        # Determine if this is a security event
        is_security_event = random.random() < 0.15  # 15% chance of security event
        
        if is_security_event:
            return self._generate_security_event(**kwargs)
        else:
            return self._generate_normal_event(**kwargs)
    
    def _generate_security_event(self, **kwargs) -> SecurityEvent:
        """Generate a security event."""
        # Select security event type
        event_types = list(self.security_events.keys())
        weights = [self.security_events[et]['weight'] for et in event_types]
        event_type = random.choices(event_types, weights=weights)[0]
        
        event_info = self.security_events[event_type]
        
        # Generate source and destination
        source = self.generate_network_endpoint("external")
        destination = self.generate_network_endpoint("internal")
        
        # Generate protocol
        protocol = random.choices(list(self.protocols.keys()), 
                                weights=list(self.protocols.values()))[0]
        
        # Generate ports
        source_port = self.generate_port(protocol)
        dest_port = self.generate_port(protocol)
        
        # Create event message
        message = f"Firewall {event_info['action']}: {event_info['description']} from {source.ip_address}:{source_port} to {destination.ip_address}:{dest_port} via {protocol}"
        
        # Generate raw data
        raw_data = {
            'action': event_info['action'],
            'protocol': protocol,
            'source_port': source_port,
            'destination_port': dest_port,
            'bytes': random.randint(64, 1500),
            'packets': random.randint(1, 10),
            'rule_id': f"FW-{random.randint(100, 999)}",
            'security_event': True,
            'event_type': event_type
        }
        
        return SecurityEvent(
            log_type=LogType.FIREWALL,
            severity=LogSeverity(event_info['severity']),
            source=source,
            destination=destination,
            message=message,
            raw_data=raw_data,
            attack_tactic=AttackTactic.RECONNAISSANCE if event_type == 'port_scan' else AttackTactic.IMPACT,
            attack_technique=event_type,
            confidence_score=random.uniform(0.8, 1.0),
            false_positive_probability=random.uniform(0.0, 0.1),
            tags=['firewall', 'security', event_type]
        )
    
    def _generate_normal_event(self, **kwargs) -> SecurityEvent:
        """Generate a normal firewall event."""
        source = self.generate_network_endpoint("external")
        destination = self.generate_network_endpoint("internal")
        
        # Generate protocol
        protocol = random.choices(list(self.protocols.keys()), 
                               weights=list(self.protocols.values()))[0]
        
        # Generate ports
        source_port = self.generate_port(protocol)
        dest_port = self.generate_port(protocol)
        
        # Generate action
        action = random.choices(list(self.actions.keys()), 
                              weights=list(self.actions.values()))[0]
        
        # Create event message
        message = f"Firewall {action}: {protocol} connection from {source.ip_address}:{source_port} to {destination.ip_address}:{dest_port}"
        
        # Generate raw data
        raw_data = {
            'action': action,
            'protocol': protocol,
            'source_port': source_port,
            'destination_port': dest_port,
            'bytes': random.randint(64, 1500),
            'packets': random.randint(1, 10),
            'rule_id': f"FW-{random.randint(100, 999)}",
            'security_event': False
        }
        
        return SecurityEvent(
            log_type=LogType.FIREWALL,
            severity=LogSeverity.LOW,
            source=source,
            destination=destination,
            message=message,
            raw_data=raw_data,
            tags=['firewall', 'normal']
        )
