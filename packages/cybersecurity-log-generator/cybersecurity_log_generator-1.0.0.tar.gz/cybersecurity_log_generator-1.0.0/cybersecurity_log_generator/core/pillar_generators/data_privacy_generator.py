"""
Data Privacy pillar generator.
"""

from typing import Dict, Any, List
from ..models import CyberdefensePillar, LogSeverity, AttackTactic, PillarAttackPattern
from .base_pillar_generator import BasePillarGenerator


class DataPrivacyGenerator(BasePillarGenerator):
    """Generator for Data Privacy pillar."""
    
    def get_pillar(self) -> CyberdefensePillar:
        return CyberdefensePillar.DATA_PRIVACY
    
    def _setup_attack_patterns(self) -> Dict[str, PillarAttackPattern]:
        """Setup data privacy attack patterns."""
        return {
            'gdpr_violation': PillarAttackPattern(
                pillar=CyberdefensePillar.DATA_PRIVACY,
                attack_type='gdpr_violation',
                severity=LogSeverity.CRITICAL,
                description='GDPR compliance violation detected',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.25,
                indicators=['data_processing_violations', 'consent_breaches', 'data_subject_rights_violations'],
                log_sources=['privacy_logs', 'compliance_logs', 'data_processing_logs'],
                mitigation_controls=['privacy_by_design', 'consent_management', 'data_protection_impact_assessment']
            ),
            'data_breach': PillarAttackPattern(
                pillar=CyberdefensePillar.DATA_PRIVACY,
                attack_type='data_breach',
                severity=LogSeverity.CRITICAL,
                description='Personal data breach detected',
                tactic=AttackTactic.COLLECTION,
                weight=0.2,
                indicators=['unauthorized_data_access', 'data_exposure', 'breach_notification'],
                log_sources=['breach_logs', 'data_access_logs', 'security_logs'],
                mitigation_controls=['data_encryption', 'access_controls', 'breach_response_plan']
            ),
            'consent_manipulation': PillarAttackPattern(
                pillar=CyberdefensePillar.DATA_PRIVACY,
                attack_type='consent_manipulation',
                severity=LogSeverity.HIGH,
                description='Consent manipulation attack',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.15,
                indicators=['consent_fraud', 'consent_bypass', 'unauthorized_consent'],
                log_sources=['consent_logs', 'privacy_logs', 'user_interaction_logs'],
                mitigation_controls=['consent_verification', 'consent_monitoring', 'user_education']
            ),
            'data_subject_rights_abuse': PillarAttackPattern(
                pillar=CyberdefensePillar.DATA_PRIVACY,
                attack_type='data_subject_rights_abuse',
                severity=LogSeverity.MEDIUM,
                description='Data subject rights abuse',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.15,
                indicators=['right_to_erasure_abuse', 'data_portability_abuse', 'access_request_abuse'],
                log_sources=['rights_logs', 'privacy_logs', 'data_subject_logs'],
                mitigation_controls=['rights_verification', 'identity_verification', 'process_automation']
            ),
            'cross_border_data_transfer_violation': PillarAttackPattern(
                pillar=CyberdefensePillar.DATA_PRIVACY,
                attack_type='cross_border_data_transfer_violation',
                severity=LogSeverity.HIGH,
                description='Cross-border data transfer violation',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.1,
                indicators=['unauthorized_transfers', 'inadequate_safeguards', 'transfer_violations'],
                log_sources=['transfer_logs', 'privacy_logs', 'compliance_logs'],
                mitigation_controls=['transfer_agreements', 'adequacy_decisions', 'safeguards']
            ),
            'privacy_policy_violation': PillarAttackPattern(
                pillar=CyberdefensePillar.DATA_PRIVACY,
                attack_type='privacy_policy_violation',
                severity=LogSeverity.MEDIUM,
                description='Privacy policy violation',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.1,
                indicators=['policy_breaches', 'unauthorized_processing', 'policy_violations'],
                log_sources=['policy_logs', 'privacy_logs', 'compliance_logs'],
                mitigation_controls=['policy_enforcement', 'privacy_training', 'compliance_monitoring']
            ),
            'data_minimization_violation': PillarAttackPattern(
                pillar=CyberdefensePillar.DATA_PRIVACY,
                attack_type='data_minimization_violation',
                severity=LogSeverity.MEDIUM,
                description='Data minimization principle violation',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.05,
                indicators=['excessive_data_collection', 'unnecessary_processing', 'data_hoarding'],
                log_sources=['collection_logs', 'privacy_logs', 'processing_logs'],
                mitigation_controls=['data_minimization', 'purpose_limitation', 'retention_policies']
            )
        }
    
    def _get_normal_activities(self) -> List[str]:
        """Return list of normal data privacy activities."""
        return [
            "Privacy impact assessment completed",
            "Data protection impact assessment",
            "Privacy policy review",
            "Consent management system update",
            "Data subject rights request processed",
            "Privacy training completed",
            "Privacy audit conducted",
            "Data minimization review",
            "Privacy by design implementation",
            "Cross-border transfer assessment",
            "Privacy incident response",
            "Privacy metrics collection",
            "Privacy tool configuration",
            "Privacy process improvement",
            "Privacy risk assessment",
            "Privacy compliance monitoring",
            "Privacy awareness training",
            "Privacy policy update",
            "Privacy governance review",
            "Privacy certification"
        ]

