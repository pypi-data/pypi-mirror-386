"""
Detection & Correlation pillar generator.
"""

from typing import Dict, Any, List
from ..models import CyberdefensePillar, LogSeverity, AttackTactic, PillarAttackPattern
from .base_pillar_generator import BasePillarGenerator


class DetectionCorrelationGenerator(BasePillarGenerator):
    """Generator for Detection & Correlation pillar."""
    
    def get_pillar(self) -> CyberdefensePillar:
        return CyberdefensePillar.DETECTION_CORRELATION
    
    def _setup_attack_patterns(self) -> Dict[str, PillarAttackPattern]:
        """Setup detection & correlation attack patterns."""
        return {
            'siem_bypass': PillarAttackPattern(
                pillar=CyberdefensePillar.DETECTION_CORRELATION,
                attack_type='siem_bypass',
                severity=LogSeverity.HIGH,
                description='SIEM detection bypass attempt',
                tactic=AttackTactic.DEFENSE_EVASION,
                weight=0.25,
                indicators=['log_tampering', 'detection_evasion', 'siem_manipulation'],
                log_sources=['siem_logs', 'security_logs', 'detection_logs'],
                mitigation_controls=['siem_hardening', 'log_integrity', 'detection_monitoring']
            ),
            'correlation_rule_evasion': PillarAttackPattern(
                pillar=CyberdefensePillar.DETECTION_CORRELATION,
                attack_type='correlation_rule_evasion',
                severity=LogSeverity.HIGH,
                description='Correlation rule evasion attack',
                tactic=AttackTactic.DEFENSE_EVASION,
                weight=0.2,
                indicators=['rule_evasion', 'timing_attacks', 'correlation_bypass'],
                log_sources=['correlation_logs', 'siem_logs', 'detection_logs'],
                mitigation_controls=['rule_optimization', 'advanced_correlation', 'behavioral_analysis']
            ),
            'false_positive_injection': PillarAttackPattern(
                pillar=CyberdefensePillar.DETECTION_CORRELATION,
                attack_type='false_positive_injection',
                severity=LogSeverity.MEDIUM,
                description='False positive injection attack',
                tactic=AttackTactic.DEFENSE_EVASION,
                weight=0.15,
                indicators=['noise_injection', 'alert_fatigue', 'detection_dilution'],
                log_sources=['alert_logs', 'siem_logs', 'detection_logs'],
                mitigation_controls=['alert_tuning', 'noise_filtering', 'detection_optimization']
            ),
            'threat_hunting_evasion': PillarAttackPattern(
                pillar=CyberdefensePillar.DETECTION_CORRELATION,
                attack_type='threat_hunting_evasion',
                severity=LogSeverity.HIGH,
                description='Threat hunting evasion',
                tactic=AttackTactic.DEFENSE_EVASION,
                weight=0.15,
                indicators=['hunting_evasion', 'stealth_techniques', 'detection_avoidance'],
                log_sources=['hunting_logs', 'security_logs', 'detection_logs'],
                mitigation_controls=['advanced_hunting', 'behavioral_analysis', 'threat_intelligence']
            ),
            'log_manipulation': PillarAttackPattern(
                pillar=CyberdefensePillar.DETECTION_CORRELATION,
                attack_type='log_manipulation',
                severity=LogSeverity.CRITICAL,
                description='Security log manipulation',
                tactic=AttackTactic.DEFENSE_EVASION,
                weight=0.1,
                indicators=['log_deletion', 'log_modification', 'audit_trail_tampering'],
                log_sources=['audit_logs', 'security_logs', 'system_logs'],
                mitigation_controls=['immutable_logging', 'log_integrity', 'audit_monitoring']
            ),
            'detection_system_compromise': PillarAttackPattern(
                pillar=CyberdefensePillar.DETECTION_CORRELATION,
                attack_type='detection_system_compromise',
                severity=LogSeverity.CRITICAL,
                description='Detection system compromise',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.1,
                indicators=['siem_compromise', 'detection_bypass', 'security_tool_abuse'],
                log_sources=['siem_logs', 'security_logs', 'system_logs'],
                mitigation_controls=['system_hardening', 'access_controls', 'security_monitoring']
            ),
            'alert_suppression': PillarAttackPattern(
                pillar=CyberdefensePillar.DETECTION_CORRELATION,
                attack_type='alert_suppression',
                severity=LogSeverity.MEDIUM,
                description='Security alert suppression',
                tactic=AttackTactic.DEFENSE_EVASION,
                weight=0.05,
                indicators=['alert_blocking', 'notification_suppression', 'detection_silencing'],
                log_sources=['alert_logs', 'notification_logs', 'security_logs'],
                mitigation_controls=['alert_monitoring', 'notification_verification', 'detection_validation']
            )
        }
    
    def _get_normal_activities(self) -> List[str]:
        """Return list of normal detection & correlation activities."""
        return [
            "Security event correlation completed",
            "Threat hunting session conducted",
            "SIEM rule optimization",
            "Detection rule tuning",
            "Security alert analysis",
            "Threat intelligence integration",
            "Security monitoring review",
            "Detection system maintenance",
            "Correlation rule update",
            "Security event investigation",
            "Threat hunting training",
            "Detection metrics collection",
            "Security tool configuration",
            "Detection process improvement",
            "Security risk assessment",
            "Detection compliance audit",
            "Security awareness training",
            "Detection policy update",
            "Security governance review",
            "Detection certification"
        ]

