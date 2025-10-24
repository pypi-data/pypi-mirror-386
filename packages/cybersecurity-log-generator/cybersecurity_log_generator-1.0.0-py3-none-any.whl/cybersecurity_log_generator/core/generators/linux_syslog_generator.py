"""
Linux Syslog generator.
Generates realistic Linux system and security events.
"""

import random
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from .base import BaseLogGenerator
from ..models import LogEvent, SecurityEvent, LogType, LogSeverity, AttackTactic


class LinuxSyslogGenerator(BaseLogGenerator):
    """Linux Syslog generator with system and security events."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._setup_linux_patterns()
    
    def _setup_linux_patterns(self):
        """Setup Linux syslog patterns."""
        self.facilities = {
            'kern': 0, 'user': 1, 'mail': 2, 'daemon': 3, 'auth': 4,
            'syslog': 5, 'lpr': 6, 'news': 7, 'uucp': 8, 'cron': 9,
            'authpriv': 10, 'ftp': 11, 'local0': 16, 'local1': 17,
            'local2': 18, 'local3': 19, 'local4': 20, 'local5': 21,
            'local6': 22, 'local7': 23
        }
        
        self.severities = {
            'emerg': 0, 'alert': 1, 'crit': 2, 'err': 3,
            'warning': 4, 'notice': 5, 'info': 6, 'debug': 7
        }
        
        self.event_types = {
            'ssh_login_success': {
                'severity': 'info',
                'facility': 'auth',
                'description': 'SSH login successful',
                'weight': 0.3
            },
            'ssh_login_failure': {
                'severity': 'warning',
                'facility': 'auth',
                'description': 'SSH login failed',
                'weight': 0.1
            },
            'sudo_command': {
                'severity': 'info',
                'facility': 'auth',
                'description': 'Sudo command executed',
                'weight': 0.15
            },
            'service_start': {
                'severity': 'info',
                'facility': 'daemon',
                'description': 'Service started',
                'weight': 0.2
            },
            'service_stop': {
                'severity': 'info',
                'facility': 'daemon',
                'description': 'Service stopped',
                'weight': 0.1
            },
            'kernel_message': {
                'severity': 'warning',
                'facility': 'kern',
                'description': 'Kernel message',
                'weight': 0.1
            },
            'cron_job': {
                'severity': 'info',
                'facility': 'cron',
                'description': 'Cron job executed',
                'weight': 0.05
            }
        }
    
    def generate_event(self, **kwargs) -> SecurityEvent:
        """Generate a single Linux syslog event."""
        # Select event type based on weights
        event_types = list(self.event_types.keys())
        weights = [self.event_types[et]['weight'] for et in event_types]
        event_type = random.choices(event_types, weights=weights)[0]
        
        return self._generate_specific_event(event_type, **kwargs)
    
    def _generate_specific_event(self, event_type: str, **kwargs) -> SecurityEvent:
        """Generate a specific Linux syslog event."""
        event_info = self.event_types[event_type]
        
        # Generate source and destination
        source = self.generate_network_endpoint("internal")
        destination = self.generate_network_endpoint("internal")
        
        # Generate user
        user = self.generate_user()
        
        # Generate process
        process = self.generate_process()
        
        # Create syslog message
        facility = event_info['facility']
        severity = event_info['severity']
        hostname = source.hostname or f"linux-{random.randint(100, 999)}"
        
        message = f"<{self.facilities[facility] * 8 + self.severities[severity]}>{self._generate_timestamp()} {hostname} {self._generate_syslog_message(event_type, user, process)}"
        
        # Generate raw data
        raw_data = {
            'facility': facility,
            'severity': severity,
            'hostname': hostname,
            'program': process,
            'pid': random.randint(1000, 9999),
            'message': event_info['description']
        }
        
        # Map string severity to LogSeverity enum
        severity_map = {
            'info': LogSeverity.LOW,
            'warning': LogSeverity.MEDIUM,
            'error': LogSeverity.HIGH,
            'critical': LogSeverity.CRITICAL
        }
        
        return SecurityEvent(
            log_type=LogType.LINUX_SYSLOG,
            severity=severity_map.get(event_info['severity'], LogSeverity.LOW),
            source=source,
            destination=destination,
            user=user,
            process=process,
            message=message,
            raw_data=raw_data,
            tags=['linux', 'syslog', event_type]
        )
    
    def _generate_timestamp(self) -> str:
        """Generate syslog timestamp."""
        now = datetime.utcnow()
        return now.strftime("%b %d %H:%M:%S")
    
    def _generate_syslog_message(self, event_type: str, user: str, process: str) -> str:
        """Generate syslog message content."""
        if event_type == 'ssh_login_success':
            return f"sshd[{random.randint(1000, 9999)}]: Accepted password for {user} from {self.generate_ip_address('external')} port {random.randint(1024, 65535)} ssh2"
        elif event_type == 'ssh_login_failure':
            return f"sshd[{random.randint(1000, 9999)}]: Failed password for {user} from {self.generate_ip_address('external')} port {random.randint(1024, 65535)} ssh2"
        elif event_type == 'sudo_command':
            return f"sudo: {user} : TTY=pts/{random.randint(0, 9)} ; PWD=/home/{user} ; USER=root ; COMMAND={process}"
        elif event_type == 'service_start':
            return f"systemd[{random.randint(1000, 9999)}]: Started {process}"
        elif event_type == 'service_stop':
            return f"systemd[{random.randint(1000, 9999)}]: Stopped {process}"
        elif event_type == 'kernel_message':
            return f"kernel: {random.choice(['Memory allocation failed', 'Network interface up', 'Disk I/O error', 'CPU temperature high'])}"
        elif event_type == 'cron_job':
            return f"CRON[{random.randint(1000, 9999)}]: ({user}) CMD ({process})"
        else:
            return f"{process}: {event_type} event"
