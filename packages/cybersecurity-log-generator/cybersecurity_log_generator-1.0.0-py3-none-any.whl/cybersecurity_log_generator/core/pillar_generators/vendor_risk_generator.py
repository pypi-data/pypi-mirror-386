"""
Vendor Risk pillar generator.
"""

from typing import Dict, Any, List
from ..models import CyberdefensePillar, LogSeverity, AttackTactic, PillarAttackPattern
from .base_pillar_generator import BasePillarGenerator


class VendorRiskGenerator(BasePillarGenerator):
    """Generator for 3rd-Party / Vendor Risk pillar."""
    
    def get_pillar(self) -> CyberdefensePillar:
        return CyberdefensePillar.VENDOR_RISK
    
    def _setup_attack_patterns(self) -> Dict[str, PillarAttackPattern]:
        """Setup vendor risk attack patterns."""
        return {
            'vendor_credential_compromise': PillarAttackPattern(
                pillar=CyberdefensePillar.VENDOR_RISK,
                attack_type='vendor_credential_compromise',
                severity=LogSeverity.HIGH,
                description='Vendor credential compromise detected',
                tactic=AttackTactic.CREDENTIAL_ACCESS,
                weight=0.25,
                indicators=['unusual_vendor_access', 'credential_stuffing', 'vendor_breach'],
                log_sources=['vendor_access_logs', 'authentication_logs', 'sso_logs'],
                mitigation_controls=['vendor_access_review', 'credential_rotation', 'mfa_enforcement']
            ),
            'supply_chain_attack': PillarAttackPattern(
                pillar=CyberdefensePillar.VENDOR_RISK,
                attack_type='supply_chain_attack',
                severity=LogSeverity.CRITICAL,
                description='Supply chain attack via vendor compromise',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.15,
                indicators=['vendor_malware', 'supply_chain_compromise', 'vendor_breach'],
                log_sources=['vendor_logs', 'security_scans', 'threat_intelligence'],
                mitigation_controls=['vendor_assessment', 'supply_chain_monitoring', 'vendor_security_requirements']
            ),
            'saas_misconfiguration': PillarAttackPattern(
                pillar=CyberdefensePillar.VENDOR_RISK,
                attack_type='saas_misconfiguration',
                severity=LogSeverity.MEDIUM,
                description='SaaS vendor misconfiguration detected',
                tactic=AttackTactic.DISCOVERY,
                weight=0.2,
                indicators=['misconfigured_saas', 'exposed_data', 'vendor_config_drift'],
                log_sources=['saas_logs', 'configuration_scans', 'vendor_reports'],
                mitigation_controls=['saas_configuration_review', 'vendor_monitoring', 'configuration_management']
            ),
            'vendor_data_breach': PillarAttackPattern(
                pillar=CyberdefensePillar.VENDOR_RISK,
                attack_type='vendor_data_breach',
                severity=LogSeverity.CRITICAL,
                description='Vendor data breach affecting organization',
                tactic=AttackTactic.EXFILTRATION,
                weight=0.2,
                indicators=['vendor_breach_notification', 'data_exposure', 'vendor_incident'],
                log_sources=['vendor_notifications', 'threat_intelligence', 'breach_reports'],
                mitigation_controls=['vendor_incident_response', 'data_protection_assessment', 'vendor_contract_review']
            ),
            'vendor_access_abuse': PillarAttackPattern(
                pillar=CyberdefensePillar.VENDOR_RISK,
                attack_type='vendor_access_abuse',
                severity=LogSeverity.HIGH,
                description='Vendor access abuse detected',
                tactic=AttackTactic.ABUSE,
                weight=0.2,
                indicators=['excessive_vendor_access', 'unauthorized_vendor_activity', 'vendor_privilege_abuse'],
                log_sources=['vendor_access_logs', 'privilege_logs', 'activity_logs'],
                mitigation_controls=['vendor_access_review', 'privilege_monitoring', 'vendor_audit']
            )
        }
    
    def _get_normal_activities(self) -> List[str]:
        """Return normal vendor risk activities."""
        return [
            'Vendor access request processed',
            'Vendor security assessment completed',
            'Vendor contract review conducted',
            'Vendor access granted',
            'Vendor access revoked',
            'Vendor security scan completed',
            'Vendor compliance check passed',
            'Vendor risk assessment updated',
            'Vendor access reviewed',
            'Vendor security requirements updated'
        ]
