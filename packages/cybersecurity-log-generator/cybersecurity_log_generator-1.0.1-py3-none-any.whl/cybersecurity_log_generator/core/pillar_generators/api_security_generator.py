"""
API Security pillar generator.
"""

from typing import Dict, Any, List
from ..models import CyberdefensePillar, LogSeverity, AttackTactic, PillarAttackPattern
from .base_pillar_generator import BasePillarGenerator


class APISecurityGenerator(BasePillarGenerator):
    """Generator for API Security pillar."""
    
    def get_pillar(self) -> CyberdefensePillar:
        return CyberdefensePillar.API_SECURITY
    
    def _setup_attack_patterns(self) -> Dict[str, PillarAttackPattern]:
        """Setup API security attack patterns."""
        return {
            'shadow_api_discovery': PillarAttackPattern(
                pillar=CyberdefensePillar.API_SECURITY,
                attack_type='shadow_api_discovery',
                severity=LogSeverity.HIGH,
                description='Shadow API discovered and accessed',
                tactic=AttackTactic.DISCOVERY,
                weight=0.2,
                indicators=['unauthorized_api_endpoint', 'shadow_api_access', 'undocumented_api'],
                log_sources=['api_gateway_logs', 'network_logs', 'application_logs'],
                mitigation_controls=['api_discovery', 'api_documentation', 'api_governance']
            ),
            'oauth_jwt_abuse': PillarAttackPattern(
                pillar=CyberdefensePillar.API_SECURITY,
                attack_type='oauth_jwt_abuse',
                severity=LogSeverity.HIGH,
                description='OAuth/JWT token abuse detected',
                tactic=AttackTactic.CREDENTIAL_ACCESS,
                weight=0.25,
                indicators=['token_manipulation', 'jwt_abuse', 'oauth_attack'],
                log_sources=['oauth_logs', 'jwt_logs', 'authentication_logs'],
                mitigation_controls=['token_validation', 'oauth_security', 'jwt_security']
            ),
            'api_injection_attack': PillarAttackPattern(
                pillar=CyberdefensePillar.API_SECURITY,
                attack_type='api_injection_attack',
                severity=LogSeverity.CRITICAL,
                description='API injection attack detected',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.15,
                indicators=['sql_injection_api', 'nosql_injection', 'command_injection'],
                log_sources=['api_logs', 'application_logs', 'database_logs'],
                mitigation_controls=['input_validation', 'api_security', 'injection_prevention']
            ),
            'api_rate_limit_bypass': PillarAttackPattern(
                pillar=CyberdefensePillar.API_SECURITY,
                attack_type='api_rate_limit_bypass',
                severity=LogSeverity.MEDIUM,
                description='API rate limit bypass attempt',
                tactic=AttackTactic.DEFENSE_EVASION,
                weight=0.2,
                indicators=['rate_limit_bypass', 'api_abuse', 'excessive_api_calls'],
                log_sources=['api_gateway_logs', 'rate_limit_logs', 'application_logs'],
                mitigation_controls=['rate_limiting', 'api_throttling', 'abuse_detection']
            ),
            'api_privilege_escalation': PillarAttackPattern(
                pillar=CyberdefensePillar.API_SECURITY,
                attack_type='api_privilege_escalation',
                severity=LogSeverity.HIGH,
                description='API privilege escalation attempt',
                tactic=AttackTactic.PRIVILEGE_ESCALATION,
                weight=0.2,
                indicators=['unauthorized_api_access', 'privilege_escalation', 'api_abuse'],
                log_sources=['api_logs', 'authorization_logs', 'audit_logs'],
                mitigation_controls=['api_authorization', 'privilege_control', 'access_review']
            )
        }
    
    def _get_normal_activities(self) -> List[str]:
        """Return normal API security activities."""
        return [
            'API request processed successfully',
            'API authentication completed',
            'API rate limit check passed',
            'API authorization verified',
            'API response generated',
            'API logging completed',
            'API security scan passed',
            'API documentation updated',
            'API version deployed',
            'API monitoring active'
        ]
