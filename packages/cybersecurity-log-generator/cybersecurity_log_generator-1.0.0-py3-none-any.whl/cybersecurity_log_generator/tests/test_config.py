"""
Tests for configuration management.
"""

import pytest
import os
import tempfile
from cybersecurity_log_generator.config import GeneratorConfig, load_config, get_default_config


def test_default_config():
    """Test default configuration."""
    config = get_default_config()
    assert config.default_count == 100
    assert config.default_time_range == "24h"
    assert config.output_format == "json"
    assert config.include_metadata is True


def test_config_validation():
    """Test configuration validation."""
    config = GeneratorConfig(
        default_count=50,
        default_time_range="12h",
        output_format="csv"
    )
    assert config.default_count == 50
    assert config.default_time_range == "12h"
    assert config.output_format == "csv"


def test_config_from_env():
    """Test configuration from environment variables."""
    # Set environment variables
    os.environ["CYBERSECURITY_LOG_DEFAULT_COUNT"] = "200"
    os.environ["CYBERSECURITY_LOG_DEFAULT_TIME_RANGE"] = "48h"
    os.environ["CYBERSECURITY_LOG_OUTPUT_FORMAT"] = "csv"
    
    config = load_config()
    assert config.default_count == 200
    assert config.default_time_range == "48h"
    assert config.output_format == "csv"
    
    # Clean up
    del os.environ["CYBERSECURITY_LOG_DEFAULT_COUNT"]
    del os.environ["CYBERSECURITY_LOG_DEFAULT_TIME_RANGE"]
    del os.environ["CYBERSECURITY_LOG_OUTPUT_FORMAT"]


def test_config_from_file():
    """Test configuration from file."""
    config_data = {
        "default_count": 150,
        "default_time_range": "36h",
        "output_format": "json",
        "include_metadata": False
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        import yaml
        yaml.dump(config_data, f)
        config_file = f.name
    
    try:
        config = load_config(config_file)
        assert config.default_count == 150
        assert config.default_time_range == "36h"
        assert config.output_format == "json"
        assert config.include_metadata is False
    finally:
        os.unlink(config_file)


def test_config_merge():
    """Test configuration merging (file + env)."""
    config_data = {
        "default_count": 100,
        "default_time_range": "24h"
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        import yaml
        yaml.dump(config_data, f)
        config_file = f.name
    
    # Set environment variable to override file config
    os.environ["CYBERSECURITY_LOG_DEFAULT_COUNT"] = "300"
    
    try:
        config = load_config(config_file)
        assert config.default_count == 300  # From env
        assert config.default_time_range == "24h"  # From file
    finally:
        os.unlink(config_file)
        del os.environ["CYBERSECURITY_LOG_DEFAULT_COUNT"]
