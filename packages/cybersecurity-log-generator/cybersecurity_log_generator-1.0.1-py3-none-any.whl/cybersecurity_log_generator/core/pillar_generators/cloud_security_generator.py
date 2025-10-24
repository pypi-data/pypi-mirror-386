"""
Cloud Security pillar generator.
"""

from typing import Dict, Any, List
from ..models import CyberdefensePillar, LogSeverity, AttackTactic, PillarAttackPattern
from .base_pillar_generator import BasePillarGenerator


class CloudSecurityGenerator(BasePillarGenerator):
    """Generator for Cloud Security pillar."""
    
    def get_pillar(self) -> CyberdefensePillar:
        return CyberdefensePillar.CLOUD_SECURITY
    
    def _setup_attack_patterns(self) -> Dict[str, PillarAttackPattern]:
        """Setup cloud security attack patterns."""
        return {
            'cloud_misconfiguration': PillarAttackPattern(
                pillar=CyberdefensePillar.CLOUD_SECURITY,
                attack_type='cloud_misconfiguration',
                severity=LogSeverity.HIGH,
                description='Cloud infrastructure misconfiguration',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.25,
                indicators=['exposed_buckets', 'open_ports', 'default_credentials'],
                log_sources=['cloud_logs', 'configuration_logs', 'security_scans'],
                mitigation_controls=['cloud_security_posture', 'configuration_management', 'security_monitoring']
            ),
            'container_escape': PillarAttackPattern(
                pillar=CyberdefensePillar.CLOUD_SECURITY,
                attack_type='container_escape',
                severity=LogSeverity.CRITICAL,
                description='Container escape attack',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.15,
                indicators=['container_breakout', 'host_access', 'privilege_escalation'],
                log_sources=['container_logs', 'runtime_logs', 'security_logs'],
                mitigation_controls=['container_hardening', 'runtime_security', 'privilege_controls']
            ),
            'serverless_abuse': PillarAttackPattern(
                pillar=CyberdefensePillar.CLOUD_SECURITY,
                attack_type='serverless_abuse',
                severity=LogSeverity.HIGH,
                description='Serverless function abuse',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.15,
                indicators=['function_abuse', 'resource_exhaustion', 'unauthorized_execution'],
                log_sources=['serverless_logs', 'function_logs', 'cloud_logs'],
                mitigation_controls=['function_security', 'resource_limits', 'execution_monitoring']
            ),
            'cloud_credential_theft': PillarAttackPattern(
                pillar=CyberdefensePillar.CLOUD_SECURITY,
                attack_type='cloud_credential_theft',
                severity=LogSeverity.CRITICAL,
                description='Cloud credential theft detected',
                tactic=AttackTactic.CREDENTIAL_ACCESS,
                weight=0.2,
                indicators=['credential_compromise', 'api_key_theft', 'service_account_abuse'],
                log_sources=['cloud_logs', 'api_logs', 'security_logs'],
                mitigation_controls=['credential_rotation', 'api_security', 'access_monitoring']
            ),
            'data_exfiltration_cloud': PillarAttackPattern(
                pillar=CyberdefensePillar.CLOUD_SECURITY,
                attack_type='data_exfiltration_cloud',
                severity=LogSeverity.CRITICAL,
                description='Data exfiltration from cloud storage',
                tactic=AttackTactic.EXFILTRATION,
                weight=0.1,
                indicators=['data_download_abuse', 'storage_access_anomalies', 'data_movement'],
                log_sources=['storage_logs', 'cloud_logs', 'data_access_logs'],
                mitigation_controls=['data_loss_prevention', 'access_controls', 'data_monitoring']
            ),
            'cloud_api_abuse': PillarAttackPattern(
                pillar=CyberdefensePillar.CLOUD_SECURITY,
                attack_type='cloud_api_abuse',
                severity=LogSeverity.HIGH,
                description='Cloud API abuse detected',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.1,
                indicators=['api_rate_limiting', 'unauthorized_api_calls', 'api_abuse'],
                log_sources=['api_logs', 'cloud_logs', 'security_logs'],
                mitigation_controls=['api_security', 'rate_limiting', 'api_monitoring']
            ),
            'multi_tenant_abuse': PillarAttackPattern(
                pillar=CyberdefensePillar.CLOUD_SECURITY,
                attack_type='multi_tenant_abuse',
                severity=LogSeverity.HIGH,
                description='Multi-tenant cloud abuse',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.05,
                indicators=['tenant_isolation_breach', 'cross_tenant_access', 'resource_abuse'],
                log_sources=['cloud_logs', 'tenant_logs', 'security_logs'],
                mitigation_controls=['tenant_isolation', 'resource_controls', 'multi_tenant_monitoring']
            )
        }
    
    def _get_normal_activities(self) -> List[str]:
        """Return list of normal cloud security activities."""
        return [
            "Cloud security posture assessment",
            "Container security scan",
            "Cloud configuration review",
            "Serverless function security check",
            "Cloud access review",
            "Cloud compliance audit",
            "Cloud security monitoring",
            "Cloud incident response",
            "Cloud security training",
            "Cloud security policy update",
            "Cloud vulnerability scan",
            "Cloud security architecture review",
            "Cloud data protection assessment",
            "Cloud backup verification",
            "Cloud disaster recovery test",
            "Cloud security metrics collection",
            "Cloud security tool configuration",
            "Cloud security process improvement",
            "Cloud security risk assessment",
            "Cloud security certification"
        ]

