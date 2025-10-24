"""
Application Security pillar generator.
"""

from typing import Dict, Any, List
from ..models import CyberdefensePillar, LogSeverity, AttackTactic, PillarAttackPattern
from .base_pillar_generator import BasePillarGenerator


class ApplicationSecurityGenerator(BasePillarGenerator):
    """Generator for Application Security pillar."""
    
    def get_pillar(self) -> CyberdefensePillar:
        return CyberdefensePillar.APPLICATION_SECURITY
    
    def _setup_attack_patterns(self) -> Dict[str, PillarAttackPattern]:
        """Setup application security attack patterns."""
        return {
            'sql_injection': PillarAttackPattern(
                pillar=CyberdefensePillar.APPLICATION_SECURITY,
                attack_type='sql_injection',
                severity=LogSeverity.HIGH,
                description='SQL injection attack detected',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.2,
                indicators=['sql_injection_attempts', 'database_errors', 'malicious_queries'],
                log_sources=['application_logs', 'database_logs', 'waf_logs'],
                mitigation_controls=['parameterized_queries', 'input_validation', 'waf_protection']
            ),
            'cross_site_scripting': PillarAttackPattern(
                pillar=CyberdefensePillar.APPLICATION_SECURITY,
                attack_type='cross_site_scripting',
                severity=LogSeverity.HIGH,
                description='Cross-site scripting (XSS) attack',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.15,
                indicators=['xss_payloads', 'script_injection', 'dom_manipulation'],
                log_sources=['application_logs', 'web_server_logs', 'security_logs'],
                mitigation_controls=['input_sanitization', 'content_security_policy', 'xss_protection']
            ),
            'cross_site_request_forgery': PillarAttackPattern(
                pillar=CyberdefensePillar.APPLICATION_SECURITY,
                attack_type='cross_site_request_forgery',
                severity=LogSeverity.MEDIUM,
                description='Cross-site request forgery (CSRF) attack',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.1,
                indicators=['csrf_tokens', 'unauthorized_requests', 'state_manipulation'],
                log_sources=['application_logs', 'web_server_logs', 'security_logs'],
                mitigation_controls=['csrf_tokens', 'same_site_cookies', 'request_validation']
            ),
            'insecure_direct_object_reference': PillarAttackPattern(
                pillar=CyberdefensePillar.APPLICATION_SECURITY,
                attack_type='insecure_direct_object_reference',
                severity=LogSeverity.HIGH,
                description='Insecure direct object reference attack',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.1,
                indicators=['unauthorized_object_access', 'idor_attempts', 'data_exposure'],
                log_sources=['application_logs', 'access_logs', 'security_logs'],
                mitigation_controls=['access_controls', 'object_authorization', 'data_protection']
            ),
            'security_misconfiguration': PillarAttackPattern(
                pillar=CyberdefensePillar.APPLICATION_SECURITY,
                attack_type='security_misconfiguration',
                severity=LogSeverity.MEDIUM,
                description='Security misconfiguration detected',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.15,
                indicators=['exposed_configurations', 'default_credentials', 'debug_mode'],
                log_sources=['application_logs', 'configuration_logs', 'security_scans'],
                mitigation_controls=['secure_configuration', 'configuration_review', 'security_hardening']
            ),
            'sensitive_data_exposure': PillarAttackPattern(
                pillar=CyberdefensePillar.APPLICATION_SECURITY,
                attack_type='sensitive_data_exposure',
                severity=LogSeverity.CRITICAL,
                description='Sensitive data exposure in application',
                tactic=AttackTactic.COLLECTION,
                weight=0.1,
                indicators=['data_leakage', 'unencrypted_data', 'exposed_credentials'],
                log_sources=['application_logs', 'data_access_logs', 'security_logs'],
                mitigation_controls=['data_encryption', 'access_controls', 'data_classification']
            ),
            'missing_function_level_access_control': PillarAttackPattern(
                pillar=CyberdefensePillar.APPLICATION_SECURITY,
                attack_type='missing_function_level_access_control',
                severity=LogSeverity.HIGH,
                description='Missing function level access control',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.1,
                indicators=['unauthorized_function_access', 'privilege_bypass', 'function_abuse'],
                log_sources=['application_logs', 'authorization_logs', 'security_logs'],
                mitigation_controls=['function_authorization', 'access_controls', 'security_review']
            ),
            'unvalidated_redirects_forwards': PillarAttackPattern(
                pillar=CyberdefensePillar.APPLICATION_SECURITY,
                attack_type='unvalidated_redirects_forwards',
                severity=LogSeverity.MEDIUM,
                description='Unvalidated redirects and forwards',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.05,
                indicators=['redirect_abuse', 'url_manipulation', 'phishing_attempts'],
                log_sources=['application_logs', 'web_server_logs', 'security_logs'],
                mitigation_controls=['url_validation', 'redirect_controls', 'user_education']
            ),
            'using_components_with_known_vulnerabilities': PillarAttackPattern(
                pillar=CyberdefensePillar.APPLICATION_SECURITY,
                attack_type='using_components_with_known_vulnerabilities',
                severity=LogSeverity.HIGH,
                description='Vulnerable components detected',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.1,
                indicators=['vulnerable_libraries', 'outdated_components', 'security_advisories'],
                log_sources=['dependency_logs', 'security_scans', 'vulnerability_reports'],
                mitigation_controls=['dependency_management', 'vulnerability_scanning', 'component_updates']
            ),
            'insufficient_logging_monitoring': PillarAttackPattern(
                pillar=CyberdefensePillar.APPLICATION_SECURITY,
                attack_type='insufficient_logging_monitoring',
                severity=LogSeverity.MEDIUM,
                description='Insufficient logging and monitoring',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.05,
                indicators=['missing_logs', 'incomplete_audit_trail', 'monitoring_gaps'],
                log_sources=['application_logs', 'audit_logs', 'monitoring_logs'],
                mitigation_controls=['comprehensive_logging', 'security_monitoring', 'audit_trail']
            )
        }
    
    def _get_normal_activities(self) -> List[str]:
        """Return list of normal application security activities."""
        return [
            "Application security scan completed",
            "Vulnerability assessment performed",
            "Security code review completed",
            "Penetration testing conducted",
            "Security configuration review",
            "Dependency vulnerability scan",
            "Security training completed",
            "Security policy update",
            "Application security testing",
            "Security architecture review",
            "Threat modeling session",
            "Security requirements review",
            "Security testing automation",
            "Security metrics collection",
            "Security incident response",
            "Security awareness training",
            "Security tool configuration",
            "Security process improvement",
            "Security compliance check",
            "Security risk assessment"
        ]

