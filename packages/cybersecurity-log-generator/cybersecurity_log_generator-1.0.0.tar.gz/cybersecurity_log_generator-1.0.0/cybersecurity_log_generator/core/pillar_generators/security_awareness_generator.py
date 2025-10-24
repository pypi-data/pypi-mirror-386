"""
Security Awareness pillar generator.
"""

from typing import Dict, Any, List
from ..models import CyberdefensePillar, LogSeverity, AttackTactic, PillarAttackPattern
from .base_pillar_generator import BasePillarGenerator


class SecurityAwarenessGenerator(BasePillarGenerator):
    """Generator for Security Awareness pillar."""
    
    def get_pillar(self) -> CyberdefensePillar:
        return CyberdefensePillar.SECURITY_AWARENESS
    
    def _setup_attack_patterns(self) -> Dict[str, PillarAttackPattern]:
        """Setup security awareness attack patterns."""
        return {
            'phishing_attack': PillarAttackPattern(
                pillar=CyberdefensePillar.SECURITY_AWARENESS,
                attack_type='phishing_attack',
                severity=LogSeverity.HIGH,
                description='Phishing attack targeting users',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.3,
                indicators=['phishing_emails', 'malicious_links', 'credential_harvesting'],
                log_sources=['email_logs', 'security_logs', 'user_interaction_logs'],
                mitigation_controls=['email_security', 'user_training', 'phishing_protection']
            ),
            'social_engineering': PillarAttackPattern(
                pillar=CyberdefensePillar.SECURITY_AWARENESS,
                attack_type='social_engineering',
                severity=LogSeverity.HIGH,
                description='Social engineering attack',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.25,
                indicators=['psychological_manipulation', 'information_gathering', 'trust_exploitation'],
                log_sources=['user_interaction_logs', 'communication_logs', 'security_logs'],
                mitigation_controls=['user_education', 'social_engineering_training', 'awareness_programs']
            ),
            'pretexting_attack': PillarAttackPattern(
                pillar=CyberdefensePillar.SECURITY_AWARENESS,
                attack_type='pretexting_attack',
                severity=LogSeverity.MEDIUM,
                description='Pretexting attack',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.15,
                indicators=['false_identity', 'deceptive_scenarios', 'information_extraction'],
                log_sources=['communication_logs', 'user_interaction_logs', 'security_logs'],
                mitigation_controls=['identity_verification', 'user_training', 'communication_security']
            ),
            'baiting_attack': PillarAttackPattern(
                pillar=CyberdefensePillar.SECURITY_AWARENESS,
                attack_type='baiting_attack',
                severity=LogSeverity.MEDIUM,
                description='Baiting attack',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.1,
                indicators=['malicious_attachments', 'infected_devices', 'curiosity_exploitation'],
                log_sources=['email_logs', 'device_logs', 'security_logs'],
                mitigation_controls=['email_security', 'device_protection', 'user_education']
            ),
            'quid_pro_quo': PillarAttackPattern(
                pillar=CyberdefensePillar.SECURITY_AWARENESS,
                attack_type='quid_pro_quo',
                severity=LogSeverity.MEDIUM,
                description='Quid pro quo attack',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.1,
                indicators=['false_services', 'information_exchange', 'trust_exploitation'],
                log_sources=['communication_logs', 'user_interaction_logs', 'security_logs'],
                mitigation_controls=['service_verification', 'user_training', 'communication_security']
            ),
            'tailgating_attack': PillarAttackPattern(
                pillar=CyberdefensePillar.SECURITY_AWARENESS,
                attack_type='tailgating_attack',
                severity=LogSeverity.MEDIUM,
                description='Tailgating physical attack',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.05,
                indicators=['unauthorized_physical_access', 'piggybacking', 'physical_social_engineering'],
                log_sources=['physical_logs', 'access_logs', 'security_logs'],
                mitigation_controls=['physical_controls', 'access_management', 'physical_training']
            ),
            'awareness_bypass': PillarAttackPattern(
                pillar=CyberdefensePillar.SECURITY_AWARENESS,
                attack_type='awareness_bypass',
                severity=LogSeverity.LOW,
                description='Security awareness bypass',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.05,
                indicators=['training_evasion', 'awareness_bypass', 'security_ignorance'],
                log_sources=['training_logs', 'awareness_logs', 'security_logs'],
                mitigation_controls=['mandatory_training', 'awareness_monitoring', 'training_enforcement']
            )
        }
    
    def _get_normal_activities(self) -> List[str]:
        """Return list of normal security awareness activities."""
        return [
            "Security awareness training completion",
            "Phishing simulation exercise",
            "Security awareness assessment",
            "Security awareness campaign",
            "Security awareness metrics collection",
            "Security awareness tool configuration",
            "Security awareness process improvement",
            "Security awareness risk assessment",
            "Security awareness compliance check",
            "Security awareness governance review",
            "Security awareness certification",
            "Security awareness monitoring",
            "Security awareness communication",
            "Security awareness incident response",
            "Security awareness policy update",
            "Security awareness training delivery",
            "Security awareness evaluation",
            "Security awareness feedback collection",
            "Security awareness program management",
            "Security awareness continuous improvement"
        ]

