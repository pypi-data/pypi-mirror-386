"""
Audit & Compliance pillar generator.
"""

from typing import Dict, Any, List
from ..models import CyberdefensePillar, LogSeverity, AttackTactic, PillarAttackPattern
from .base_pillar_generator import BasePillarGenerator


class AuditComplianceGenerator(BasePillarGenerator):
    """Generator for Audit & Compliance pillar."""
    
    def get_pillar(self) -> CyberdefensePillar:
        return CyberdefensePillar.AUDIT_COMPLIANCE
    
    def _setup_attack_patterns(self) -> Dict[str, PillarAttackPattern]:
        """Setup audit & compliance attack patterns."""
        return {
            'compliance_violation': PillarAttackPattern(
                pillar=CyberdefensePillar.AUDIT_COMPLIANCE,
                attack_type='compliance_violation',
                severity=LogSeverity.HIGH,
                description='Regulatory compliance violation detected',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.25,
                indicators=['policy_violations', 'regulatory_breaches', 'compliance_failures'],
                log_sources=['audit_logs', 'compliance_logs', 'policy_logs'],
                mitigation_controls=['policy_enforcement', 'compliance_monitoring', 'regulatory_training']
            ),
            'audit_trail_tampering': PillarAttackPattern(
                pillar=CyberdefensePillar.AUDIT_COMPLIANCE,
                attack_type='audit_trail_tampering',
                severity=LogSeverity.CRITICAL,
                description='Audit trail tampering detected',
                tactic=AttackTactic.IMPACT,
                weight=0.2,
                indicators=['log_deletion', 'audit_trail_modification', 'evidence_tampering'],
                log_sources=['audit_logs', 'system_logs', 'security_logs'],
                mitigation_controls=['immutable_logging', 'log_integrity', 'audit_monitoring']
            ),
            'data_retention_violation': PillarAttackPattern(
                pillar=CyberdefensePillar.AUDIT_COMPLIANCE,
                attack_type='data_retention_violation',
                severity=LogSeverity.MEDIUM,
                description='Data retention policy violation',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.15,
                indicators=['data_retention_breaches', 'policy_violations', 'data_governance_failures'],
                log_sources=['data_governance_logs', 'retention_logs', 'policy_logs'],
                mitigation_controls=['data_retention_policies', 'automated_cleanup', 'governance_monitoring']
            ),
            'access_control_violation': PillarAttackPattern(
                pillar=CyberdefensePillar.AUDIT_COMPLIANCE,
                attack_type='access_control_violation',
                severity=LogSeverity.HIGH,
                description='Access control compliance violation',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.15,
                indicators=['unauthorized_access', 'access_policy_violations', 'privilege_abuse'],
                log_sources=['access_logs', 'authorization_logs', 'compliance_logs'],
                mitigation_controls=['access_controls', 'privilege_monitoring', 'compliance_auditing']
            ),
            'data_privacy_breach': PillarAttackPattern(
                pillar=CyberdefensePillar.AUDIT_COMPLIANCE,
                attack_type='data_privacy_breach',
                severity=LogSeverity.CRITICAL,
                description='Data privacy regulation breach',
                tactic=AttackTactic.COLLECTION,
                weight=0.1,
                indicators=['gdpr_violations', 'data_exposure', 'privacy_breaches'],
                log_sources=['privacy_logs', 'data_access_logs', 'compliance_logs'],
                mitigation_controls=['privacy_controls', 'data_protection', 'privacy_monitoring']
            ),
            'regulatory_reporting_failure': PillarAttackPattern(
                pillar=CyberdefensePillar.AUDIT_COMPLIANCE,
                attack_type='regulatory_reporting_failure',
                severity=LogSeverity.HIGH,
                description='Regulatory reporting failure',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.1,
                indicators=['reporting_deadlines_missed', 'incomplete_reports', 'regulatory_failures'],
                log_sources=['reporting_logs', 'compliance_logs', 'regulatory_logs'],
                mitigation_controls=['automated_reporting', 'compliance_monitoring', 'regulatory_training']
            ),
            'internal_control_failure': PillarAttackPattern(
                pillar=CyberdefensePillar.AUDIT_COMPLIANCE,
                attack_type='internal_control_failure',
                severity=LogSeverity.MEDIUM,
                description='Internal control failure detected',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.05,
                indicators=['control_weaknesses', 'process_failures', 'control_breaches'],
                log_sources=['control_logs', 'audit_logs', 'compliance_logs'],
                mitigation_controls=['control_improvements', 'process_monitoring', 'control_testing']
            )
        }
    
    def _get_normal_activities(self) -> List[str]:
        """Return list of normal audit & compliance activities."""
        return [
            "Compliance audit completed",
            "Regulatory assessment performed",
            "Audit trail review",
            "Compliance monitoring check",
            "Policy compliance verification",
            "Regulatory reporting submitted",
            "Internal audit conducted",
            "Compliance training completed",
            "Audit findings documented",
            "Compliance metrics collected",
            "Regulatory update review",
            "Audit plan execution",
            "Compliance gap analysis",
            "Audit evidence collection",
            "Compliance dashboard review",
            "Regulatory change assessment",
            "Audit report generation",
            "Compliance certification",
            "Audit follow-up actions",
            "Compliance risk assessment"
        ]

