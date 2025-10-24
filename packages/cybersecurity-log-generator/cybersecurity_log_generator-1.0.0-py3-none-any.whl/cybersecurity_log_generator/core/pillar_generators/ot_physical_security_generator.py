"""
OT/ICS & Physical Security pillar generator.
"""

from typing import Dict, Any, List
from ..models import CyberdefensePillar, LogSeverity, AttackTactic, PillarAttackPattern
from .base_pillar_generator import BasePillarGenerator


class OTPhysicalSecurityGenerator(BasePillarGenerator):
    """Generator for OT/ICS & Physical Security pillar."""
    
    def get_pillar(self) -> CyberdefensePillar:
        return CyberdefensePillar.OT_PHYSICAL_SECURITY
    
    def _setup_attack_patterns(self) -> Dict[str, PillarAttackPattern]:
        """Setup OT/ICS & Physical Security attack patterns."""
        return {
            'ot_system_compromise': PillarAttackPattern(
                pillar=CyberdefensePillar.OT_PHYSICAL_SECURITY,
                attack_type='ot_system_compromise',
                severity=LogSeverity.CRITICAL,
                description='OT/ICS system compromise',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.25,
                indicators=['ot_breach', 'ics_compromise', 'industrial_system_attack'],
                log_sources=['ot_logs', 'ics_logs', 'industrial_logs'],
                mitigation_controls=['ot_security', 'ics_protection', 'industrial_monitoring']
            ),
            'physical_security_breach': PillarAttackPattern(
                pillar=CyberdefensePillar.OT_PHYSICAL_SECURITY,
                attack_type='physical_security_breach',
                severity=LogSeverity.HIGH,
                description='Physical security breach',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.2,
                indicators=['unauthorized_physical_access', 'facility_breach', 'physical_intrusion'],
                log_sources=['physical_logs', 'access_logs', 'security_logs'],
                mitigation_controls=['physical_controls', 'access_management', 'physical_monitoring']
            ),
            'scada_attack': PillarAttackPattern(
                pillar=CyberdefensePillar.OT_PHYSICAL_SECURITY,
                attack_type='scada_attack',
                severity=LogSeverity.CRITICAL,
                description='SCADA system attack',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.15,
                indicators=['scada_compromise', 'industrial_control_attack', 'scada_manipulation'],
                log_sources=['scada_logs', 'control_logs', 'industrial_logs'],
                mitigation_controls=['scada_security', 'control_protection', 'industrial_monitoring']
            ),
            'physical_asset_theft': PillarAttackPattern(
                pillar=CyberdefensePillar.OT_PHYSICAL_SECURITY,
                attack_type='physical_asset_theft',
                severity=LogSeverity.HIGH,
                description='Physical asset theft',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.15,
                indicators=['asset_removal', 'equipment_theft', 'physical_asset_compromise'],
                log_sources=['asset_logs', 'physical_logs', 'security_logs'],
                mitigation_controls=['asset_tracking', 'physical_controls', 'asset_monitoring']
            ),
            'ot_network_compromise': PillarAttackPattern(
                pillar=CyberdefensePillar.OT_PHYSICAL_SECURITY,
                attack_type='ot_network_compromise',
                severity=LogSeverity.HIGH,
                description='OT network compromise',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.1,
                indicators=['ot_network_breach', 'industrial_network_attack', 'ot_network_manipulation'],
                log_sources=['ot_network_logs', 'industrial_logs', 'network_logs'],
                mitigation_controls=['ot_network_security', 'industrial_protection', 'network_monitoring']
            ),
            'physical_surveillance_breach': PillarAttackPattern(
                pillar=CyberdefensePillar.OT_PHYSICAL_SECURITY,
                attack_type='physical_surveillance_breach',
                severity=LogSeverity.MEDIUM,
                description='Physical surveillance breach',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.1,
                indicators=['surveillance_compromise', 'camera_manipulation', 'physical_monitoring_breach'],
                log_sources=['surveillance_logs', 'camera_logs', 'physical_logs'],
                mitigation_controls=['surveillance_security', 'camera_protection', 'physical_monitoring']
            ),
            'ot_protocol_abuse': PillarAttackPattern(
                pillar=CyberdefensePillar.OT_PHYSICAL_SECURITY,
                attack_type='ot_protocol_abuse',
                severity=LogSeverity.MEDIUM,
                description='OT protocol abuse',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.05,
                indicators=['protocol_manipulation', 'ot_protocol_abuse', 'industrial_protocol_attack'],
                log_sources=['protocol_logs', 'ot_logs', 'industrial_logs'],
                mitigation_controls=['protocol_security', 'ot_monitoring', 'protocol_validation']
            )
        }
    
    def _get_normal_activities(self) -> List[str]:
        """Return list of normal OT/ICS & Physical Security activities."""
        return [
            "OT security monitoring",
            "Physical security assessment",
            "SCADA system security check",
            "Physical access control review",
            "OT network security scan",
            "Physical asset inventory",
            "OT security training",
            "Physical security policy update",
            "OT security audit",
            "Physical security metrics collection",
            "OT security tool configuration",
            "Physical security process improvement",
            "OT security risk assessment",
            "Physical security compliance check",
            "OT security awareness training",
            "Physical security governance review",
            "OT security certification",
            "Physical security monitoring",
            "OT security communication",
            "Physical security incident response"
        ]

