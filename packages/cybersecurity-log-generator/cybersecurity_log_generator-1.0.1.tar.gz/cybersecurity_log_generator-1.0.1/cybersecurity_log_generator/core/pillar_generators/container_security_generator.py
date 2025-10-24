"""
Container Security pillar generator.
"""

from typing import Dict, Any, List
from ..models import CyberdefensePillar, LogSeverity, AttackTactic, PillarAttackPattern
from .base_pillar_generator import BasePillarGenerator


class ContainerSecurityGenerator(BasePillarGenerator):
    """Generator for Container Security pillar."""
    
    def get_pillar(self) -> CyberdefensePillar:
        return CyberdefensePillar.CONTAINER_SECURITY
    
    def _setup_attack_patterns(self) -> Dict[str, PillarAttackPattern]:
        """Setup container security attack patterns."""
        return {
            'container_escape': PillarAttackPattern(
                pillar=CyberdefensePillar.CONTAINER_SECURITY,
                attack_type='container_escape',
                severity=LogSeverity.CRITICAL,
                description='Container escape attack detected',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.25,
                indicators=['container_breakout', 'host_access', 'privilege_escalation'],
                log_sources=['container_logs', 'runtime_logs', 'security_logs'],
                mitigation_controls=['container_hardening', 'runtime_security', 'privilege_controls']
            ),
            'malicious_container_image': PillarAttackPattern(
                pillar=CyberdefensePillar.CONTAINER_SECURITY,
                attack_type='malicious_container_image',
                severity=LogSeverity.HIGH,
                description='Malicious container image detected',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.2,
                indicators=['malicious_packages', 'backdoors', 'crypto_miners'],
                log_sources=['image_scan_logs', 'container_logs', 'security_logs'],
                mitigation_controls=['image_scanning', 'trusted_registries', 'image_security']
            ),
            'container_runtime_abuse': PillarAttackPattern(
                pillar=CyberdefensePillar.CONTAINER_SECURITY,
                attack_type='container_runtime_abuse',
                severity=LogSeverity.HIGH,
                description='Container runtime abuse',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.15,
                indicators=['runtime_abuse', 'privilege_escalation', 'resource_abuse'],
                log_sources=['runtime_logs', 'container_logs', 'security_logs'],
                mitigation_controls=['runtime_security', 'resource_limits', 'runtime_monitoring']
            ),
            'orchestration_attack': PillarAttackPattern(
                pillar=CyberdefensePillar.CONTAINER_SECURITY,
                attack_type='orchestration_attack',
                severity=LogSeverity.CRITICAL,
                description='Container orchestration attack',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.15,
                indicators=['k8s_abuse', 'orchestrator_compromise', 'cluster_escape'],
                log_sources=['orchestrator_logs', 'cluster_logs', 'security_logs'],
                mitigation_controls=['orchestrator_security', 'cluster_hardening', 'rbac_controls']
            ),
            'container_network_abuse': PillarAttackPattern(
                pillar=CyberdefensePillar.CONTAINER_SECURITY,
                attack_type='container_network_abuse',
                severity=LogSeverity.MEDIUM,
                description='Container network abuse',
                tactic=AttackTactic.LATERAL_MOVEMENT,
                weight=0.1,
                indicators=['network_policy_violations', 'lateral_movement', 'network_abuse'],
                log_sources=['network_logs', 'container_logs', 'security_logs'],
                mitigation_controls=['network_policies', 'network_segmentation', 'network_monitoring']
            ),
            'container_registry_compromise': PillarAttackPattern(
                pillar=CyberdefensePillar.CONTAINER_SECURITY,
                attack_type='container_registry_compromise',
                severity=LogSeverity.HIGH,
                description='Container registry compromise',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.1,
                indicators=['registry_breach', 'image_tampering', 'credential_theft'],
                log_sources=['registry_logs', 'container_logs', 'security_logs'],
                mitigation_controls=['registry_security', 'image_signing', 'access_controls']
            ),
            'container_secrets_abuse': PillarAttackPattern(
                pillar=CyberdefensePillar.CONTAINER_SECURITY,
                attack_type='container_secrets_abuse',
                severity=LogSeverity.HIGH,
                description='Container secrets abuse',
                tactic=AttackTactic.CREDENTIAL_ACCESS,
                weight=0.05,
                indicators=['secrets_exposure', 'credential_abuse', 'secret_theft'],
                log_sources=['secrets_logs', 'container_logs', 'security_logs'],
                mitigation_controls=['secrets_management', 'secret_rotation', 'access_controls']
            )
        }
    
    def _get_normal_activities(self) -> List[str]:
        """Return list of normal container security activities."""
        return [
            "Container image scan completed",
            "Container runtime security check",
            "Container orchestration security review",
            "Container network policy enforcement",
            "Container registry security scan",
            "Container secrets management",
            "Container security monitoring",
            "Container vulnerability assessment",
            "Container security policy update",
            "Container security training",
            "Container incident response",
            "Container security architecture review",
            "Container compliance audit",
            "Container backup verification",
            "Container disaster recovery test",
            "Container security metrics collection",
            "Container security tool configuration",
            "Container security process improvement",
            "Container security risk assessment",
            "Container security certification"
        ]

