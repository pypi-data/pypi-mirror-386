"""
Disaster Recovery pillar generator.
"""

from typing import Dict, Any, List
from ..models import CyberdefensePillar, LogSeverity, AttackTactic, PillarAttackPattern
from .base_pillar_generator import BasePillarGenerator


class DisasterRecoveryGenerator(BasePillarGenerator):
    """Generator for Disaster Recovery pillar."""
    
    def get_pillar(self) -> CyberdefensePillar:
        return CyberdefensePillar.DISASTER_RECOVERY
    
    def _setup_attack_patterns(self) -> Dict[str, PillarAttackPattern]:
        """Setup disaster recovery attack patterns."""
        return {
            'backup_compromise': PillarAttackPattern(
                pillar=CyberdefensePillar.DISASTER_RECOVERY,
                attack_type='backup_compromise',
                severity=LogSeverity.CRITICAL,
                description='Backup system compromise',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.25,
                indicators=['backup_tampering', 'backup_encryption_breach', 'backup_access_abuse'],
                log_sources=['backup_logs', 'storage_logs', 'security_logs'],
                mitigation_controls=['backup_encryption', 'backup_access_controls', 'backup_monitoring']
            ),
            'recovery_system_attack': PillarAttackPattern(
                pillar=CyberdefensePillar.DISASTER_RECOVERY,
                attack_type='recovery_system_attack',
                severity=LogSeverity.CRITICAL,
                description='Recovery system attack',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.2,
                indicators=['recovery_compromise', 'dr_system_abuse', 'recovery_bypass'],
                log_sources=['recovery_logs', 'dr_logs', 'security_logs'],
                mitigation_controls=['recovery_hardening', 'access_controls', 'recovery_monitoring']
            ),
            'failover_manipulation': PillarAttackPattern(
                pillar=CyberdefensePillar.DISASTER_RECOVERY,
                attack_type='failover_manipulation',
                severity=LogSeverity.HIGH,
                description='Failover system manipulation',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.15,
                indicators=['failover_abuse', 'redundancy_compromise', 'failover_manipulation'],
                log_sources=['failover_logs', 'redundancy_logs', 'security_logs'],
                mitigation_controls=['failover_monitoring', 'redundancy_controls', 'system_validation']
            ),
            'recovery_data_corruption': PillarAttackPattern(
                pillar=CyberdefensePillar.DISASTER_RECOVERY,
                attack_type='recovery_data_corruption',
                severity=LogSeverity.CRITICAL,
                description='Recovery data corruption',
                tactic=AttackTactic.IMPACT,
                weight=0.15,
                indicators=['recovery_data_tampering', 'backup_corruption', 'recovery_integrity_violations'],
                log_sources=['recovery_logs', 'backup_logs', 'integrity_logs'],
                mitigation_controls=['data_integrity_checks', 'backup_verification', 'recovery_validation']
            ),
            'dr_plan_compromise': PillarAttackPattern(
                pillar=CyberdefensePillar.DISASTER_RECOVERY,
                attack_type='dr_plan_compromise',
                severity=LogSeverity.HIGH,
                description='Disaster recovery plan compromise',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.1,
                indicators=['dr_plan_tampering', 'recovery_procedure_abuse', 'dr_plan_manipulation'],
                log_sources=['dr_logs', 'plan_logs', 'security_logs'],
                mitigation_controls=['plan_protection', 'access_controls', 'plan_monitoring']
            ),
            'recovery_testing_abuse': PillarAttackPattern(
                pillar=CyberdefensePillar.DISASTER_RECOVERY,
                attack_type='recovery_testing_abuse',
                severity=LogSeverity.MEDIUM,
                description='Recovery testing abuse',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.1,
                indicators=['test_abuse', 'recovery_simulation_manipulation', 'dr_test_compromise'],
                log_sources=['test_logs', 'recovery_logs', 'security_logs'],
                mitigation_controls=['test_monitoring', 'recovery_validation', 'test_controls']
            ),
            'recovery_communication_attack': PillarAttackPattern(
                pillar=CyberdefensePillar.DISASTER_RECOVERY,
                attack_type='recovery_communication_attack',
                severity=LogSeverity.MEDIUM,
                description='Recovery communication attack',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.05,
                indicators=['communication_disruption', 'recovery_notification_abuse', 'dr_communication_attack'],
                log_sources=['communication_logs', 'recovery_logs', 'security_logs'],
                mitigation_controls=['communication_monitoring', 'notification_verification', 'communication_backup']
            )
        }
    
    def _get_normal_activities(self) -> List[str]:
        """Return list of normal disaster recovery activities."""
        return [
            "Disaster recovery plan review",
            "Backup system verification",
            "Recovery system testing",
            "Failover system check",
            "Recovery procedure update",
            "Disaster recovery training",
            "Recovery system maintenance",
            "Backup integrity verification",
            "Recovery communication test",
            "Disaster recovery audit",
            "Recovery metrics collection",
            "Recovery tool configuration",
            "Recovery process improvement",
            "Recovery risk assessment",
            "Recovery compliance check",
            "Recovery awareness training",
            "Recovery policy update",
            "Recovery governance review",
            "Recovery incident response",
            "Recovery certification"
        ]

