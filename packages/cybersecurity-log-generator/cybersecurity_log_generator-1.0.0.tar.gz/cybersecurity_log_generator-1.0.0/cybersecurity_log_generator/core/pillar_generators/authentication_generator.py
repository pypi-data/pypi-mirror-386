"""
Authentication pillar generator.
"""

from typing import Dict, Any, List
from ..models import CyberdefensePillar, LogSeverity, AttackTactic, PillarAttackPattern
from .base_pillar_generator import BasePillarGenerator


class AuthenticationGenerator(BasePillarGenerator):
    """Generator for Authentication pillar."""
    
    def get_pillar(self) -> CyberdefensePillar:
        return CyberdefensePillar.AUTHENTICATION
    
    def _setup_attack_patterns(self) -> Dict[str, PillarAttackPattern]:
        """Setup authentication attack patterns."""
        return {
            'credential_stuffing': PillarAttackPattern(
                pillar=CyberdefensePillar.AUTHENTICATION,
                attack_type='credential_stuffing',
                severity=LogSeverity.HIGH,
                description='Credential stuffing attack detected',
                tactic=AttackTactic.CREDENTIAL_ACCESS,
                weight=0.25,
                indicators=['multiple_failed_logins', 'credential_reuse', 'automated_attempts'],
                log_sources=['authentication_logs', 'login_logs', 'failed_login_logs'],
                mitigation_controls=['rate_limiting', 'account_lockout', 'credential_monitoring']
            ),
            'brute_force_attack': PillarAttackPattern(
                pillar=CyberdefensePillar.AUTHENTICATION,
                attack_type='brute_force_attack',
                severity=LogSeverity.HIGH,
                description='Brute force authentication attack',
                tactic=AttackTactic.CREDENTIAL_ACCESS,
                weight=0.2,
                indicators=['rapid_login_attempts', 'password_guessing', 'account_enumeration'],
                log_sources=['authentication_logs', 'security_logs', 'failed_login_logs'],
                mitigation_controls=['account_lockout', 'rate_limiting', 'strong_passwords']
            ),
            'mfa_bypass': PillarAttackPattern(
                pillar=CyberdefensePillar.AUTHENTICATION,
                attack_type='mfa_bypass',
                severity=LogSeverity.CRITICAL,
                description='Multi-factor authentication bypass attempt',
                tactic=AttackTactic.CREDENTIAL_ACCESS,
                weight=0.15,
                indicators=['mfa_bypass_attempts', 'sms_interception', 'token_replay'],
                log_sources=['mfa_logs', 'authentication_logs', 'security_logs'],
                mitigation_controls=['hardware_tokens', 'biometric_auth', 'mfa_monitoring']
            ),
            'session_hijacking': PillarAttackPattern(
                pillar=CyberdefensePillar.AUTHENTICATION,
                attack_type='session_hijacking',
                severity=LogSeverity.HIGH,
                description='Session hijacking attack detected',
                tactic=AttackTactic.CREDENTIAL_ACCESS,
                weight=0.15,
                indicators=['session_token_theft', 'concurrent_sessions', 'unusual_session_activity'],
                log_sources=['session_logs', 'authentication_logs', 'application_logs'],
                mitigation_controls=['session_timeout', 'token_rotation', 'session_monitoring']
            ),
            'privilege_escalation': PillarAttackPattern(
                pillar=CyberdefensePillar.AUTHENTICATION,
                attack_type='privilege_escalation',
                severity=LogSeverity.CRITICAL,
                description='Privilege escalation through authentication bypass',
                tactic=AttackTactic.PRIVILEGE_ESCALATION,
                weight=0.1,
                indicators=['admin_access_attempts', 'privilege_abuse', 'authentication_bypass'],
                log_sources=['authentication_logs', 'authorization_logs', 'admin_logs'],
                mitigation_controls=['least_privilege', 'privilege_monitoring', 'admin_controls']
            ),
            'kerberoasting': PillarAttackPattern(
                pillar=CyberdefensePillar.AUTHENTICATION,
                attack_type='kerberoasting',
                severity=LogSeverity.HIGH,
                description='Kerberoasting attack on Active Directory',
                tactic=AttackTactic.CREDENTIAL_ACCESS,
                weight=0.1,
                indicators=['kerberos_ticket_abuse', 'service_account_attacks', 'ticket_encryption_weakness'],
                log_sources=['kerberos_logs', 'domain_controller_logs', 'authentication_logs'],
                mitigation_controls=['strong_service_passwords', 'kerberos_monitoring', 'privileged_access_management']
            ),
            'pass_the_hash': PillarAttackPattern(
                pillar=CyberdefensePillar.AUTHENTICATION,
                attack_type='pass_the_hash',
                severity=LogSeverity.HIGH,
                description='Pass-the-hash attack detected',
                tactic=AttackTactic.CREDENTIAL_ACCESS,
                weight=0.05,
                indicators=['hash_reuse', 'lateral_movement', 'credential_theft'],
                log_sources=['authentication_logs', 'network_logs', 'security_logs'],
                mitigation_controls=['credential_protection', 'network_segmentation', 'authentication_monitoring']
            )
        }
    
    def _get_normal_activities(self) -> List[str]:
        """Return list of normal authentication activities."""
        return [
            "Successful user login",
            "Password change completed",
            "MFA setup completed",
            "Account lockout due to failed attempts",
            "Password reset requested",
            "Session timeout occurred",
            "User logout",
            "Account creation",
            "Password policy compliance check",
            "Authentication token refresh",
            "Single sign-on (SSO) login",
            "Biometric authentication",
            "Hardware token authentication",
            "Certificate-based authentication",
            "OAuth authentication flow",
            "SAML authentication",
            "LDAP authentication",
            "Active Directory authentication",
            "Multi-factor authentication",
            "Risk-based authentication"
        ]
