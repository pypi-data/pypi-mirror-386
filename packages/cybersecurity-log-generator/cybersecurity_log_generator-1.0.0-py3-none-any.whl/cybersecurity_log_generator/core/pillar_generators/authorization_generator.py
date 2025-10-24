"""
Authorization pillar generator.
"""

from typing import Dict, Any, List
from ..models import CyberdefensePillar, LogSeverity, AttackTactic, PillarAttackPattern
from .base_pillar_generator import BasePillarGenerator


class AuthorizationGenerator(BasePillarGenerator):
    """Generator for Authorization pillar."""
    
    def get_pillar(self) -> CyberdefensePillar:
        return CyberdefensePillar.AUTHORIZATION
    
    def _setup_attack_patterns(self) -> Dict[str, PillarAttackPattern]:
        """Setup authorization attack patterns."""
        return {
            'privilege_escalation': PillarAttackPattern(
                pillar=CyberdefensePillar.AUTHORIZATION,
                attack_type='privilege_escalation',
                severity=LogSeverity.CRITICAL,
                description='Unauthorized privilege escalation detected',
                tactic=AttackTactic.PRIVILEGE_ESCALATION,
                weight=0.25,
                indicators=['admin_access_abuse', 'role_escalation', 'permission_abuse'],
                log_sources=['authorization_logs', 'rbac_logs', 'permission_logs'],
                mitigation_controls=['least_privilege', 'role_review', 'access_monitoring']
            ),
            'rbac_violation': PillarAttackPattern(
                pillar=CyberdefensePillar.AUTHORIZATION,
                attack_type='rbac_violation',
                severity=LogSeverity.HIGH,
                description='Role-based access control violation',
                tactic=AttackTactic.PRIVILEGE_ESCALATION,
                weight=0.2,
                indicators=['unauthorized_role_access', 'role_conflict', 'permission_creep'],
                log_sources=['rbac_logs', 'authorization_logs', 'access_logs'],
                mitigation_controls=['role_review', 'access_audit', 'permission_cleanup']
            ),
            'horizontal_privilege_escalation': PillarAttackPattern(
                pillar=CyberdefensePillar.AUTHORIZATION,
                attack_type='horizontal_privilege_escalation',
                severity=LogSeverity.HIGH,
                description='Horizontal privilege escalation attack',
                tactic=AttackTactic.PRIVILEGE_ESCALATION,
                weight=0.15,
                indicators=['cross_user_access', 'data_access_abuse', 'account_takeover'],
                log_sources=['authorization_logs', 'data_access_logs', 'user_activity_logs'],
                mitigation_controls=['data_classification', 'access_controls', 'user_monitoring']
            ),
            'vertical_privilege_escalation': PillarAttackPattern(
                pillar=CyberdefensePillar.AUTHORIZATION,
                attack_type='vertical_privilege_escalation',
                severity=LogSeverity.CRITICAL,
                description='Vertical privilege escalation attack',
                tactic=AttackTactic.PRIVILEGE_ESCALATION,
                weight=0.15,
                indicators=['admin_privilege_abuse', 'system_access_abuse', 'root_access_attempts'],
                log_sources=['authorization_logs', 'system_logs', 'admin_logs'],
                mitigation_controls=['privileged_access_management', 'admin_monitoring', 'system_hardening']
            ),
            'access_token_abuse': PillarAttackPattern(
                pillar=CyberdefensePillar.AUTHORIZATION,
                attack_type='access_token_abuse',
                severity=LogSeverity.HIGH,
                description='Access token abuse detected',
                tactic=AttackTactic.CREDENTIAL_ACCESS,
                weight=0.1,
                indicators=['token_reuse', 'token_theft', 'unauthorized_token_use'],
                log_sources=['token_logs', 'authorization_logs', 'api_logs'],
                mitigation_controls=['token_rotation', 'token_monitoring', 'api_security']
            ),
            'permission_creep': PillarAttackPattern(
                pillar=CyberdefensePillar.AUTHORIZATION,
                attack_type='permission_creep',
                severity=LogSeverity.MEDIUM,
                description='Unauthorized permission accumulation',
                tactic=AttackTactic.PRIVILEGE_ESCALATION,
                weight=0.1,
                indicators=['excessive_permissions', 'unused_permissions', 'permission_accumulation'],
                log_sources=['permission_logs', 'authorization_logs', 'access_review_logs'],
                mitigation_controls=['permission_review', 'access_cleanup', 'regular_audits']
            ),
            'admin_abuse': PillarAttackPattern(
                pillar=CyberdefensePillar.AUTHORIZATION,
                attack_type='admin_abuse',
                severity=LogSeverity.CRITICAL,
                description='Administrative privilege abuse',
                tactic=AttackTactic.PRIVILEGE_ESCALATION,
                weight=0.05,
                indicators=['admin_action_abuse', 'unauthorized_admin_access', 'privilege_abuse'],
                log_sources=['admin_logs', 'authorization_logs', 'system_logs'],
                mitigation_controls=['admin_monitoring', 'privileged_access_management', 'admin_review']
            )
        }
    
    def _get_normal_activities(self) -> List[str]:
        """Return list of normal authorization activities."""
        return [
            "User role assignment",
            "Permission grant",
            "Access request approval",
            "Role modification",
            "Permission revocation",
            "Access review completion",
            "Authorization policy update",
            "User access provisioning",
            "Access deprovisioning",
            "Role-based access control check",
            "Permission validation",
            "Access control list update",
            "Authorization decision",
            "Access token validation",
            "Permission audit",
            "Role hierarchy update",
            "Access policy enforcement",
            "Authorization workflow",
            "Access control matrix update",
            "Permission inheritance"
        ]

