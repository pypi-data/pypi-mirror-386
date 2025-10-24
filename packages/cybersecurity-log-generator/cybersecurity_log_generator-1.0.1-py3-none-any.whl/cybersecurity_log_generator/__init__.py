"""
Cybersecurity Log Generator

A comprehensive Python package for generating synthetic cybersecurity logs
across all 24 cyberdefense pillars with realistic attack patterns and threat intelligence.
"""

from .core.generator import LogGenerator
from .core.enhanced_generator import EnhancedLogGenerator
from .core.models import LogType, ThreatActor, CyberdefensePillar

__version__ = "1.0.0"
__author__ = "Cybersecurity Log Generator Team"
__email__ = "support@cybersecurity-log-generator.com"
__description__ = "Generate synthetic cybersecurity logs for testing and analysis"

__all__ = [
    "LogGenerator",
    "EnhancedLogGenerator", 
    "LogType",
    "ThreatActor",
    "CyberdefensePillar"
]