"""
Web Access log generator.
Enhanced version with realistic web application security events.
"""

import random
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from .base import BaseLogGenerator
from ..models import LogEvent, SecurityEvent, LogType, LogSeverity, AttackTactic


class WebAccessLogGenerator(BaseLogGenerator):
    """Advanced web access log generator with security events."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._setup_web_patterns()
    
    def _setup_web_patterns(self):
        """Setup web application patterns and security events."""
        self.http_methods = {
            'GET': 0.6, 'POST': 0.25, 'PUT': 0.05, 'DELETE': 0.03,
            'HEAD': 0.03, 'OPTIONS': 0.02, 'PATCH': 0.02
        }
        
        self.status_codes = {
            '200': 0.7, '201': 0.05, '204': 0.05, '301': 0.05,
            '302': 0.05, '304': 0.05, '400': 0.02, '401': 0.01,
            '403': 0.01, '404': 0.02, '500': 0.01
        }
        
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59'
        ]
        
        self.security_events = {
            'sql_injection': {
                'severity': 'critical',
                'description': 'SQL injection attempt detected',
                'tactic': AttackTactic.INITIAL_ACCESS,
                'weight': 0.1
            },
            'xss_attack': {
                'severity': 'high',
                'description': 'Cross-site scripting attempt',
                'tactic': AttackTactic.INITIAL_ACCESS,
                'weight': 0.1
            },
            'directory_traversal': {
                'severity': 'high',
                'description': 'Directory traversal attempt',
                'tactic': AttackTactic.INITIAL_ACCESS,
                'weight': 0.05
            },
            'file_upload_attack': {
                'severity': 'high',
                'description': 'Malicious file upload attempt',
                'tactic': AttackTactic.INITIAL_ACCESS,
                'weight': 0.05
            },
            'brute_force_login': {
                'severity': 'medium',
                'description': 'Brute force login attempt',
                'tactic': AttackTactic.CREDENTIAL_ACCESS,
                'weight': 0.15
            },
            'suspicious_request': {
                'severity': 'medium',
                'description': 'Suspicious request pattern',
                'tactic': AttackTactic.RECONNAISSANCE,
                'weight': 0.2
            }
        }
        
        self.resource_patterns = [
            '/api/users', '/api/products', '/api/orders', '/api/auth',
            '/dashboard', '/admin', '/login', '/logout', '/profile',
            '/search', '/upload', '/download', '/reports'
        ]
    
    def generate_event(self, **kwargs) -> SecurityEvent:
        """Generate a single web access event."""
        # Determine if this is a security event
        is_security_event = random.random() < 0.1  # 10% chance of security event
        
        if is_security_event:
            return self._generate_security_event(**kwargs)
        else:
            return self._generate_normal_event(**kwargs)
    
    def _generate_security_event(self, **kwargs) -> SecurityEvent:
        """Generate a security event."""
        # Select security event type
        event_types = list(self.security_events.keys())
        weights = [self.security_events[et]['weight'] for et in event_types]
        event_type = random.choices(event_types, weights=weights)[0]
        
        event_info = self.security_events[event_type]
        
        # Generate source and destination
        source = self.generate_network_endpoint("external")
        destination = self.generate_network_endpoint("internal")
        
        # Generate HTTP method and resource
        method = random.choices(list(self.http_methods.keys()), 
                              weights=list(self.http_methods.values()))[0]
        
        resource = self._generate_malicious_resource(event_type)
        
        # Generate user agent (might be suspicious)
        user_agent = self._generate_suspicious_user_agent() if random.random() < 0.3 else random.choice(self.user_agents)
        
        # Generate status code (likely error for security events)
        status_code = random.choice(['400', '401', '403', '404', '500'])
        
        # Create event message
        message = f"{method} {resource} - {status_code} - {event_info['description']}"
        
        # Generate raw data
        raw_data = {
            'method': method,
            'resource': resource,
            'status_code': status_code,
            'user_agent': user_agent,
            'referrer': self._generate_referrer(),
            'bytes_sent': random.randint(100, 10000),
            'response_time': random.uniform(0.1, 5.0),
            'security_event': True,
            'event_type': event_type
        }
        
        return SecurityEvent(
            log_type=LogType.WEB_ACCESS,
            severity=LogSeverity(event_info['severity']),
            source=source,
            destination=destination,
            user=self.generate_user(),
            message=message,
            raw_data=raw_data,
            attack_tactic=event_info['tactic'],
            attack_technique=event_type,
            confidence_score=random.uniform(0.8, 1.0),
            false_positive_probability=random.uniform(0.0, 0.05),
            tags=['security', 'web', event_type]
        )
    
    def _generate_normal_event(self, **kwargs) -> SecurityEvent:
        """Generate a normal web access event."""
        source = self.generate_network_endpoint("internal")
        destination = self.generate_network_endpoint("internal")
        
        # Generate HTTP method and resource
        method = random.choices(list(self.http_methods.keys()), 
                              weights=list(self.http_methods.values()))[0]
        
        resource = random.choice(self.resource_patterns)
        
        # Generate status code
        status_code = random.choices(list(self.status_codes.keys()), 
                                   weights=list(self.status_codes.values()))[0]
        
        # Generate user agent
        user_agent = random.choice(self.user_agents)
        
        # Create event message
        message = f"{method} {resource} - {status_code}"
        
        # Generate raw data
        raw_data = {
            'method': method,
            'resource': resource,
            'status_code': status_code,
            'user_agent': user_agent,
            'referrer': self._generate_referrer(),
            'bytes_sent': random.randint(100, 10000),
            'response_time': random.uniform(0.1, 2.0),
            'security_event': False
        }
        
        return SecurityEvent(
            log_type=LogType.WEB_ACCESS,
            severity=LogSeverity.LOW,
            source=source,
            destination=destination,
            user=self.generate_user(),
            message=message,
            raw_data=raw_data,
            tags=['normal', 'web']
        )
    
    def _generate_malicious_resource(self, event_type: str) -> str:
        """Generate malicious resource paths based on attack type."""
        if event_type == 'sql_injection':
            payloads = [
                "/api/users?id=1' OR '1'='1",
                "/search?q=admin' UNION SELECT * FROM users--",
                "/api/products?id=1; DROP TABLE users--"
            ]
            return random.choice(payloads)
        elif event_type == 'xss_attack':
            payloads = [
                "/search?q=<script>alert('xss')</script>",
                "/api/comment?text=<img src=x onerror=alert('xss')>",
                "/profile?name=<script>document.location='http://evil.com'</script>"
            ]
            return random.choice(payloads)
        elif event_type == 'directory_traversal':
            payloads = [
                "/../../etc/passwd",
                "/....//....//....//etc/passwd",
                "/api/../../etc/shadow"
            ]
            return random.choice(payloads)
        elif event_type == 'file_upload_attack':
            payloads = [
                "/upload/malware.php",
                "/api/upload/backdoor.jsp",
                "/files/shell.asp"
            ]
            return random.choice(payloads)
        else:
            return random.choice(self.resource_patterns)
    
    def _generate_suspicious_user_agent(self) -> str:
        """Generate suspicious user agents."""
        suspicious_agents = [
            'sqlmap/1.0-dev',
            'nikto/2.1.6',
            'nmap/7.80',
            'curl/7.68.0',
            'wget/1.20.3',
            'python-requests/2.25.1',
            'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
            'Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)'
        ]
        return random.choice(suspicious_agents)
    
    def _generate_referrer(self) -> str:
        """Generate referrer URL."""
        if random.random() < 0.3:
            return '-'
        else:
            return f"https://{self.faker.domain_name()}{random.choice(self.resource_patterns)}"
