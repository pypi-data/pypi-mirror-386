"""
Windows Event Log generator.
Generates realistic Windows security and system events.
"""

import random
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from .base import BaseLogGenerator
from ..models import LogEvent, SecurityEvent, LogType, LogSeverity, AttackTactic


class WindowsEventLogGenerator(BaseLogGenerator):
    """Windows Event Log generator with security events."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._setup_windows_patterns()
    
    def _setup_windows_patterns(self):
        """Setup Windows event patterns."""
        self.event_types = {
            'logon_success': {
                'severity': 'low',
                'description': 'Successful logon',
                'event_id': 4624,
                'weight': 0.3
            },
            'logon_failure': {
                'severity': 'medium',
                'description': 'Failed logon attempt',
                'event_id': 4625,
                'weight': 0.1
            },
            'privilege_escalation': {
                'severity': 'high',
                'description': 'Privilege escalation attempt',
                'event_id': 4672,
                'weight': 0.05
            },
            'service_start': {
                'severity': 'low',
                'description': 'Service started',
                'event_id': 7036,
                'weight': 0.2
            },
            'service_stop': {
                'severity': 'low',
                'description': 'Service stopped',
                'event_id': 7034,
                'weight': 0.1
            },
            'process_creation': {
                'severity': 'low',
                'description': 'Process created',
                'event_id': 4688,
                'weight': 0.15
            },
            'file_access': {
                'severity': 'low',
                'description': 'File accessed',
                'event_id': 4663,
                'weight': 0.1
            }
        }
        
        self.logon_types = {
            2: 'Interactive',
            3: 'Network',
            4: 'Batch',
            5: 'Service',
            7: 'Unlock',
            8: 'NetworkCleartext',
            9: 'NewCredentials',
            10: 'RemoteInteractive',
            11: 'CachedInteractive'
        }
    
    def generate_event(self, **kwargs) -> SecurityEvent:
        """Generate a single Windows event."""
        # Select event type based on weights
        event_types = list(self.event_types.keys())
        weights = [self.event_types[et]['weight'] for et in event_types]
        event_type = random.choices(event_types, weights=weights)[0]
        
        return self._generate_specific_event(event_type, **kwargs)
    
    def _generate_specific_event(self, event_type: str, **kwargs) -> SecurityEvent:
        """Generate a specific Windows event type."""
        event_info = self.event_types[event_type]
        
        # Generate source and destination
        source = self.generate_network_endpoint("internal")
        destination = self.generate_network_endpoint("internal")
        
        # Generate user
        user = self.generate_user()
        
        # Generate process
        process = self.generate_process()
        
        # Create event message
        message = f"Windows Event {event_info['event_id']}: {event_info['description']}"
        
        # Generate raw data
        raw_data = {
            'event_id': event_info['event_id'],
            'log_name': 'Security',
            'source': 'Microsoft-Windows-Security-Auditing',
            'computer_name': source.hostname or f"WIN-{random.randint(1000, 9999)}",
            'user_name': user,
            'process_name': process,
            'logon_type': random.choice(list(self.logon_types.keys())),
            'workstation_name': destination.hostname or f"WORKSTATION-{random.randint(100, 999)}"
        }
        
        return SecurityEvent(
            log_type=LogType.WINDOWS_EVENT,
            severity=LogSeverity(event_info['severity']),
            source=source,
            destination=destination,
            user=user,
            process=process,
            event_id=str(event_info['event_id']),
            message=message,
            raw_data=raw_data,
            tags=['windows', 'event', event_type]
        )
