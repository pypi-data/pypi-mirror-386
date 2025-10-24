"""
Main cybersecurity log generator class.
Orchestrates all log generators and provides unified interface.
"""

from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
import asyncio
import json
import yaml
import random
from pathlib import Path

from .models import (
    LogEvent, SecurityEvent, AttackCampaign, GeneratorConfig, 
    LogType, ThreatActor, NetworkTopology, UserProfile
)
from .generators import (
    IDSLogGenerator, WebAccessLogGenerator, EndpointLogGenerator,
    WindowsEventLogGenerator, LinuxSyslogGenerator, FirewallLogGenerator
)


class LogGenerator:
    """Main cybersecurity log generator with advanced capabilities."""
    
    def __init__(self, config: Optional[Union[Dict[str, Any], str, Path]] = None):
        """Initialize the log generator with configuration."""
        self.config = self._load_config(config)
        self._setup_generators()
        self._setup_attack_patterns()
    
    def _load_config(self, config) -> GeneratorConfig:
        """Load configuration from various sources."""
        if config is None:
            return GeneratorConfig()
        elif isinstance(config, str):
            if config.endswith(('.yaml', '.yml')):
                with open(config, 'r') as f:
                    config_dict = yaml.safe_load(f)
                return GeneratorConfig(**config_dict)
            else:
                config_dict = json.loads(config)
                return GeneratorConfig(**config_dict)
        elif isinstance(config, Path):
            with open(config, 'r') as f:
                config_dict = yaml.safe_load(f)
            return GeneratorConfig(**config_dict)
        elif isinstance(config, dict):
            return GeneratorConfig(**config)
        else:
            return GeneratorConfig()
    
    def _setup_generators(self):
        """Setup all log generators."""
        self.generators = {
            LogType.IDS: IDSLogGenerator(self.config.model_dump()),
            LogType.WEB_ACCESS: WebAccessLogGenerator(self.config.model_dump()),
            LogType.ENDPOINT: EndpointLogGenerator(self.config.model_dump()),
            LogType.WINDOWS_EVENT: WindowsEventLogGenerator(self.config.model_dump()),
            LogType.LINUX_SYSLOG: LinuxSyslogGenerator(self.config.model_dump()),
            LogType.FIREWALL: FirewallLogGenerator(self.config.model_dump()),
        }
    
    def _setup_attack_patterns(self):
        """Setup attack patterns and threat intelligence."""
        self.threat_actors = {
            ThreatActor.APT29: {
                'sophistication': 'high',
                'tactics': ['initial_access', 'persistence', 'exfiltration'],
                'targets': ['government', 'healthcare', 'finance']
            },
            ThreatActor.APT28: {
                'sophistication': 'high', 
                'tactics': ['execution', 'lateral_movement', 'collection'],
                'targets': ['government', 'military', 'energy']
            },
            ThreatActor.LAZARUS: {
                'sophistication': 'medium',
                'tactics': ['initial_access', 'exfiltration'],
                'targets': ['finance', 'cryptocurrency']
            }
        }
    
    def generate_logs(self, log_type: LogType, count: int = 1000, 
                    time_range: str = "24h", **kwargs) -> List[SecurityEvent]:
        """Generate logs of specified type."""
        generator = self.generators.get(log_type)
        if not generator:
            raise ValueError(f"Unsupported log type: {log_type}")
        
        return generator.generate_events(count=count, **kwargs)
    
    def generate_security_campaign(self, threat_actor: ThreatActor, 
                                 duration: str = "24h", target_count: int = 50,
                                 **kwargs) -> AttackCampaign:
        """Generate a coordinated attack campaign."""
        # Parse duration
        duration_hours = self._parse_duration(duration)
        
        # Get threat actor info
        actor_info = self.threat_actors.get(threat_actor, {})
        tactics = actor_info.get('tactics', ['initial_access', 'execution'])
        
        # Generate campaign events
        events = []
        start_time = datetime.utcnow()
        
        # Generate events for each tactic
        for tactic in tactics:
            tactic_events = self._generate_tactic_events(
                threat_actor, tactic, duration_hours, target_count // len(tactics)
            )
            events.extend(tactic_events)
        
        # Sort events by timestamp
        events.sort(key=lambda x: x.timestamp)
        
        # Create campaign
        campaign = AttackCampaign(
            threat_actor=threat_actor,
            start_time=start_time,
            duration=duration,
            target_count=target_count,
            events=events,
            description=f"{threat_actor} attack campaign",
            objectives=tactics
        )
        
        return campaign
    
    def generate_correlated_events(self, log_types: List[LogType], 
                                 correlation_strength: float = 0.8,
                                 time_window: str = "1h", **kwargs) -> List[SecurityEvent]:
        """Generate correlated events across multiple log types."""
        events = []
        time_window_hours = self._parse_duration(time_window)
        
        # Generate base events
        for log_type in log_types:
            base_events = self.generate_logs(log_type, count=100, **kwargs)
            events.extend(base_events)
        
        # Add correlation
        if correlation_strength > 0:
            correlated_events = self._add_correlation(events, correlation_strength, time_window_hours)
            events.extend(correlated_events)
        
        return sorted(events, key=lambda x: x.timestamp)
    
    def generate_network_topology_events(self, topology: NetworkTopology, 
                                       event_count: int = 1000) -> List[SecurityEvent]:
        """Generate events based on network topology."""
        events = []
        
        # Generate events for each subnet
        for subnet in topology.subnets:
            subnet_events = self._generate_subnet_events(subnet, event_count // len(topology.subnets))
            events.extend(subnet_events)
        
        # Generate internet-facing events
        for ip in topology.internet_facing_ips:
            internet_events = self._generate_internet_events(ip, event_count // len(topology.internet_facing_ips))
            events.extend(internet_events)
        
        return sorted(events, key=lambda x: x.timestamp)
    
    def export_logs(self, events: List[SecurityEvent], 
                   format: str = "json", output_path: Optional[str] = None) -> str:
        """Export logs in specified format."""
        if format == "json":
            return self._export_json(events, output_path)
        elif format == "csv":
            return self._export_csv(events, output_path)
        elif format == "syslog":
            return self._export_syslog(events, output_path)
        elif format == "cef":
            return self._export_cef(events, output_path)
        elif format == "leef":
            return self._export_leef(events, output_path)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _parse_duration(self, duration: str) -> int:
        """Parse duration string to hours."""
        if duration.endswith('h'):
            return int(duration[:-1])
        elif duration.endswith('d'):
            return int(duration[:-1]) * 24
        elif duration.endswith('m'):
            return int(duration[:-1]) / 60
        else:
            return int(duration)
    
    def _generate_tactic_events(self, threat_actor: ThreatActor, tactic: str, 
                              duration_hours: int, count: int) -> List[SecurityEvent]:
        """Generate events for a specific attack tactic."""
        events = []
        
        # Determine which log types to use for this tactic
        if tactic == 'initial_access':
            log_types = [LogType.WEB_ACCESS, LogType.IDS]
        elif tactic == 'execution':
            log_types = [LogType.ENDPOINT, LogType.IDS]
        elif tactic == 'lateral_movement':
            log_types = [LogType.IDS, LogType.ENDPOINT]
        elif tactic == 'exfiltration':
            log_types = [LogType.IDS, LogType.WEB_ACCESS]
        else:
            log_types = [LogType.IDS]
        
        # Generate events for each log type
        for log_type in log_types:
            generator = self.generators.get(log_type)
            if generator:
                tactic_events = generator.generate_events(count=count // len(log_types))
                # Set threat actor and tactic
                for event in tactic_events:
                    event.threat_actor = threat_actor
                    event.attack_tactic = tactic
                events.extend(tactic_events)
        
        return events
    
    def _add_correlation(self, events: List[SecurityEvent], 
                        correlation_strength: float, time_window_hours: float) -> List[SecurityEvent]:
        """Add correlation between events."""
        correlated_events = []
        
        # Group events by time windows
        time_windows = {}
        for event in events:
            window_key = int(event.timestamp.timestamp() // (time_window_hours * 3600))
            if window_key not in time_windows:
                time_windows[window_key] = []
            time_windows[window_key].append(event)
        
        # Add correlations within time windows
        for window_events in time_windows.values():
            if len(window_events) > 1 and random.random() < correlation_strength:
                # Create correlated events
                correlated_event = self._create_correlated_event(window_events)
                correlated_events.append(correlated_event)
        
        return correlated_events
    
    def _create_correlated_event(self, base_events: List[SecurityEvent]) -> SecurityEvent:
        """Create a correlated event from base events."""
        # Use the first event as template
        template = base_events[0]
        
        # Create correlated event
        correlated = SecurityEvent(
            log_type=template.log_type,
            severity=LogSeverity.HIGH,
            source=template.source,
            destination=template.destination,
            user=template.user,
            message=f"Correlated security event: {len(base_events)} related events detected",
            raw_data={
                'correlation_type': 'multi_event',
                'base_events': [e.id for e in base_events],
                'correlation_score': random.uniform(0.7, 1.0)
            },
            tags=['correlated', 'security', 'multi_event']
        )
        
        return correlated
    
    def _generate_subnet_events(self, subnet: str, count: int) -> List[SecurityEvent]:
        """Generate events for a specific subnet."""
        events = []
        
        # Generate internal network events
        for _ in range(count):
            # Randomly select log type
            log_type = random.choice([LogType.IDS, LogType.ENDPOINT])
            generator = self.generators.get(log_type)
            
            if generator:
                event = generator.generate_event()
                # Set subnet-specific IPs
                event.source.ip_address = self._generate_subnet_ip(subnet)
                event.destination.ip_address = self._generate_subnet_ip(subnet)
                events.append(event)
        
        return events
    
    def _generate_internet_events(self, ip: str, count: int) -> List[SecurityEvent]:
        """Generate internet-facing events."""
        events = []
        
        for _ in range(count):
            # Generate external-facing events
            log_type = random.choice([LogType.WEB_ACCESS, LogType.IDS])
            generator = self.generators.get(log_type)
            
            if generator:
                event = generator.generate_event()
                # Set internet-facing IP
                event.destination.ip_address = ip
                events.append(event)
        
        return events
    
    def _generate_subnet_ip(self, subnet: str) -> str:
        """Generate IP address within subnet."""
        import ipaddress
        import random
        network = ipaddress.IPv4Network(subnet)
        # Generate random IP within the network
        host_bits = 32 - network.prefixlen
        random_host = random.randint(1, (1 << host_bits) - 2)  # Avoid network and broadcast
        return str(ipaddress.IPv4Address(int(network.network_address) + random_host))
    
    def _export_json(self, events: List[SecurityEvent], output_path: Optional[str]) -> str:
        """Export events as JSON."""
        data = [event.dict() for event in events]
        
        if output_path:
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            return f"Exported {len(events)} events to {output_path}"
        else:
            return json.dumps(data, indent=2, default=str)
    
    def _export_csv(self, events: List[SecurityEvent], output_path: Optional[str]) -> str:
        """Export events as CSV."""
        import csv
        import io
        
        if not events:
            return "No events to export"
        
        # Get all field names
        fieldnames = set()
        for event in events:
            fieldnames.update(event.dict().keys())
        
        fieldnames = sorted(fieldnames)
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for event in events:
            writer.writerow(event.dict())
        
        csv_data = output.getvalue()
        
        if output_path:
            with open(output_path, 'w') as f:
                f.write(csv_data)
            return f"Exported {len(events)} events to {output_path}"
        else:
            return csv_data
    
    def _export_syslog(self, events: List[SecurityEvent], output_path: Optional[str]) -> str:
        """Export events as syslog format."""
        syslog_lines = []
        
        for event in events:
            # Format as syslog
            timestamp = event.timestamp.strftime("%b %d %H:%M:%S")
            hostname = event.source.hostname or event.source.ip_address
            severity = event.severity.upper()
            message = event.message
            
            syslog_line = f"<{severity}> {timestamp} {hostname} {message}"
            syslog_lines.append(syslog_line)
        
        syslog_data = "\n".join(syslog_lines)
        
        if output_path:
            with open(output_path, 'w') as f:
                f.write(syslog_data)
            return f"Exported {len(events)} events to {output_path}"
        else:
            return syslog_data
    
    def _export_cef(self, events: List[SecurityEvent], output_path: Optional[str]) -> str:
        """Export events as CEF format."""
        cef_lines = []
        
        for event in events:
            # Format as CEF
            timestamp = int(event.timestamp.timestamp() * 1000)
            hostname = event.source.hostname or event.source.ip_address
            severity = event.severity.upper()
            
            cef_line = f"CEF:0|CybersecurityLogGenerator|1.0|{event.log_type}|{event.id}|{event.message}|{severity}|{timestamp}|{hostname}"
            cef_lines.append(cef_line)
        
        cef_data = "\n".join(cef_lines)
        
        if output_path:
            with open(output_path, 'w') as f:
                f.write(cef_data)
            return f"Exported {len(events)} events to {output_path}"
        else:
            return cef_data
    
    def _export_leef(self, events: List[SecurityEvent], output_path: Optional[str]) -> str:
        """Export events as LEEF format."""
        leef_lines = []
        
        for event in events:
            # Format as LEEF
            timestamp = int(event.timestamp.timestamp() * 1000)
            hostname = event.source.hostname or event.source.ip_address
            
            leef_line = f"LEEF:1.0|CybersecurityLogGenerator|1.0|{event.log_type}|{event.id}|{event.message}|{timestamp}|{hostname}"
            leef_lines.append(leef_line)
        
        leef_data = "\n".join(leef_lines)
        
        if output_path:
            with open(output_path, 'w') as f:
                f.write(leef_data)
            return f"Exported {len(events)} events to {output_path}"
        else:
            return leef_data
