"""
Data Protection pillar generator.
"""

from typing import Dict, Any, List
from ..models import CyberdefensePillar, LogSeverity, AttackTactic, PillarAttackPattern
from .base_pillar_generator import BasePillarGenerator


class DataProtectionGenerator(BasePillarGenerator):
    """Generator for Data Protection pillar."""
    
    def get_pillar(self) -> CyberdefensePillar:
        return CyberdefensePillar.DATA_PROTECTION
    
    def _setup_attack_patterns(self) -> Dict[str, PillarAttackPattern]:
        """Setup data protection attack patterns."""
        return {
            'data_exfiltration': PillarAttackPattern(
                pillar=CyberdefensePillar.DATA_PROTECTION,
                attack_type='data_exfiltration',
                severity=LogSeverity.CRITICAL,
                description='Data exfiltration attack detected',
                tactic=AttackTactic.EXFILTRATION,
                weight=0.25,
                indicators=['unauthorized_data_transfer', 'data_movement_anomalies', 'exfiltration_attempts'],
                log_sources=['data_access_logs', 'network_logs', 'dlp_logs'],
                mitigation_controls=['data_loss_prevention', 'network_monitoring', 'access_controls']
            ),
            'backup_compromise': PillarAttackPattern(
                pillar=CyberdefensePillar.DATA_PROTECTION,
                attack_type='backup_compromise',
                severity=LogSeverity.HIGH,
                description='Backup system compromise',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.2,
                indicators=['backup_tampering', 'backup_encryption_breach', 'backup_access_abuse'],
                log_sources=['backup_logs', 'storage_logs', 'security_logs'],
                mitigation_controls=['backup_encryption', 'backup_access_controls', 'backup_monitoring']
            ),
            'encryption_key_compromise': PillarAttackPattern(
                pillar=CyberdefensePillar.DATA_PROTECTION,
                attack_type='encryption_key_compromise',
                severity=LogSeverity.CRITICAL,
                description='Encryption key compromise detected',
                tactic=AttackTactic.CREDENTIAL_ACCESS,
                weight=0.15,
                indicators=['key_theft', 'key_abuse', 'encryption_breach'],
                log_sources=['key_management_logs', 'encryption_logs', 'security_logs'],
                mitigation_controls=['key_rotation', 'hardware_security_modules', 'key_monitoring']
            ),
            'data_corruption': PillarAttackPattern(
                pillar=CyberdefensePillar.DATA_PROTECTION,
                attack_type='data_corruption',
                severity=LogSeverity.HIGH,
                description='Data corruption attack',
                tactic=AttackTactic.IMPACT,
                weight=0.15,
                indicators=['data_integrity_violations', 'corruption_attempts', 'data_tampering'],
                log_sources=['integrity_logs', 'data_logs', 'security_logs'],
                mitigation_controls=['data_integrity_checks', 'backup_verification', 'corruption_detection']
            ),
            'ransomware_attack': PillarAttackPattern(
                pillar=CyberdefensePillar.DATA_PROTECTION,
                attack_type='ransomware_attack',
                severity=LogSeverity.CRITICAL,
                description='Ransomware attack on data',
                tactic=AttackTactic.IMPACT,
                weight=0.1,
                indicators=['file_encryption', 'ransom_notes', 'data_inaccessibility'],
                log_sources=['file_system_logs', 'security_logs', 'malware_logs'],
                mitigation_controls=['backup_restoration', 'endpoint_protection', 'user_education']
            ),
            'data_classification_violation': PillarAttackPattern(
                pillar=CyberdefensePillar.DATA_PROTECTION,
                attack_type='data_classification_violation',
                severity=LogSeverity.MEDIUM,
                description='Data classification violation',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.1,
                indicators=['misclassified_data', 'classification_errors', 'sensitivity_violations'],
                log_sources=['classification_logs', 'data_logs', 'compliance_logs'],
                mitigation_controls=['automated_classification', 'classification_training', 'classification_review']
            ),
            'data_retention_violation': PillarAttackPattern(
                pillar=CyberdefensePillar.DATA_PROTECTION,
                attack_type='data_retention_violation',
                severity=LogSeverity.MEDIUM,
                description='Data retention policy violation',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.05,
                indicators=['retention_breaches', 'data_hoarding', 'retention_policy_violations'],
                log_sources=['retention_logs', 'data_logs', 'policy_logs'],
                mitigation_controls=['automated_retention', 'retention_policies', 'data_governance']
            )
        }
    
    def _get_normal_activities(self) -> List[str]:
        """Return list of normal data protection activities."""
        return [
            "Data backup completed",
            "Data encryption verification",
            "Data integrity check",
            "Data classification review",
            "Data retention policy enforcement",
            "Data protection assessment",
            "Data recovery test",
            "Data loss prevention scan",
            "Data protection training",
            "Data protection policy update",
            "Data protection monitoring",
            "Data protection incident response",
            "Data protection audit",
            "Data protection metrics collection",
            "Data protection tool configuration",
            "Data protection process improvement",
            "Data protection risk assessment",
            "Data protection compliance check",
            "Data protection awareness training",
            "Data protection certification"
        ]

