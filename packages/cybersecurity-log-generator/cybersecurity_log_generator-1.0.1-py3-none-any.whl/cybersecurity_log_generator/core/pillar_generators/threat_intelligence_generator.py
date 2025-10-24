"""
Threat Intelligence pillar generator.
"""

from typing import Dict, Any, List
from ..models import CyberdefensePillar, LogSeverity, AttackTactic, PillarAttackPattern
from .base_pillar_generator import BasePillarGenerator


class ThreatIntelligenceGenerator(BasePillarGenerator):
    """Generator for Threat Intelligence pillar."""
    
    def get_pillar(self) -> CyberdefensePillar:
        return CyberdefensePillar.THREAT_INTELLIGENCE
    
    def _setup_attack_patterns(self) -> Dict[str, PillarAttackPattern]:
        """Setup threat intelligence attack patterns."""
        return {
            'threat_intel_compromise': PillarAttackPattern(
                pillar=CyberdefensePillar.THREAT_INTELLIGENCE,
                attack_type='threat_intel_compromise',
                severity=LogSeverity.CRITICAL,
                description='Threat intelligence compromise',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.25,
                indicators=['intel_breach', 'threat_data_theft', 'intelligence_compromise'],
                log_sources=['intel_logs', 'threat_logs', 'security_logs'],
                mitigation_controls=['intel_protection', 'threat_data_security', 'intelligence_monitoring']
            ),
            'ioc_manipulation': PillarAttackPattern(
                pillar=CyberdefensePillar.THREAT_INTELLIGENCE,
                attack_type='ioc_manipulation',
                severity=LogSeverity.HIGH,
                description='Indicator of Compromise manipulation',
                tactic=AttackTactic.DEFENSE_EVASION,
                weight=0.2,
                indicators=['ioc_tampering', 'indicator_manipulation', 'threat_evasion'],
                log_sources=['ioc_logs', 'threat_logs', 'security_logs'],
                mitigation_controls=['ioc_validation', 'threat_monitoring', 'indicator_verification']
            ),
            'threat_feed_poisoning': PillarAttackPattern(
                pillar=CyberdefensePillar.THREAT_INTELLIGENCE,
                attack_type='threat_feed_poisoning',
                severity=LogSeverity.HIGH,
                description='Threat intelligence feed poisoning',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.15,
                indicators=['feed_manipulation', 'intel_poisoning', 'threat_data_corruption'],
                log_sources=['feed_logs', 'intel_logs', 'threat_logs'],
                mitigation_controls=['feed_validation', 'intel_verification', 'threat_monitoring']
            ),
            'intelligence_analysis_manipulation': PillarAttackPattern(
                pillar=CyberdefensePillar.THREAT_INTELLIGENCE,
                attack_type='intelligence_analysis_manipulation',
                severity=LogSeverity.HIGH,
                description='Intelligence analysis manipulation',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.15,
                indicators=['analysis_tampering', 'intel_manipulation', 'threat_analysis_corruption'],
                log_sources=['analysis_logs', 'intel_logs', 'threat_logs'],
                mitigation_controls=['analysis_validation', 'intel_verification', 'threat_analysis_monitoring']
            ),
            'threat_actor_impersonation': PillarAttackPattern(
                pillar=CyberdefensePillar.THREAT_INTELLIGENCE,
                attack_type='threat_actor_impersonation',
                severity=LogSeverity.MEDIUM,
                description='Threat actor impersonation',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.1,
                indicators=['actor_impersonation', 'threat_identity_theft', 'actor_manipulation'],
                log_sources=['actor_logs', 'threat_logs', 'intel_logs'],
                mitigation_controls=['actor_verification', 'threat_validation', 'intelligence_monitoring']
            ),
            'threat_intelligence_bypass': PillarAttackPattern(
                pillar=CyberdefensePillar.THREAT_INTELLIGENCE,
                attack_type='threat_intelligence_bypass',
                severity=LogSeverity.MEDIUM,
                description='Threat intelligence bypass',
                tactic=AttackTactic.DEFENSE_EVASION,
                weight=0.1,
                indicators=['intel_bypass', 'threat_evasion', 'intelligence_avoidance'],
                log_sources=['intel_logs', 'threat_logs', 'security_logs'],
                mitigation_controls=['intel_monitoring', 'threat_detection', 'intelligence_validation']
            ),
            'threat_intelligence_evasion': PillarAttackPattern(
                pillar=CyberdefensePillar.THREAT_INTELLIGENCE,
                attack_type='threat_intelligence_evasion',
                severity=LogSeverity.LOW,
                description='Threat intelligence evasion',
                tactic=AttackTactic.DEFENSE_EVASION,
                weight=0.05,
                indicators=['intel_evasion', 'threat_avoidance', 'intelligence_bypass'],
                log_sources=['intel_logs', 'threat_logs', 'security_logs'],
                mitigation_controls=['intel_monitoring', 'threat_detection', 'intelligence_validation']
            )
        }
    
    def _get_normal_activities(self) -> List[str]:
        """Return list of normal threat intelligence activities."""
        return [
            "Threat intelligence collection",
            "Threat analysis completion",
            "IOC validation and processing",
            "Threat intelligence sharing",
            "Threat intelligence training",
            "Threat intelligence policy update",
            "Threat intelligence audit",
            "Threat intelligence metrics collection",
            "Threat intelligence tool configuration",
            "Threat intelligence process improvement",
            "Threat intelligence risk assessment",
            "Threat intelligence compliance check",
            "Threat intelligence awareness training",
            "Threat intelligence governance review",
            "Threat intelligence certification",
            "Threat intelligence monitoring",
            "Threat intelligence communication",
            "Threat intelligence incident response",
            "Threat intelligence continuous improvement",
            "Threat intelligence program management"
        ]

