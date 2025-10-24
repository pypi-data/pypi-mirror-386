"""
Incident Response pillar generator.
"""

from typing import Dict, Any, List
from ..models import CyberdefensePillar, LogSeverity, AttackTactic, PillarAttackPattern
from .base_pillar_generator import BasePillarGenerator


class IncidentResponseGenerator(BasePillarGenerator):
    """Generator for Incident Response pillar."""
    
    def get_pillar(self) -> CyberdefensePillar:
        return CyberdefensePillar.INCIDENT_RESPONSE
    
    def _setup_attack_patterns(self) -> Dict[str, PillarAttackPattern]:
        """Setup incident response attack patterns."""
        return {
            'incident_response_bypass': PillarAttackPattern(
                pillar=CyberdefensePillar.INCIDENT_RESPONSE,
                attack_type='incident_response_bypass',
                severity=LogSeverity.HIGH,
                description='Incident response bypass attack',
                tactic=AttackTactic.DEFENSE_EVASION,
                weight=0.25,
                indicators=['response_bypass', 'incident_evasion', 'response_manipulation'],
                log_sources=['incident_logs', 'response_logs', 'security_logs'],
                mitigation_controls=['response_monitoring', 'incident_validation', 'response_controls']
            ),
            'forensic_evidence_tampering': PillarAttackPattern(
                pillar=CyberdefensePillar.INCIDENT_RESPONSE,
                attack_type='forensic_evidence_tampering',
                severity=LogSeverity.CRITICAL,
                description='Forensic evidence tampering',
                tactic=AttackTactic.DEFENSE_EVASION,
                weight=0.2,
                indicators=['evidence_tampering', 'forensic_manipulation', 'evidence_destruction'],
                log_sources=['forensic_logs', 'evidence_logs', 'security_logs'],
                mitigation_controls=['evidence_protection', 'forensic_integrity', 'evidence_monitoring']
            ),
            'incident_communication_attack': PillarAttackPattern(
                pillar=CyberdefensePillar.INCIDENT_RESPONSE,
                attack_type='incident_communication_attack',
                severity=LogSeverity.MEDIUM,
                description='Incident communication attack',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.15,
                indicators=['communication_disruption', 'incident_manipulation', 'response_delay'],
                log_sources=['communication_logs', 'incident_logs', 'response_logs'],
                mitigation_controls=['communication_backup', 'incident_monitoring', 'response_validation']
            ),
            'response_team_compromise': PillarAttackPattern(
                pillar=CyberdefensePillar.INCIDENT_RESPONSE,
                attack_type='response_team_compromise',
                severity=LogSeverity.CRITICAL,
                description='Incident response team compromise',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.15,
                indicators=['team_compromise', 'response_breach', 'team_manipulation'],
                log_sources=['team_logs', 'response_logs', 'security_logs'],
                mitigation_controls=['team_security', 'response_protection', 'team_monitoring']
            ),
            'incident_data_manipulation': PillarAttackPattern(
                pillar=CyberdefensePillar.INCIDENT_RESPONSE,
                attack_type='incident_data_manipulation',
                severity=LogSeverity.HIGH,
                description='Incident data manipulation',
                tactic=AttackTactic.DEFENSE_EVASION,
                weight=0.1,
                indicators=['data_manipulation', 'incident_tampering', 'data_corruption'],
                log_sources=['incident_logs', 'data_logs', 'security_logs'],
                mitigation_controls=['data_integrity', 'incident_validation', 'data_monitoring']
            ),
            'response_automation_abuse': PillarAttackPattern(
                pillar=CyberdefensePillar.INCIDENT_RESPONSE,
                attack_type='response_automation_abuse',
                severity=LogSeverity.MEDIUM,
                description='Response automation abuse',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.1,
                indicators=['automation_abuse', 'response_manipulation', 'automation_bypass'],
                log_sources=['automation_logs', 'response_logs', 'security_logs'],
                mitigation_controls=['automation_monitoring', 'response_validation', 'automation_controls']
            ),
            'incident_escalation_abuse': PillarAttackPattern(
                pillar=CyberdefensePillar.INCIDENT_RESPONSE,
                attack_type='incident_escalation_abuse',
                severity=LogSeverity.MEDIUM,
                description='Incident escalation abuse',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.05,
                indicators=['escalation_abuse', 'incident_manipulation', 'escalation_bypass'],
                log_sources=['escalation_logs', 'incident_logs', 'response_logs'],
                mitigation_controls=['escalation_monitoring', 'incident_validation', 'escalation_controls']
            )
        }
    
    def _get_normal_activities(self) -> List[str]:
        """Return list of normal incident response activities."""
        return [
            "Incident detection and analysis",
            "Incident containment",
            "Incident eradication",
            "Incident recovery",
            "Incident lessons learned",
            "Incident response training",
            "Incident response plan update",
            "Incident response drill",
            "Incident response audit",
            "Incident response metrics collection",
            "Incident response tool configuration",
            "Incident response process improvement",
            "Incident response risk assessment",
            "Incident response compliance check",
            "Incident response awareness training",
            "Incident response policy update",
            "Incident response governance review",
            "Incident response certification",
            "Incident response monitoring",
            "Incident response communication"
        ]

