"""
SIEM Logs Generator for Priority Security Logs

This generator creates synthetic logs for all 13 SIEM priority categories
as defined in the National Cyber Security Agency guidance document.
"""

import random
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from faker import Faker

from .base_pillar_generator import BasePillarGenerator
from ..models import (
    CyberdefensePillar, LogEvent, LogSeverity, AttackTactic, 
    PillarAttackPattern, NetworkEndpoint, UserProfile, SecurityEvent
)

fake = Faker()


class SIEMLogsGenerator(BasePillarGenerator):
    """Generator for SIEM Priority Logs covering all 13 categories."""

    def get_pillar(self) -> CyberdefensePillar:
        return CyberdefensePillar.SIEM_LOGS

    def _setup_attack_patterns(self) -> Dict[str, PillarAttackPattern]:
        """Setup SIEM-specific attack patterns for all 13 categories."""
        return {
            # EDR Attack Patterns
            'edr_malware_detection': PillarAttackPattern(
                pillar=CyberdefensePillar.SIEM_LOGS,
                attack_type='edr_malware_detection',
                severity=LogSeverity.HIGH,
                description='EDR detected malware execution',
                tactic=AttackTactic.EXECUTION,
                weight=0.15,
                indicators=['malware_signature', 'suspicious_process', 'file_quarantine'],
                log_sources=['edr_logs', 'antivirus_logs', 'endpoint_security'],
                mitigation_controls=['quarantine_file', 'block_process', 'alert_security']
            ),
            
            # Network Attack Patterns
            'network_intrusion': PillarAttackPattern(
                pillar=CyberdefensePillar.SIEM_LOGS,
                attack_type='network_intrusion',
                severity=LogSeverity.HIGH,
                description='Network intrusion detected',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.12,
                indicators=['suspicious_traffic', 'port_scan', 'brute_force'],
                log_sources=['firewall_logs', 'ids_logs', 'network_logs'],
                mitigation_controls=['block_ip', 'rate_limiting', 'intrusion_prevention']
            ),
            
            # Active Directory Attack Patterns
            'ad_privilege_escalation': PillarAttackPattern(
                pillar=CyberdefensePillar.SIEM_LOGS,
                attack_type='ad_privilege_escalation',
                severity=LogSeverity.CRITICAL,
                description='Active Directory privilege escalation detected',
                tactic=AttackTactic.PRIVILEGE_ESCALATION,
                weight=0.10,
                indicators=['group_membership_change', 'privilege_assignment', 'dcsync'],
                log_sources=['ad_logs', 'domain_controller_logs', 'security_logs'],
                mitigation_controls=['revoke_privileges', 'audit_changes', 'alert_admins']
            ),
            
            # Windows Endpoint Attack Patterns
            'windows_persistence': PillarAttackPattern(
                pillar=CyberdefensePillar.SIEM_LOGS,
                attack_type='windows_persistence',
                severity=LogSeverity.HIGH,
                description='Windows persistence mechanism detected',
                tactic=AttackTactic.PERSISTENCE,
                weight=0.08,
                indicators=['scheduled_task_creation', 'service_installation', 'registry_modification'],
                log_sources=['windows_event_logs', 'sysmon_logs', 'security_logs'],
                mitigation_controls=['remove_persistence', 'monitor_changes', 'alert_security']
            ),
            
            # Cloud Attack Patterns
            'cloud_privilege_escalation': PillarAttackPattern(
                pillar=CyberdefensePillar.SIEM_LOGS,
                attack_type='cloud_privilege_escalation',
                severity=LogSeverity.HIGH,
                description='Cloud privilege escalation detected',
                tactic=AttackTactic.PRIVILEGE_ESCALATION,
                weight=0.07,
                indicators=['role_assignment', 'permission_change', 'service_principal_creation'],
                log_sources=['cloud_audit_logs', 'azure_logs', 'aws_cloudtrail'],
                mitigation_controls=['revoke_permissions', 'audit_roles', 'alert_cloud_admins']
            ),
            
            # Container Attack Patterns
            'container_escape': PillarAttackPattern(
                pillar=CyberdefensePillar.SIEM_LOGS,
                attack_type='container_escape',
                severity=LogSeverity.CRITICAL,
                description='Container escape attempt detected',
                tactic=AttackTactic.PRIVILEGE_ESCALATION,
                weight=0.05,
                indicators=['privilege_escalation', 'host_access', 'kernel_exploit'],
                log_sources=['container_logs', 'kubernetes_logs', 'docker_logs'],
                mitigation_controls=['isolate_container', 'update_runtime', 'alert_security']
            ),
            
            # Database Attack Patterns
            'database_injection': PillarAttackPattern(
                pillar=CyberdefensePillar.SIEM_LOGS,
                attack_type='database_injection',
                severity=LogSeverity.HIGH,
                description='Database injection attack detected',
                tactic=AttackTactic.INITIAL_ACCESS,
                weight=0.06,
                indicators=['sql_injection', 'unusual_queries', 'privilege_escalation'],
                log_sources=['database_logs', 'application_logs', 'audit_logs'],
                mitigation_controls=['block_query', 'parameterize_queries', 'alert_dba']
            ),
            
            # Mobile Device Attack Patterns
            'mobile_malware': PillarAttackPattern(
                pillar=CyberdefensePillar.SIEM_LOGS,
                attack_type='mobile_malware',
                severity=LogSeverity.MEDIUM,
                description='Mobile malware detected',
                tactic=AttackTactic.EXECUTION,
                weight=0.04,
                indicators=['suspicious_app', 'jailbreak_detection', 'data_exfiltration'],
                log_sources=['mdm_logs', 'mobile_security_logs', 'device_logs'],
                mitigation_controls=['quarantine_device', 'remove_app', 'alert_user']
            ),
            
            # DNS Attack Patterns
            'dns_tunneling': PillarAttackPattern(
                pillar=CyberdefensePillar.SIEM_LOGS,
                attack_type='dns_tunneling',
                severity=LogSeverity.HIGH,
                description='DNS tunneling detected',
                tactic=AttackTactic.COMMAND_AND_CONTROL,
                weight=0.03,
                indicators=['unusual_dns_queries', 'data_exfiltration', 'c2_communication'],
                log_sources=['dns_logs', 'network_logs', 'security_logs'],
                mitigation_controls=['block_domain', 'monitor_dns', 'alert_security']
            ),
            
            # Linux Attack Patterns
            'linux_privilege_escalation': PillarAttackPattern(
                pillar=CyberdefensePillar.SIEM_LOGS,
                attack_type='linux_privilege_escalation',
                severity=LogSeverity.HIGH,
                description='Linux privilege escalation detected',
                tactic=AttackTactic.PRIVILEGE_ESCALATION,
                weight=0.05,
                indicators=['sudo_abuse', 'suid_exploitation', 'kernel_exploit'],
                log_sources=['linux_audit_logs', 'syslog', 'security_logs'],
                mitigation_controls=['revoke_privileges', 'patch_system', 'alert_admins']
            ),
            
            # macOS Attack Patterns
            'macos_persistence': PillarAttackPattern(
                pillar=CyberdefensePillar.SIEM_LOGS,
                attack_type='macos_persistence',
                severity=LogSeverity.MEDIUM,
                description='macOS persistence mechanism detected',
                tactic=AttackTactic.PERSISTENCE,
                weight=0.03,
                indicators=['launchd_modification', 'kernel_extension', 'scheduled_task'],
                log_sources=['macos_logs', 'unified_logs', 'security_logs'],
                mitigation_controls=['remove_persistence', 'monitor_changes', 'alert_user']
            )
        }

    def _get_normal_activities(self) -> List[str]:
        """Return list of normal SIEM activities across all categories."""
        return [
            # EDR Normal Activities
            "Successful antivirus scan completed",
            "Endpoint health check passed",
            "Security policy applied successfully",
            "User login from authorized device",
            "File access from trusted application",
            
            # Network Normal Activities
            "Firewall rule applied successfully",
            "VPN connection established",
            "Network traffic within normal parameters",
            "DNS resolution successful",
            "Load balancer health check passed",
            
            # Active Directory Normal Activities
            "User authentication successful",
            "Group policy applied",
            "Password change completed",
            "Account lockout policy enforced",
            "Domain controller replication successful",
            
            # Windows Endpoint Normal Activities
            "Windows update installed",
            "Service started successfully",
            "Scheduled task executed",
            "Registry backup completed",
            "System integrity check passed",
            
            # Cloud Normal Activities
            "Cloud resource created",
            "IAM policy applied",
            "Storage access granted",
            "API call successful",
            "Cloud backup completed",
            
            # Container Normal Activities
            "Container started successfully",
            "Pod scheduled on node",
            "Image pulled from registry",
            "Service endpoint created",
            "Health check passed",
            
            # Database Normal Activities
            "Database connection established",
            "Query executed successfully",
            "Backup completed",
            "User session created",
            "Transaction committed",
            
            # Mobile Device Normal Activities
            "Device enrolled successfully",
            "App installed from store",
            "Policy applied to device",
            "Certificate installed",
            "Device compliance check passed",
            
            # DNS Normal Activities
            "DNS query resolved",
            "Cache updated",
            "Zone transfer completed",
            "Record updated",
            "Query rate within limits",
            
            # Linux Normal Activities
            "SSH connection established",
            "Package installed",
            "Service restarted",
            "Log rotation completed",
            "System update applied",
            
            # macOS Normal Activities
            "Application launched",
            "System preference updated",
            "Keychain access granted",
            "File system check passed",
            "Time machine backup completed"
        ]

    def _generate_edr_log(self) -> LogEvent:
        """Generate EDR (Endpoint Detection and Response) log."""
        log_types = [
            "antivirus_detection", "process_creation", "file_access", 
            "network_connection", "registry_modification", "scheduled_task"
        ]
        
        log_type = random.choice(log_types)
        
        if log_type == "antivirus_detection":
            message = f"Antivirus detected {random.choice(['malware', 'suspicious file', 'trojan', 'virus'])}: {fake.file_path()}"
            severity = LogSeverity.HIGH
        elif log_type == "process_creation":
            message = f"Process created: {fake.word()}.exe (PID: {random.randint(1000, 9999)}) by user {fake.user_name()}"
            severity = LogSeverity.MEDIUM
        elif log_type == "file_access":
            message = f"File accessed: {fake.file_path()} by process {fake.word()}.exe"
            severity = LogSeverity.LOW
        elif log_type == "network_connection":
            message = f"Network connection: {fake.ipv4()}:{random.randint(1, 65535)} -> {fake.ipv4()}:{random.randint(1, 65535)}"
            severity = LogSeverity.MEDIUM
        elif log_type == "registry_modification":
            message = f"Registry modified: {fake.word()}\\{fake.word()}\\{fake.word()}"
            severity = LogSeverity.MEDIUM
        else:  # scheduled_task
            message = f"Scheduled task created: {fake.word()} by {fake.user_name()}"
            severity = LogSeverity.MEDIUM

        return LogEvent(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            log_type=log_type,
            severity=severity,
            source=NetworkEndpoint(
                ip_address=fake.ipv4(),
                hostname=fake.hostname(),
                port=random.randint(1, 65535)
            ),
            destination=NetworkEndpoint(
                ip_address=fake.ipv4(),
                hostname=fake.hostname(),
                port=random.randint(1, 65535)
            ),
            user=fake.user_name(),
            message=message,
            raw_data={
                "edr_vendor": random.choice(["CrowdStrike", "SentinelOne", "Carbon Black", "Microsoft Defender"]),
                "threat_score": random.randint(1, 100),
                "file_hash": fake.sha256(),
                "process_id": random.randint(1000, 9999),
                "parent_process": fake.word() + ".exe"
            },
            tags=["edr", "endpoint", "security"]
        )

    def _generate_network_device_log(self) -> LogEvent:
        """Generate network device log."""
        device_types = ["firewall", "router", "switch", "ids", "ips", "proxy", "vpn"]
        device_type = random.choice(device_types)
        
        if device_type == "firewall":
            actions = ["ALLOW", "DENY", "DROP"]
            action = random.choice(actions)
            message = f"Firewall {action}: {fake.ipv4()} -> {fake.ipv4()} port {random.randint(1, 65535)}"
            severity = LogSeverity.HIGH if action == "DENY" else LogSeverity.MEDIUM
        elif device_type == "router":
            message = f"Routing table updated: {fake.ipv4()}/{random.randint(8, 30)} via {fake.ipv4()}"
            severity = LogSeverity.MEDIUM
        elif device_type == "switch":
            message = f"Port {random.randint(1, 48)} status changed: {random.choice(['UP', 'DOWN'])}"
            severity = LogSeverity.LOW
        elif device_type in ["ids", "ips"]:
            message = f"Intrusion {random.choice(['detected', 'prevented'])}: {fake.word()} attack from {fake.ipv4()}"
            severity = LogSeverity.HIGH
        elif device_type == "proxy":
            message = f"Proxy request: {fake.user_name()} -> {fake.url()}"
            severity = LogSeverity.MEDIUM
        else:  # vpn
            message = f"VPN connection: {fake.user_name()} from {fake.ipv4()}"
            severity = LogSeverity.MEDIUM

        return LogEvent(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            log_type=f"{device_type}_log",
            severity=severity,
            source=NetworkEndpoint(
                ip_address=fake.ipv4(),
                hostname=fake.hostname()
            ),
            destination=NetworkEndpoint(
                ip_address=fake.ipv4(),
                hostname=fake.hostname()
            ),
            user=fake.user_name() if device_type in ["proxy", "vpn"] else None,
            message=message,
            raw_data={
                "device_type": device_type,
                "vendor": random.choice(["Cisco", "Juniper", "Fortinet", "Palo Alto", "Check Point"]),
                "interface": f"eth{random.randint(0, 10)}",
                "protocol": random.choice(["TCP", "UDP", "ICMP", "HTTP", "HTTPS"]),
                "bytes": random.randint(64, 1500)
            },
            tags=["network", device_type, "security"]
        )

    def _generate_ad_log(self) -> LogEvent:
        """Generate Active Directory log."""
        event_ids = [4624, 4625, 4634, 4648, 4768, 4769, 4776, 4720, 4722, 4723, 4724, 4725, 4726]
        event_id = random.choice(event_ids)
        
        if event_id == 4624:  # Successful logon
            message = f"Successful logon: {fake.user_name()} from {fake.ipv4()}"
            severity = LogSeverity.LOW
        elif event_id == 4625:  # Failed logon
            message = f"Failed logon: {fake.user_name()} from {fake.ipv4()} - {random.choice(['Invalid password', 'Account locked', 'Account disabled'])}"
            severity = LogSeverity.HIGH
        elif event_id == 4634:  # Logoff
            message = f"Logoff: {fake.user_name()} from {fake.ipv4()}"
            severity = LogSeverity.LOW
        elif event_id == 4648:  # Logon with explicit credentials
            message = f"Logon with explicit credentials: {fake.user_name()} using {fake.user_name()}"
            severity = LogSeverity.MEDIUM
        elif event_id == 4768:  # Kerberos authentication
            message = f"Kerberos authentication: {fake.user_name()} for {fake.word()}"
            severity = LogSeverity.MEDIUM
        elif event_id == 4769:  # Kerberos service ticket
            message = f"Kerberos service ticket: {fake.user_name()} for {fake.word()}"
            severity = LogSeverity.MEDIUM
        elif event_id == 4776:  # Credential validation
            message = f"Credential validation: {fake.user_name()} from {fake.ipv4()}"
            severity = LogSeverity.MEDIUM
        elif event_id == 4720:  # User account created
            message = f"User account created: {fake.user_name()}"
            severity = LogSeverity.MEDIUM
        elif event_id == 4722:  # User account enabled
            message = f"User account enabled: {fake.user_name()}"
            severity = LogSeverity.MEDIUM
        elif event_id == 4723:  # Password change attempt
            message = f"Password change attempt: {fake.user_name()}"
            severity = LogSeverity.MEDIUM
        elif event_id == 4724:  # Password reset
            message = f"Password reset: {fake.user_name()}"
            severity = LogSeverity.HIGH
        elif event_id == 4725:  # User account disabled
            message = f"User account disabled: {fake.user_name()}"
            severity = LogSeverity.MEDIUM
        elif event_id == 4726:  # User account deleted
            message = f"User account deleted: {fake.user_name()}"
            severity = LogSeverity.HIGH

        return LogEvent(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            log_type="ad_security_log",
            severity=severity,
            source=NetworkEndpoint(
                ip_address=fake.ipv4(),
                hostname=fake.hostname()
            ),
            destination=NetworkEndpoint(
                ip_address=fake.ipv4(),
                hostname=f"DC-{fake.word()}"
            ),
            user=fake.user_name(),
            message=message,
            raw_data={
                "event_id": event_id,
                "domain": fake.word() + ".local",
                "logon_type": random.randint(2, 11),
                "authentication_package": random.choice(["Kerberos", "NTLM", "Negotiate"]),
                "workstation_name": fake.hostname(),
                "source_port": random.randint(1024, 65535)
            },
            tags=["active_directory", "security", "authentication"]
        )

    def _generate_windows_endpoint_log(self) -> LogEvent:
        """Generate Windows endpoint log."""
        log_sources = ["security", "system", "application", "sysmon", "powershell", "wmi"]
        log_source = random.choice(log_sources)
        
        if log_source == "security":
            event_ids = [4624, 4625, 4634, 4648, 4672, 4673, 4688, 4689, 4698, 4702]
            event_id = random.choice(event_ids)
            message = f"Security Event {event_id}: {fake.sentence()}"
            severity = LogSeverity.HIGH if event_id in [4625, 4673] else LogSeverity.MEDIUM
        elif log_source == "system":
            message = f"System Event: {random.choice(['Service started', 'Service stopped', 'Driver loaded', 'System startup'])}"
            severity = LogSeverity.LOW
        elif log_source == "application":
            message = f"Application Event: {fake.word()} application {random.choice(['started', 'stopped', 'crashed', 'updated'])}"
            severity = LogSeverity.MEDIUM
        elif log_source == "sysmon":
            event_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26]
            event_id = random.choice(event_ids)
            message = f"Sysmon Event {event_id}: {fake.sentence()}"
            severity = LogSeverity.MEDIUM
        elif log_source == "powershell":
            message = f"PowerShell: {fake.word()} script executed by {fake.user_name()}"
            severity = LogSeverity.MEDIUM
        else:  # wmi
            message = f"WMI Event: {fake.word()} operation performed"
            severity = LogSeverity.LOW

        return LogEvent(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            log_type=f"windows_{log_source}",
            severity=severity,
            source=NetworkEndpoint(
                ip_address=fake.ipv4(),
                hostname=fake.hostname()
            ),
            destination=None,
            user=fake.user_name(),
            message=message,
            raw_data={
                "log_source": log_source,
                "computer_name": fake.hostname(),
                "process_id": random.randint(1000, 9999),
                "thread_id": random.randint(1000, 9999),
                "session_id": random.randint(1, 10)
            },
            tags=["windows", log_source, "endpoint"]
        )

    def _generate_cloud_log(self) -> LogEvent:
        """Generate cloud platform log."""
        cloud_providers = ["aws", "azure", "gcp", "office365"]
        provider = random.choice(cloud_providers)
        
        if provider == "aws":
            services = ["ec2", "s3", "iam", "cloudtrail", "vpc", "lambda"]
            service = random.choice(services)
            message = f"AWS {service.upper()}: {fake.sentence()}"
            severity = LogSeverity.MEDIUM
        elif provider == "azure":
            services = ["entra", "storage", "compute", "network", "security"]
            service = random.choice(services)
            message = f"Azure {service.title()}: {fake.sentence()}"
            severity = LogSeverity.MEDIUM
        elif provider == "gcp":
            services = ["compute", "storage", "iam", "network", "security"]
            service = random.choice(services)
            message = f"GCP {service.title()}: {fake.sentence()}"
            severity = LogSeverity.MEDIUM
        else:  # office365
            services = ["exchange", "sharepoint", "teams", "onedrive"]
            service = random.choice(services)
            message = f"Office 365 {service.title()}: {fake.sentence()}"
            severity = LogSeverity.MEDIUM

        return LogEvent(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            log_type=f"cloud_{provider}",
            severity=severity,
            source=NetworkEndpoint(
                ip_address=fake.ipv4(),
                hostname=fake.hostname()
            ),
            destination=NetworkEndpoint(
                ip_address=fake.ipv4(),
                hostname=f"{provider}.com"
            ),
            user=fake.user_name(),
            message=message,
            raw_data={
                "cloud_provider": provider,
                "service": service,
                "region": random.choice(["us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1"]),
                "resource_id": f"res-{fake.uuid4()}",
                "api_version": f"v{random.randint(1, 3)}.{random.randint(0, 9)}"
            },
            tags=["cloud", provider, service]
        )

    def _generate_container_log(self) -> LogEvent:
        """Generate container log."""
        container_events = ["container_start", "container_stop", "image_pull", "pod_create", "service_create"]
        event_type = random.choice(container_events)
        
        if event_type == "container_start":
            message = f"Container started: {fake.word()}:{fake.word()} (ID: {fake.uuid4()[:8]})"
            severity = LogSeverity.LOW
        elif event_type == "container_stop":
            message = f"Container stopped: {fake.word()}:{fake.word()} (ID: {fake.uuid4()[:8]})"
            severity = LogSeverity.LOW
        elif event_type == "image_pull":
            message = f"Image pulled: {fake.word()}/{fake.word()}:{fake.word()}"
            severity = LogSeverity.LOW
        elif event_type == "pod_create":
            message = f"Pod created: {fake.word()}-{fake.word()} in namespace {fake.word()}"
            severity = LogSeverity.MEDIUM
        else:  # service_create
            message = f"Service created: {fake.word()}-service in namespace {fake.word()}"
            severity = LogSeverity.MEDIUM

        return LogEvent(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            log_type="container_log",
            severity=severity,
            source=NetworkEndpoint(
                ip_address=fake.ipv4(),
                hostname=fake.hostname()
            ),
            destination=None,
            user=fake.user_name(),
            message=message,
            raw_data={
                "container_runtime": random.choice(["docker", "containerd", "cri-o"]),
                "orchestrator": random.choice(["kubernetes", "docker-swarm", "nomad"]),
                "namespace": fake.word(),
                "pod_name": f"{fake.word()}-{fake.word()}",
                "container_name": fake.word(),
                "image": f"{fake.word()}/{fake.word()}:{fake.word()}"
            },
            tags=["container", "orchestration", "cloud-native"]
        )

    def _generate_database_log(self) -> LogEvent:
        """Generate database log."""
        db_types = ["mysql", "postgresql", "oracle", "sqlserver", "mongodb"]
        db_type = random.choice(db_types)
        
        operations = ["SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER", "GRANT", "REVOKE"]
        operation = random.choice(operations)
        
        if operation in ["INSERT", "UPDATE", "DELETE"]:
            message = f"Database {operation}: {fake.word()}.{fake.word()} by {fake.user_name()}"
            severity = LogSeverity.MEDIUM
        elif operation in ["CREATE", "DROP", "ALTER"]:
            message = f"Database {operation}: {fake.word()} by {fake.user_name()}"
            severity = LogSeverity.HIGH
        elif operation in ["GRANT", "REVOKE"]:
            message = f"Database {operation}: {fake.word()} to {fake.user_name()}"
            severity = LogSeverity.HIGH
        else:  # SELECT
            message = f"Database {operation}: {fake.word()}.{fake.word()} by {fake.user_name()}"
            severity = LogSeverity.LOW

        return LogEvent(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            log_type=f"database_{db_type}",
            severity=severity,
            source=NetworkEndpoint(
                ip_address=fake.ipv4(),
                hostname=fake.hostname()
            ),
            destination=NetworkEndpoint(
                ip_address=fake.ipv4(),
                hostname=f"db-{fake.word()}"
            ),
            user=fake.user_name(),
            message=message,
            raw_data={
                "database_type": db_type,
                "operation": operation,
                "table_name": fake.word(),
                "schema": fake.word(),
                "query_time": random.uniform(0.001, 10.0),
                "rows_affected": random.randint(0, 1000)
            },
            tags=["database", db_type, "sql"]
        )

    def _generate_mobile_device_log(self) -> LogEvent:
        """Generate mobile device management log."""
        device_events = ["device_enroll", "app_install", "policy_apply", "compliance_check", "threat_detection"]
        event_type = random.choice(device_events)
        
        if event_type == "device_enroll":
            message = f"Device enrolled: {fake.word()} {fake.word()} (iOS {random.randint(14, 17)}.{random.randint(0, 9)})"
            severity = LogSeverity.LOW
        elif event_type == "app_install":
            message = f"App installed: {fake.word()} by {fake.user_name()}"
            severity = LogSeverity.LOW
        elif event_type == "policy_apply":
            message = f"Policy applied: {fake.word()} policy to device {fake.word()}"
            severity = LogSeverity.MEDIUM
        elif event_type == "compliance_check":
            message = f"Compliance check: Device {fake.word()} - {random.choice(['Compliant', 'Non-compliant'])}"
            severity = LogSeverity.MEDIUM
        else:  # threat_detection
            message = f"Threat detected: {random.choice(['Malware', 'Suspicious app', 'Jailbreak'])} on device {fake.word()}"
            severity = LogSeverity.HIGH

        return LogEvent(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            log_type="mobile_device",
            severity=severity,
            source=NetworkEndpoint(
                ip_address=fake.ipv4(),
                hostname=fake.hostname()
            ),
            destination=None,
            user=fake.user_name(),
            message=message,
            raw_data={
                "device_type": random.choice(["iPhone", "Android", "iPad", "Windows Mobile"]),
                "os_version": f"{random.randint(10, 17)}.{random.randint(0, 9)}",
                "device_id": fake.uuid4(),
                "mdm_vendor": random.choice(["Microsoft Intune", "VMware Workspace ONE", "Jamf", "MobileIron"]),
                "app_name": fake.word(),
                "policy_name": fake.word()
            },
            tags=["mobile", "mdm", "device_management"]
        )

    def _generate_dns_log(self) -> LogEvent:
        """Generate DNS server log."""
        dns_events = ["query", "response", "zone_transfer", "update", "cache"]
        event_type = random.choice(dns_events)
        
        if event_type == "query":
            message = f"DNS Query: {fake.domain_name()} {random.choice(['A', 'AAAA', 'MX', 'CNAME', 'TXT'])} from {fake.ipv4()}"
            severity = LogSeverity.LOW
        elif event_type == "response":
            message = f"DNS Response: {fake.domain_name()} -> {fake.ipv4()} (TTL: {random.randint(300, 86400)})"
            severity = LogSeverity.LOW
        elif event_type == "zone_transfer":
            message = f"Zone Transfer: {fake.domain_name()} to {fake.ipv4()}"
            severity = LogSeverity.MEDIUM
        elif event_type == "update":
            message = f"DNS Update: {fake.domain_name()} {random.choice(['A', 'AAAA', 'MX'])} record"
            severity = LogSeverity.MEDIUM
        else:  # cache
            message = f"DNS Cache: {fake.domain_name()} cached for {random.randint(300, 86400)} seconds"
            severity = LogSeverity.LOW

        return LogEvent(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            log_type="dns_server",
            severity=severity,
            source=NetworkEndpoint(
                ip_address=fake.ipv4(),
                hostname=fake.hostname()
            ),
            destination=NetworkEndpoint(
                ip_address=fake.ipv4(),
                hostname=f"dns-{fake.word()}"
            ),
            user=None,
            message=message,
            raw_data={
                "query_type": random.choice(["A", "AAAA", "MX", "CNAME", "TXT", "NS", "SOA"]),
                "response_code": random.choice([0, 1, 2, 3, 4, 5]),
                "ttl": random.randint(300, 86400),
                "zone": fake.domain_name(),
                "recursive": random.choice([True, False])
            },
            tags=["dns", "network", "infrastructure"]
        )

    def _generate_linux_log(self) -> LogEvent:
        """Generate Linux endpoint audit log."""
        audit_events = ["user_login", "sudo_command", "file_access", "process_exec", "network_connection"]
        event_type = random.choice(audit_events)
        
        if event_type == "user_login":
            message = f"User login: {fake.user_name()} from {fake.ipv4()} via {random.choice(['ssh', 'console', 'tty'])}"
            severity = LogSeverity.LOW
        elif event_type == "sudo_command":
            message = f"Sudo command: {fake.user_name()} executed {fake.word()} as {fake.user_name()}"
            severity = LogSeverity.MEDIUM
        elif event_type == "file_access":
            message = f"File access: {fake.file_path()} by {fake.user_name()}"
            severity = LogSeverity.LOW
        elif event_type == "process_exec":
            message = f"Process execution: {fake.word()} by {fake.user_name()}"
            severity = LogSeverity.LOW
        else:  # network_connection
            message = f"Network connection: {fake.ipv4()}:{random.randint(1, 65535)} -> {fake.ipv4()}:{random.randint(1, 65535)}"
            severity = LogSeverity.MEDIUM

        return LogEvent(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            log_type="linux_audit",
            severity=severity,
            source=NetworkEndpoint(
                ip_address=fake.ipv4(),
                hostname=fake.hostname()
            ),
            destination=NetworkEndpoint(
                ip_address=fake.ipv4(),
                hostname=fake.hostname()
            ),
            user=fake.user_name(),
            message=message,
            raw_data={
                "audit_type": event_type,
                "pid": random.randint(1000, 9999),
                "ppid": random.randint(1000, 9999),
                "session_id": random.randint(1, 10),
                "command": fake.word(),
                "exit_code": random.randint(0, 255)
            },
            tags=["linux", "audit", "security"]
        )

    def _generate_macos_log(self) -> LogEvent:
        """Generate macOS endpoint log."""
        macos_events = ["app_launch", "file_access", "network_connection", "system_event", "security_event"]
        event_type = random.choice(macos_events)
        
        if event_type == "app_launch":
            message = f"Application launched: {fake.word()} by {fake.user_name()}"
            severity = LogSeverity.LOW
        elif event_type == "file_access":
            message = f"File access: {fake.file_path()} by {fake.word()}"
            severity = LogSeverity.LOW
        elif event_type == "network_connection":
            message = f"Network connection: {fake.ipv4()}:{random.randint(1, 65535)} -> {fake.ipv4()}:{random.randint(1, 65535)}"
            severity = LogSeverity.MEDIUM
        elif event_type == "system_event":
            message = f"System event: {random.choice(['Kernel extension loaded', 'Service started', 'Update installed'])}"
            severity = LogSeverity.LOW
        else:  # security_event
            message = f"Security event: {random.choice(['Gatekeeper blocked', 'XProtect detected', 'Certificate validation'])}"
            severity = LogSeverity.MEDIUM

        return LogEvent(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            log_type="macos_log",
            severity=severity,
            source=NetworkEndpoint(
                ip_address=fake.ipv4(),
                hostname=fake.hostname()
            ),
            destination=NetworkEndpoint(
                ip_address=fake.ipv4(),
                hostname=fake.hostname()
            ),
            user=fake.user_name(),
            message=message,
            raw_data={
                "subsystem": random.choice(["com.apple.security", "com.apple.network", "com.apple.system"]),
                "category": random.choice(["default", "info", "debug", "error"]),
                "process": fake.word(),
                "pid": random.randint(1000, 9999),
                "thread_id": random.randint(1000, 9999)
            },
            tags=["macos", "apple", "security"]
        )

    def generate_event(self, **kwargs) -> SecurityEvent:
        """Generate a single SIEM security event."""
        # Select category based on weights
        category_weights = {
            'edr': 0.20,           # 20% - EDR logs
            'network': 0.15,        # 15% - Network device logs
            'ad': 0.12,            # 12% - Active Directory logs
            'windows': 0.10,        # 10% - Windows endpoint logs
            'cloud': 0.08,          # 8% - Cloud logs
            'container': 0.06,      # 6% - Container logs
            'database': 0.05,       # 5% - Database logs
            'mobile': 0.04,         # 4% - Mobile device logs
            'dns': 0.05,            # 5% - DNS logs
            'linux': 0.08,          # 8% - Linux logs
            'macos': 0.04,          # 4% - macOS logs
            'virtualization': 0.02, # 2% - Virtualization logs
            'ot': 0.01              # 1% - OT logs
        }
        
        category = random.choices(
            list(category_weights.keys()),
            weights=list(category_weights.values()),
            k=1
        )[0]
        
        # Generate log based on category
        if category == 'edr':
            log = self._generate_edr_log()
        elif category == 'network':
            log = self._generate_network_device_log()
        elif category == 'ad':
            log = self._generate_ad_log()
        elif category == 'windows':
            log = self._generate_windows_endpoint_log()
        elif category == 'cloud':
            log = self._generate_cloud_log()
        elif category == 'container':
            log = self._generate_container_log()
        elif category == 'database':
            log = self._generate_database_log()
        elif category == 'mobile':
            log = self._generate_mobile_device_log()
        elif category == 'dns':
            log = self._generate_dns_log()
        elif category == 'linux':
            log = self._generate_linux_log()
        elif category == 'macos':
            log = self._generate_macos_log()
        else:
            # Fallback to EDR for virtualization and OT
            log = self._generate_edr_log()
            log.tags = [category, "infrastructure"]
        
        # Ensure the category tag is present
        if category not in log.tags:
            log.tags.append(category)
        
        # Convert LogEvent to SecurityEvent
        return SecurityEvent(
            id=log.id,
            timestamp=log.timestamp,
            pillar=self.get_pillar(),
            log_type=log.log_type,
            severity=log.severity,
            source=log.source,
            destination=log.destination,
            user=log.user,
            message=log.message,
            raw_data=log.raw_data,
            tags=log.tags,
            threat_actor=None,
            attack_tactic=None,
            attack_technique=None,
            ioc_type=None,
            ioc_value=None,
            confidence_score=None,
            false_positive_probability=None,
            correlation_id=None,
            campaign_id=None
        )

    def generate_logs(self, count: int = 100) -> List[LogEvent]:
        """Generate SIEM logs covering all 13 priority categories."""
        logs = []
        
        # Define category weights for realistic distribution
        category_weights = {
            'edr': 0.20,           # 20% - EDR logs
            'network': 0.15,        # 15% - Network device logs
            'ad': 0.12,            # 12% - Active Directory logs
            'windows': 0.10,        # 10% - Windows endpoint logs
            'cloud': 0.08,          # 8% - Cloud logs
            'container': 0.06,      # 6% - Container logs
            'database': 0.05,       # 5% - Database logs
            'mobile': 0.04,         # 4% - Mobile device logs
            'dns': 0.05,            # 5% - DNS logs
            'linux': 0.08,          # 8% - Linux logs
            'macos': 0.04,          # 4% - macOS logs
            'virtualization': 0.02, # 2% - Virtualization logs
            'ot': 0.01              # 1% - OT logs
        }
        
        for _ in range(count):
            # Select category based on weights
            category = random.choices(
                list(category_weights.keys()),
                weights=list(category_weights.values()),
                k=1
            )[0]
            
            # Generate log based on category
            if category == 'edr':
                log = self._generate_edr_log()
            elif category == 'network':
                log = self._generate_network_device_log()
            elif category == 'ad':
                log = self._generate_ad_log()
            elif category == 'windows':
                log = self._generate_windows_endpoint_log()
            elif category == 'cloud':
                log = self._generate_cloud_log()
            elif category == 'container':
                log = self._generate_container_log()
            elif category == 'database':
                log = self._generate_database_log()
            elif category == 'mobile':
                log = self._generate_mobile_device_log()
            elif category == 'dns':
                log = self._generate_dns_log()
            elif category == 'linux':
                log = self._generate_linux_log()
            elif category == 'macos':
                log = self._generate_macos_log()
            else:
                # Fallback to EDR for virtualization and OT
                log = self._generate_edr_log()
                log.tags = [category, "infrastructure"]
            
            # Ensure the category tag is present
            if category not in log.tags:
                log.tags.append(category)
            
            logs.append(log)
        
        return logs
