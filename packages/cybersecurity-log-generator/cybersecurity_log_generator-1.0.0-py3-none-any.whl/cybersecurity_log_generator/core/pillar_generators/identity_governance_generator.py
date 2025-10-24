"""
Identity Governance pillar generator.
"""

from typing import Dict, Any, List
from ..models import CyberdefensePillar, LogSeverity, AttackTactic, PillarAttackPattern
from .base_pillar_generator import BasePillarGenerator


class IdentityGovernanceGenerator(BasePillarGenerator):
    """Generator for Identity Governance pillar."""
    
    def get_pillar(self) -> CyberdefensePillar:
        return CyberdefensePillar.IDENTITY_GOVERNANCE
    
    def _setup_attack_patterns(self) -> Dict[str, PillarAttackPattern]:
        """Setup identity governance attack patterns."""
        return {
            'identity_theft': PillarAttackPattern(
                pillar=CyberdefensePillar.IDENTITY_GOVERNANCE,
                attack_type='identity_theft',
                severity=LogSeverity.CRITICAL,
                description='Identity theft attack',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.25,
                indicators=['identity_compromise', 'personal_data_theft', 'identity_abuse'],
                log_sources=['identity_logs', 'personal_data_logs', 'security_logs'],
                mitigation_controls=['identity_verification', 'personal_data_protection', 'identity_monitoring']
            ),
            'privilege_creep': PillarAttackPattern(
                pillar=CyberdefensePillar.IDENTITY_GOVERNANCE,
                attack_type='privilege_creep',
                severity=LogSeverity.HIGH,
                description='Unauthorized privilege accumulation',
                tactic=AttackTactic.PRIVILEGE_ESCALATION,
                weight=0.2,
                indicators=['privilege_accumulation', 'access_creep', 'permission_abuse'],
                log_sources=['privilege_logs', 'access_logs', 'governance_logs'],
                mitigation_controls=['privilege_review', 'access_controls', 'privilege_monitoring']
            ),
            'orphaned_account_abuse': PillarAttackPattern(
                pillar=CyberdefensePillar.IDENTITY_GOVERNANCE,
                attack_type='orphaned_account_abuse',
                severity=LogSeverity.HIGH,
                description='Orphaned account abuse',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.15,
                indicators=['orphaned_account_usage', 'abandoned_account_abuse', 'zombie_accounts'],
                log_sources=['account_logs', 'identity_logs', 'governance_logs'],
                mitigation_controls=['account_cleanup', 'orphaned_account_monitoring', 'account_governance']
            ),
            'identity_spoofing': PillarAttackPattern(
                pillar=CyberdefensePillar.IDENTITY_GOVERNANCE,
                attack_type='identity_spoofing',
                severity=LogSeverity.HIGH,
                description='Identity spoofing attack',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.15,
                indicators=['identity_impersonation', 'spoofing_attempts', 'identity_fraud'],
                log_sources=['identity_logs', 'authentication_logs', 'security_logs'],
                mitigation_controls=['identity_verification', 'biometric_auth', 'identity_monitoring']
            ),
            'access_certification_bypass': PillarAttackPattern(
                pillar=CyberdefensePillar.IDENTITY_GOVERNANCE,
                attack_type='access_certification_bypass',
                severity=LogSeverity.MEDIUM,
                description='Access certification bypass',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.1,
                indicators=['certification_bypass', 'access_review_evasion', 'governance_bypass'],
                log_sources=['certification_logs', 'access_logs', 'governance_logs'],
                mitigation_controls=['certification_enforcement', 'access_review', 'governance_monitoring']
            ),
            'identity_lifecycle_abuse': PillarAttackPattern(
                pillar=CyberdefensePillar.IDENTITY_GOVERNANCE,
                attack_type='identity_lifecycle_abuse',
                severity=LogSeverity.MEDIUM,
                description='Identity lifecycle abuse',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.1,
                indicators=['lifecycle_manipulation', 'identity_abuse', 'lifecycle_violations'],
                log_sources=['lifecycle_logs', 'identity_logs', 'governance_logs'],
                mitigation_controls=['lifecycle_monitoring', 'identity_controls', 'lifecycle_validation']
            ),
            'identity_governance_evasion': PillarAttackPattern(
                pillar=CyberdefensePillar.IDENTITY_GOVERNANCE,
                attack_type='identity_governance_evasion',
                severity=LogSeverity.MEDIUM,
                description='Identity governance evasion',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.05,
                indicators=['governance_evasion', 'identity_bypass', 'governance_manipulation'],
                log_sources=['governance_logs', 'identity_logs', 'compliance_logs'],
                mitigation_controls=['governance_enforcement', 'identity_monitoring', 'governance_validation']
            )
        }
    
    def _get_normal_activities(self) -> List[str]:
        """Return list of normal identity governance activities."""
        return [
            "Identity access review",
            "Privilege certification",
            "Account lifecycle management",
            "Identity governance audit",
            "Access certification process",
            "Identity policy update",
            "Identity governance training",
            "Identity metrics collection",
            "Identity governance monitoring",
            "Identity incident response",
            "Identity governance tool configuration",
            "Identity governance process improvement",
            "Identity governance risk assessment",
            "Identity governance compliance check",
            "Identity governance awareness training",
            "Identity governance policy update",
            "Identity governance governance review",
            "Identity governance certification",
            "Identity governance incident response",
            "Identity governance monitoring"
        ]

