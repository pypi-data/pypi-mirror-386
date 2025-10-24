"""
Due Diligence pillar generator.
"""

from typing import Dict, Any, List
from ..models import CyberdefensePillar, LogSeverity, AttackTactic, PillarAttackPattern
from .base_pillar_generator import BasePillarGenerator


class DueDiligenceGenerator(BasePillarGenerator):
    """Generator for Due Diligence pillar."""
    
    def get_pillar(self) -> CyberdefensePillar:
        return CyberdefensePillar.DUE_DILIGENCE
    
    def _setup_attack_patterns(self) -> Dict[str, PillarAttackPattern]:
        """Setup due diligence attack patterns."""
        return {
            'vendor_assessment_fraud': PillarAttackPattern(
                pillar=CyberdefensePillar.DUE_DILIGENCE,
                attack_type='vendor_assessment_fraud',
                severity=LogSeverity.HIGH,
                description='Vendor assessment fraud detected',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.25,
                indicators=['fraudulent_assessments', 'vendor_deception', 'assessment_manipulation'],
                log_sources=['assessment_logs', 'vendor_logs', 'compliance_logs'],
                mitigation_controls=['independent_assessments', 'vendor_verification', 'assessment_monitoring']
            ),
            'risk_assessment_manipulation': PillarAttackPattern(
                pillar=CyberdefensePillar.DUE_DILIGENCE,
                attack_type='risk_assessment_manipulation',
                severity=LogSeverity.HIGH,
                description='Risk assessment manipulation',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.2,
                indicators=['risk_data_manipulation', 'assessment_bias', 'risk_underestimation'],
                log_sources=['risk_logs', 'assessment_logs', 'compliance_logs'],
                mitigation_controls=['independent_risk_assessment', 'risk_validation', 'assessment_review']
            ),
            'compliance_certification_fraud': PillarAttackPattern(
                pillar=CyberdefensePillar.DUE_DILIGENCE,
                attack_type='compliance_certification_fraud',
                severity=LogSeverity.CRITICAL,
                description='Compliance certification fraud',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.15,
                indicators=['fraudulent_certifications', 'certification_bypass', 'compliance_deception'],
                log_sources=['certification_logs', 'compliance_logs', 'audit_logs'],
                mitigation_controls=['certification_verification', 'independent_audits', 'certification_monitoring']
            ),
            'due_diligence_bypass': PillarAttackPattern(
                pillar=CyberdefensePillar.DUE_DILIGENCE,
                attack_type='due_diligence_bypass',
                severity=LogSeverity.HIGH,
                description='Due diligence process bypass',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.15,
                indicators=['process_bypass', 'diligence_evasion', 'assessment_avoidance'],
                log_sources=['diligence_logs', 'process_logs', 'compliance_logs'],
                mitigation_controls=['process_enforcement', 'diligence_monitoring', 'assessment_validation']
            ),
            'vendor_relationship_abuse': PillarAttackPattern(
                pillar=CyberdefensePillar.DUE_DILIGENCE,
                attack_type='vendor_relationship_abuse',
                severity=LogSeverity.MEDIUM,
                description='Vendor relationship abuse',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.1,
                indicators=['relationship_manipulation', 'vendor_abuse', 'relationship_exploitation'],
                log_sources=['relationship_logs', 'vendor_logs', 'compliance_logs'],
                mitigation_controls=['relationship_monitoring', 'vendor_controls', 'relationship_validation']
            ),
            'assessment_data_tampering': PillarAttackPattern(
                pillar=CyberdefensePillar.DUE_DILIGENCE,
                attack_type='assessment_data_tampering',
                severity=LogSeverity.HIGH,
                description='Assessment data tampering',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.1,
                indicators=['data_manipulation', 'assessment_tampering', 'data_integrity_violations'],
                log_sources=['assessment_logs', 'data_logs', 'integrity_logs'],
                mitigation_controls=['data_integrity', 'assessment_validation', 'data_monitoring']
            ),
            'due_diligence_evasion': PillarAttackPattern(
                pillar=CyberdefensePillar.DUE_DILIGENCE,
                attack_type='due_diligence_evasion',
                severity=LogSeverity.MEDIUM,
                description='Due diligence evasion',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.05,
                indicators=['diligence_avoidance', 'process_evasion', 'assessment_bypass'],
                log_sources=['diligence_logs', 'process_logs', 'compliance_logs'],
                mitigation_controls=['process_enforcement', 'diligence_monitoring', 'assessment_validation']
            )
        }
    
    def _get_normal_activities(self) -> List[str]:
        """Return list of normal due diligence activities."""
        return [
            "Vendor due diligence assessment",
            "Risk assessment completion",
            "Compliance certification review",
            "Due diligence process execution",
            "Vendor relationship evaluation",
            "Assessment data collection",
            "Due diligence training",
            "Assessment methodology update",
            "Due diligence audit",
            "Assessment metrics collection",
            "Due diligence tool configuration",
            "Due diligence process improvement",
            "Due diligence risk assessment",
            "Due diligence compliance check",
            "Due diligence awareness training",
            "Due diligence policy update",
            "Due diligence governance review",
            "Due diligence incident response",
            "Due diligence certification",
            "Due diligence monitoring"
        ]

