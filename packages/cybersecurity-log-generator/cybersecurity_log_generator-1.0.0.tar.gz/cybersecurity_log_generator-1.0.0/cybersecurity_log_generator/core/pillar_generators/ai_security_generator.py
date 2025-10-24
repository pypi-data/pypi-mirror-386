"""
AI Security pillar generator.
"""

from typing import Dict, Any, List
from ..models import CyberdefensePillar, LogSeverity, AttackTactic, PillarAttackPattern
from .base_pillar_generator import BasePillarGenerator


class AISecurityGenerator(BasePillarGenerator):
    """Generator for AI Security pillar."""
    
    def get_pillar(self) -> CyberdefensePillar:
        return CyberdefensePillar.AI_SECURITY
    
    def _setup_attack_patterns(self) -> Dict[str, PillarAttackPattern]:
        """Setup AI security attack patterns."""
        return {
            'adversarial_attack': PillarAttackPattern(
                pillar=CyberdefensePillar.AI_SECURITY,
                attack_type='adversarial_attack',
                severity=LogSeverity.HIGH,
                description='Adversarial attack on AI model',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.25,
                indicators=['model_manipulation', 'adversarial_examples', 'ai_bypass'],
                log_sources=['ai_logs', 'model_logs', 'security_logs'],
                mitigation_controls=['adversarial_training', 'model_robustness', 'ai_monitoring']
            ),
            'model_poisoning': PillarAttackPattern(
                pillar=CyberdefensePillar.AI_SECURITY,
                attack_type='model_poisoning',
                severity=LogSeverity.CRITICAL,
                description='AI model poisoning attack',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.2,
                indicators=['training_data_manipulation', 'model_corruption', 'ai_compromise'],
                log_sources=['training_logs', 'model_logs', 'security_logs'],
                mitigation_controls=['data_validation', 'model_verification', 'training_monitoring']
            ),
            'data_poisoning': PillarAttackPattern(
                pillar=CyberdefensePillar.AI_SECURITY,
                attack_type='data_poisoning',
                severity=LogSeverity.HIGH,
                description='Training data poisoning',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.15,
                indicators=['malicious_training_data', 'data_manipulation', 'training_corruption'],
                log_sources=['training_logs', 'data_logs', 'security_logs'],
                mitigation_controls=['data_quality_checks', 'training_validation', 'data_monitoring']
            ),
            'model_extraction': PillarAttackPattern(
                pillar=CyberdefensePillar.AI_SECURITY,
                attack_type='model_extraction',
                severity=LogSeverity.HIGH,
                description='AI model extraction attack',
                tactic=AttackTactic.COLLECTION,
                weight=0.15,
                indicators=['model_theft', 'intellectual_property_theft', 'model_replication'],
                log_sources=['model_logs', 'api_logs', 'security_logs'],
                mitigation_controls=['model_protection', 'api_security', 'access_controls']
            ),
            'inference_attack': PillarAttackPattern(
                pillar=CyberdefensePillar.AI_SECURITY,
                attack_type='inference_attack',
                severity=LogSeverity.MEDIUM,
                description='AI inference attack',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.1,
                indicators=['inference_manipulation', 'model_abuse', 'ai_exploitation'],
                log_sources=['inference_logs', 'ai_logs', 'security_logs'],
                mitigation_controls=['inference_monitoring', 'model_controls', 'ai_security']
            ),
            'ai_bias_exploitation': PillarAttackPattern(
                pillar=CyberdefensePillar.AI_SECURITY,
                attack_type='ai_bias_exploitation',
                severity=LogSeverity.MEDIUM,
                description='AI bias exploitation',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.1,
                indicators=['bias_manipulation', 'unfair_ai_usage', 'discriminatory_ai'],
                log_sources=['ai_logs', 'bias_logs', 'security_logs'],
                mitigation_controls=['bias_detection', 'fair_ai_practices', 'ai_governance']
            ),
            'ai_supply_chain_attack': PillarAttackPattern(
                pillar=CyberdefensePillar.AI_SECURITY,
                attack_type='ai_supply_chain_attack',
                severity=LogSeverity.CRITICAL,
                description='AI supply chain attack',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.05,
                indicators=['ai_library_compromise', 'model_tampering', 'ai_supply_chain_breach'],
                log_sources=['supply_chain_logs', 'ai_logs', 'security_logs'],
                mitigation_controls=['supply_chain_security', 'ai_verification', 'library_monitoring']
            )
        }
    
    def _get_normal_activities(self) -> List[str]:
        """Return list of normal AI security activities."""
        return [
            "AI model security assessment",
            "Adversarial robustness testing",
            "AI bias detection and mitigation",
            "AI model monitoring",
            "AI security training",
            "AI incident response",
            "AI security policy update",
            "AI compliance audit",
            "AI security metrics collection",
            "AI tool configuration",
            "AI security process improvement",
            "AI security risk assessment",
            "AI security compliance check",
            "AI security awareness training",
            "AI security governance review",
            "AI security certification",
            "AI model validation",
            "AI security architecture review",
            "AI threat intelligence integration",
            "AI security monitoring"
        ]

