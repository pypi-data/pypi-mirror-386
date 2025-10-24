"""
Base generator class for all log generators.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import random
import ipaddress
from faker import Faker

from ..models import LogEvent, SecurityEvent, NetworkEndpoint, LogType, LogSeverity


class BaseLogGenerator(ABC):
    """Base class for all log generators."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.faker = Faker()
        self._setup_generators()
    
    def _setup_generators(self):
        """Setup internal generators and data sources."""
        pass
    
    @abstractmethod
    def generate_event(self, **kwargs) -> LogEvent:
        """Generate a single log event."""
        pass
    
    def generate_events(self, count: int, **kwargs) -> List[LogEvent]:
        """Generate multiple log events."""
        events = []
        for _ in range(count):
            events.append(self.generate_event(**kwargs))
        return events
    
    def generate_ip_address(self, network_type: str = "random") -> str:
        """Generate a realistic IP address."""
        if network_type == "internal":
            # Generate internal IP addresses
            internal_networks = [
                "10.0.0.0/8",
                "172.16.0.0/12", 
                "192.168.0.0/16"
            ]
            network = random.choice(internal_networks)
            # Generate random IP within the network
            net = ipaddress.IPv4Network(network)
            # Get random host bits
            host_bits = 32 - net.prefixlen
            random_host = random.randint(1, (1 << host_bits) - 2)  # Avoid network and broadcast
            return str(ipaddress.IPv4Address(int(net.network_address) + random_host))
        elif network_type == "external":
            # Generate external IP addresses (avoiding private ranges)
            while True:
                ip = self.faker.ipv4()
                if not ipaddress.IPv4Address(ip).is_private:
                    return ip
        else:
            # Random IP (could be internal or external)
            return self.faker.ipv4()
    
    def generate_port(self, protocol: str = "tcp") -> int:
        """Generate a realistic port number."""
        if protocol.lower() == "tcp":
            # Common TCP ports with weighted distribution
            common_ports = [80, 443, 22, 21, 25, 53, 110, 143, 993, 995, 587, 465]
            if random.random() < 0.7:  # 70% chance of common port
                return random.choice(common_ports)
            else:
                return random.randint(1024, 65535)
        elif protocol.lower() == "udp":
            common_udp_ports = [53, 67, 68, 69, 123, 161, 162, 514]
            if random.random() < 0.6:  # 60% chance of common UDP port
                return random.choice(common_udp_ports)
            else:
                return random.randint(1024, 65535)
        else:
            return random.randint(1, 65535)
    
    def generate_timestamp(self, start_time: Optional[datetime] = None, 
                          end_time: Optional[datetime] = None) -> datetime:
        """Generate a realistic timestamp."""
        if start_time is None:
            start_time = datetime.utcnow() - timedelta(hours=24)
        if end_time is None:
            end_time = datetime.utcnow()
        
        # Generate timestamp with realistic distribution
        time_diff = (end_time - start_time).total_seconds()
        random_seconds = random.randint(0, int(time_diff))
        return start_time + timedelta(seconds=random_seconds)
    
    def generate_severity(self, weights: Optional[Dict[str, float]] = None) -> LogSeverity:
        """Generate log severity with realistic distribution."""
        if weights is None:
            weights = {
                "low": 0.5,
                "medium": 0.3,
                "high": 0.15,
                "critical": 0.05
            }
        
        severities = list(weights.keys())
        probabilities = list(weights.values())
        return LogSeverity(random.choices(severities, weights=probabilities)[0])
    
    def generate_network_endpoint(self, network_type: str = "random") -> NetworkEndpoint:
        """Generate a network endpoint."""
        ip = self.generate_ip_address(network_type)
        port = self.generate_port()
        hostname = self.faker.hostname() if random.random() < 0.3 else None
        
        return NetworkEndpoint(
            ip_address=ip,
            port=port,
            hostname=hostname
        )
    
    def generate_user(self) -> str:
        """Generate a realistic username."""
        if random.random() < 0.7:
            # Realistic username based on name
            first_name = self.faker.first_name().lower()
            last_name = self.faker.last_name().lower()
            return f"{first_name}.{last_name}"
        else:
            # System or service account
            system_accounts = ["admin", "service", "system", "root", "administrator"]
            return random.choice(system_accounts)
    
    def generate_process(self) -> str:
        """Generate a realistic process name."""
        common_processes = [
            "explorer.exe", "chrome.exe", "firefox.exe", "notepad.exe",
            "winlogon.exe", "svchost.exe", "lsass.exe", "csrss.exe",
            "services.exe", "smss.exe", "system", "kernel"
        ]
        return random.choice(common_processes)
