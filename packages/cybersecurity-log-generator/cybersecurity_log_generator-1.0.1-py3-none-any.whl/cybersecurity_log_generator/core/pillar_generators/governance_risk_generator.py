"""
Governance, Risk & Strategy pillar generator.
"""

from typing import Dict, Any, List
from ..models import CyberdefensePillar, LogSeverity, AttackTactic, PillarAttackPattern
from .base_pillar_generator import BasePillarGenerator


class GovernanceRiskGenerator(BasePillarGenerator):
    """Generator for Governance, Risk & Strategy pillar."""
    
    def get_pillar(self) -> CyberdefensePillar:
        return CyberdefensePillar.GOVERNANCE_RISK
    
    def _setup_attack_patterns(self) -> Dict[str, PillarAttackPattern]:
        """Setup governance, risk & strategy attack patterns."""
        return {
            'governance_bypass': PillarAttackPattern(
                pillar=CyberdefensePillar.GOVERNANCE_RISK,
                attack_type='governance_bypass',
                severity=LogSeverity.HIGH,
                description='Governance framework bypass',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.25,
                indicators=['governance_evasion', 'policy_bypass', 'framework_manipulation'],
                log_sources=['governance_logs', 'policy_logs', 'compliance_logs'],
                mitigation_controls=['governance_enforcement', 'policy_monitoring', 'framework_validation']
            ),
            'risk_assessment_manipulation': PillarAttackPattern(
                pillar=CyberdefensePillar.GOVERNANCE_RISK,
                attack_type='risk_assessment_manipulation',
                severity=LogSeverity.HIGH,
                description='Risk assessment manipulation',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.2,
                indicators=['risk_data_manipulation', 'assessment_bias', 'risk_underestimation'],
                log_sources=['risk_logs', 'assessment_logs', 'governance_logs'],
                mitigation_controls=['independent_risk_assessment', 'risk_validation', 'assessment_review']
            ),
            'strategic_plan_compromise': PillarAttackPattern(
                pillar=CyberdefensePillar.GOVERNANCE_RISK,
                attack_type='strategic_plan_compromise',
                severity=LogSeverity.CRITICAL,
                description='Strategic plan compromise',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.15,
                indicators=['plan_tampering', 'strategy_manipulation', 'strategic_compromise'],
                log_sources=['strategy_logs', 'plan_logs', 'governance_logs'],
                mitigation_controls=['plan_protection', 'strategy_validation', 'plan_monitoring']
            ),
            'compliance_framework_abuse': PillarAttackPattern(
                pillar=CyberdefensePillar.GOVERNANCE_RISK,
                attack_type='compliance_framework_abuse',
                severity=LogSeverity.HIGH,
                description='Compliance framework abuse',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.15,
                indicators=['framework_abuse', 'compliance_manipulation', 'framework_evasion'],
                log_sources=['framework_logs', 'compliance_logs', 'governance_logs'],
                mitigation_controls=['framework_monitoring', 'compliance_validation', 'framework_controls']
            ),
            'risk_tolerance_violation': PillarAttackPattern(
                pillar=CyberdefensePillar.GOVERNANCE_RISK,
                attack_type='risk_tolerance_violation',
                severity=LogSeverity.MEDIUM,
                description='Risk tolerance violation',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.1,
                indicators=['tolerance_breach', 'risk_violation', 'tolerance_abuse'],
                log_sources=['tolerance_logs', 'risk_logs', 'governance_logs'],
                mitigation_controls=['tolerance_monitoring', 'risk_controls', 'tolerance_validation']
            ),
            'governance_data_tampering': PillarAttackPattern(
                pillar=CyberdefensePillar.GOVERNANCE_RISK,
                attack_type='governance_data_tampering',
                severity=LogSeverity.HIGH,
                description='Governance data tampering',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.1,
                indicators=['data_manipulation', 'governance_tampering', 'data_integrity_violations'],
                log_sources=['governance_logs', 'data_logs', 'integrity_logs'],
                mitigation_controls=['data_integrity', 'governance_validation', 'data_monitoring']
            ),
            'strategic_decision_manipulation': PillarAttackPattern(
                pillar=CyberdefensePillar.GOVERNANCE_RISK,
                attack_type='strategic_decision_manipulation',
                severity=LogSeverity.CRITICAL,
                description='Strategic decision manipulation',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.05,
                indicators=['decision_manipulation', 'strategic_influence', 'decision_tampering'],
                log_sources=['decision_logs', 'strategy_logs', 'governance_logs'],
                mitigation_controls=['decision_validation', 'strategic_monitoring', 'decision_controls']
            )
        }
    
    def _get_normal_activities(self) -> List[str]:
        """Return list of normal governance, risk & strategy activities."""
        return [
            "Governance framework review",
            "Risk assessment completion",
            "Strategic plan update",
            "Compliance framework audit",
            "Risk tolerance evaluation",
            "Governance data collection",
            "Strategic decision making",
            "Governance training",
            "Risk metrics collection",
            "Strategic monitoring",
            "Governance incident response",
            "Risk assessment methodology update",
            "Strategic planning session",
            "Governance compliance check",
            "Risk awareness training",
            "Strategic policy update",
            "Governance governance review",
            "Risk certification",
            "Strategic risk assessment",
            "Governance monitoring"
        ]

