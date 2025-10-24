"""
Encryption pillar generator.
"""

from typing import Dict, Any, List
from ..models import CyberdefensePillar, LogSeverity, AttackTactic, PillarAttackPattern
from .base_pillar_generator import BasePillarGenerator


class EncryptionGenerator(BasePillarGenerator):
    """Generator for Encryption pillar."""
    
    def get_pillar(self) -> CyberdefensePillar:
        return CyberdefensePillar.ENCRYPTION
    
    def _setup_attack_patterns(self) -> Dict[str, PillarAttackPattern]:
        """Setup encryption attack patterns."""
        return {
            'encryption_key_compromise': PillarAttackPattern(
                pillar=CyberdefensePillar.ENCRYPTION,
                attack_type='encryption_key_compromise',
                severity=LogSeverity.CRITICAL,
                description='Encryption key compromise detected',
                tactic=AttackTactic.CREDENTIAL_ACCESS,
                weight=0.25,
                indicators=['key_theft', 'key_abuse', 'encryption_breach'],
                log_sources=['key_management_logs', 'encryption_logs', 'security_logs'],
                mitigation_controls=['key_rotation', 'hardware_security_modules', 'key_monitoring']
            ),
            'weak_encryption_attack': PillarAttackPattern(
                pillar=CyberdefensePillar.ENCRYPTION,
                attack_type='weak_encryption_attack',
                severity=LogSeverity.HIGH,
                description='Weak encryption algorithm attack',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.2,
                indicators=['weak_algorithm_usage', 'encryption_vulnerabilities', 'crypto_weaknesses'],
                log_sources=['encryption_logs', 'crypto_logs', 'security_logs'],
                mitigation_controls=['strong_algorithms', 'crypto_standards', 'encryption_monitoring']
            ),
            'crypto_implementation_flaw': PillarAttackPattern(
                pillar=CyberdefensePillar.ENCRYPTION,
                attack_type='crypto_implementation_flaw',
                severity=LogSeverity.HIGH,
                description='Cryptographic implementation flaw',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.15,
                indicators=['implementation_vulnerabilities', 'crypto_bugs', 'encryption_errors'],
                log_sources=['crypto_logs', 'implementation_logs', 'security_logs'],
                mitigation_controls=['secure_implementation', 'crypto_testing', 'implementation_review']
            ),
            'side_channel_attack': PillarAttackPattern(
                pillar=CyberdefensePillar.ENCRYPTION,
                attack_type='side_channel_attack',
                severity=LogSeverity.HIGH,
                description='Side-channel attack on encryption',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.15,
                indicators=['timing_attacks', 'power_analysis', 'electromagnetic_analysis'],
                log_sources=['crypto_logs', 'hardware_logs', 'security_logs'],
                mitigation_controls=['side_channel_protection', 'hardware_security', 'crypto_hardening']
            ),
            'quantum_crypto_attack': PillarAttackPattern(
                pillar=CyberdefensePillar.ENCRYPTION,
                attack_type='quantum_crypto_attack',
                severity=LogSeverity.CRITICAL,
                description='Quantum computing attack on encryption',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.1,
                indicators=['quantum_algorithm_usage', 'post_quantum_threats', 'crypto_breakthrough'],
                log_sources=['crypto_logs', 'quantum_logs', 'security_logs'],
                mitigation_controls=['post_quantum_crypto', 'quantum_resistant_algorithms', 'crypto_evolution']
            ),
            'encryption_bypass': PillarAttackPattern(
                pillar=CyberdefensePillar.ENCRYPTION,
                attack_type='encryption_bypass',
                severity=LogSeverity.HIGH,
                description='Encryption bypass attack',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.1,
                indicators=['encryption_evasion', 'crypto_bypass', 'encryption_weakness'],
                log_sources=['encryption_logs', 'crypto_logs', 'security_logs'],
                mitigation_controls=['encryption_validation', 'crypto_monitoring', 'encryption_hardening']
            ),
            'crypto_supply_chain_attack': PillarAttackPattern(
                pillar=CyberdefensePillar.ENCRYPTION,
                attack_type='crypto_supply_chain_attack',
                severity=LogSeverity.CRITICAL,
                description='Cryptographic supply chain attack',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.05,
                indicators=['crypto_library_compromise', 'supply_chain_attack', 'crypto_tampering'],
                log_sources=['supply_chain_logs', 'crypto_logs', 'security_logs'],
                mitigation_controls=['supply_chain_security', 'crypto_verification', 'library_monitoring']
            )
        }
    
    def _get_normal_activities(self) -> List[str]:
        """Return list of normal encryption activities."""
        return [
            "Encryption key generation",
            "Encryption algorithm implementation",
            "Crypto key rotation",
            "Encryption performance testing",
            "Crypto compliance audit",
            "Encryption key management",
            "Crypto vulnerability assessment",
            "Encryption policy update",
            "Crypto training completion",
            "Encryption monitoring",
            "Crypto incident response",
            "Encryption metrics collection",
            "Crypto tool configuration",
            "Encryption process improvement",
            "Crypto risk assessment",
            "Encryption compliance check",
            "Crypto awareness training",
            "Encryption policy update",
            "Crypto governance review",
            "Encryption certification"
        ]

