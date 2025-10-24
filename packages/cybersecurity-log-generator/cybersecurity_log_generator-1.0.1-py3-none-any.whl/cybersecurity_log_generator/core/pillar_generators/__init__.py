"""
Pillar generators module.

This module contains specialized generators for each of the 24 cyberdefense pillars,
providing realistic attack patterns and security events for comprehensive testing.
"""

# Import only the generators that actually exist
from .base_pillar_generator import BasePillarGenerator
from .siem_logs_generator import SIEMLogsGenerator

# Try to import other generators if they exist
try:
    from .authentication_generator import AuthenticationGenerator
except ImportError:
    AuthenticationGenerator = None

try:
    from .network_security_generator import NetworkSecurityGenerator
except ImportError:
    NetworkSecurityGenerator = None

try:
    from .endpoint_security_generator import EndpointSecurityGenerator
except ImportError:
    EndpointSecurityGenerator = None

try:
    from .cloud_security_generator import CloudSecurityGenerator
except ImportError:
    CloudSecurityGenerator = None

# Only include generators that exist
__all__ = ["BasePillarGenerator", "SIEMLogsGenerator"]

if AuthenticationGenerator:
    __all__.append("AuthenticationGenerator")
if NetworkSecurityGenerator:
    __all__.append("NetworkSecurityGenerator")
if EndpointSecurityGenerator:
    __all__.append("EndpointSecurityGenerator")
if CloudSecurityGenerator:
    __all__.append("CloudSecurityGenerator")