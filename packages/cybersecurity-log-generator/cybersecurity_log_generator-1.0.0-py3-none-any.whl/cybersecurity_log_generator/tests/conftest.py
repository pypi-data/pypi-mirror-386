"""
Pytest configuration and fixtures.
"""

import pytest
from cybersecurity_log_generator.core.generator import LogGenerator
from cybersecurity_log_generator.core.enhanced_generator import EnhancedLogGenerator


@pytest.fixture
def basic_generator():
    """Fixture for basic log generator."""
    return LogGenerator()


@pytest.fixture
def enhanced_generator():
    """Fixture for enhanced log generator."""
    return EnhancedLogGenerator()


@pytest.fixture
def sample_logs():
    """Fixture for sample log data."""
    return [
        {
            "timestamp": "2024-01-01T00:00:00Z",
            "event_type": "login",
            "severity": "INFO",
            "source": "auth_server",
            "user": "test_user"
        },
        {
            "timestamp": "2024-01-01T00:01:00Z",
            "event_type": "failed_login",
            "severity": "WARNING",
            "source": "auth_server",
            "user": "test_user"
        }
    ]
