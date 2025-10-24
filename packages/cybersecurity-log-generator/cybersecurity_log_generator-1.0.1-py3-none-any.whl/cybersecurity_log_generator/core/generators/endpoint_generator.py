"""
Endpoint Detection & Response (EDR) log generator.
Enhanced version with advanced malware detection and system events.
"""

import random
import hashlib
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from .base import BaseLogGenerator
from ..models import LogEvent, SecurityEvent, LogType, LogSeverity, AttackTactic


class EndpointLogGenerator(BaseLogGenerator):
    """Advanced endpoint log generator with malware detection and system events."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._setup_endpoint_patterns()
    
    def _setup_endpoint_patterns(self):
        """Setup endpoint patterns and malware signatures."""
        self.event_types = {
            'malware_detected': {
                'severity': 'critical',
                'description': 'Malware detected on endpoint',
                'tactic': AttackTactic.EXECUTION,
                'weight': 0.15
            },
            'scan_started': {
                'severity': 'low',
                'description': 'Antivirus scan started',
                'tactic': None,
                'weight': 0.2
            },
            'scan_completed': {
                'severity': 'low', 
                'description': 'Antivirus scan completed',
                'tactic': None,
                'weight': 0.2
            },
            'update_applied': {
                'severity': 'low',
                'description': 'Security update applied',
                'tactic': None,
                'weight': 0.15
            },
            'exception': {
                'severity': 'medium',
                'description': 'Security exception occurred',
                'tactic': AttackTactic.DEFENSE_EVASION,
                'weight': 0.1
            },
            'protection_disabled': {
                'severity': 'high',
                'description': 'Real-time protection disabled',
                'tactic': AttackTactic.DEFENSE_EVASION,
                'weight': 0.05
            },
            'protection_enabled': {
                'severity': 'low',
                'description': 'Real-time protection enabled',
                'tactic': None,
                'weight': 0.1
            },
            'suspicious_activity': {
                'severity': 'medium',
                'description': 'Suspicious endpoint activity',
                'tactic': AttackTactic.EXECUTION,
                'weight': 0.05
            }
        }
        
        self.malware_families = [
            'Trojan.Win32.Generic', 'Virus.Win32.Worm', 'Backdoor.Win32.Remote',
            'Ransomware.Win32.Crypto', 'Spyware.Win32.Keylogger', 'Adware.Win32.Popup',
            'Rootkit.Win32.Stealth', 'Exploit.Win32.Memory', 'Dropper.Win32.Payload',
            'Downloader.Win32.Malware'
        ]
        
        self.malicious_files = [
            'password_stealer.exe', 'keylogger.exe', 'ransom.exe', 'bot.exe',
            'backdoor.exe', 'trojan.exe', 'virus.exe', 'worm.exe', 'spyware.exe',
            'adware.exe', 'rootkit.exe', 'exploit.exe'
        ]
        
        self.legitimate_processes = [
            'explorer.exe', 'winlogon.exe', 'svchost.exe', 'lsass.exe',
            'services.exe', 'smss.exe', 'csrss.exe', 'chrome.exe',
            'firefox.exe', 'notepad.exe', 'calc.exe', 'mspaint.exe'
        ]
        
        self.scan_types = ['Full Scan', 'Quick Scan', 'Custom Scan', 'Real-time Scan', 'Boot-time Scan']
        self.update_types = ['Definition Update', 'Threat Database Update', 'Software Update', 'Engine Update']
        self.actions = ['Quarantine', 'Delete', 'Clean', 'Allow', 'Block', 'Report']
    
    def generate_event(self, **kwargs) -> SecurityEvent:
        """Generate a single endpoint event."""
        # Select event type based on weights
        event_types = list(self.event_types.keys())
        weights = [self.event_types[et]['weight'] for et in event_types]
        event_type = random.choices(event_types, weights=weights)[0]
        
        return self._generate_specific_event(event_type, **kwargs)
    
    def _generate_specific_event(self, event_type: str, **kwargs) -> SecurityEvent:
        """Generate a specific type of endpoint event."""
        event_info = self.event_types[event_type]
        
        # Generate source (endpoint)
        source = self.generate_network_endpoint("internal")
        source.hostname = self._generate_computer_name()
        
        # Generate user
        user = self.generate_user()
        
        # Generate process if applicable
        process = self.generate_process() if random.random() < 0.7 else None
        
        # Generate event-specific data
        if event_type == 'malware_detected':
            return self._generate_malware_event(source, user, process)
        elif event_type == 'scan_started':
            return self._generate_scan_started_event(source, user)
        elif event_type == 'scan_completed':
            return self._generate_scan_completed_event(source, user)
        elif event_type == 'update_applied':
            return self._generate_update_event(source, user)
        elif event_type == 'exception':
            return self._generate_exception_event(source, user, process)
        elif event_type == 'protection_disabled':
            return self._generate_protection_disabled_event(source, user)
        elif event_type == 'protection_enabled':
            return self._generate_protection_enabled_event(source, user)
        elif event_type == 'suspicious_activity':
            return self._generate_suspicious_activity_event(source, user, process)
        else:
            return self._generate_generic_event(source, user, process, event_info)
    
    def _generate_malware_event(self, source, user, process) -> SecurityEvent:
        """Generate malware detection event."""
        # Generate malicious file
        malicious_file = random.choice(self.malicious_files)
        file_path = f"C:\\Users\\{user}\\Downloads\\{malicious_file}"
        
        # Generate file hash
        file_hash = hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()
        
        # Generate threat name
        threat_name = random.choice(self.malware_families)
        
        # Generate action taken
        action = random.choices(self.actions, weights=[0.4, 0.3, 0.2, 0.05, 0.03, 0.02])[0]
        
        message = f"Malware detected: {threat_name} in {malicious_file}"
        
        raw_data = {
            'file_name': malicious_file,
            'file_path': file_path,
            'file_hash': file_hash,
            'threat_name': threat_name,
            'action_taken': action,
            'scan_engine': 'Windows Defender',
            'threat_level': random.choice(['Low', 'Medium', 'High', 'Critical']),
            'quarantine_location': f"C:\\Quarantine\\{file_hash[:8]}"
        }
        
        return SecurityEvent(
            log_type=LogType.ENDPOINT,
            severity=LogSeverity.CRITICAL,
            source=source,
            user=user,
            process=process,
            message=message,
            raw_data=raw_data,
            attack_tactic=AttackTactic.EXECUTION,
            attack_technique='malware_execution',
            confidence_score=random.uniform(0.9, 1.0),
            false_positive_probability=random.uniform(0.0, 0.05),
            tags=['malware', 'detection', 'critical']
        )
    
    def _generate_scan_started_event(self, source, user) -> SecurityEvent:
        """Generate scan started event."""
        scan_type = random.choice(self.scan_types)
        message = f"Antivirus scan started: {scan_type}"
        
        raw_data = {
            'scan_type': scan_type,
            'scan_engine': 'Windows Defender',
            'scan_mode': random.choice(['Manual', 'Scheduled', 'Real-time']),
            'target_paths': ['C:\\', 'D:\\'] if scan_type == 'Full Scan' else ['C:\\Users']
        }
        
        return SecurityEvent(
            log_type=LogType.ENDPOINT,
            severity=LogSeverity.LOW,
            source=source,
            user=user,
            process="MsMpEng.exe",  # Windows Defender process
            message=message,
            raw_data=raw_data,
            tags=['scan', 'antivirus']
        )
    
    def _generate_scan_completed_event(self, source, user) -> SecurityEvent:
        """Generate scan completed event."""
        scan_type = random.choice(self.scan_types)
        malware_found = random.randint(0, 5) if random.random() < 0.2 else 0
        message = f"Antivirus scan completed: {scan_type} - {malware_found} threats found"
        
        raw_data = {
            'scan_type': scan_type,
            'scan_engine': 'Windows Defender',
            'malware_found': malware_found,
            'files_scanned': random.randint(10000, 100000),
            'scan_duration': random.randint(300, 3600),  # seconds
            'scan_result': 'Completed' if malware_found == 0 else 'Threats Found'
        }
        
        return SecurityEvent(
            log_type=LogType.ENDPOINT,
            severity=LogSeverity.LOW,
            message=message,
            source=source,
            user=user,
            process="MsMpEng.exe",  # Windows Defender process
            raw_data=raw_data,
            tags=['scan', 'antivirus', 'completed']
        )
    
    def _generate_update_event(self, source, user) -> SecurityEvent:
        """Generate update applied event."""
        update_type = random.choice(self.update_types)
        version = f"{random.randint(1, 9)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        message = f"Security update applied: {update_type} v{version}"
        
        raw_data = {
            'update_type': update_type,
            'update_version': version,
            'update_engine': 'Windows Defender',
            'update_size': random.randint(1024, 10485760),  # 1KB to 10MB
            'update_source': 'Microsoft Update'
        }
        
        return SecurityEvent(
            log_type=LogType.ENDPOINT,
            severity=LogSeverity.LOW,
            source=source,
            user=user,
            message=message,
            raw_data=raw_data,
            tags=['update', 'security']
        )
    
    def _generate_exception_event(self, source, user, process) -> SecurityEvent:
        """Generate security exception event."""
        reasons = [
            'Trusted Application', 'Whitelisted Process', 'Administrator Override',
            'Digital Signature Valid', 'Corporate Policy Exception'
        ]
        reason = random.choice(reasons)
        process_name = process or random.choice(self.legitimate_processes)
        
        message = f"Security exception: {reason} for {process_name}"
        
        raw_data = {
            'process_name': process_name,
            'exception_reason': reason,
            'exception_type': 'Process Exception',
            'digital_signature': 'Valid' if 'Signature' in reason else 'N/A',
            'whitelist_entry': 'Found' if 'Whitelisted' in reason else 'Not Found'
        }
        
        return SecurityEvent(
            log_type=LogType.ENDPOINT,
            severity=LogSeverity.MEDIUM,
            source=source,
            user=user,
            process=process_name,
            message=message,
            raw_data=raw_data,
            attack_tactic=AttackTactic.DEFENSE_EVASION,
            attack_technique='process_exception',
            confidence_score=random.uniform(0.6, 0.9),
            tags=['exception', 'security', 'process']
        )
    
    def _generate_protection_disabled_event(self, source, user) -> SecurityEvent:
        """Generate protection disabled event."""
        reasons = ['Manual Disable', 'Scheduled Maintenance', 'System Override', 'Policy Change']
        reason = random.choice(reasons)
        message = f"Real-time protection disabled: {reason}"
        
        raw_data = {
            'protection_type': 'Real-time Protection',
            'disable_reason': reason,
            'disabled_by': user,
            'disable_time': datetime.utcnow().isoformat(),
            'protection_engine': 'Windows Defender'
        }
        
        return SecurityEvent(
            log_type=LogType.ENDPOINT,
            severity=LogSeverity.HIGH,
            source=source,
            user=user,
            message=message,
            raw_data=raw_data,
            attack_tactic=AttackTactic.DEFENSE_EVASION,
            attack_technique='disable_security',
            confidence_score=random.uniform(0.8, 1.0),
            tags=['protection', 'disabled', 'security']
        )
    
    def _generate_protection_enabled_event(self, source, user) -> SecurityEvent:
        """Generate protection enabled event."""
        message = "Real-time protection enabled"
        
        raw_data = {
            'protection_type': 'Real-time Protection',
            'enabled_by': user,
            'enable_time': datetime.utcnow().isoformat(),
            'protection_engine': 'Windows Defender',
            'protection_level': 'High'
        }
        
        return SecurityEvent(
            log_type=LogType.ENDPOINT,
            severity=LogSeverity.LOW,
            source=source,
            user=user,
            message=message,
            raw_data=raw_data,
            tags=['protection', 'enabled', 'security']
        )
    
    def _generate_suspicious_activity_event(self, source, user, process) -> SecurityEvent:
        """Generate suspicious activity event."""
        activities = [
            'Unusual network connections', 'Suspicious file modifications',
            'Abnormal process behavior', 'Suspicious registry changes',
            'Unusual system calls', 'Suspicious memory access'
        ]
        activity = random.choice(activities)
        process_name = process or random.choice(self.legitimate_processes)
        
        message = f"Suspicious activity detected: {activity} in {process_name}"
        
        raw_data = {
            'activity_type': activity,
            'process_name': process_name,
            'suspicion_level': random.choice(['Low', 'Medium', 'High']),
            'behavior_analysis': 'Anomalous',
            'threat_score': random.randint(60, 95)
        }
        
        return SecurityEvent(
            log_type=LogType.ENDPOINT,
            severity=LogSeverity.MEDIUM,
            source=source,
            user=user,
            process=process_name,
            message=message,
            raw_data=raw_data,
            attack_tactic=AttackTactic.EXECUTION,
            attack_technique='suspicious_behavior',
            confidence_score=random.uniform(0.7, 0.9),
            false_positive_probability=random.uniform(0.1, 0.3),
            tags=['suspicious', 'behavior', 'analysis']
        )
    
    def _generate_generic_event(self, source, user, process, event_info) -> SecurityEvent:
        """Generate a generic endpoint event."""
        message = event_info['description']
        
        raw_data = {
            'event_type': event_info['description'],
            'endpoint_id': str(uuid.uuid4()),
            'system_info': {
                'os': 'Windows 10',
                'architecture': 'x64',
                'version': '10.0.19041'
            }
        }
        
        return SecurityEvent(
            log_type=LogType.ENDPOINT,
            severity=LogSeverity(event_info['severity']),
            source=source,
            user=user,
            process=process,
            message=message,
            raw_data=raw_data,
            attack_tactic=event_info['tactic'],
            tags=['endpoint', 'system']
        )
    
    def _generate_computer_name(self) -> str:
        """Generate a realistic computer name."""
        prefixes = ['DESKTOP', 'LAPTOP', 'WORKSTATION', 'SERVER']
        prefix = random.choice(prefixes)
        suffix = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=6))
        return f"{prefix}-{suffix}"
