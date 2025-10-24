"""
Endpoint Security pillar generator.
"""

from typing import Dict, Any, List
from ..models import CyberdefensePillar, LogSeverity, AttackTactic, PillarAttackPattern
from .base_pillar_generator import BasePillarGenerator


class EndpointSecurityGenerator(BasePillarGenerator):
    """Generator for Endpoint Security pillar."""
    
    def get_pillar(self) -> CyberdefensePillar:
        return CyberdefensePillar.ENDPOINT_SECURITY
    
    def _setup_attack_patterns(self) -> Dict[str, PillarAttackPattern]:
        """Setup endpoint security attack patterns."""
        return {
            'malware_detection': PillarAttackPattern(
                pillar=CyberdefensePillar.ENDPOINT_SECURITY,
                attack_type='malware_detection',
                severity=LogSeverity.CRITICAL,
                description='Malware detected on endpoint',
                tactic=AttackTactic.EXECUTION,
                weight=0.2,
                indicators=['malware_signature', 'suspicious_process', 'file_quarantine'],
                log_sources=['antivirus_logs', 'edr_logs', 'system_logs'],
                mitigation_controls=['malware_prevention', 'endpoint_protection', 'quarantine']
            ),
            'ransomware_attack': PillarAttackPattern(
                pillar=CyberdefensePillar.ENDPOINT_SECURITY,
                attack_type='ransomware_attack',
                severity=LogSeverity.CRITICAL,
                description='Ransomware attack detected',
                tactic=AttackTactic.IMPACT,
                weight=0.15,
                indicators=['file_encryption', 'ransom_note', 'crypto_locker'],
                log_sources=['file_system_logs', 'process_logs', 'network_logs'],
                mitigation_controls=['backup_restore', 'endpoint_isolation', 'incident_response']
            ),
            'privilege_escalation': PillarAttackPattern(
                pillar=CyberdefensePillar.ENDPOINT_SECURITY,
                attack_type='privilege_escalation',
                severity=LogSeverity.HIGH,
                description='Privilege escalation attempt detected',
                tactic=AttackTactic.PRIVILEGE_ESCALATION,
                weight=0.2,
                indicators=['privilege_escalation', 'unauthorized_access', 'admin_abuse'],
                log_sources=['system_logs', 'privilege_logs', 'audit_logs'],
                mitigation_controls=['privilege_control', 'access_review', 'privilege_monitoring']
            ),
            'lateral_movement': PillarAttackPattern(
                pillar=CyberdefensePillar.ENDPOINT_SECURITY,
                attack_type='lateral_movement',
                severity=LogSeverity.HIGH,
                description='Lateral movement detected',
                tactic=AttackTactic.LATERAL_MOVEMENT,
                weight=0.15,
                indicators=['network_scanning', 'credential_dumping', 'pass_the_hash'],
                log_sources=['network_logs', 'authentication_logs', 'system_logs'],
                mitigation_controls=['network_segmentation', 'credential_protection', 'lateral_movement_detection']
            ),
            'insider_threat': PillarAttackPattern(
                pillar=CyberdefensePillar.ENDPOINT_SECURITY,
                attack_type='insider_threat',
                severity=LogSeverity.HIGH,
                description='Insider threat activity detected',
                tactic=AttackTactic.ABUSE,
                weight=0.15,
                indicators=['unauthorized_data_access', 'data_exfiltration', 'privilege_abuse'],
                log_sources=['access_logs', 'data_logs', 'user_activity_logs'],
                mitigation_controls=['user_monitoring', 'data_protection', 'insider_threat_detection']
            ),
            'endpoint_compromise': PillarAttackPattern(
                pillar=CyberdefensePillar.ENDPOINT_SECURITY,
                attack_type='endpoint_compromise',
                severity=LogSeverity.CRITICAL,
                description='Endpoint compromise detected',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.15,
                indicators=['system_compromise', 'persistent_access', 'backdoor'],
                log_sources=['system_logs', 'network_logs', 'security_logs'],
                mitigation_controls=['endpoint_isolation', 'incident_response', 'forensic_analysis']
            )
        }
    
    def _get_normal_activities(self) -> List[str]:
        """Return normal endpoint security activities."""
        return [
            'Endpoint security scan completed',
            'Antivirus update applied',
            'Endpoint patch installed',
            'Security policy applied',
            'Endpoint monitoring active',
            'User login successful',
            'Application launched',
            'File access authorized',
            'Network connection established',
            'Security event logged'
        ]
