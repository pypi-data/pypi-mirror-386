"""
Network Security pillar generator.
"""

from typing import Dict, Any, List
from ..models import CyberdefensePillar, LogSeverity, AttackTactic, PillarAttackPattern
from .base_pillar_generator import BasePillarGenerator


class NetworkSecurityGenerator(BasePillarGenerator):
    """Generator for Network Security pillar."""
    
    def get_pillar(self) -> CyberdefensePillar:
        return CyberdefensePillar.NETWORK_SECURITY
    
    def _setup_attack_patterns(self) -> Dict[str, PillarAttackPattern]:
        """Setup network security attack patterns."""
        return {
            'ddos_attack': PillarAttackPattern(
                pillar=CyberdefensePillar.NETWORK_SECURITY,
                attack_type='ddos_attack',
                severity=LogSeverity.HIGH,
                description='Distributed Denial of Service attack',
                tactic=AttackTactic.IMPACT,
                weight=0.2,
                indicators=['traffic_flooding', 'resource_exhaustion', 'service_unavailability'],
                log_sources=['network_logs', 'firewall_logs', 'traffic_logs'],
                mitigation_controls=['ddos_protection', 'traffic_filtering', 'network_monitoring']
            ),
            'network_intrusion': PillarAttackPattern(
                pillar=CyberdefensePillar.NETWORK_SECURITY,
                attack_type='network_intrusion',
                severity=LogSeverity.HIGH,
                description='Network intrusion attack',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.2,
                indicators=['unauthorized_access', 'network_breach', 'intrusion_attempts'],
                log_sources=['network_logs', 'ids_logs', 'security_logs'],
                mitigation_controls=['network_segmentation', 'intrusion_detection', 'access_controls']
            ),
            'man_in_the_middle': PillarAttackPattern(
                pillar=CyberdefensePillar.NETWORK_SECURITY,
                attack_type='man_in_the_middle',
                severity=LogSeverity.HIGH,
                description='Man-in-the-middle attack',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.15,
                indicators=['traffic_interception', 'certificate_spoofing', 'session_hijacking'],
                log_sources=['network_logs', 'ssl_logs', 'security_logs'],
                mitigation_controls=['certificate_pinning', 'encrypted_communications', 'network_monitoring']
            ),
            'network_scanning': PillarAttackPattern(
                pillar=CyberdefensePillar.NETWORK_SECURITY,
                attack_type='network_scanning',
                severity=LogSeverity.MEDIUM,
                description='Network reconnaissance scanning',
                tactic=AttackTactic.RECONNAISSANCE,
                weight=0.15,
                indicators=['port_scanning', 'service_enumeration', 'network_discovery'],
                log_sources=['network_logs', 'firewall_logs', 'ids_logs'],
                mitigation_controls=['network_monitoring', 'intrusion_detection', 'access_controls']
            ),
            'vlan_hopping': PillarAttackPattern(
                pillar=CyberdefensePillar.NETWORK_SECURITY,
                attack_type='vlan_hopping',
                severity=LogSeverity.HIGH,
                description='VLAN hopping attack',
                tactic=AttackTactic.LATERAL_MOVEMENT,
                weight=0.1,
                indicators=['vlan_manipulation', 'network_segmentation_bypass', 'lateral_movement'],
                log_sources=['network_logs', 'switch_logs', 'security_logs'],
                mitigation_controls=['vlan_security', 'network_segmentation', 'switch_monitoring']
            ),
            'dns_poisoning': PillarAttackPattern(
                pillar=CyberdefensePillar.NETWORK_SECURITY,
                attack_type='dns_poisoning',
                severity=LogSeverity.HIGH,
                description='DNS cache poisoning attack',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.1,
                indicators=['dns_manipulation', 'cache_poisoning', 'dns_redirection'],
                log_sources=['dns_logs', 'network_logs', 'security_logs'],
                mitigation_controls=['dns_security', 'dns_monitoring', 'dns_validation']
            ),
            'network_protocol_abuse': PillarAttackPattern(
                pillar=CyberdefensePillar.NETWORK_SECURITY,
                attack_type='network_protocol_abuse',
                severity=LogSeverity.MEDIUM,
                description='Network protocol abuse',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.1,
                indicators=['protocol_manipulation', 'protocol_abuse', 'network_anomalies'],
                log_sources=['network_logs', 'protocol_logs', 'security_logs'],
                mitigation_controls=['protocol_monitoring', 'network_analysis', 'protocol_validation']
            )
        }
    
    def _get_normal_activities(self) -> List[str]:
        """Return list of normal network security activities."""
        return [
            "Network security monitoring",
            "Firewall rule review",
            "Network vulnerability scan",
            "Network traffic analysis",
            "Network security assessment",
            "Network incident response",
            "Network security training",
            "Network security policy update",
            "Network security audit",
            "Network security metrics collection",
            "Network security tool configuration",
            "Network security process improvement",
            "Network security risk assessment",
            "Network security compliance check",
            "Network security awareness training",
            "Network security governance review",
            "Network security certification",
            "Network security monitoring",
            "Network security communication",
            "Network security incident response"
        ]

